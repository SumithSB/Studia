"""Curriculum topics seeded from a profile. No database."""

import db


def _capture_topics(monkeypatch):
    saved = []

    def upsert_topic(topic_id, label, category="", keywords=None):
        saved.append(
            {
                "id": topic_id,
                "label": label,
                "category": category,
                "keywords": list(keywords or []),
            }
        )

    monkeypatch.setattr(db, "upsert_topic", upsert_topic)
    return saved


def test_profile_fields_become_stable_topic_ids(monkeypatch):
    """Onboarding labels are the topic ids later used for progress suggestions."""
    saved = _capture_topics(monkeypatch)

    db.ensure_curriculum_from_profile(
        {
            "name": "Ada Lovelace",
            "consulting": "not a topic",
            "study_style": "not a topic",
            "needs_depth": ["B-tree indexes"],
            "strong_areas": ["API design"],
            "target_roles": ["Backend engineer"],
            "interview_styles_to_prepare": ["System design"],
        }
    )

    by_id = {row["id"]: row for row in saved}
    assert list(by_id) == [
        "custom.api_design",
        "custom.b_tree_indexes",
        "custom.backend_engineer",
        "custom.system_design",
    ]
    assert all(row["category"] == "custom" for row in saved)
    assert by_id["custom.b_tree_indexes"]["label"] == "B-tree indexes"
    # A one-letter token is not a keyword, so "B" cannot match needs-depth later.
    assert by_id["custom.b_tree_indexes"]["keywords"] == ["tree", "indexes"]
    assert by_id["custom.api_design"]["keywords"] == ["api", "design"]


def test_blank_duplicate_and_punctuation_only_labels(monkeypatch):
    saved = _capture_topics(monkeypatch)

    db.ensure_curriculum_from_profile(
        {
            "needs_depth": ["  SQL internals  ", "", "   ", None, 3],
            "strong_areas": ["SQL internals"],
            "target_roles": None,
            "interview_styles_to_prepare": ["???", "C++"],
        }
    )

    by_id = {row["id"]: row for row in saved}
    assert set(by_id) == {"custom.sql_internals", "custom.c", "custom.topic"}
    assert len(saved) == 3
    assert by_id["custom.sql_internals"]["label"] == "SQL internals"
    assert by_id["custom.sql_internals"]["keywords"] == ["sql", "internals"]
    assert by_id["custom.c"]["label"] == "C++"
    assert by_id["custom.c"]["keywords"] == []
    assert by_id["custom.topic"]["label"] == "???"
    assert by_id["custom.topic"]["keywords"] == []
