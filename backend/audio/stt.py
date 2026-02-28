"""Whisper speech-to-text via faster-whisper."""

import io

from config import SAMPLE_RATE, WHISPER_DEVICE, WHISPER_MODEL_SIZE


def transcribe(audio_bytes: bytes) -> str:
    """Transcribe WAV audio (16kHz mono) to text."""
    from faster_whisper import Whisper

    model = Whisper(WHISPER_MODEL_SIZE, device=WHISPER_DEVICE, compute_type="int8")
    segments, info = model.transcribe(
        io.BytesIO(audio_bytes),
        language="en",
        beam_size=1,
        vad_filter=True,
    )
    return " ".join(s.text.strip() for s in segments if s.text).strip() or ""
