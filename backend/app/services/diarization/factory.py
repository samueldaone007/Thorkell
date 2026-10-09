from __future__ import annotations

from app.config import get_settings
from app.services.diarization.base import DiarizationProvider


def get_diarization_provider() -> DiarizationProvider:
    settings = get_settings()
    choice = settings.diarization_provider.lower()

    if choice == "manual":
        from app.services.diarization.manual import ManualDiarizationProvider

        return ManualDiarizationProvider()

    raise ValueError(
        f"Unknown DIARIZATION_PROVIDER: {choice!r}. "
        "Implement and register it in app/services/diarization/factory.py."
    )
