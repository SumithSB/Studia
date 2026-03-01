"""Tool definitions and executor for agent AI."""

import json

from db import ensure_curriculum_from_profile, get_default_profile_id, save_profile, set_default_profile_id
from . import research, session, tracker

CREATE_PROFILE_TOOL = {
    "type": "function",
    "function": {
        "name": "create_profile",
        "description": "Create the user's profile from the information they provided. Call this when you have enough details (name, role, targets, strengths, areas to improve).",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Full name"},
                "current_role": {"type": "string", "description": "Current job title or role"},
                "target_roles": {"type": "array", "items": {"type": "string"}, "description": "Target job roles"},
                "strong_areas": {"type": "array", "items": {"type": "string"}, "description": "Strong areas"},
                "needs_depth": {"type": "array", "items": {"type": "string"}, "description": "Areas needing more depth"},
                "experience_highlights": {"type": "array", "items": {"type": "string"}, "description": "Key experience highlights"},
                "interview_styles_to_prepare": {"type": "array", "items": {"type": "string"}, "description": "Interview styles to prepare for"},
                "study_style": {"type": "string", "description": "Preferred study style"},
                "consulting": {"type": "string"},
                "experience_years": {"type": "integer"},
                "target_market": {"type": "string"},
                "label": {"type": "string", "description": "Profile label (optional)"},
            },
        },
    },
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "research_company",
            "description": "Research a company's interview process. Use when user mentions a company they are targeting.",
            "parameters": {
                "type": "object",
                "required": ["company"],
                "properties": {"company": {"type": "string"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "parse_jd",
            "description": "Parse a job description and return gap analysis. Use when user pastes a JD.",
            "parameters": {
                "type": "object",
                "required": ["jd_text"],
                "properties": {"jd_text": {"type": "string"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_progress",
            "description": "Get user's weak/strong topics and suggested next. Use when user asks what to study.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_curriculum",
            "description": "Look up topics in the curriculum. Use when user asks about available topics.",
            "parameters": {
                "type": "object",
                "properties": {"category": {"type": "string"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_topic_score",
            "description": "Update a topic score after assessing understanding. Use when conversation about a topic concludes.",
            "parameters": {
                "type": "object",
                "required": ["topic_id", "assessment"],
                "properties": {
                    "topic_id": {"type": "string"},
                    "assessment": {"type": "string", "enum": ["strong", "partial", "weak"]},
                },
            },
        },
    },
]

TOOLS_SETUP = [CREATE_PROFILE_TOOL] + TOOLS


def _ensure_list(v) -> list:
    """Normalise value to list of strings."""
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    return [str(v).strip()] if str(v).strip() else []


def _profile_id_for_session(session_id: str) -> str | None:
    """Resolve profile_id for this session (from session store or default)."""
    s = session.get_session(session_id)
    return s.get("profile_id") or get_default_profile_id()


def execute_tool(name: str, arguments: dict, session_id: str) -> str:
    """Execute a tool and return result as string for the assistant."""
    args = arguments or {}
    profile_id = _profile_id_for_session(session_id)

    try:
        if name == "create_profile":
            label = (args.get("label") or "").strip() or "Profile"
            data = {
                "name": (args.get("name") or "").strip(),
                "current_role": (args.get("current_role") or "").strip(),
                "consulting": (args.get("consulting") or "").strip(),
                "experience_years": int(args.get("experience_years") or 0),
                "target_roles": _ensure_list(args.get("target_roles")),
                "target_market": (args.get("target_market") or "").strip(),
                "strong_areas": _ensure_list(args.get("strong_areas")),
                "needs_depth": _ensure_list(args.get("needs_depth")),
                "experience_highlights": _ensure_list(args.get("experience_highlights")),
                "interview_styles_to_prepare": _ensure_list(args.get("interview_styles_to_prepare")),
                "study_style": (args.get("study_style") or "").strip(),
            }
            new_id = save_profile(profile_id=None, label=label, data=data)
            ensure_curriculum_from_profile(data)
            if not get_default_profile_id():
                set_default_profile_id(new_id)
            s = session.get_session(session_id)
            session.ensure_session(session_id, new_id, s.get("target_role"))
            return json.dumps({"status": "created", "profile_id": new_id, "message": "Profile created. The user can start interview prep."})

        if name == "research_company":
            company = args.get("company", "")
            if not company:
                return "Error: company is required"
            result = research.research_company(company)
            summary = result.get("summary", "")
            session.set_research_context(session_id, company, summary)
            return json.dumps(result)

        if name == "parse_jd":
            jd_text = args.get("jd_text", "")
            if not jd_text:
                return "Error: jd_text is required"
            if not profile_id:
                return json.dumps({"error": "No profile yet"})
            return json.dumps(research.parse_jd(jd_text, profile_id))

        if name == "get_progress":
            if not profile_id:
                return json.dumps({"error": "No profile yet", "weak": [], "strong": [], "suggested_next": ""})
            return json.dumps(tracker.get_progress_summary(profile_id))

        if name == "lookup_curriculum":
            curriculum = tracker.load_curriculum()
            category = args.get("category")
            if category:
                curriculum = [t for t in curriculum if category.lower() in t.get("category", "").lower()]
            return json.dumps({"topics": curriculum})

        if name == "update_topic_score":
            topic_id = args.get("topic_id")
            assessment = args.get("assessment")
            if not topic_id or not assessment:
                return "Error: topic_id and assessment required"
            if not profile_id:
                return json.dumps({"error": "No profile yet"})
            tracker.update_score(topic_id, assessment, profile_id)
            return '{"status": "updated"}'

    except Exception as e:
        return json.dumps({"error": str(e)})

    return json.dumps({"error": f"Unknown tool: {name}"})
