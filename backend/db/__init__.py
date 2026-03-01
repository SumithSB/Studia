"""Database layer: connection, schema, and repository API for profiles, progress, and sessions.

Uses PostgreSQL only (DATABASE_URL must be a postgresql:// connection string).
"""

import re

from db._shared import _slug
from db import postgres_backend as _backend

# Re-export all backend functions so the rest of the app imports from db only
list_curriculum = _backend.list_curriculum
get_topic = _backend.get_topic
upsert_topic = _backend.upsert_topic
get_profile = _backend.get_profile
list_profiles = _backend.list_profiles
save_profile = _backend.save_profile
get_default_profile_id = _backend.get_default_profile_id
set_default_profile_id = _backend.set_default_profile_id
profile_exists = _backend.profile_exists
get_progress = _backend.get_progress
save_progress = _backend.save_progress
get_session = _backend.get_session
save_session = _backend.save_session
health_check = _backend.health_check


def ensure_curriculum_from_profile(profile_data: dict) -> None:
    """Build curriculum topics from profile onboarding (needs_depth, strong_areas, target_roles). Idempotent."""
    labels = set()
    for key in ("needs_depth", "strong_areas", "target_roles", "interview_styles_to_prepare"):
        for item in (profile_data.get(key) or []):
            if isinstance(item, str) and item.strip():
                labels.add(item.strip())
    for label in sorted(labels):
        tid = "custom." + _slug(label)
        keywords = [w for w in re.split(r"[^a-z0-9]+", label.lower()) if len(w) > 1]
        upsert_topic(tid, label, "custom", keywords)
