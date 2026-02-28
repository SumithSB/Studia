# Tasks: Studia

**Input**: specs.md (root), plan.md
**Structure**: backend/ + frontend/ per specs.md

## Phase 1: Setup

- [x] T001 Create backend/ directory, requirements.txt with fastapi uvicorn[standard] faster-whisper scipy numpy requests beautifulsoup4 ddgs pyttsx3 python-multipart in backend/
- [x] T002 Create frontend/ Flutter project with pubspec.yaml (http, record, provider, shared_preferences) in frontend/
- [x] T003 Create backend/config.py with OLLAMA_MODEL OLLAMA_BASE_URL WHISPER_MODEL_SIZE SAMPLE_RATE TTS_ENABLED MAX_HISTORY_EXCHANGES etc. per specs in backend/config.py

## Phase 2: Backend Core (Foundational)

- [x] T004 [P] Create backend/profile.json from specs Section 6 in backend/profile.json
- [x] T005 [P] Create backend/curriculum.json with topics from specs Section 9 in backend/curriculum.json
- [x] T006 Implement backend/context.py — load profile, assemble system prompt, inject research/JD context per specs in backend/context.py
- [x] T007 Implement backend/llm.py — Ollama streaming, strip think tags, SSE token stream per specs in backend/llm.py
- [x] T008 Implement backend/stt.py — Whisper transcription, WAV 16kHz input per specs in backend/stt.py
- [x] T009 Implement backend/tts.py — pyttsx3 in background thread per specs in backend/tts.py
- [x] T010 Implement backend/session.py — session state, history, context window summarisation per specs in backend/session.py
- [x] T011 Implement backend/tracker.py — curriculum loading, weak area scoring, topic suggestion per specs in backend/tracker.py
- [x] T012 Implement backend/research.py — ddgs search, LeetCode/Blind/GitHub scraping, JD parsing, cache per specs in backend/research.py

## Phase 3: Backend Endpoints (US1–US5)

- [x] T013 [US1] Implement POST /chat — accept message + session_id, stream SSE tokens, call context+llm+session+tracker in backend/main.py
- [x] T014 [US2] Implement POST /voice — accept WAV, transcribe via stt, stream SSE with transcript first then tokens in backend/main.py
- [x] T015 [US3] Implement GET /progress — return weak/strong/suggested_next from tracker in backend/main.py
- [x] T016 [US4] Implement POST /research — company or jd type, return summary/gap_analysis/topics_to_prioritise in backend/main.py
- [x] T017 [US5] Implement GET /session/history — query session_id, return [{role, content}] in backend/main.py

## Phase 4: Flutter Frontend

- [x] T018 [P] Create lib/models/message.dart and topic.dart per specs in frontend/lib/models/
- [x] T019 Implement lib/services/api_service.dart — HTTP to FastAPI, SSE streaming for /chat and /voice in frontend/lib/services/api_service.dart
- [x] T020 Implement lib/services/audio_service.dart — record WAV 16kHz mono via RecordConfig in frontend/lib/services/audio_service.dart
- [x] T021 Create lib/widgets/message_bubble.dart, topic_chip.dart, voice_button.dart in frontend/lib/widgets/
- [x] T022 Implement lib/screens/chat_screen.dart — message list, input, mic, streaming UI, research banner, JD modal in frontend/lib/screens/chat_screen.dart
- [x] T023 Implement lib/screens/progress_screen.dart — topic list, score bars, suggested next, tap to chat in frontend/lib/screens/progress_screen.dart
- [x] T024 Implement lib/main.dart — app entry, navigation chat↔progress, Provider setup in frontend/lib/main.dart

## Phase 5: Scripts & Polish

- [x] T025 Create start.sh — ollama serve, sleep, uvicorn backend per specs in start.sh
- [x] T026 Create stop.sh — kill backend and ollama PIDs in stop.sh
- [x] T027 Add .gitignore for __pycache__ venv .dart_tool build sessions/*.json .backend.pid .ollama.pid

## Dependencies

- Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
- T006–T012 (backend core) must complete before T013–T017 (endpoints)
