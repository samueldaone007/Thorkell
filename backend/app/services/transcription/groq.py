from __future__ import annotations

from pathlib import Path

import httpx

from app.config import get_settings
from app.services.transcription.base import (
    TranscribedSegment,
    TranscriptionProvider,
    TranscriptionResult,
)


class GroqTranscriptionProvider(TranscriptionProvider):
    """Free-tier cloud transcription via Groq's OpenAI-compatible endpoint."""

    name = "groq"

    def __init__(self) -> None:
        self.settings = get_settings()
        if not self.settings.groq_api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Add it to backend/.env or set "
                "TRANSCRIPTION_PROVIDER=whisper_local."
            )

    async def transcribe(
        self, audio_path: Path, language: str | None = None
    ) -> TranscriptionResult:
        url = f"{self.settings.groq_base_url.rstrip('/')}/audio/transcriptions"
        headers = {"Authorization": f"Bearer {self.settings.groq_api_key}"}

        data = {
            "model": self.settings.groq_transcription_model,
            "response_format": "verbose_json",
        }
        if language:
            data["language"] = language

        with audio_path.open("rb") as fh:
            files = {"file": (audio_path.name, fh, "application/octet-stream")}
            async with httpx.AsyncClient(timeout=600) as client:
                resp = await client.post(url, headers=headers, data=data, files=files)

        if resp.status_code >= 400:
            raise RuntimeError(f"Groq transcription failed ({resp.status_code}): {resp.text}")

        payload = resp.json()
        raw_segments = payload.get("segments") or []
        segments: list[TranscribedSegment] = []
        for seg in raw_segments:
            segments.append(
                TranscribedSegment(
                    start_ms=int(round(float(seg.get("start", 0.0)) * 1000)),
                    end_ms=int(round(float(seg.get("end", 0.0)) * 1000)),
                    text=str(seg.get("text", "")).strip(),
                )
            )

        # Fallback: some responses only carry a flat `text` field.
        if not segments and payload.get("text"):
            segments.append(
                TranscribedSegment(start_ms=0, end_ms=0, text=str(payload["text"]).strip())
            )

        duration_ms = None
        if payload.get("duration"):
            duration_ms = int(round(float(payload["duration"]) * 1000))

        return TranscriptionResult(
            provider=self.name,
            model=self.settings.groq_transcription_model,
            language=payload.get("language") or language,
            duration_ms=duration_ms,
            segments=segments,
        )
