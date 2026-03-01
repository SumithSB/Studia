"""Shared DB helpers (slug, etc.) used by backends."""

import re


def _slug(s: str) -> str:
    """Slugify for topic id: lowercase, alphanumeric and underscores only."""
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return re.sub(r"_+", "_", s).strip("_") or "topic"
