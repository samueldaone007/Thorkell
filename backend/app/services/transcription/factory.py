from __future__ import annotations

from app.config import get_settings
from app.services.transcription.base import TranscriptionProvider


def get_transcription_provider() -> TranscriptionProvider:
    """Resolve the configured transcription provider.

    Register new (paid) providers here — the rest of the app is untouched.
    """
    settings = get_settings()
    choice = settings.transcription_provider.lower()

    if choice == "groq":
        from app.services.transcription.groq import GroqTranscriptionProvider

        return GroqTranscriptionProvider()

    if choice == "whisper_local":
        from app.services.transcription.whisper_local import WhisperLocalProvider

        return WhisperLocalProvider()

    raise ValueError(f"Unknown TRANSCRIPTION_PROVIDER: {choice!r}")
