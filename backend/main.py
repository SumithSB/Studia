"""FastAPI app for Studia."""

import json
from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

import context
import session
import tracker
import research
import llm
import stt
import tts
from config import TTS_ENABLED

app = FastAPI(title="Studia")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _sse_event(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    """Stream LLM response via SSE."""
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
                for h in session.get_messages_for_llm(session_id)
            ],
        ]
        full_response = []
        for token, done, _ in llm.stream_completion(messages):
            if token:
                full_response.append(token)
                yield _sse_event({"token": token})
            if done:
                content = "".join(full_response)
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
                for h in session.get_messages_for_llm(session_id)
            ],
        ]
        full_response = []
        for token, done, _ in llm.stream_completion(messages):
            if token:
                full_response.append(token)
                yield _sse_event({"token": token})
            if done:
                content = "".join(full_response)
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
