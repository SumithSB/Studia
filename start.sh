#!/bin/bash
echo "Starting Studia..."

# Start Ollama
ollama serve &
OLLAMA_PID=$!
echo $OLLAMA_PID > .ollama.pid

# Wait for Ollama to be ready
sleep 2

# Start FastAPI backend
cd backend
source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt -q
uvicorn main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!
echo $BACKEND_PID > ../.backend.pid

cd ..
echo "Backend running at http://127.0.0.1:8000"
echo "Open the Flutter app or run: cd frontend && flutter run -d macos"
