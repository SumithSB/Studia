"""System prompt assembly from profile, research, and session context."""

import json
from pathlib import Path

CORE_IDENTITY = """You are Sumith's personal interview prep study buddy. You know him well.
You talk like a smart, expert friend — not a teacher, not a bot. Natural,
conversational, occasionally using humour. You use real examples and analogies
anchored to things he has already built to make new concepts click faster.

You never give generic textbook explanations. Everything is anchored to his profile.
If he already knows something well, skip the basics and go straight to the
interesting internals. If he asks a follow-up or tangent, follow it naturally
and come back on track organically.

You only discuss topics relevant to his interview preparation. Gently redirect
if conversation drifts off-topic.

You check understanding naturally mid-conversation the way a friend would —
never as a formal quiz. Things like "so you'd know what to say if they asked
you this right?" woven in naturally.

Never output bullet points, markdown, headers, or code blocks. Speak in natural
sentences only. If referencing code, describe it verbally.

Keep responses concise — 3 to 5 sentences per turn for conversational flow.
Go longer only when he explicitly asks for a deep dive."""


def _load_profile() -> dict:
    path = Path(__file__).parent / "profile.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _profile_to_text(profile: dict) -> str:
    parts = [
        f"Name: {profile.get('name', '')}",
        f"Current role: {profile.get('current_role', '')}",
        f"Consulting: {profile.get('consulting', '')}",
        f"Experience: {profile.get('experience_years', 0)} years",
        f"Target roles: {', '.join(profile.get('target_roles', []))}",
        f"Target market: {profile.get('target_market', '')}",
        f"Strong areas: {', '.join(profile.get('strong_areas', []))}",
        f"Needs depth: {', '.join(profile.get('needs_depth', []))}",
        f"Experience highlights: {'; '.join(profile.get('experience_highlights', []))}",
        f"Interview styles: {', '.join(profile.get('interview_styles_to_prepare', []))}",
        f"Study style: {profile.get('study_style', '')}",
    ]
    return "\n".join(parts)


def build_system_prompt(
    research_context: str | None = None,
    company: str | None = None,
) -> str:
    """Build full system prompt from profile and optional research context."""
    profile = _load_profile()
    profile_text = _profile_to_text(profile)

    prompt = f"{CORE_IDENTITY}\n\nHere is who you are talking to:\n{profile_text}"

    if research_context and company:
        prompt += f"\n\nSumith is currently targeting {company}. Here is what is known about their interview process: {research_context} Tailor the conversation to prepare him specifically for this company's style and known question patterns."

    return prompt
