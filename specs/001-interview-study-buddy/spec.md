# Feature Specification: Studia

**Feature Branch**: `001-interview-study-buddy`
**Created**: 2026-02-28
**Status**: Draft
**Authoritative Spec**: Root `specs.md` — this file summarizes; all implementation MUST follow specs.md.

## User Scenarios

### User Story 1 — Text Chat (Priority: P1)
User types a message, receives streaming LLM response. Profile-aware, topic-aware. Session history persisted.

**Acceptance**: POST /chat returns SSE stream; Flutter displays tokens as they arrive.

### User Story 2 — Voice Input (Priority: P2)
User records voice, backend transcribes with Whisper, sends to chat logic, streams response. Same UX as text chat.

**Acceptance**: POST /voice accepts WAV, returns SSE with transcript first event then token stream.

### User Story 3 — Progress & Weak Area Tracking (Priority: P3)
Topics from curriculum.json; scores from tracker. Progress screen shows weak/strong topics; suggested next.

**Acceptance**: GET /progress returns weak/strong/suggested_next; tap topic navigates to chat.

### User Story 4 — Company Research (Priority: P4)
User mentions company or pastes JD; backend scrapes, summarises, injects context. Cached per company.

**Acceptance**: POST /research or auto-trigger from chat; context injected into system prompt.

### User Story 5 — Session & JD Paste (Priority: P5)
Session history restored on reopen; JD paste via modal.

**Acceptance**: GET /session/history returns exchanges; paperclip opens paste modal.

## Requirements Summary

- FastAPI backend: /chat (SSE), /voice (SSE), /research, /progress, /session/history
- Flutter frontend: chat screen, progress screen, streaming UI, voice recording (WAV 16kHz mono)
- Local-only: Ollama, Whisper, pyttsx3 (server-side TTS), ddgs for research
- start.sh / stop.sh orchestrate Ollama + backend
