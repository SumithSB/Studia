"""Ollama /api/chat streaming. No network."""

from core import llm


class _Stream:
    def __init__(self, lines):
        self._lines = lines

    def raise_for_status(self):
        return None

    def iter_lines(self, decode_unicode=True):
        yield from self._lines

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def _patch_post(monkeypatch, lines):
    captured = {}

    def fake_post(url, json=None, stream=None, timeout=None):
        captured["url"] = url
        captured["json"] = json
        captured["stream"] = stream
        return _Stream(lines)

    monkeypatch.setattr(llm.requests, "post", fake_post)
    return captured


def test_ollama_ndjson_tokens_are_not_dropped(monkeypatch):
    """Native Ollama streams one JSON object per line, with no SSE prefix."""
    captured = _patch_post(
        monkeypatch,
        [
            '{"message":{"role":"assistant","content":"Hi"},"done":false}',
            "not-json",
            '{"message":{"role":"assistant","content":" there"},"done":true}',
        ],
    )

    tokens = list(llm.stream_completion([{"role": "user", "content": "hello"}]))

    assert captured["stream"] is True
    assert captured["url"].endswith("/api/chat")
    assert tokens == [("Hi", False, None), (" there", False, None), ("", True, None)]


def test_sse_prefixed_lines_still_stream(monkeypatch):
    _patch_post(
        monkeypatch,
        [
            'data: {"message":{"content":"A"},"done":false}',
            "data: [DONE]",
        ],
    )

    tokens = list(llm.stream_completion([{"role": "user", "content": "hello"}]))

    assert tokens == [("A", False, None), ("", True, None)]
