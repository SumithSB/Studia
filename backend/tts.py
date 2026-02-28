"""Text-to-speech via pyttsx3 (server-side playback)."""

import threading
from config import TTS_ENABLED, TTS_RATE


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
