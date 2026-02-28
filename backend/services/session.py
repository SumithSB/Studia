"""Session state and history with context window management."""

import json
from datetime import datetime

from config import BACKEND_ROOT, LOG_SESSIONS, MAX_HISTORY_EXCHANGES

SESSIONS_DIR = BACKEND_ROOT / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)

_sessions: dict[str, dict] = {}


def get_session(session_id: str) -> dict:
    """Get or create session state."""
    if session_id not in _sessions:
        _sessions[session_id] = {
            "history": [],
            "summary": None,
            "research_context": None,
            "company": None,
        }
    return _sessions[session_id]


def add_exchange(session_id: str, role: str, content: str) -> None:
    """Add user/assistant exchange to history."""
    session = get_session(session_id)
    session["history"].append({"role": role, "content": content})


def get_history(session_id: str) -> list[dict]:
    """Return full exchange history for API."""
    return get_session(session_id).get("history", [])


def get_messages_for_llm(
    session_id: str,
    summarise_fn=None,
) -> list[dict]:
    """Get message list for LLM, applying context window management."""
    session = get_session(session_id)
    history = session["history"].copy()
    summary = session.get("summary")

    if len(history) <= MAX_HISTORY_EXCHANGES:
        return [{"role": h["role"], "content": h["content"]} for h in history]

    if summarise_fn and not summary:
        old = history[:-10]
        summary = summarise_fn(old)
        session["summary"] = summary
        history = history[-10:]

    messages = []
    if summary:
        messages.append({
            "role": "system",
            "content": f"[Previous conversation summary]: {summary}",
        })
    for h in history:
        messages.append({"role": h["role"], "content": h["content"]})
    return messages


def set_research_context(session_id: str, company: str, context: str) -> None:
    """Store company research context for this session."""
    session = get_session(session_id)
    session["research_context"] = context
    session["company"] = company


def get_research_context(session_id: str) -> tuple[str | None, str | None]:
    """Return (company, research_context) if set."""
    s = get_session(session_id)
    return s.get("company"), s.get("research_context")


def log_session(session_id: str) -> None:
    """Write session to file if logging enabled."""
    if not LOG_SESSIONS:
        return
    session = get_session(session_id)
    path = SESSIONS_DIR / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"session_id": session_id, "history": session["history"]}, f, indent=2)
