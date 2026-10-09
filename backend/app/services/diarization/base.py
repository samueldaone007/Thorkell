from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from app.services.transcription.base import TranscribedSegment


class DiarizationProvider(ABC):
    """Assigns a speaker label to each transcript segment.

    v1 ships only the manual provider (labels are set by the user in the UI).
    A future paid provider (AssemblyAI, Deepgram, pyannote) implements this
    interface and becomes selectable via DIARIZATION_PROVIDER.
    """

    name: str = "base"

    @abstractmethod
    async def label(
        self, audio_path: Path, segments: list[TranscribedSegment]
    ) -> list[TranscribedSegment]:
        raise NotImplementedError
