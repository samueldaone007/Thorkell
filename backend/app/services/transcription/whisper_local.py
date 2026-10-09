from __future__ import annotations

import asyncio
from pathlib import Path

from app.config import get_settings
from app.services.transcription.base import (
    TranscribedSegment,
    TranscriptionProvider,
    TranscriptionResult,
)


class WhisperLocalProvider(TranscriptionProvider):
    """Fully-local, offline transcription using faster-whisper.

    Requires `pip install faster-whisper` (see requirements-optional.txt).
    Good for privacy and zero API cost, but slower on a modest CPU.
    """

    name = "whisper_local"

    def __init__(self) -> None:
        self.settings = get_settings()
        try:
            from faster_whisper import WhisperModel  # noqa: F401
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise RuntimeError(
                "faster-whisper is not installed. Run "
                "`pip install -r requirements-optional.txt` or use the Groq provider."
            ) from exc

    async def transcribe(
        self, audio_path: Path, language: str | None = None
    ) -> TranscriptionResult:
        return await asyncio.get_running_loop().run_in_executor(
            None, self._transcribe_sync, audio_path, language
        )

    def _transcribe_sync(self, audio_path: Path, language: str | None) -> TranscriptionResult:
        from faster_whisper import WhisperModel

        model = WhisperModel(
            self.settings.whisper_local_model,
            device=self.settings.whisper_local_device,
            compute_type="int8",
        )
        raw_segments, info = model.transcribe(
            str(audio_path), language=language, vad_filter=True
        )

        segments: list[TranscribedSegment] = []
        for seg in raw_segments:
            segments.append(
                TranscribedSegment(
                    start_ms=int(round(seg.start * 1000)),
                    end_ms=int(round(seg.end * 1000)),
                    text=seg.text.strip(),
                )
            )

        return TranscriptionResult(
            provider=self.name,
            model=self.settings.whisper_local_model,
            language=getattr(info, "language", language),
            duration_ms=int(round(getattr(info, "duration", 0.0) * 1000)) or None,
            segments=segments,
        )
