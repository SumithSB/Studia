"""Ollama streaming interface with think-tag stripping."""

import json
import logging
import re
import requests

from config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT

logger = logging.getLogger(__name__)

THINK_PATTERN = re.compile(r"<think>.*?</think>", re.DOTALL)


def strip_think_tags(text: str) -> str:
    """Remove DeepSeek-R1 think blocks from output. Also strips unclosed <think> at end."""
    out = THINK_PATTERN.sub("", text)
    # Remove unclosed <think>... to end of string
    if "<think>" in out:
        out = re.sub(r"<think>.*", "", out, flags=re.DOTALL)
    return out.strip()


def stream_completion(messages: list[dict]):
    """Stream LLM tokens from Ollama. Yields (token, done, topic_detected)."""
    url = f"{OLLAMA_BASE_URL}/api/chat"
    payload = {"model": OLLAMA_MODEL, "messages": messages, "stream": True}

    raw_buffer = ""
    emitted_len = 0

    with requests.post(url, json=payload, stream=True, timeout=OLLAMA_TIMEOUT) as r:
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
            # Only run regex when think blocks might be present (avoids O(n²) for models without think)
            if "<think>" in raw_buffer or obj.get("done"):
                cleaned = strip_think_tags(raw_buffer)
            else:
                cleaned = raw_buffer
            if len(cleaned) > emitted_len:
                yield (cleaned[emitted_len:], False, None)
                emitted_len = len(cleaned)
            if obj.get("done"):
                yield ("", True, None)
                return


# Max chars to send for summarization to avoid blowing context
SUMMARISE_MAX_CHARS = 60_000


def summarise_history(messages: list[dict]) -> str:
    """Non-streaming call to Ollama to summarise old conversation exchanges.

    Used by session.get_messages_for_llm() when history exceeds MAX_HISTORY_EXCHANGES.
    Returns a concise context block (max ~400 words) or empty string on failure.
    """
    parts = []
    for m in messages:
        role = m.get("role", "")
        content = m.get("content", "")
        if content and role in ("user", "assistant"):
            prefix = "User" if role == "user" else "Assistant"
            parts.append(f"{prefix}: {content}")

    if not parts:
        return ""

    conversation_text = "\n".join(parts)
    if len(conversation_text) > SUMMARISE_MAX_CHARS:
        conversation_text = conversation_text[-SUMMARISE_MAX_CHARS:]

    url = f"{OLLAMA_BASE_URL}/api/chat"
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Summarise this interview prep conversation into a concise context block "
                    "(max 400 words). Preserve: key topics discussed, questions asked, concepts "
                    "explained, and the user's demonstrated level of understanding."
                ),
            },
            {"role": "user", "content": conversation_text},
        ],
        "stream": False,
    }

    try:
        r = requests.post(url, json=payload, timeout=OLLAMA_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        response = (data.get("message") or {}).get("content", "") or ""
        return strip_think_tags(response)
    except Exception as e:
        logger.debug("Summarise history failed: %s", e)
        return ""
