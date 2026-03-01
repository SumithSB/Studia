"""Configuration for Studia backend. Load from environment with sensible defaults."""

import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parent
# Load .env from project root or backend/ so DATABASE_URL etc. are set when running via start.sh or uvicorn
load_dotenv(BACKEND_ROOT.parent / ".env")
load_dotenv(BACKEND_ROOT / ".env")

# Ollama
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "300"))

# Agent
AGENT_MODE = os.getenv("AGENT_MODE", "true").lower() in ("true", "1", "yes")
MAX_AGENT_TURNS = int(os.getenv("MAX_AGENT_TURNS", "5"))

# Session and history
LOG_SESSIONS = os.getenv("LOG_SESSIONS", "true").lower() in ("true", "1", "yes")
MAX_HISTORY_EXCHANGES = int(os.getenv("MAX_HISTORY_EXCHANGES", "30"))

# Research
RESEARCH_MAX_SOURCES = int(os.getenv("RESEARCH_MAX_SOURCES", "8"))
RESEARCH_CACHE_DAYS = int(os.getenv("RESEARCH_CACHE_DAYS", "7"))

# Server
BACKEND_HOST = os.getenv("BACKEND_HOST", "127.0.0.1")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))

# Database: PostgreSQL only. Set DATABASE_URL (e.g. postgresql://user:password@localhost:5432/studia).
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if not DATABASE_URL or not DATABASE_URL.lower().startswith("postgresql"):
    raise RuntimeError(
        "DATABASE_URL must be set to a PostgreSQL connection string, e.g. "
        "postgresql://user:password@localhost:5432/studia"
    )
