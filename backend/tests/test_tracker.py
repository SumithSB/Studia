"""Topic scores and the progress summary. No database."""

import pytest

from services import tracker


def _patch_store(monkeypatch, topics, curriculum, profile_data=None):
    """In-memory stand-in for the progress and curriculum tables."""
    store = {"topics": {k: dict(v) for k, v in topics.items()}}
    saved = []

    def get_progress(_profile_id):
        return {"topics": {k: dict(v) for k, v in store["topics"].items()}}

    def save_progress(_profile_id, progress):
        saved.append(progress)
        store["topics"] = {k: dict(v) for k, v in progress.get("topics", {}).items()}

    monkeypatch.setattr(tracker, "get_progress", get_progress)
    monkeypatch.setattr(tracker, "save_progress", save_progress)
    monkeypatch.setattr(tracker, "list_curriculum", lambda: list(curriculum))
    monkeypatch.setattr(
        tracker,
        "get_profile",
        lambda _profile_id: {"data": profile_data or {}},
    )
    return store, saved


def test_update_score_applies_deltas_and_clamps(monkeypatch):
    store, _saved = _patch_store(
        monkeypatch,
        {
            "strong_topic": {"score": 0.8, "label": "Strong", "last_visited": None},
            "partial_topic": {"score": 0.5, "label": "Partial", "last_visited": None},
            "weak_topic": {"score": 0.05, "label": "Weak", "last_visited": None},
            "unknown_assessment": {"score": 0.4, "label": "Same", "last_visited": None},
        },
        curriculum=[],
    )

    tracker.update_score("strong_topic", "Strong", "p1")
    tracker.update_score("partial_topic", "partial", "p1")
    tracker.update_score("weak_topic", "weak", "p1")
    tracker.update_score("unknown_assessment", "n/a", "p1")

    assert store["topics"]["strong_topic"]["score"] == pytest.approx(1.0)
    assert store["topics"]["partial_topic"]["score"] == pytest.approx(0.6)
    assert store["topics"]["weak_topic"]["score"] == pytest.approx(0.0)
    assert store["topics"]["unknown_assessment"]["score"] == pytest.approx(0.4)
    assert store["topics"]["strong_topic"]["last_visited"]


def test_update_score_ignores_topics_outside_the_curriculum(monkeypatch):
    store, saved = _patch_store(
        monkeypatch,
        {"indexes": {"score": 0.5, "label": "Indexes", "last_visited": None}},
        curriculum=[],
    )

    tracker.update_score("missing", "strong", "p1")

    assert saved == []
    assert store["topics"]["indexes"]["score"] == pytest.approx(0.5)
    assert "missing" not in store["topics"]


def test_update_score_seeds_a_curriculum_topic_at_the_midpoint(monkeypatch):
    store, _saved = _patch_store(
        monkeypatch,
        {"other": {"score": 0.5, "label": "Other", "last_visited": None}},
        curriculum=[{"id": "locks", "label": "Locking", "keywords": ["locking"]}],
    )

    tracker.update_score("locks", "weak", "p1")

    assert store["topics"]["locks"]["score"] == pytest.approx(0.4)
    assert store["topics"]["locks"]["label"] == "Locking"


def test_summary_classifies_scores_and_prefers_needs_depth(monkeypatch):
    _patch_store(
        monkeypatch,
        {
            "locks": {"score": 0.2, "label": "Locking", "last_visited": None},
            "indexes": {"score": 0.55, "label": "Indexes", "last_visited": None},
            "api": {"score": 0.9, "label": "API design", "last_visited": None},
            "borderline": {"score": 0.4, "label": "Borderline", "last_visited": None},
            "solid": {"score": 0.7, "label": "Solid", "last_visited": None},
        },
        curriculum=[
            {"id": "locks", "label": "Locking", "keywords": ["locking"]},
            {"id": "indexes", "label": "Indexes", "keywords": ["indexes", "postgres"]},
            {"id": "api", "label": "API design", "keywords": ["http"]},
            {"id": "borderline", "label": "Borderline", "keywords": ["borderline"]},
            {"id": "solid", "label": "Solid", "keywords": ["solid"]},
        ],
        profile_data={"needs_depth": ["btree indexes"]},
    )

    summary = tracker.get_progress_summary("p1")

    assert [item["id"] for item in summary["weak"]] == ["locks"]
    assert [item["id"] for item in summary["strong"]] == ["api", "solid"]
    assert summary["suggested_next"] == "indexes"
    assert summary["suggested_next_label"] == "Indexes"


def test_summary_falls_back_to_the_weakest_topic(monkeypatch):
    _patch_store(
        monkeypatch,
        {
            "locks": {"score": 0.2, "label": "Locking", "last_visited": None},
            "caching": {"score": 0.35, "label": "Caching", "last_visited": None},
        },
        curriculum=[
            {"id": "locks", "label": "Locking", "keywords": ["locking"]},
            {"id": "caching", "label": "Caching", "keywords": ["caching", "sql"]},
        ],
        # Three-letter tokens are ignored, so this must not steal the suggestion.
        profile_data={"needs_depth": ["SQL"]},
    )

    summary = tracker.get_progress_summary("p1")

    assert summary["suggested_next"] == "locks"
    assert summary["suggested_next_label"] == "Locking"


def test_empty_progress_is_seeded_before_suggesting_a_topic(monkeypatch):
    store, saved = _patch_store(
        monkeypatch,
        {},
        curriculum=[
            {"id": "indexes", "label": "Indexes", "keywords": ["indexes"]},
            {"id": "locks", "label": "Locking", "keywords": ["locking"]},
        ],
        profile_data={"needs_depth": ["btree indexes"]},
    )

    summary = tracker.get_progress_summary("p1")

    assert saved
    assert store["topics"]["indexes"]["score"] == pytest.approx(0.5)
    assert store["topics"]["locks"]["score"] == pytest.approx(0.5)
    assert summary["weak"] == []
    assert summary["strong"] == []
    assert summary["suggested_next"] == "indexes"
    assert summary["suggested_next_label"] == "Indexes"
