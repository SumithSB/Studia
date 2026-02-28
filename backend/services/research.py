"""Company/JD research via ddgs and Ollama summarisation."""

import json
from datetime import datetime, timedelta

from config import (
    BACKEND_ROOT,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    RESEARCH_CACHE_DAYS,
    RESEARCH_MAX_SOURCES,
)

CACHE_PATH = BACKEND_ROOT / "sessions" / "research_cache.json"
CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load_cache() -> dict:
    if CACHE_PATH.exists():
        with open(CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_cache(cache: dict) -> None:
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)


def _search(query: str, max_results: int = 5) -> list[dict]:
    """Search via ddgs."""
    try:
        from ddgs import DDGS
        results = list(DDGS().text(query, max_results=max_results))
        return [r.get("body", "") or r.get("title", "") for r in results]
    except Exception:
        return []


def _summarise_with_ollama(text: str, company: str) -> str:
    """Use Ollama to summarise scraped content."""
    import requests
    prompt = f"""Summarise the interview process at {company} for backend/AI engineering roles.
Cover: number of rounds, types of rounds, technical topics commonly asked,
difficulty level, any patterns or tips. Be specific and concise.
Keep it under 300 words.

Raw content:
{text[:8000]}"""

    url = f"{OLLAMA_BASE_URL}/api/generate"
    r = requests.post(
        url,
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=120,
    )
    r.raise_for_status()
    return r.json().get("response", "")


def research_company(company: str) -> dict:
    """Research company interview process. Returns cached if fresh."""
    cache = _load_cache()
    key = company.lower().strip()
    entry = cache.get(key, {})
    fetched = entry.get("fetched_at")
    if fetched:
        try:
            dt = datetime.fromisoformat(fetched)
            if datetime.now() - dt < timedelta(days=RESEARCH_CACHE_DAYS):
                return {
                    "summary": entry.get("summary", ""),
                    "gap_analysis": entry.get("gap_analysis", ""),
                    "topics_to_prioritise": entry.get("topics_to_prioritise", []),
                }
        except Exception:
            pass

    snippets = []
    queries = [
        f"site:leetcode.com/discuss {company} interview experience",
        f"site:teamblind.com {company} interview",
        f"{company} software engineer interview questions site:glassdoor.com",
        f"{company} interview prep questions site:github.com",
    ]
    for q in queries[:RESEARCH_MAX_SOURCES]:
        snippets.extend(_search(q, max_results=3))

    text = "\n\n".join(snippets[:RESEARCH_MAX_SOURCES * 2])
    summary = _summarise_with_ollama(text, company) if text else "No data found."

    cache[key] = {
        "fetched_at": datetime.now().isoformat(),
        "summary": summary,
        "sources_used": ["leetcode", "blind", "glassdoor", "github"],
    }
    _save_cache(cache)

    return {
        "summary": summary,
        "gap_analysis": "",
        "topics_to_prioritise": [],
    }


def parse_jd(jd_text: str) -> dict:
    """Parse job description and return gap analysis."""
    import requests

    profile_path = BACKEND_ROOT / "profile.json"
    with open(profile_path, encoding="utf-8") as f:
        profile = json.load(f)

    prompt = f"""Extract from this job description:
- Required technical skills
- Nice-to-have skills
- Seniority signals
- Tech stack mentioned

Then cross-reference against this profile:
{json.dumps(profile, indent=2)[:2000]}

Provide gap analysis: what should the candidate focus on given this JD?
Output format: summary (2-3 sentences), topics_to_prioritise (list of topic IDs from: python.internals.gil, dsa.dp.2d_patterns, system_design.rate_limiter, ml.llm.rag_pipeline, etc.)
Keep response under 200 words."""

    url = f"{OLLAMA_BASE_URL}/api/generate"
    r = requests.post(
        url,
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=120,
    )
    r.raise_for_status()
    resp = r.json().get("response", "")
    return {
        "summary": resp[:500],
        "gap_analysis": resp,
        "topics_to_prioritise": [],
    }
