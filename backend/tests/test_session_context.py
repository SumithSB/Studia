"""Context-window behaviour for chat history. No database or LLM."""

from core import llm
from services import session as session_mod


def _stored(history, summary=None):
    return {
        "history": history,
        "summary": summary,
        "profile_id": "p1",
        "target_role": "backend",
        "research_context": None,
        "company": None,
    }


def _patch_db(monkeypatch, stored):
    saved = {}

    def get_session(_session_id):
        return stored

    def save_session(_session_id, profile_id, history, **kwargs):
        saved["profile_id"] = profile_id
        saved["history"] = history
        saved["summary"] = kwargs.get("summary")
        stored["history"] = history
        stored["summary"] = kwargs.get("summary")

    monkeypatch.setattr(session_mod, "_db_get", get_session)
    monkeypatch.setattr(session_mod, "_db_save", save_session)
    return saved


def test_short_history_is_returned_unchanged(monkeypatch):
    monkeypatch.setattr(session_mod, "MAX_HISTORY_EXCHANGES", 4)
    history = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]
    _patch_db(monkeypatch, _stored(history))

    messages = session_mod.get_messages_for_llm("s", summarise_fn=lambda _m: "nope")

    assert messages == history


def test_summary_stays_in_the_prompt_after_history_drops_under_the_cap(monkeypatch):
    monkeypatch.setattr(session_mod, "MAX_HISTORY_EXCHANGES", 4)
    history = [{"role": "user", "content": "latest question"}]
    _patch_db(monkeypatch, _stored(history, summary="covered index scans"))

    messages = session_mod.get_messages_for_llm("s")

    assert messages == [
        {
            "role": "system",
            "content": "[Previous conversation summary]: covered index scans",
        },
        {"role": "user", "content": "latest question"},
    ]


def test_later_overflow_folds_the_existing_summary_and_trims(monkeypatch):
    monkeypatch.setattr(session_mod, "MAX_HISTORY_EXCHANGES", 4)
    history = [{"role": "user", "content": f"m{i}"} for i in range(6)]
    saved = _patch_db(monkeypatch, _stored(history, summary="old summary"))
    seen = {}

    def summarise(old):
        seen["old"] = old
        return "new summary"

    messages = session_mod.get_messages_for_llm("s", summarise_fn=summarise)

    assert seen["old"][0] == {
        "role": "system",
        "content": "[Previous conversation summary]: old summary",
    }
    assert [m["content"] for m in seen["old"][1:]] == ["m0", "m1"]
    assert saved["summary"] == "new summary"
    assert [m["content"] for m in saved["history"]] == ["m2", "m3", "m4", "m5"]
    assert [m["content"] for m in messages] == [
        "[Previous conversation summary]: new summary",
        "m2",
        "m3",
        "m4",
        "m5",
    ]


def test_first_overflow_keeps_a_verbatim_tail(monkeypatch):
    monkeypatch.setattr(session_mod, "MAX_HISTORY_EXCHANGES", 12)
    history = [{"role": "user", "content": f"m{i}"} for i in range(13)]
    saved = _patch_db(monkeypatch, _stored(history))

    def summarise(old):
        assert [m["content"] for m in old] == ["m0", "m1", "m2"]
        return "summary"

    messages = session_mod.get_messages_for_llm("s", summarise_fn=summarise)

    assert len(saved["history"]) == session_mod._RECENT_TAIL
    assert [m["content"] for m in messages[1:]] == [f"m{i}" for i in range(3, 13)]


def test_failed_summary_does_not_drop_stored_turns(monkeypatch):
    monkeypatch.setattr(session_mod, "MAX_HISTORY_EXCHANGES", 4)
    history = [{"role": "user", "content": f"m{i}"} for i in range(6)]
    saved = _patch_db(monkeypatch, _stored(list(history), summary="keep me"))

    messages = session_mod.get_messages_for_llm("s", summarise_fn=lambda _old: "")

    assert saved == {}
    assert messages[0]["content"] == "[Previous conversation summary]: keep me"
    assert [m["content"] for m in messages[1:]] == [f"m{i}" for i in range(6)]


def test_missing_session_returns_no_messages(monkeypatch):
    monkeypatch.setattr(session_mod, "_db_get", lambda _session_id: None)

    assert session_mod.get_messages_for_llm("missing") == []


def test_summarise_history_keeps_prior_summary_context(monkeypatch):
    captured = {}

    class _Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"message": {"content": "folded"}}

    def fake_post(_url, json=None, timeout=None):
        captured["messages"] = json["messages"]
        return _Response()

    monkeypatch.setattr(llm.requests, "post", fake_post)

    result = llm.summarise_history([
        {"role": "system", "content": "[Previous conversation summary]: indexes"},
        {"role": "user", "content": "what about locking?"},
    ])

    assert result == "folded"
    prompt = captured["messages"][1]["content"]
    assert "indexes" in prompt
    assert "what about locking?" in prompt
