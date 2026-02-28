# Studia — Full Build Specification

> A fully local, voice + text interview preparation study companion. Flutter frontend (CV-worthy showcase project) talking to a FastAPI backend, powered by Ollama (local LLM), Whisper (local STT), and on-demand company research. Runs only when you need it. Feels like Claude/ChatGPT but knows everything about you.

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────┐
│              Flutter App (Frontend)              │
│   Chat UI · Voice Recording · JD Upload         │
└────────────────────┬────────────────────────────┘
                     │ HTTP / WebSocket (localhost)
┌────────────────────▼────────────────────────────┐
│           FastAPI Backend (Python)               │
│                                                  │
│  ┌─────────┐ ┌─────────┐ ┌──────────────────┐  │
│  │  /chat  │ │ /voice  │ │    /research      │  │
│  └────┬────┘ └────┬────┘ └────────┬─────────┘  │
│       │           │               │              │
│  ┌────▼───────────▼───┐  ┌────────▼──────────┐  │
│  │   context.py       │  │   research.py      │  │
│  │   tracker.py       │  │   (scraping +      │  │
│  │ agent+tools+llm    │  │    summarisation)  │  │
│  └────────────────────┘  └───────────────────┘  │
│                                                  │
│  ┌─────────────────────────────────────────┐    │
│  │  stt.py (Whisper)  │  tts.py (pyttsx3)  │    │
│  └─────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│              Ollama (local LLM)                  │
│         qwen3 (agent + tool calling)             │
│         Runs only when backend is running        │
└─────────────────────────────────────────────────┘
```

### Key Design Decisions
- Flutter app is the only thing the user touches
- `start.sh` starts both Ollama and the FastAPI backend; `stop.sh` stops both. Backend does not start Ollama via subprocess.
- All data (profile, progress, sessions, research cache) lives on the local filesystem, never a cloud database
- Streaming responses — FastAPI streams LLM output token by token to Flutter so it feels instant, like ChatGPT

---

## 2. Repository Structure

```
studia/
│
├── backend/                         # FastAPI Python backend
│   ├── main.py                      # FastAPI app, route definitions
│   ├── config.py                    # All settings, BACKEND_ROOT
│   ├── core/                        # LLM, agent, context
│   │   ├── agent.py                 # Agent loop with tool calling
│   │   ├── context.py               # System prompt assembly
│   │   └── llm.py                   # Ollama streaming interface
│   ├── services/                    # Business logic
│   │   ├── research.py              # Company/JD research and scraping
│   │   ├── session.py               # Session state and history
│   │   ├── tools.py                 # Tool definitions and executor
│   │   └── tracker.py               # Weak area tracker
│   ├── audio/                       # Speech
│   │   ├── stt.py                   # Whisper speech-to-text
│   │   └── tts.py                   # pyttsx3 text-to-speech
│   ├── profile.json                 # Your profile — edit freely
│   ├── curriculum.json              # Topic taxonomy (IDs, labels, category mapping)
│   ├── progress.json                # Topic scores (auto-created)
│   ├── requirements.txt
│   └── sessions/                    # Session logs (auto-created)
│       ├── session_YYYYMMDD_HHMMSS.json
│       └── research_cache.json
│
├── frontend/                        # Flutter app
│   ├── lib/
│   │   ├── main.dart
│   │   ├── screens/
│   │   │   ├── chat_screen.dart     # Main chat UI
│   │   │   └── progress_screen.dart # Topic progress view
│   │   ├── widgets/
│   │   │   ├── message_bubble.dart  # Chat message component
│   │   │   ├── voice_button.dart    # Record button with states
│   │   │   └── topic_chip.dart      # Topic suggestion chips
│   │   ├── services/
│   │   │   ├── api_service.dart     # HTTP calls to FastAPI
│   │   │   └── audio_service.dart   # Mic recording logic
│   │   └── models/
│   │       ├── message.dart
│   │       └── topic.dart
│   └── pubspec.yaml
│
├── start.sh                         # One command to start everything
└── stop.sh                          # One command to stop everything
```

---

## 3. Start / Stop Scripts

### `start.sh`
```bash
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
source venv/bin/activate
uvicorn main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!
echo $BACKEND_PID > ../.backend.pid

echo "Backend running at http://127.0.0.1:8000"
echo "Open the Flutter app or run: flutter run -d macos"
```

### `stop.sh`
```bash
#!/bin/bash
echo "Stopping Studia..."
kill $(cat .backend.pid) 2>/dev/null
kill $(cat .ollama.pid) 2>/dev/null
rm -f .backend.pid .ollama.pid
echo "Stopped."
```

---

## 4. Backend — FastAPI (`backend/main.py`)

### API Endpoints

#### `POST /chat`
Main text conversation endpoint. Accepts a message, returns a streaming response.

**Request:**
```json
{
  "message": "Let's talk about the event loop",
  "session_id": "abc123"
}
```

**Response:** Server-Sent Events (SSE) stream — tokens arrive one by one so Flutter can render them as they come in, exactly like ChatGPT.

```
data: {"token": "Sure"}
data: {"token": " —"}
data: {"token": " so"}
data: {"done": true, "topic_detected": "python.advanced.async_event_loop"}
```

#### `POST /voice`
Accepts a WAV audio file, transcribes it with Whisper, sends to `/chat` logic, and returns both transcript and streaming bot response in a single response — same pattern as `/chat`.

**Request:** `multipart/form-data` with `audio` field (WAV file) and `session_id`

**Response:** Server-Sent Events (SSE) stream. First event contains transcript and metadata; subsequent events stream tokens:
```
data: {"transcript": "Let's talk about the event loop", "session_id": "abc123"}
data: {"token": "Sure"}
data: {"token": " —"}
data: {"token": " so"}
data: {"done": true, "topic_detected": "python.advanced.async_event_loop"}
```
Client displays transcript as user message, then streams bot tokens as they arrive — one request, no second `stream_url` call.

#### `POST /research`
Triggers company research or JD parsing.

**Request:**
```json
{
  "type": "company",
  "value": "Monzo"
}
```
or
```json
{
  "type": "jd",
  "value": "We are looking for a Senior AI Engineer... [full JD text]"
}
```

**Response:**
```json
{
  "summary": "Monzo typically runs 4 rounds for backend/AI roles...",
  "gap_analysis": "Based on this JD vs your profile, focus on: ...",
  "topics_to_prioritise": ["system_design.rate_limiter", "backend.reliability.observability"]
}
```

#### `GET /progress`
Returns current topic scores for the progress screen.

**Response:**
```json
{
  "weak": [
    {"id": "dsa.dp.2d_patterns", "score": 0.0, "label": "2D Dynamic Programming"},
    {"id": "python.internals.gil", "score": 0.2, "label": "The GIL"}
  ],
  "strong": [
    {"id": "ml.llm.rag_pipeline", "score": 0.8, "label": "RAG Pipeline Architecture"}
  ],
  "suggested_next": "dsa.dp.2d_patterns"
}
```

#### `GET /session/history`
Returns current session conversation history for UI restore on app reopen.

**Request:** Query param `session_id` (required)

**Response:**
```json
[
  {"role": "user", "content": "Let's talk about the event loop"},
  {"role": "assistant", "content": "Sure — so the event loop in Python..."}
]
```

---

## 5. Backend — Configuration (`backend/config.py`)

```python
OLLAMA_MODEL            = "qwen3"
AGENT_MODE              = True
MAX_AGENT_TURNS         = 5
OLLAMA_BASE_URL         = "http://localhost:11434"
WHISPER_MODEL_SIZE      = "base.en"
WHISPER_DEVICE          = "cpu"
SAMPLE_RATE             = 16000
TTS_ENABLED             = True          # Set False to disable spoken responses
TTS_RATE                = 160
LOG_SESSIONS            = True
MAX_HISTORY_EXCHANGES   = 30
RESEARCH_MAX_SOURCES    = 8
RESEARCH_CACHE_DAYS     = 7
BACKEND_HOST            = "127.0.0.1"
BACKEND_PORT            = 8000
```

When `AGENT_MODE` is True, the chat/voice endpoints use `agent.agent_stream()` instead of `llm.stream_completion()`. The agent passes tools to Ollama (qwen3). When the model returns `tool_calls`, the backend executes them via `tools.execute_tool()` and continues the loop until a text response or `MAX_AGENT_TURNS` is reached.

**Tools:** `research_company`, `parse_jd`, `get_progress`, `lookup_curriculum`, `update_topic_score`. SSE may include `{"tool_call": "name", "args": {...}}` for frontend "Researching…" UI.

---

## 6. Your Profile (`backend/profile.json`)

Edit this file freely — it is loaded fresh on every request so changes take effect immediately without restarting.

```json
{
  "name": "Sumith",
  "current_role": "MSc Advanced Computer Science, University of Leicester (graduating July 2026)",
  "consulting": "Technical Consultant at TechMachinery Labs and Visiminds Technologies — leading AI and cybersecurity projects",
  "experience_years": 4,
  "target_roles": ["AI Engineer", "Backend Engineer", "ML Engineer"],
  "target_market": "UK — full-time with visa sponsorship, applying from July 2026",

  "strong_areas": [
    "LLM integration and RAG pipelines",
    "Flask and FastAPI backend development",
    "Multi-cloud architecture",
    "Cybersecurity automation",
    "Flutter full-stack development",
    "MongoDB, Redis, Firestore",
    "JWT and OAuth authentication",
    "AI-assisted development (Cursor, Claude)"
  ],

  "needs_depth": [
    "Python internals — GIL, memory management, CPython",
    "DSA — trees, graphs, dynamic programming",
    "System design at scale",
    "SQL internals and query optimisation",
    "ML fundamentals — bias/variance, gradient descent",
    "Transformer architecture internals",
    "Distributed systems"
  ],

  "experience_highlights": [
    "Co-founded Drogher Technologies",
    "Production systems at Honeywell Forge handling thousands of requests",
    "Built portfolio website in Flutter using AI agents in under 6 hours",
    "Led AI and cybersecurity projects at TechMachinery Labs / Visiminds",
    "Dissertation: Fashion AI — hybrid CV + rule-based + LLM styling system"
  ],

  "interview_styles_to_prepare": [
    "AI/ML system design rounds",
    "Backend architectural deep dives",
    "Live coding with verbal explanation",
    "Behavioural and values-based rounds",
    "LLM engineering and RAG system design"
  ],

  "study_style": "Conversational — talk like a smart friend, use real examples anchored to my background, go deep on internals, allow natural tangents and follow-up questions"
}
```

---

## 7. System Prompt (`backend/context.py`)

Assembled dynamically from three parts:

### Part 1 — Core Identity (hardcoded)
```
You are Sumith's personal interview prep study buddy. You know him well.
You talk like a smart, expert friend — not a teacher, not a bot. Natural,
conversational, occasionally using humour. You use real examples and analogies
anchored to things he has already built to make new concepts click faster.

You never give generic textbook explanations. Everything is anchored to his profile.
If he already knows something well, skip the basics and go straight to the
interesting internals. If he asks a follow-up or tangent, follow it naturally
and come back on track organically.

You only discuss topics relevant to his interview preparation. Gently redirect
if conversation drifts off-topic.

You check understanding naturally mid-conversation the way a friend would —
never as a formal quiz. Things like "so you'd know what to say if they asked
you this right?" woven in naturally.

Never output bullet points, markdown, headers, or code blocks. Speak in natural
sentences only. If referencing code, describe it verbally.

Keep responses concise — 3 to 5 sentences per turn for conversational flow.
Go longer only when he explicitly asks for a deep dive.
```

### Part 2 — Profile (from profile.json, injected at runtime)
```
Here is who you are talking to:
[profile.json contents serialised as natural language]
```

### Part 3 — Company/JD Context (injected only when research has run)
```
Sumith is currently targeting [Company]. Here is what is known about their
interview process: [research summary]. Tailor the conversation to prepare
him specifically for this company's style and known question patterns.
```

---

## 8. Company Research (`backend/research.py`)

### Trigger Detection
Detected in every incoming message before sending to LLM. Triggers if message contains:
- A known company name pattern ("targeting X", "interview at X", "applying to X", "what does X ask")
- A pasted block over 200 words (treated as a JD)

### Scraping Sources
For each company, search and scrape in this order:

**1. LeetCode Discuss**
Query: `site:leetcode.com/discuss [company] interview experience`
Extract: question types, difficulty, rounds described

**2. Blind**
Query: `site:teamblind.com [company] interview`
Extract: candid round descriptions, what to expect, time pressure

**3. Glassdoor**
Query: `[company] software engineer interview questions site:glassdoor.com`
Note: Glassdoor blocks direct scraping — use DuckDuckGo snippets only, do not attempt direct fetch

**4. GitHub**
Query: `[company] interview prep questions site:github.com`
Extract: curated question lists, experience writeups

### Summarisation
After scraping, send all extracted text to Ollama with:
```
Summarise the interview process at [company] for backend/AI engineering roles.
Cover: number of rounds, types of rounds, technical topics commonly asked,
difficulty level, any patterns or tips. Be specific and concise.
Keep it under 300 words.
```

### JD Parsing
Extract from JD text:
- Required technical skills
- Nice-to-have skills
- Seniority signals
- Tech stack mentioned

Cross-reference against `profile.json` strong_areas and needs_depth.
Generate gap analysis: what the user needs to focus on given this specific JD.

### Cache (`backend/sessions/research_cache.json`)
```json
{
  "monzo": {
    "fetched_at": "2026-02-28T14:00:00",
    "summary": "Monzo runs 4 rounds for backend roles...",
    "sources_used": ["leetcode", "blind", "github"]
  }
}
```
TTL: `RESEARCH_CACHE_DAYS` from config. Stale cache is refreshed automatically.

---

## 9. Curriculum & Weak Area Tracker

### Curriculum (`backend/curriculum.json`)

Canonical topic taxonomy used by the tracker and progress screen. Maps topic IDs (used in `progress.json`) to labels and categories. `needs_depth` items in profile are matched to these IDs by keyword/semantic overlap.

**Schema:**
```json
{
  "topics": [
    {"id": "python.internals.gil", "label": "The GIL", "category": "python.internals", "keywords": ["gil", "memory management", "cpython"]},
    {"id": "python.internals.memory", "label": "Python Memory Management", "category": "python.internals", "keywords": ["memory", "gc", "reference counting"]},
    {"id": "python.advanced.async_event_loop", "label": "Async and Event Loop", "category": "python.advanced", "keywords": ["async", "event loop", "asyncio"]},
    {"id": "dsa.dp.1d", "label": "1D Dynamic Programming", "category": "dsa.dp", "keywords": ["dp", "dynamic programming", "1d"]},
    {"id": "dsa.dp.2d_patterns", "label": "2D Dynamic Programming", "category": "dsa.dp", "keywords": ["2d dp", "grid dp"]},
    {"id": "dsa.trees", "label": "Trees and Traversals", "category": "dsa", "keywords": ["trees", "bst", "traversal"]},
    {"id": "dsa.graphs", "label": "Graphs and Algorithms", "category": "dsa", "keywords": ["graphs", "bfs", "dfs"]},
    {"id": "system_design.rate_limiter", "label": "Rate Limiting", "category": "system_design", "keywords": ["rate limiter", "throttling"]},
    {"id": "system_design.scale", "label": "System Design at Scale", "category": "system_design", "keywords": ["scaling", "distributed"]},
    {"id": "ml.llm.rag_pipeline", "label": "RAG Pipeline Architecture", "category": "ml.llm", "keywords": ["rag", "retrieval", "embedding"]},
    {"id": "ml.fundamentals", "label": "ML Fundamentals", "category": "ml", "keywords": ["bias variance", "gradient descent"]},
    {"id": "ml.transformers", "label": "Transformer Architecture", "category": "ml.llm", "keywords": ["transformer", "attention"]},
    {"id": "backend.reliability.observability", "label": "Observability and Reliability", "category": "backend", "keywords": ["observability", "logging", "metrics"]},
    {"id": "sql.internals", "label": "SQL Internals and Query Optimisation", "category": "sql", "keywords": ["sql", "query optimization", "indexes"]}
  ]
}
```

`progress.json` is auto-created from this curriculum when a topic is first visited; initial score is 0.5. Tracker maps `needs_depth` free text to curriculum IDs using keyword matching (e.g. "Python internals — GIL" → `python.internals.gil`).

### Tracker (`backend/tracker.py`)

#### Silent Background Scoring
After each topic conversation naturally concludes, a silent call to Ollama (never shown in UI, never spoken) assesses understanding:

```
Based on this conversation about [topic], did the user demonstrate:
strong understanding, partial understanding, or did they struggle?
Reply with exactly one word: strong / partial / weak
```

Score updates:
- `strong` → +0.3 (max 1.0)
- `partial` → +0.1
- `weak` → -0.1 (min 0.0)

### Topic Suggestion Logic
When user asks what to study or starts a session without a topic:
1. Load topics from `curriculum.json`; filter to those matching `needs_depth` (profile) via keyword overlap
2. Sort by score ascending (from `progress.json`)
3. Break ties by `last_visited` ascending (oldest first)
4. Return top suggestion with a brief reason ("You haven't touched 2D DP yet and it comes up a lot in FAANG-style rounds")

---

## 10. Flutter Frontend

### Screen 1 — Chat Screen (`chat_screen.dart`)

**Layout:**
- Top bar: app name + progress icon button (navigates to Screen 2)
- Message list: scrollable, auto-scrolls to bottom on new message
- Bottom bar: text input field + send button + mic button

**Message Bubbles:**
- User messages: right-aligned, solid fill
- Bot messages: left-aligned, subtle background — stream tokens in as they arrive (append character by character to simulate ChatGPT feel)
- Topic chips: when bot suggests a topic, render it as a tappable chip below the message

**Voice Button States:**
- Idle: mic icon
- Recording: pulsing red dot + "Recording..." label — tap again to stop
- Processing: spinner while backend transcribes and responds
- On stop: send WAV to `POST /voice`, display transcript as user message, stream bot response

**Company Research:**
- When user types a company name, a subtle banner appears: "Fetching interview data for Monzo..." with a spinner
- Once done, a system message appears in chat: "I've pulled Monzo's interview patterns. Here's what to know..."

**JD Upload:**
- Paperclip icon in top bar opens a text paste modal (v1: paste text; v2: file picker for PDF)

### Screen 2 — Progress Screen (`progress_screen.dart`)

**Layout:**
- Simple list of topics grouped by category
- Each topic shows a score bar (0 to 100%) and last visited date
- "Suggested Next" card at the top highlighting the weakest topic
- Tap any topic to jump back to chat with that topic pre-loaded

---

## 11. Flutter Dependencies (`pubspec.yaml`)

```yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^1.2.0                  # API calls to FastAPI
  record: ^5.0.0                # Mic recording — use RecordConfig(wav, 16kHz, mono)
  provider: ^6.1.1              # State management
  shared_preferences: ^2.2.2    # Store session_id locally
```

**v1 TTS note:** TTS is server-side only — pyttsx3 plays on the backend machine; user hears it if app and backend run on same Mac. `just_audio` is reserved for v2 (Kokoro) when audio is streamed to Flutter.

---

## 12. Backend Dependencies (`backend/requirements.txt`)

```
fastapi
uvicorn[standard]
faster-whisper
scipy
numpy
requests
beautifulsoup4
ddgs
pyttsx3
python-multipart
```

**Notes:** `ddgs` is the successor to duckduckgo-search. `sounddevice` removed — add back only if using faster-whisper with GPU audio I/O.

---

## 13. Setup Instructions

### Step 1: Install Ollama
```bash
brew install ollama
ollama pull deepseek-r1:8b
# Optional but recommended for system design / AI topics:
ollama pull qwen2.5:14b
```

### Step 2: Python Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Flutter Frontend
```bash
cd frontend
flutter pub get
```

### Step 4: Edit Your Profile
Edit `backend/profile.json` with any updates before first run.

### Step 5: Run
```bash
# From project root
chmod +x start.sh stop.sh
./start.sh

# Then in a new terminal
cd frontend
flutter run -d macos
```

---

## 14. v1 vs v2 Scope

### v1 — Build This First
- [x] FastAPI backend with `/chat` (streaming), `/voice`, `/research`, `/progress` endpoints
- [x] Flutter chat screen with streaming message rendering
- [x] Voice recording — click to start, click to stop, send WAV to backend
- [x] Text conversation — full chat interface
- [x] Profile-aware system prompt loaded from `profile.json`
- [x] Ollama streaming via SSE
- [x] Whisper STT in backend
- [x] Company research triggered automatically from chat messages
- [x] JD paste via modal
- [x] Progress screen with topic scores
- [x] Weak area tracker with silent background scoring
- [x] Session logging
- [x] start.sh / stop.sh scripts

### v2 — After v1 Works
- [ ] Polished UI — dark mode, animations, Claude-style design
- [ ] Kokoro TTS replacing pyttsx3 — streams audio to Flutter; add `just_audio` for playback
- [ ] PDF JD upload (file picker)
- [ ] Spaced repetition scheduling
- [ ] Topic heatmap visualisation on progress screen
- [ ] Export session as PDF study notes

---

## 15. CV / Portfolio Framing

This project demonstrates the full stack of skills relevant to AI engineering roles:

**Backend:** FastAPI, streaming APIs (SSE), REST design, Python async, local AI inference pipeline

**AI/ML:** Local LLM orchestration with Ollama, Whisper STT integration, prompt engineering, context management, RAG-adjacent pattern (retrieve → inject → generate)

**Frontend:** Flutter cross-platform app, real-time streaming UI, audio recording and processing

**Systems:** Local-first architecture, caching, session management, subprocess orchestration

**Description for CV:**
*"Studia — a fully local AI-powered interview preparation assistant using Flutter (frontend), FastAPI (backend), and Ollama (local LLM inference). Features voice and text conversation, profile-aware adaptive tutoring, real-time company interview data research, and cross-session weak area tracking. Runs entirely on-device with no API costs or rate limits."*

---

## 16. Known Constraints & Gotchas

- **DeepSeek-R1 think tokens**: Always strip `<think>...</think>` from LLM output before streaming to Flutter or sending to TTS. These can be very long.
- **SSE in Flutter**: Use the `http` package with chunked response reading. Do not use a WebSocket — SSE is simpler for one-directional streaming.
- **Glassdoor scraping**: Does not allow direct scraping. Use DuckDuckGo search snippets only. Never attempt a direct Glassdoor fetch.
- **pyttsx3 on macOS**: Blocking call — run in a background thread in FastAPI so it does not block the API response.
- **Ollama must be running before backend starts**: `start.sh` handles this with a 2-second sleep after starting Ollama. If Ollama is slow to start, increase the sleep.
- **profile.json hot reload**: The file is read on every `/chat` request so edits take effect immediately without restarting the backend.
- **Context window management** (`session.py`): After `MAX_HISTORY_EXCHANGES` turns, call Ollama with: "Summarise this interview prep conversation into a concise context block (max 400 words) preserving key topics discussed and user's level." Prepend the summary to subsequent requests; keep only the last 10 exchanges verbatim in the prompt. Store summarised block in session state; do not rewrite session files.
- **Audio format**: Flutter `record` package outputs AAC by default on macOS. Use `RecordConfig(encoder: AudioEncoder.wav, sampleRate: 16000, numChannels: 1)` for WAV (PCM 16-bit, 16kHz mono) to match Whisper's expected input format.