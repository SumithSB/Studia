#!/bin/bash
echo "Stopping Studia..."
# Kill by PID file first
kill -9 $(cat .backend.pid 2>/dev/null) 2>/dev/null
kill -9 $(cat .ollama.pid 2>/dev/null) 2>/dev/null
# Fallback: kill any process on port 8000 (uvicorn --reload spawns children)
lsof -ti :8000 | xargs kill -9 2>/dev/null
# Fallback: kill any process on port 11434 (Ollama)
lsof -ti :11434 | xargs kill -9 2>/dev/null
# Fallback: kill any uvicorn matching our app
pkill -9 -f "uvicorn main:app" 2>/dev/null
# Fallback: kill any ollama serve
pkill -9 -f "ollama serve" 2>/dev/null
rm -f .backend.pid .ollama.pid
echo "Stopped."
