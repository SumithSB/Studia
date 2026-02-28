"""Agent loop with tool calling for Studia."""

import json
import requests

from config import OLLAMA_BASE_URL, OLLAMA_MODEL, MAX_AGENT_TURNS
from services import tools


def _call_ollama(messages: list[dict], stream: bool = False) -> requests.Response:
    """Call Ollama /api/chat with tools."""
    url = f"{OLLAMA_BASE_URL}/api/chat"
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": stream,
        "tools": tools.TOOLS,
    }
    return requests.post(url, json=payload, stream=stream, timeout=120)


def agent_stream(messages: list[dict], session_id: str):
    """Run agent loop with tool calls. Yields (token, done, tool_call_info)."""
    turn = 0
    current_messages = list(messages)

    while turn < MAX_AGENT_TURNS:
        turn += 1
        r = _call_ollama(current_messages, stream=False)
        r.raise_for_status()
        data = r.json()
        msg = data.get("message", {})

        tool_calls = msg.get("tool_calls") or []
        content = msg.get("content") or ""

        if tool_calls:
            current_messages.append({"role": "assistant", "tool_calls": tool_calls})
            for tc in tool_calls:
                fn = tc.get("function") or {}
                name = fn.get("name", "")
                raw_args = fn.get("arguments")
                if isinstance(raw_args, str):
                    try:
                        args = json.loads(raw_args) if raw_args else {}
                    except json.JSONDecodeError:
                        args = {}
                else:
                    args = raw_args or {}

                yield (None, False, {"tool": name, "args": args})

                result = tools.execute_tool(name, args, session_id)
                current_messages.append({
                    "role": "tool",
                    "tool_name": name,
                    "content": result,
                })
            continue

        if content:
            for i in range(0, len(content), 64):
                chunk = content[i : i + 64]
                yield (chunk, False, None)
            yield ("", True, None)
            return

    yield ("", True, None)
