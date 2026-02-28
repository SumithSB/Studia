# Implementation Plan: Studia

**Branch**: `001-interview-study-buddy` | **Date**: 2026-02-28 | **Spec**: [specs.md](../../specs.md) (root)

## Summary

Build a local interview prep companion: FastAPI backend with Ollama (LLM), Whisper (STT), pyttsx3 (TTS), ddgs (research); Flutter frontend with streaming chat, voice recording, progress screen.

## Technical Context

**Language/Version**: Python 3.10+, Flutter 3.x
**Primary Dependencies**: FastAPI, uvicorn, faster-whisper, ddgs, pyttsx3; Flutter http, record, provider
**Storage**: Local JSON files (profile.json, progress.json, curriculum.json, sessions/)
**Target Platform**: macOS (start.sh/stop.sh); backend 127.0.0.1:8000
**Project Type**: Web service (backend) + desktop/mobile app (Flutter)
**Constraints**: Local-first, no cloud; streaming responses; 16kHz mono WAV for Whisper

## Constitution Check

- specs.md is source of truth: Pass
- Local-first, no cloud: Pass
- Spec consistency resolved before coding: Pass (fixes applied)
- Streaming by default: Pass (SSE for /chat and /voice)
- Curriculum-driven progress: Pass (curriculum.json defined)

## Project Structure

```
backend/
├── main.py, config.py
├── llm.py, stt.py, tts.py, context.py, session.py, tracker.py, research.py
├── profile.json, curriculum.json, progress.json (auto-created)
├── requirements.txt
└── sessions/ (auto-created)

frontend/
├── lib/main.dart
├── lib/screens/chat_screen.dart, progress_screen.dart
├── lib/widgets/message_bubble.dart, voice_button.dart, topic_chip.dart
├── lib/services/api_service.dart, audio_service.dart
├── lib/models/message.dart, topic.dart
└── pubspec.yaml

start.sh, stop.sh (project root)
```
