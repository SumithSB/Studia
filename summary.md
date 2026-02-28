# Studia — Project Summary

## Problem

- **Generic prep doesn’t scale:** Off-the-shelf interview prep (LeetCode, generic guides) isn’t tailored to a candidate’s background, target companies, or weak spots.
- **Scattered context:** Resumes, LinkedIn, JDs, and topic progress live in different places; no single place uses all of it for study.
- **Manual research:** Looking up company interview processes and JD fit is manual and time-consuming.
- **Privacy and cost:** Cloud AI and databases mean sending personal data elsewhere and paying per use.

## Solution

**Studia** is a fully local interview-prep companion that:

1. **Builds a single profile** from your resumes and LinkedIn export (onboarding), so the AI knows your experience, strengths, and goals.
2. **Acts as an agent:** It decides when to research a company, parse a JD, check your progress, or update topic scores—no fixed buttons for every action.
3. **Stays on your machine:** Ollama (LLM), Whisper (STT), and pyttsx3 (TTS) run locally; profile, progress, and sessions are stored as local JSON files. No cloud DB, no API keys.
4. **Streams like ChatGPT:** Text and voice chat stream token-by-token over SSE for a responsive feel.

---

## Features

### Onboarding (first run)

- App checks for `profile.json`. If missing, it shows an **onboarding screen**.
- User uploads **resumes** (PDF, DOCX, TXT) and optional **LinkedIn “Download your data”** ZIP.
- Backend extracts text, sends it to Ollama with the profile schema, and writes **profile.json**.
- After that, user goes to chat. No manual editing required unless they prefer it.

### Agent AI

- Model: **qwen3** (Ollama), with **tool calling** enabled.
- **Tools:** `research_company`, `parse_jd`, `get_progress`, `lookup_curriculum`, `update_topic_score`.
- The model chooses when to call tools (e.g. “I’m targeting Google” → research; “What should I study?” → get_progress).
- SSE can include `{"tool_call": "name", "args": {...}}` so the UI can show e.g. “Researching Google…”.

### Chat and voice

- **Text chat:** Message + session_id → SSE stream of tokens; optional TTS playback on the server.
- **Voice:** Upload WAV → Whisper transcript → same streaming reply as chat. One request, no second “stream URL” call.
- Both endpoints return **503** if profile doesn’t exist (user must complete onboarding).
- **Chat vs Voice mode:** Segmented toggle (Chat | Voice). Voice mode is **persistent** until the user switches back to Chat; in Voice mode the mic is prominent and the text field is optional (“Add a message (optional)”). Mode is persisted in SharedPreferences.

### Conversational UI

- **Typing / analysing indicator:** When the LLM is working and no tokens or tool status have arrived yet, an assistant-style bubble shows “Studia is typing…” with **animated bouncing dots** so the user never sees a blank wait.
- **Tool-call status:** When the agent runs a tool, the UI shows a compact status row (e.g. “Researching Monzo…”, “Checking your progress…”, “Analyzing job description…”) above the input. Status is cleared when the next token or `done` arrives.
- Result: the user always sees either typing, tool status, or streamed text—never an empty loading state.

### In-chat profile update (file upload)

- **Attach button** (paperclip) in the chat input opens a file picker for PDF, DOCX, TXT (resumes) and ZIP (LinkedIn). Selected files appear as chips with a remove (×); max 5 files.
- **Send with attachments:** If the user sends while files are attached, the app first calls `POST /profile/from-uploads` with the selected resumes and (if present) one LinkedIn ZIP. On success it clears attachments, shows “Profile updated from your uploads.”, then sends a user message (typed text or “I’ve uploaded my resume / LinkedIn — please use it for our conversation.”) and streams the reply so the conversation continues with the new profile. On 4xx, an error is shown and no message is sent.
- Users can refresh their profile from the chat without going back to onboarding.

### Profile-aware behaviour

- System prompt is built from **profile.json** (name, role, strong_areas, needs_depth, experience_highlights, study_style, etc.).
- Answers are tailored to the user’s level and goals; the model is instructed to avoid generic explanations.

### Weak area tracking

- **Curriculum:** Topic taxonomy in `curriculum.json` (IDs like `dsa.dp.2d_patterns`, `ml.llm.rag_pipeline`).
- **Progress:** `progress.json` stores per-topic scores; tracker suggests weak/strong and “suggested next” (aligned with profile’s `needs_depth`).
- The agent can call **update_topic_score** when a topic discussion ends and it infers understanding (strong/partial/weak).

### Company and JD research

- **Company:** Search (e.g. LeetCode, Blind, Glassdoor, GitHub); summarise with Ollama; cache in `sessions/research_cache.json`. When the agent runs company research, it can set **session research context** so later replies are company-specific.
- **JD:** Paste job description → Ollama gap analysis vs profile; returns summary and topics to prioritise.
- `/research` remains available as a direct API for the Flutter “research” flow if needed.

### Progress screen

- Shows weak topics, strong topics, and a suggested next topic; user can tap to open chat with that topic as context.

### 100% local

- No cloud databases; no mandatory API keys. Ollama, Whisper, and TTS run on the host. All persistent data is under `backend/` (profile, progress, curriculum, sessions).

---

## Tech Stack

| Layer    | Technologies |
|----------|----------------|
| Frontend | Flutter (macOS), http, record, provider, file_picker, shared_preferences |
| Backend  | FastAPI, uvicorn, SSE streaming |
| LLM      | Ollama (qwen3, agent + tool calling) |
| STT      | faster-whisper |
| TTS      | pyttsx3 (server-side) |
| Research | ddgs (DuckDuckGo), BeautifulSoup |
| Profile  | pypdf, python-docx (resume/LinkedIn extraction) |

---

## Architecture (high level)

- **Flutter app:** On startup, calls `GET /profile/status`. If no profile → **OnboardingScreen** (upload resumes + LinkedIn ZIP → `POST /profile/from-uploads`). If profile exists → **ChatScreen**. Progress screen available from chat.
- **Backend:** `main.py` defines routes. **core/** holds LLM, agent loop, and context (system prompt). **services/** holds research, session, tracker, tools, profile_builder. **audio/** holds STT and TTS.
- **Agent loop:** For each user message, backend builds messages (system + history), calls Ollama with `tools`. If the model returns `tool_calls`, backend runs tools, appends results, calls Ollama again (up to `MAX_AGENT_TURNS`). When the model returns only text, that stream is sent to the client.
- **Data:** Profile, progress, curriculum, and session logs live under `backend/` as JSON; research cache under `backend/sessions/`. All gitignored where sensitive.

---

## API Summary

| Endpoint                 | Method | Purpose |
|--------------------------|--------|---------|
| `/profile/status`        | GET    | `{ "exists": true \| false }` — drive onboarding vs chat |
| `/profile/from-uploads`  | POST   | Multipart: resumes + optional LinkedIn ZIP → create profile.json |
| `/chat`                  | POST   | Text chat; SSE stream; 503 if no profile |
| `/voice`                 | POST   | WAV → transcript + SSE stream; 503 if no profile |
| `/research`              | POST   | Company or JD research (type + value) |
| `/progress`              | GET    | Weak/strong topics, suggested_next |
| `/session/history`       | GET    | Conversation history for a session_id |

---

## Configuration and run

- **Backend:** `backend/config.py` — `OLLAMA_MODEL` (qwen3), `AGENT_MODE`, `BACKEND_ROOT`, Whisper/TTS/history limits.
- **Start:** From repo root, `./start.sh` (starts Ollama then backend). Then `cd frontend && flutter run -d macos`.
- **Profile:** Created by onboarding or by copying `backend/profile.example.json` to `backend/profile.json` and editing.

---

## What stays local (gitignored)

- `backend/profile.json` — your profile
- `backend/progress.json` — topic scores
- `backend/sessions/*.json` — session logs and research cache

No cloud DB; no API keys required for core use.
