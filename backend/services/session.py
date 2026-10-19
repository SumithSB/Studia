"""Session state and history with context window management. Persisted via DB repository."""

from config import LOG_SESSIONS, MAX_HISTORY_EXCHANGES
from db import get_session as _db_get, save_session as _db_save


def ensure_session(session_id: str, profile_id: str, target_role: str | None = None) -> None:
    """Create or update session with profile_id and target_role. Call at start of chat."""
    s = _db_get(session_id)
    if s is None:
        _db_save(session_id, profile_id, [], target_role=target_role)
    else:
        _db_save(
            session_id,
            profile_id,
            s["history"],
            target_role=target_role or s.get("target_role"),
            research_context=s.get("research_context"),
            company=s.get("company"),
            summary=s.get("summary"),
        )


def get_session(session_id: str) -> dict:
    """Get session state from DB. Creates in-memory placeholder if not in DB (for backward compat)."""
    s = _db_get(session_id)
    if s is not None:
        return {
            "history": s["history"],
            "summary": s.get("summary"),
            "research_context": s.get("research_context"),
            "company": s.get("company"),
            "profile_id": s.get("profile_id"),
            "target_role": s.get("target_role"),
        }
    return {
        "history": [],
        "summary": None,
        "research_context": None,
        "company": None,
        "profile_id": None,
        "target_role": None,
    }


def add_exchange(session_id: str, role: str, content: str) -> None:
    """Add user/assistant exchange to history and persist."""
    s = _db_get(session_id)
    if s is None:
        _db_save(session_id, "", [{"role": role, "content": content}])
        return
    history = s["history"] + [{"role": role, "content": content}]
    _db_save(
        session_id,
        s["profile_id"],
        history,
        target_role=s.get("target_role"),
        research_context=s.get("research_context"),
        company=s.get("company"),
        summary=s.get("summary"),
    )


def get_history(session_id: str) -> list[dict]:
    """Return full exchange history for API."""
    s = _db_get(session_id)
    return s["history"] if s else []


# Turns kept verbatim after a summary. Older turns are folded into the summary.
_RECENT_TAIL = 10


def get_messages_for_llm(
    session_id: str,
    summarise_fn=None,
) -> list[dict]:
    """Get message list for LLM, applying context window management.

    The stored summary is always included, including after history has been
    trimmed back under the cap. When history grows past the cap again, the
    overflow is summarised into the existing summary and only the recent tail
    is kept. A failed summary leaves the stored history unchanged.
    """
    s = _db_get(session_id)
    if s is None:
        return []
    history = list(s["history"])
    summary = s.get("summary") or None

    if len(history) > MAX_HISTORY_EXCHANGES and summarise_fn:
        tail_len = min(_RECENT_TAIL, MAX_HISTORY_EXCHANGES)
        if tail_len <= 0:
            tail, overflow = [], history
        else:
            tail, overflow = history[-tail_len:], history[:-tail_len]
        if overflow:
            to_summarise = list(overflow)
            if summary:
                # Passed as a system turn so the previous summary is folded in
                # rather than treated as a new user message.
                to_summarise.insert(0, {
                    "role": "system",
                    "content": f"[Previous conversation summary]: {summary}",
                })
            new_summary = summarise_fn(to_summarise)
            if new_summary:
                summary = new_summary
                _db_save(
                    session_id,
                    s["profile_id"],
                    tail,
                    target_role=s.get("target_role"),
                    research_context=s.get("research_context"),
                    company=s.get("company"),
                    summary=summary,
                )
                history = tail

    messages = []
    if summary:
        messages.append({
            "role": "system",
            "content": f"[Previous conversation summary]: {summary}",
        })
    messages.extend({"role": h["role"], "content": h["content"]} for h in history)
    return messages


def set_research_context(session_id: str, company: str, context: str) -> None:
    """Store company research context for this session."""
    s = _db_get(session_id)
    if s is None:
        return
    _db_save(
        session_id,
        s["profile_id"],
        s["history"],
        target_role=s.get("target_role"),
        research_context=context,
        company=company,
        summary=s.get("summary"),
    )


def get_research_context(session_id: str) -> tuple[str | None, str | None]:
    """Return (company, research_context) if set."""
    s = _db_get(session_id)
    if s is None:
        return None, None
    return s.get("company"), s.get("research_context")


def log_session(session_id: str) -> None:
    """No-op when using DB (history already persisted). Kept for API compatibility."""
    if not LOG_SESSIONS:
        return
    # Optional: write a copy to sessions/ for backup/debug
    pass
