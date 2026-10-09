from __future__ import annotations

import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path

from app.config import get_settings


@dataclass
class StoredFile:
    filename: str
    stored_path: Path
    size_bytes: int
    mime_type: str


def save_upload(original_name: str, mime_type: str, stream) -> StoredFile:
    """Persist an uploaded recording to the storage directory."""
    settings = get_settings()
    settings.storage_dir.mkdir(parents=True, exist_ok=True)

    suffix = Path(original_name).suffix or ".webm"
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    dest = settings.storage_dir / stored_name

    with dest.open("wb") as out:
        shutil.copyfileobj(stream, out)

    return StoredFile(
        filename=original_name,
        stored_path=dest,
        size_bytes=dest.stat().st_size,
        mime_type=mime_type or "application/octet-stream",
    )


def delete_file(stored_path: str | Path) -> None:
    try:
        Path(stored_path).unlink(missing_ok=True)
    except OSError:
        pass
