from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ directory
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Thorkell"
    debug: bool = True

    database_url: str = f"sqlite:///{(BASE_DIR / 'thorkell.db').as_posix()}"
    storage_dir: Path = BASE_DIR / "storage"

    # --- Providers (free now, swappable to paid later) ---
    transcription_provider: str = "groq"  # groq | whisper_local
    summarization_provider: str = "groq"  # groq | none
    diarization_provider: str = "manual"  # manual | assemblyai

    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_transcription_model: str = "whisper-large-v3-turbo"
    # llama-3.3-70b-versatile was decommissioned 2026-08-16; see
    # https://console.groq.com/docs/deprecations for the current model list.
    groq_chat_model: str = "openai/gpt-oss-120b"

    whisper_local_model: str = "base.en"
    whisper_local_device: str = "cpu"

    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Max upload size in bytes (default 200 MB)
    max_upload_bytes: int = 200 * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
