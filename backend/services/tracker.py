"""Weak area tracker with curriculum and progress. Curriculum and progress per profile via DB."""

from datetime import datetime

from db import get_profile, get_progress, list_curriculum, save_progress


def load_curriculum() -> list[dict]:
    """Load topic taxonomy from DB (can be updated dynamically from conversation)."""
    return list_curriculum()


def load_progress(profile_id: str) -> dict:
    """Load progress for profile from DB; initialise from curriculum if missing."""
    progress = get_progress(profile_id)
    topics = progress.get("topics", {})
    if not topics:
        curriculum = load_curriculum()
        for t in curriculum:
            topics[t["id"]] = {
                "score": 0.5,
                "label": t["label"],
                "last_visited": None,
            }
        save_progress(profile_id, {"topics": topics})
        progress = {"topics": topics}
    return progress


def _match_needs_depth(topic: dict, needs_depth: list[str]) -> bool:
    keywords = " ".join(topic.get("keywords", [])).lower()
    for nd in needs_depth:
        for word in nd.lower().split():
            if len(word) > 3 and word in keywords:
                return True
    return False


def update_score(topic_id: str, assessment: str, profile_id: str) -> None:
    """Update topic score for profile: strong +0.3, partial +0.1, weak -0.1."""
    progress = load_progress(profile_id)
    topics = progress.get("topics", {})
    if topic_id not in topics:
        curriculum = load_curriculum()
        for t in curriculum:
            if t["id"] == topic_id:
                topics[topic_id] = {"score": 0.5, "label": t["label"], "last_visited": None}
                break
    if topic_id not in topics:
        return
    delta = {"strong": 0.3, "partial": 0.1, "weak": -0.1}.get(assessment.lower(), 0)
    s = topics[topic_id]["score"]
    topics[topic_id]["score"] = max(0, min(1, s + delta))
    topics[topic_id]["last_visited"] = datetime.now().isoformat()
    save_progress(profile_id, progress)


def get_progress_summary(profile_id: str) -> dict:
    """Return weak, strong, suggested_next for /progress API for the given profile."""
    progress = load_progress(profile_id)
    profile_obj = get_profile(profile_id)
    profile_data = (profile_obj or {}).get("data") or {}
    needs_depth = profile_data.get("needs_depth", [])

    topics = progress.get("topics", {})
    curriculum = load_curriculum()

    weak = []
    strong = []
    for tid, t in topics.items():
        cur = next((c for c in curriculum if c["id"] == tid), None)
        label = t.get("label") or (cur["label"] if cur else tid)
        score = t.get("score", 0.5)
        entry = {"id": tid, "score": score, "label": label}
        if score < 0.4:
            weak.append(entry)
        elif score >= 0.7:
            strong.append(entry)

    weak.sort(key=lambda x: (x["score"], 0))
    strong.sort(key=lambda x: (-x["score"], 0))

    suggested = None
    priority = [t for t in curriculum if _match_needs_depth(t, needs_depth)]
    if priority:
        scored = [(tid, topics.get(tid, {}).get("score", 0.5)) for tid in [p["id"] for p in priority]]
        scored.sort(key=lambda x: (x[1], 0))
        if scored:
            suggested = scored[0][0]
    if not suggested and weak:
        suggested = weak[0]["id"]

    suggested_label = ""
    if suggested:
        entry = next((e for e in weak + strong if e["id"] == suggested), None)
        if entry:
            suggested_label = entry.get("label", suggested)
        else:
            cur = next((c for c in curriculum if c["id"] == suggested), None)
            suggested_label = cur["label"] if cur else suggested

    return {
        "weak": weak[:10],
        "strong": strong[:10],
        "suggested_next": suggested or "",
        "suggested_next_label": suggested_label,
    }
