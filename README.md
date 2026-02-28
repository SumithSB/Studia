# Studia

A fully local, voice + text interview preparation study companion. Flutter frontend talking to a FastAPI backend, powered by Ollama (local LLM), Whisper (STT), and on-demand company research. Runs only when you need it — feels like Claude/ChatGPT but knows everything about you.

## Features

- **Text & voice chat** — Type or speak; get streaming LLM responses with ChatGPT-style token-by-token rendering
- **Profile-aware** — Adapts to your background, strengths, and areas to improve via `profile.json`
- **Weak area tracking** — Silently scores understanding per topic; suggests what to study next
- **Company research** — Pastes a company name or JD; fetches interview patterns from LeetCode, Blind, Glassdoor, GitHub
- **Progress screen** — View weak/strong topics, tap to jump into chat with suggested topics
- **100% local** — No cloud databases, no API keys; Ollama + Whisper + pyttsx3 run on your machine

## Tech Stack

| Layer   | Technologies                                      |
|---------|---------------------------------------------------|
| Frontend| Flutter (macOS), http, record, provider           |
| Backend | FastAPI, uvicorn, SSE streaming                   |
| LLM     | Ollama (qwen3 with agent/tool calling)          |
| STT     | faster-whisper                                    |
| TTS     | pyttsx3 (server-side; v2: Kokoro → Flutter)       |
| Research| ddgs (DuckDuckGo), BeautifulSoup                  |

## Quick Start

### Prerequisites

- [Ollama](https://ollama.ai) — `brew install ollama`
- [Flutter](https://flutter.dev) SDK (macOS)
- Python 3.10+

### 1. Pull the LLM model

```bash
ollama pull qwen3
```

(qwen3 supports tool calling; deepseek-r1 does not.)

### 2. Setup backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Setup frontend

```bash
cd frontend
flutter pub get
```

### 4. Customize your profile

```bash
cp backend/profile.example.json backend/profile.json
```

Edit `backend/profile.json` with your experience, target roles, strong areas, and areas to improve. (This file is gitignored — your personal data stays local.)

### 5. Run

```bash
# From project root
chmod +x start.sh stop.sh
./start.sh
```

Then in a new terminal:

```bash
cd frontend
flutter run -d macos
```

Backend runs at http://127.0.0.1:8000.

### Stop

```bash
./stop.sh
```

## Project Structure

```
studia/
├── backend/              # FastAPI Python backend
│   ├── main.py           # Routes: /chat, /voice, /research, /progress, /session/history
│   ├── config.py         # Settings, BACKEND_ROOT
│   ├── core/             # LLM, agent, context
│   ├── services/         # Research, session, tracker, tools
│   ├── audio/            # STT, TTS
│   ├── profile.json      # Your profile (edit freely)
│   ├── curriculum.json   # Topic taxonomy
│   └── progress.json    # Auto-created topic scores
├── frontend/             # Flutter app
│   └── lib/
│       ├── screens/      # Chat, Progress
│       ├── widgets/      # Message bubble, voice button, topic chips
│       └── services/     # API, audio recording
├── start.sh              # Starts Ollama + backend
└── stop.sh               # Stops both
```

## API Reference

| Endpoint             | Method | Description                          |
|----------------------|--------|--------------------------------------|
| `/chat`              | POST   | Text chat; SSE stream                |
| `/voice`             | POST   | WAV audio → transcript + SSE stream |
| `/research`          | POST   | Company or JD research               |
| `/progress`          | GET    | Weak/strong topics, suggested next   |
| `/session/history`   | GET    | Conversation history for session     |

## Configuration

- **Backend**: `backend/config.py` — model (`qwen3`), `AGENT_MODE` (tool calling), Whisper size, TTS on/off, history limits
- **Profile**: `backend/profile.json` — loaded on every request (hot reload)
- **Curriculum**: `backend/curriculum.json` — topic IDs, labels, keywords
- **Frontend API URL**: `frontend/lib/services/api_service.dart` — `baseUrl` (default `http://127.0.0.1:8000`). Change if backend runs elsewhere.

## External dependencies (outside your control)

Things that may break or need updates as third parties change:

| Dependency | What to watch |
|------------|---------------|
| **Ollama model** | `qwen3` — Ollama can rename/remove models. Update `config.py` if the model name changes. Set `AGENT_MODE=False` to fall back to plain LLM without tools. |
| **ddgs** | DuckDuckGo search for company research. Rate limits or API changes can affect `/research`. |
| **Research sources** | LeetCode, Blind, Glassdoor, GitHub — site structure or scraping policies can change. Spec already notes Glassdoor blocks direct fetch. |
| **faster-whisper** | Pulls models from Hugging Face; model availability may change. |
| **pyttsx3** | Uses system TTS; behavior differs by OS. |

## Roadmap

- **v1** (current): Text + voice chat, progress tracking, company research, JD paste
- **v2**: Dark mode, Kokoro TTS, PDF JD upload, spaced repetition, export notes

## What stays local (gitignored)

- `backend/profile.json` — your personal profile (name, employers, experience)
- `backend/progress.json` — your topic scores and study history
- `backend/sessions/*.json` — session logs and research cache
- `.env` — any API keys or secrets (none required for local use)

Copy `profile.example.json` to `profile.json` to get started.
