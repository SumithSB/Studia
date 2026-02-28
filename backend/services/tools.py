"""Tool definitions and executor for agent AI."""

import json

from . import research, session, tracker

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


def execute_tool(name: str, arguments: dict, session_id: str) -> str:
    """Execute a tool and return result as string for the assistant."""
    args = arguments or {}

    try:
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
            return json.dumps(research.parse_jd(jd_text))

        if name == "get_progress":
            return json.dumps(tracker.get_progress_summary())

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
            tracker.update_score(topic_id, assessment)
            return '{"status": "updated"}'

    except Exception as e:
        return json.dumps({"error": str(e)})

    return json.dumps({"error": f"Unknown tool: {name}"})
