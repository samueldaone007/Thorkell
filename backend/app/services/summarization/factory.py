from __future__ import annotations

from app.config import get_settings
from app.services.summarization.base import SummarizationProvider


def get_summarization_provider() -> SummarizationProvider | None:
    """Resolve the configured summarization provider (or None if disabled)."""
    settings = get_settings()
    choice = settings.summarization_provider.lower()

    if choice in ("none", "off", ""):
        return None

    if choice == "groq":
        from app.services.summarization.groq import GroqSummarizationProvider

        return GroqSummarizationProvider()

    raise ValueError(f"Unknown SUMMARIZATION_PROVIDER: {choice!r}")
