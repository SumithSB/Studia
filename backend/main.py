"""FastAPI app for Studia."""

import json
from fastapi import FastAPI, File, HTTPException, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel

from audio import stt, tts
from config import AGENT_MODE, TTS_ENABLED
from core import agent, context, llm
from services import profile_builder, research, session, tracker


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class TtsRequest(BaseModel):
    text: str


app = FastAPI(title="Studia")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _sse_event(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


def _stream_response(messages: list[dict], session_id: str):
    """Unified stream: yields (token, done, tool_info)."""
    if AGENT_MODE:
        yield from agent.agent_stream(messages, session_id)
    else:
        for token, done, _ in llm.stream_completion(messages):
            yield (token, done, None)


@app.post("/tts")
def tts_endpoint(req: TtsRequest):
    """Generate speech from text and return audio bytes for client playback."""
    if not TTS_ENABLED:
        raise HTTPException(503, "TTS is disabled.")
    text = (req.text or "").strip()
    if not text:
        raise HTTPException(400, "Text is required.")
    audio_bytes = tts.speak_to_bytes(text)
    if not audio_bytes:
        raise HTTPException(500, "Could not generate speech.")
    return Response(
        content=audio_bytes,
        media_type="audio/wav",
    )


@app.get("/profile/status")
def profile_status_endpoint():
    """Return whether profile.json exists (for onboarding routing)."""
    return {"exists": context.profile_exists()}


@app.post("/profile/from-uploads")
async def profile_from_uploads_endpoint(
    resumes: list[UploadFile] = File(default=[]),
    linkedin: UploadFile | None = File(default=None),
):
    """Build profile.json from resume files (PDF, DOCX, TXT) and optional LinkedIn ZIP."""
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
        profile = profile_builder.build_profile_from_uploads(resume_files, linkedin_bytes)
        return {"ok": True, "profile": profile}
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Could not create profile: {e}")


@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    """Stream LLM response via SSE."""
    if not context.profile_exists():
        raise HTTPException(503, "Profile not set. Complete onboarding (upload resumes and LinkedIn data) first.")
    message, session_id = req.message, req.session_id

    def generate():
        session.add_exchange(session_id, "user", message)
        company, research_ctx = session.get_research_context(session_id)
        sys_prompt = context.build_system_prompt(
            research_context=research_ctx,
            company=company,
        )
        messages = [
            {"role": "system", "content": sys_prompt},
            *[
                {"role": h["role"], "content": h["content"]}
                for h in session.get_messages_for_llm(session_id, summarise_fn=llm.summarise_history)
            ],
        ]
        full_response = []
        for token, done, tool_info in _stream_response(messages, session_id):
            if tool_info:
                yield _sse_event({"tool_call": tool_info.get("tool"), "args": tool_info.get("args", {})})
            if token:
                full_response.append(token)
                yield _sse_event({"token": token})
            if done:
                content = "".join(full_response)
                if content:
                    session.add_exchange(session_id, "assistant", content)
                if TTS_ENABLED and content:
                    tts.speak(content)
                yield _sse_event({"done": True})
                session.log_session(session_id)
                return

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/voice")
def voice_endpoint(audio: UploadFile = ..., session_id: str = Form("default")):
    """Transcribe WAV, then stream LLM response via SSE."""
    if not context.profile_exists():
        raise HTTPException(503, "Profile not set. Complete onboarding (upload resumes and LinkedIn data) first.")
    audio_bytes = audio.file.read()
    transcript = stt.transcribe(audio_bytes)
    session.add_exchange(session_id, "user", transcript)

    def generate():
        yield _sse_event({"transcript": transcript, "session_id": session_id})
        company, research_ctx = session.get_research_context(session_id)
        sys_prompt = context.build_system_prompt(
            research_context=research_ctx,
            company=company,
        )
        messages = [
            {"role": "system", "content": sys_prompt},
            *[
                {"role": h["role"], "content": h["content"]}
                for h in session.get_messages_for_llm(session_id, summarise_fn=llm.summarise_history)
            ],
        ]
        full_response = []
        for token, done, tool_info in _stream_response(messages, session_id):
            if tool_info:
                yield _sse_event({"tool_call": tool_info.get("tool"), "args": tool_info.get("args", {})})
            if token:
                full_response.append(token)
                yield _sse_event({"token": token})
            if done:
                content = "".join(full_response)
                if content:
                    session.add_exchange(session_id, "assistant", content)
                if TTS_ENABLED and content:
                    tts.speak(content)
                yield _sse_event({"done": True})
                session.log_session(session_id)
                return

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/progress")
def progress_endpoint():
    """Return weak/strong topics and suggested next."""
    return tracker.get_progress_summary()


@app.post("/research")
def research_endpoint(type: str = Form(...), value: str = Form(...)):
    """Company or JD research."""
    if type == "company":
        result = research.research_company(value)
        return result
    if type == "jd":
        result = research.parse_jd(value)
        return result
    return {"summary": "", "gap_analysis": "", "topics_to_prioritise": []}


@app.get("/session/history")
def session_history_endpoint(session_id: str = "default"):
    """Return conversation history for session."""
    return session.get_history(session_id)
