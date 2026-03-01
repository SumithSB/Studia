# Studia

A local, API-first interview preparation coach. FastAPI backend with a minimal HTML/CSS/JS web UI, powered by Ollama (local LLM). Profiles and conversation history live in PostgreSQL.

![Studia — Ready to practice](docs/screenshot-ready-to-practice.png)

## Features

### Profiles

**Purpose:** Give the coach a clear picture of who you are so advice is tailored, not generic.

- **Create from documents** — Upload one or more resumes (PDF, DOCX, TXT) and optionally a LinkedIn export ZIP. The LLM extracts structured data: name, current role, target roles, strong areas, areas needing depth, experience highlights, interview styles to prepare for, and study style. This is stored as a profile in the database.
- **Multiple profiles** — You can create several profiles (e.g. different resumes or personas). Each has its own progress and curriculum. The UI lets you switch the active profile and set a default.
- **Onboarding without uploads** — If you have no profile yet, you can describe yourself in chat; the agent can create a profile via a `create_profile` tool using the details you provide.
- **Target role** — Per session you can set a target role (e.g. “Backend engineer”). The coach uses this to focus advice and system design questions on that role.

### Chat

**Purpose:** Main way to interact with the coach — ask questions, paste job descriptions, name topics, or attach files.

- **Streaming responses** — Replies are streamed over SSE so you see text as it’s generated.
- **Session and context** — Each conversation is tied to a session ID. History is stored in the database and used to build the context sent to the LLM (with optional summarisation for long threads). The coach also receives your active profile and target role so answers are personalised.
- **Attachments** — You can attach files (e.g. PDF, DOCX, TXT) in chat. If you have no profile, attaching a resume can create one automatically; otherwise the extracted text is appended to your message so the coach can reference it.
- **Setup mode** — When no profile exists, the app runs in “setup” mode: the agent can create a profile from conversation or from uploaded files, and the system prompt guides the coach to collect what’s needed.

### Agent and tools

**Purpose:** The LLM can act on your behalf — research companies, parse job descriptions, look up progress and curriculum, and update topic scores — so you get concrete, up-to-date answers.

- **research_company** — When you mention a company, the agent can look it up. The backend searches LeetCode discussions, Blind, Glassdoor, and GitHub for interview experiences, then uses the LLM to summarise rounds, topics, difficulty, and tips. Results are cached for a few days to avoid repeated lookups.
- **parse_jd** — When you paste a job description, the agent parses it and runs a gap analysis against your profile: required vs nice-to-have skills, seniority, tech stack, and what you should focus on. Requires an active profile.
- **get_progress** — When you ask what to study next or about weak/strong topics, the agent fetches your progress: weak topics (score &lt; 0.4), strong topics (score ≥ 0.7), and a suggested next topic (prioritising areas that match your profile’s “needs depth” or your weakest score).
- **lookup_curriculum** — Returns the list of topics (optionally by category) so the coach can suggest specific curriculum items or explain what’s available.
- **update_topic_score** — After discussing a topic, the agent can record your level: `strong`, `partial`, or `weak`. Scores are updated in the database (strong +0.3, partial +0.1, weak −0.1, clamped 0–1). This keeps weak/strong and “suggested next” in sync with how you’re actually doing.

### Progress and curriculum

**Purpose:** Track which topics you’re strong or weak in and what to study next, so the coach can recommend accordingly.

- **Curriculum** — A taxonomy of topics (id, label, category, keywords). It is seeded from your profile when you onboard: labels from “strong areas”, “needs depth”, “target roles”, and “interview styles” become curriculum topics. The agent can also add or reference topics over time.
- **Progress** — Stored per profile: for each topic, a score (0–1), label, and last_visited. Weak/strong lists and “suggested next” are derived from these scores (weak &lt; 0.4, strong ≥ 0.7). Suggested next prefers topics that match your profile’s “needs depth”, then falls back to your weakest topic.
- **API** — `GET /progress?profile_id=...` returns weak, strong, suggested_next, and suggested_next_label for the given (or default) profile.

### Company and JD research (standalone API)

**Purpose:** Let the web UI or other clients trigger research without going through chat.

- **POST /research** — `type=company` and `value=Company Name` returns the same company research (summary from LeetCode/Blind/Glassdoor/GitHub, cached). `type=jd` and `value=<job description text>` plus optional `profile_id` returns JD parsing and gap analysis against that profile. Useful for “paste a job description” or “research this company” buttons in the UI.

### Session history

**Purpose:** Persist conversation so you can resume or inspect past chats.

- **GET /session/history?session_id=...** — Returns the conversation history for that session (list of role/content exchanges). Stored in the database; the coach uses it (with optional summarisation) to maintain context across long threads.

### Data and deployment

- **Database** — All state (profiles, progress, curriculum, sessions) lives in PostgreSQL. No file-based storage for runtime data. Set `DATABASE_URL` in `.env`.
- **Local only** — No cloud APIs or keys; Ollama runs on your machine. Research uses DuckDuckGo and the local LLM for summarisation; company research cache is stored under `backend/sessions/` (gitignored).
- **API-first** — Every feature is driven by APIs. The bundled web UI is a static HTML/CSS/JS client; you can replace it with another front end or CLI.

## Tech stack

| Layer   | Technologies |
|---------|---------------|
| Frontend | Static HTML/CSS/JS (served by backend); no build step |
| Backend | FastAPI, uvicorn, SSE streaming |
| Database | PostgreSQL (`DATABASE_URL` required) |
| LLM | Ollama (qwen3 with agent/tool calling) |
| Research | ddgs (DuckDuckGo) |

## Quick start

### Prerequisites

- [Ollama](https://ollama.ai) — e.g. `brew install ollama`
- [PostgreSQL](https://www.postgresql.org/) — create a database (e.g. `createdb studia`) and set `DATABASE_URL`
- Python 3.10+

### 1. Pull the LLM model

```bash
ollama pull qwen3
```

### 2. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate   # or: venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set `DATABASE_URL` to your PostgreSQL connection string (see Configuration).

### 3. Run

```bash
# From project root (start Ollama + backend)
./start.sh
```

Then open **http://127.0.0.1:8000**. First time: create a profile via onboarding (resumes/LinkedIn). Then select profile and target role, and chat.

### Stop

```bash
./stop.sh
```

### Run with Docker

Run Ollama on the host (e.g. `ollama pull qwen3` and start Ollama). Then:

```bash
docker compose up --build
```

Open **http://127.0.0.1:8000**. The backend in the container uses `OLLAMA_BASE_URL=http://host.docker.internal:11434` by default so it can reach Ollama on the host (Mac/Windows). On Linux, set `OLLAMA_BASE_URL=http://host.docker.internal:11434` or use your host’s IP. Set `DATABASE_URL` to your PostgreSQL instance (e.g. `docker compose --profile postgres up` for a Postgres service and point the backend at it).

## API reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check; returns `{ "status": "ok", "db": "ok" }` |
| `/profile/status` | GET | `exists`, `default_profile_id`, `profiles: [{ id, label }]` |
| `/profile/from-uploads` | POST | Multipart: resumes + optional linkedin ZIP + optional `label` → creates profile, returns `profile_id` |
| `/profile/default` | POST | Form: `profile_id` — set default profile |
| `/chat` | POST | JSON: `message`, `session_id`, `profile_id` (required), optional `target_role` → SSE stream |
| `/progress` | GET | Query: optional `profile_id` (default profile if omitted) |
| `/research` | POST | Form: `type` (company/jd), `value`; for jd, optional `profile_id` |
| `/session/history` | GET | Query: `session_id` → conversation history |

The backend is API-first: you can build another client (CLI, mobile app, etc.) that talks to these endpoints; all state is in the database.

## Configuration

Configuration is via environment variables. Copy `.env.example` to `.env` and adjust. Key variables:

- `OLLAMA_BASE_URL` — default `http://localhost:11434`
- `OLLAMA_MODEL` — default `qwen3`
- `BACKEND_HOST`, `BACKEND_PORT` — server bind
- `DATABASE_URL` — **required**; PostgreSQL connection string, e.g. `postgresql://user:password@localhost:5432/studia`.

See `.env.example` for the full list. All app state (profiles, progress, curriculum, sessions) is in PostgreSQL; `.env` and `backend/sessions/` (research cache) are gitignored.

---

*Built with [Cursor](https://cursor.com) and Claude — vibe coded.*
