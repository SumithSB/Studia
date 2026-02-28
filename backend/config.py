"""Configuration for Studia backend."""

from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent

OLLAMA_MODEL = "qwen3"
OLLAMA_BASE_URL = "http://localhost:11434"
AGENT_MODE = True
MAX_AGENT_TURNS = 5
LOG_SESSIONS = True
MAX_HISTORY_EXCHANGES = 30
RESEARCH_MAX_SOURCES = 8
RESEARCH_CACHE_DAYS = 7
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8000
