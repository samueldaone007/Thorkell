from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TranscribedSegment:
    start_ms: int
    end_ms: int
    text: str
    speaker_label: str | None = None


@dataclass
class TranscriptionResult:
    provider: str
    model: str
    language: str | None = None
    duration_ms: int | None = None
    segments: list[TranscribedSegment] = field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join(s.text.strip() for s in self.segments).strip()


class TranscriptionProvider(ABC):
    """Interface every transcription backend implements.

    Adding a paid provider (OpenAI, Deepgram, AssemblyAI, ...) means writing a
    new subclass and registering it in `factory.py` — no changes to the API layer.
    """

    name: str = "base"

    @abstractmethod
    async def transcribe(self, audio_path: Path, language: str | None = None) -> TranscriptionResult:
        raise NotImplementedError
