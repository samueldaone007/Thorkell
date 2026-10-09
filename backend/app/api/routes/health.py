from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "transcription_provider": settings.transcription_provider,
        "summarization_provider": settings.summarization_provider,
        "diarization_provider": settings.diarization_provider,
        "groq_configured": bool(settings.groq_api_key),
    }
