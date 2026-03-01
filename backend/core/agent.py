"""Agent loop with tool calling for Studia."""

import json
import requests

from config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT, MAX_AGENT_TURNS
from core.llm import strip_think_tags
from services import tools


def _call_ollama(messages: list[dict], stream: bool = False, setup_mode: bool = False) -> requests.Response:
    """Call Ollama /api/chat with tools. setup_mode: include create_profile tool."""
    url = f"{OLLAMA_BASE_URL}/api/chat"
    tool_list = tools.TOOLS_SETUP if setup_mode else tools.TOOLS
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": stream,
        "tools": tool_list,
    }
    return requests.post(url, json=payload, stream=stream, timeout=OLLAMA_TIMEOUT)


def agent_stream(messages: list[dict], session_id: str, setup_mode: bool = False):
    """Run agent loop with tool calls. Yields (token, done, tool_call_info). setup_mode: use tools that include create_profile."""
    turn = 0
    current_messages = list(messages)

    while turn < MAX_AGENT_TURNS:
        turn += 1
        r = _call_ollama(current_messages, stream=False, setup_mode=setup_mode)
        r.raise_for_status()
        data = r.json()
        msg = data.get("message", {})

        tool_calls = msg.get("tool_calls") or []
        content = strip_think_tags(msg.get("content") or "")

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
