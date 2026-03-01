"""FastAPI app for Studia."""

import json
import logging
from pathlib import Path

import requests
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import AGENT_MODE, BACKEND_ROOT
from core import agent, context, llm
from db import get_default_profile_id, get_profile, list_profiles, set_default_profile_id
from services import profile_builder, research, session, tracker

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    profile_id: str = ""
    target_role: str | None = None


app = FastAPI(title="Studia")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log request method/path and response status."""
    response = await call_next(request)
    logger.info("%s %s %s", request.method, request.url.path, response.status_code)
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Log unhandled exceptions and return generic 500 (no stack trace in response)."""
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "An internal error occurred."})


def _sse_event(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


def _stream_response(messages: list[dict], session_id: str, setup_mode: bool = False):
    """Unified stream: yields (token, done, tool_info). setup_mode: no profile yet, use setup tools."""
    if AGENT_MODE:
        yield from agent.agent_stream(messages, session_id, setup_mode=setup_mode)
    else:
        for token, done, _ in llm.stream_completion(messages):
            yield (token, done, None)


@app.get("/health")
def health_endpoint():
    """Health check for orchestration. Returns 200 and db status."""
    from db import health_check
    return {"status": "ok", "db": "ok" if health_check() else "error"}


@app.get("/profile/status")
def profile_status_endpoint():
    """Return whether any profile exists, default_profile_id, and list of profiles."""
    exists = context.profile_exists()
    default_id = get_default_profile_id() if exists else None
    profiles = list_profiles() if exists else []
    if exists and not default_id and profiles:
        set_default_profile_id(profiles[0]["id"])
        default_id = profiles[0]["id"]
    return {
        "exists": exists,
        "default_profile_id": default_id,
        "profiles": [{"id": p["id"], "label": p["label"]} for p in profiles],
    }


@app.post("/profile/from-uploads")
async def profile_from_uploads_endpoint(
    resumes: list[UploadFile] = File(default=[]),
    linkedin: UploadFile | None = File(default=None),
    label: str = Form(""),
):
    """Build profile from resume files (PDF, DOCX, TXT) and optional LinkedIn ZIP. Saves to DB."""
    if not resumes and not linkedin:
        raise HTTPException(400, "Upload at least one resume or a LinkedIn export ZIP.")

    resume_files = []
    total = 0
    for f in resumes:
        data = await f.read()
        total += len(data)
        if total > profile_builder.MAX_TOTAL_BYTES:
            raise HTTPException(400, "Total upload size exceeded.")
        fn = f.filename or "resume"
        if not fn.lower().endswith((".pdf", ".docx", ".txt")):
            raise HTTPException(400, f"Unsupported resume type: {fn}")
        resume_files.append((fn, data))

    linkedin_bytes = None
    if linkedin and linkedin.filename and linkedin.filename.lower().endswith(".zip"):
        linkedin_bytes = await linkedin.read()
        if len(linkedin_bytes) > profile_builder.MAX_FILE_BYTES:
            raise HTTPException(400, "LinkedIn ZIP too large.")

    try:
        profile, profile_id = profile_builder.build_profile_from_uploads(
            resume_files, linkedin_bytes, profile_id=None, label=label or "Profile"
        )
        if not get_default_profile_id():
            set_default_profile_id(profile_id)
        return {"ok": True, "profile": profile, "profile_id": profile_id}
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.exception("Profile creation failed")
        raise HTTPException(500, "Could not create profile.")


def _validate_profile_id(profile_id: str) -> None:
    """Raise HTTPException 404 if profile does not exist."""
    if not get_profile(profile_id):
        raise HTTPException(404, "Profile not found")


@app.post("/profile/default")
def set_default_profile_endpoint(profile_id: str = Form(...)):
    """Set the default profile for new sessions."""
    _validate_profile_id(profile_id)
    set_default_profile_id(profile_id)
    return {"ok": True}


def _chat_stream(message: str, session_id: str, profile_id: str, target_role: str | None, setup_mode: bool):
    """Inner generator for chat SSE. Caller must have already ensured session and added user message."""
    session.add_exchange(session_id, "user", message)
    if setup_mode:
        sys_prompt = context.build_setup_system_prompt()
    else:
        company, research_ctx = session.get_research_context(session_id)
        sys_prompt = context.build_system_prompt(
            profile_id=profile_id,
            research_context=research_ctx,
            company=company,
            target_role=target_role,
        )
    messages = [
        {"role": "system", "content": sys_prompt},
        *[
            {"role": h["role"], "content": h["content"]}
            for h in session.get_messages_for_llm(session_id, summarise_fn=llm.summarise_history)
        ],
    ]
    full_response = []
    try:
        for token, done, tool_info in _stream_response(messages, session_id, setup_mode=setup_mode):
            if tool_info:
                yield _sse_event({"tool_call": tool_info.get("tool"), "args": tool_info.get("args", {})})
            if token:
                full_response.append(token)
                yield _sse_event({"token": token})
            if done:
                content = "".join(full_response)
                if content:
                    session.add_exchange(session_id, "assistant", content)
                yield _sse_event({"done": True})
                session.log_session(session_id)
                return
    except requests.exceptions.Timeout:
        yield _sse_event({"error": "The model took too long to respond. Try a shorter prompt or increase OLLAMA_TIMEOUT in .env."})
        yield _sse_event({"done": True})


@app.post("/chat")
async def chat_endpoint(request: Request):
    """Stream LLM response via SSE. Accepts JSON or multipart (with optional files). When no profiles exist (setup mode), profile_id is optional."""
    content_type = (request.headers.get("content-type") or "").lower()
    message = ""
    session_id = "default"
    profile_id = ""
    target_role = None
    files_content: list[tuple[str, bytes]] = []

    if "multipart/form-data" in content_type:
        form = await request.form()
        message = (form.get("message") or "").strip()
        session_id = (form.get("session_id") or "default").strip() or "default"
        profile_id = (form.get("profile_id") or "").strip()
        tr = form.get("target_role")
        target_role = tr.strip() if (tr and isinstance(tr, str)) else None
        uploads = form.getlist("files")
        if not isinstance(uploads, list):
            uploads = [uploads] if uploads else []
        for f in uploads:
            if hasattr(f, "read") and hasattr(f, "filename"):
                data = await f.read()
                if data and getattr(f, "filename", None):
                    files_content.append((f.filename, data))
    else:
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(400, "Invalid JSON body")
        req = ChatRequest(**body)
        message = req.message
        session_id = req.session_id
        profile_id = req.profile_id or ""
        target_role = req.target_role

    # Append extracted text from attached files to message
    if files_content:
        extracted = profile_builder.extract_text_from_files(files_content)
        if extracted:
            message = (message or "").strip()
            if message:
                message += "\n\n[Attached documents]\n" + extracted
            else:
                message = "[Attached documents]\n" + extracted

    setup_mode = not context.profile_exists()

    # If no profile and user sent files: create profile from files, then run turn in normal mode
    if setup_mode and files_content:
        try:
            profile, new_id = profile_builder.build_profile_from_uploads(
                files_content, None, profile_id=None, label="Profile"
            )
            if not get_default_profile_id():
                set_default_profile_id(new_id)
            session.ensure_session(session_id, new_id, target_role)
            profile_id = new_id
            setup_mode = False
            if not message.strip():
                message = "I've added my resume."
        except ValueError as e:
            raise HTTPException(400, str(e))
        except Exception:
            logger.exception("Profile creation from chat files failed")
            raise HTTPException(500, "Could not create profile from attachments.")

    if setup_mode:
        profile_id = ""
        session.ensure_session(session_id, profile_id, target_role)
    else:
        profile_id = profile_id or get_default_profile_id()
        if not profile_id:
            raise HTTPException(400, "profile_id required when no default profile is set.")
        _validate_profile_id(profile_id)
        session.ensure_session(session_id, profile_id, target_role)

    return StreamingResponse(
        _chat_stream(message, session_id, profile_id, target_role, setup_mode),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/progress")
def progress_endpoint(profile_id: str | None = None):
    """Return weak/strong topics and suggested next for profile. Uses default profile if profile_id omitted."""
    pid = profile_id or get_default_profile_id()
    if not pid:
        return {"weak": [], "strong": [], "suggested_next": "", "suggested_next_label": ""}
    _validate_profile_id(pid)
    return tracker.get_progress_summary(pid)


@app.post("/research")
def research_endpoint(type: str = Form(...), value: str = Form(...), profile_id: str = Form("")):
    """Company or JD research. profile_id required for JD for gap analysis."""
    if type == "company":
        return research.research_company(value)
    if type == "jd":
        pid = (profile_id or "").strip() or get_default_profile_id()
        if not pid:
            return {"summary": "", "gap_analysis": "Set a profile first.", "topics_to_prioritise": []}
        _validate_profile_id(pid)
        return research.parse_jd(value, pid)
    return {"summary": "", "gap_analysis": "", "topics_to_prioritise": []}


@app.get("/session/history")
def session_history_endpoint(session_id: str = "default"):
    """Return conversation history for session."""
    return session.get_history(session_id)


# Mount web UI after all API routes so /health, /chat etc. take precedence
web_dir = BACKEND_ROOT.parent / "web"
if web_dir.exists():
    app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="web")
