# Studia Constitution

## Core Principles

### I. specs.md is the Source of Truth
The root file `specs.md` is the authoritative specification. All implementation MUST follow it. No feature, API design, or architectural decision may contradict what is documented there. If implementation reveals a spec ambiguity or error, the spec MUST be updated before code proceeds.

### II. Local-First, No Cloud
All data (profile, progress, sessions, research cache) lives on the local filesystem. No cloud databases, no external API keys (aside from optional DuckDuckGo-style search). The app runs entirely on-device with Ollama, Whisper, and the FastAPI backend.

### III. Spec Consistency Before Coding
Resolve any spec inconsistencies from the review (voice API, TTS, curriculum, context window, etc.) before implementing. Do not code around spec gaps — fix the spec first, then implement.

### IV. Streaming by Default
Chat and voice responses use SSE streaming. Tokens arrive one by one so the Flutter UI feels instant, like ChatGPT. Do not block on full LLM responses when streaming is specified.

### V. Curriculum-Driven Progress
Topic IDs and labels come from `curriculum.json`. Tracker and progress screen MUST use this taxonomy. Profile `needs_depth` is mapped to curriculum IDs via keyword overlap — no free-form topic IDs in progress.

## Technology Stack

- **Backend**: FastAPI, Ollama (local LLM), faster-whisper (STT), pyttsx3 (v1 TTS), ddgs (research)
- **Frontend**: Flutter, record (WAV 16kHz mono), provider, shared_preferences
- **Start/Stop**: start.sh and stop.sh orchestrate Ollama and backend; backend does not subprocess Ollama

## Development Workflow

- Implement features in order: backend core (config, llm, context) → endpoints → frontend
- Run `/speckit.analyze` before `/speckit.implement` to validate consistency
- Session logging and research cache are mandatory for v1

## Governance

Constitution supersedes ad-hoc development practices. Amendments require updating this file and bumping the version. All PRs must verify compliance with principles I–V.

**Version**: 1.0.0 | **Ratified**: 2026-02-28 | **Last Amended**: 2026-02-28
