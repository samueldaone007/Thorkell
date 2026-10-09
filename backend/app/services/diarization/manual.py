from __future__ import annotations

from pathlib import Path

from app.services.diarization.base import DiarizationProvider
from app.services.transcription.base import TranscribedSegment


class ManualDiarizationProvider(DiarizationProvider):
    """No automatic speaker detection — labels are assigned by the user.

    This is the default because it needs no extra compute, works on a modest
    machine, and costs nothing.
    """

    name = "manual"

    async def label(
        self, audio_path: Path, segments: list[TranscribedSegment]
    ) -> list[TranscribedSegment]:
        return segments
