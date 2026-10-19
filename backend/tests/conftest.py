"""Pytest configuration and fixtures.

The app imports only when DATABASE_URL is a postgresql:// URL. Unit tests mock
the repository and do not connect. API tests run when that database is reachable.
"""

import os
import socket
import sys
from pathlib import Path
from urllib.parse import urlparse

import pytest

# Ensure backend root is on path so "from main import app" works
_backend_root = Path(__file__).resolve().parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

# config.py rejects non-PostgreSQL URLs at import. Do not overwrite a real URL.
_db_url = os.environ.get("DATABASE_URL", "")
if not _db_url.lower().startswith("postgresql"):
    os.environ["DATABASE_URL"] = "postgresql://studia:studia@127.0.0.1:5432/studia"
os.environ["STUDIA_TESTING"] = "1"

from fastapi.testclient import TestClient

from main import app


def _postgres_reachable() -> bool:
    """True when something accepts TCP on the DATABASE_URL host. Does not log in."""
    parsed = urlparse(os.environ["DATABASE_URL"])
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 5432
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


@pytest.fixture
def client():
    if not _postgres_reachable():
        pytest.skip("PostgreSQL is not reachable; API tests need DATABASE_URL")
    return TestClient(app)
