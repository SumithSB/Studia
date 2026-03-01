"""Pytest configuration and fixtures. Use in-memory SQLite for tests."""

import os
import sys
from pathlib import Path

import pytest

# Ensure backend root is on path so "from main import app" works
_backend_root = Path(__file__).resolve().parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

# Set test DB and skip curriculum seed before any db or main import
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["STUDIA_TESTING"] = "1"

from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    return TestClient(app)
