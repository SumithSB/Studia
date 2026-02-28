"""Text-to-speech via pyttsx3 (server-side playback and audio generation for client)."""

import tempfile
import threading
from pathlib import Path

from config import TTS_ENABLED, TTS_RATE


def _synthesize_to_file(text: str, path: str) -> bool:
    """Generate speech to file. Returns True on success."""
    if not text.strip():
        return False
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", TTS_RATE)
        engine.save_to_file(text, path)
        engine.runAndWait()
        engine.stop()
        return Path(path).exists() and Path(path).stat().st_size > 0
    except Exception:
        return False


def speak_to_bytes(text: str) -> bytes | None:
    """Generate speech as audio bytes for client playback. Returns WAV bytes or None."""
    if not TTS_ENABLED or not text.strip():
        return None
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        path = f.name
    try:
        if _synthesize_to_file(text, path):
            return Path(path).read_bytes()
    finally:
        try:
            Path(path).unlink(missing_ok=True)
        except OSError:
            pass
    return None


def speak(text: str) -> None:
    """Speak text using pyttsx3. Runs in background thread to avoid blocking."""
    if not TTS_ENABLED or not text.strip():
        return

    def _run():
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", TTS_RATE)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception:
            pass

    threading.Thread(target=_run, daemon=True).start()
