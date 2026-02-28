"""Ollama streaming interface with think-tag stripping."""

import json
import re
import requests

from config import OLLAMA_BASE_URL, OLLAMA_MODEL

THINK_PATTERN = re.compile(r"<think>.*?</think>", re.DOTALL)


def strip_think_tags(text: str) -> str:
    """Remove DeepSeek-R1 think blocks from output."""
    return THINK_PATTERN.sub("", text).strip()


def stream_completion(messages: list[dict]):
    """Stream LLM tokens from Ollama. Yields (token, done, topic_detected)."""
    url = f"{OLLAMA_BASE_URL}/api/chat"
    payload = {"model": OLLAMA_MODEL, "messages": messages, "stream": True}

    raw_buffer = ""
    emitted_len = 0

    with requests.post(url, json=payload, stream=True, timeout=60) as r:
        r.raise_for_status()
        for line in r.iter_lines(decode_unicode=True):
            if not line or not line.strip():
                continue
            if not line.startswith("data: "):
                continue
            data = line[6:]
            if data == "[DONE]":
                yield ("", True, None)
                return
            try:
                obj = json.loads(data)
            except json.JSONDecodeError:
                continue
            msg = obj.get("message", {})
            content = msg.get("content", "") or ""
            raw_buffer += content
            cleaned = strip_think_tags(raw_buffer)
            if len(cleaned) > emitted_len:
                yield (cleaned[emitted_len:], False, None)
                emitted_len = len(cleaned)
            if obj.get("done"):
                yield ("", True, None)
                return
