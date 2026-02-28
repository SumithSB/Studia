"""Weak area tracker with curriculum and progress."""

import json
from datetime import datetime
from pathlib import Path

CURRICULUM_PATH = Path(__file__).parent / "curriculum.json"
PROGRESS_PATH = Path(__file__).parent / "progress.json"
PROFILE_PATH = Path(__file__).parent / "profile.json"


def _load_json(path: Path, default: dict) -> dict:
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default.copy()


def _save_progress(data: dict) -> None:
    with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_curriculum() -> list[dict]:
    """Load topic taxonomy from curriculum.json."""
    data = _load_json(CURRICULUM_PATH, {"topics": []})
    return data.get("topics", [])


def load_progress() -> dict:
    """Load progress.json; initialise from curriculum if missing."""
    if PROGRESS_PATH.exists():
        with open(PROGRESS_PATH, encoding="utf-8") as f:
            return json.load(f)
    curriculum = load_curriculum()
    progress = {"topics": {}}
    for t in curriculum:
        progress["topics"][t["id"]] = {
            "score": 0.5,
            "label": t["label"],
            "last_visited": None,
        }
    _save_progress(progress)
    return progress


def _match_needs_depth(topic: dict, needs_depth: list[str]) -> bool:
    keywords = " ".join(topic.get("keywords", [])).lower()
    for nd in needs_depth:
        for word in nd.lower().split():
            if len(word) > 3 and word in keywords:
                return True
    return False


def update_score(topic_id: str, assessment: str) -> None:
    """Update topic score: strong +0.3, partial +0.1, weak -0.1."""
    progress = load_progress()
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
    _save_progress(progress)


def get_progress_summary() -> dict:
    """Return weak, strong, suggested_next for /progress API."""
    progress = load_progress()
    profile = _load_json(PROFILE_PATH, {})
    needs_depth = profile.get("needs_depth", [])

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

    return {"weak": weak[:10], "strong": strong[:10], "suggested_next": suggested or ""}
