from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.config import get_settings
from app.db import get_db
from app.models import (
    ActionItem,
    AudioAsset,
    Conversation,
    Speaker,
    Summary,
    Tag,
    Transcript,
    TranscriptSegment,
)
from app.schemas import (
    ConversationCreate,
    ConversationDetailOut,
    ConversationSummaryOut,
    ConversationUpdate,
    TagCreate,
)
from app.services import search as search_service
from app.services import storage
from app.services.diarization import get_diarization_provider
from app.services.export.markdown import to_markdown
from app.services.export.pdf import to_pdf
from app.services.summarization import get_summarization_provider
from app.services.transcription import get_transcription_provider

router = APIRouter(prefix="/conversations", tags=["conversations"])


def _get_conversation(db: Session, conversation_id: str) -> Conversation:
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


def _detail_query():
    return (
        select(Conversation)
        .options(
            selectinload(Conversation.tags),
            selectinload(Conversation.audio_assets),
            selectinload(Conversation.transcripts).selectinload(Transcript.segments),
            selectinload(Conversation.speakers),
            selectinload(Conversation.summaries),
            selectinload(Conversation.action_items),
        )
    )


@router.get("", response_model=list[ConversationSummaryOut])
def list_conversations(db: Session = Depends(get_db)) -> list[ConversationSummaryOut]:
    conversations = (
        db.execute(
            select(Conversation)
            .options(selectinload(Conversation.tags), selectinload(Conversation.transcripts))
            .order_by(Conversation.created_at.desc())
        )
        .scalars()
        .all()
    )
    out: list[ConversationSummaryOut] = []
    for c in conversations:
        item = ConversationSummaryOut.model_validate(c)
        item.has_transcript = any(t.segments for t in c.transcripts)
        out.append(item)
    return out


@router.post("", response_model=ConversationDetailOut, status_code=201)
def create_conversation(
    payload: ConversationCreate, db: Session = Depends(get_db)
) -> Conversation:
    conversation = Conversation(
        title=(payload.title or "Untitled conversation").strip() or "Untitled conversation",
        notes=payload.notes,
    )
    db.add(conversation)
    db.commit()
    return db.execute(_detail_query().where(Conversation.id == conversation.id)).scalar_one()


@router.get("/{conversation_id}", response_model=ConversationDetailOut)
def get_conversation(conversation_id: str, db: Session = Depends(get_db)) -> Conversation:
    conversation = db.execute(
        _detail_query().where(Conversation.id == conversation_id)
    ).scalar_one_or_none()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.patch("/{conversation_id}", response_model=ConversationDetailOut)
def update_conversation(
    conversation_id: str, payload: ConversationUpdate, db: Session = Depends(get_db)
) -> Conversation:
    conversation = _get_conversation(db, conversation_id)
    if payload.title is not None:
        conversation.title = payload.title.strip() or conversation.title
    if payload.notes is not None:
        conversation.notes = payload.notes
    db.commit()
    return db.execute(_detail_query().where(Conversation.id == conversation_id)).scalar_one()


@router.delete("/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: str, db: Session = Depends(get_db)) -> Response:
    conversation = _get_conversation(db, conversation_id)
    for asset in conversation.audio_assets:
        storage.delete_file(asset.stored_path)
    search_service.remove_conversation(db, conversation_id)
    db.delete(conversation)
    db.commit()
    return Response(status_code=204)


# --- Audio ---
@router.post("/{conversation_id}/audio", response_model=ConversationDetailOut)
def upload_audio(
    conversation_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> Conversation:
    conversation = _get_conversation(db, conversation_id)
    settings = get_settings()

    stored = storage.save_upload(
        file.filename or "recording.webm", file.content_type or "audio/webm", file.file
    )
    if stored.size_bytes > settings.max_upload_bytes:
        storage.delete_file(stored.stored_path)
        raise HTTPException(status_code=413, detail="Recording exceeds the maximum upload size")

    asset = AudioAsset(
        conversation_id=conversation.id,
        filename=stored.filename,
        stored_path=str(stored.stored_path),
        mime_type=stored.mime_type,
        size_bytes=stored.size_bytes,
    )
    db.add(asset)
    conversation.status = "recorded"
    conversation.error = None
    db.commit()
    return db.execute(_detail_query().where(Conversation.id == conversation_id)).scalar_one()


@router.get("/{conversation_id}/audio/{asset_id}")
def get_audio(
    conversation_id: str, asset_id: str, db: Session = Depends(get_db)
) -> FileResponse:
    asset = db.get(AudioAsset, asset_id)
    if asset is None or asset.conversation_id != conversation_id:
        raise HTTPException(status_code=404, detail="Audio not found")
    return FileResponse(asset.stored_path, media_type=asset.mime_type, filename=asset.filename)


# --- Transcription ---
@router.post("/{conversation_id}/transcribe", response_model=ConversationDetailOut)
async def transcribe_conversation(
    conversation_id: str, db: Session = Depends(get_db)
) -> Conversation:
    conversation = _get_conversation(db, conversation_id)
    if not conversation.audio_assets:
        raise HTTPException(status_code=400, detail="No audio uploaded yet")

    asset = conversation.audio_assets[-1]
    conversation.status = "transcribing"
    conversation.error = None
    db.commit()

    try:
        provider = get_transcription_provider()
        audio_path = Path(asset.stored_path)
        result = await provider.transcribe(audio_path)

        diarizer = get_diarization_provider()
        result.segments = await diarizer.label(audio_path, result.segments)

        # Replace any previous transcript so search stays clean.
        search_service.remove_conversation(db, conversation.id)
        for old in list(conversation.transcripts):
            db.delete(old)
        db.flush()

        transcript = Transcript(
            conversation_id=conversation.id,
            provider=result.provider,
            model=result.model,
            language=result.language,
        )
        db.add(transcript)
        db.flush()

        labels_seen: set[str] = set()
        for seg in result.segments:
            segment = TranscriptSegment(
                transcript_id=transcript.id,
                start_ms=seg.start_ms,
                end_ms=seg.end_ms,
                text=seg.text,
                speaker_label=seg.speaker_label,
            )
            db.add(segment)
            db.flush()
            search_service.index_segment(db, segment.id, conversation.id, seg.text)
            if seg.speaker_label:
                labels_seen.add(seg.speaker_label)

        existing_labels = set(
            db.execute(
                select(Speaker.label).where(Speaker.conversation_id == conversation.id)
            ).scalars()
        )
        for label in sorted(labels_seen - existing_labels):
            db.add(Speaker(conversation_id=conversation.id, label=label))

        conversation.status = "transcribed"
        conversation.language = result.language
        conversation.duration_ms = (
            result.duration_ms
            or (result.segments[-1].end_ms if result.segments else conversation.duration_ms)
        )
        db.commit()
    except Exception as exc:  # noqa: BLE001 - surface provider errors to the UI
        db.rollback()
        conversation = _get_conversation(db, conversation_id)
        conversation.status = "failed"
        conversation.error = str(exc)
        db.commit()
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return db.execute(_detail_query().where(Conversation.id == conversation_id)).scalar_one()


# --- Summarization ---
@router.post("/{conversation_id}/summarize", response_model=ConversationDetailOut)
async def summarize_conversation(
    conversation_id: str, db: Session = Depends(get_db)
) -> Conversation:
    conversation = _get_conversation(db, conversation_id)
    if not conversation.transcripts or not conversation.transcripts[-1].segments:
        raise HTTPException(status_code=400, detail="No transcript available to summarize")

    provider = get_summarization_provider()
    if provider is None:
        raise HTTPException(status_code=400, detail="Summarization is disabled")

    transcript_text = "\n".join(
        f"{seg.speaker_label or 'Speaker'}: {seg.text}"
        for seg in conversation.transcripts[-1].segments
    )

    try:
        result = await provider.summarize(transcript_text, conversation.title)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    db.add(
        Summary(
            conversation_id=conversation.id,
            provider=result.provider,
            model=result.model,
            content=result.summary,
        )
    )
    for draft in result.action_items:
        db.add(
            ActionItem(
                conversation_id=conversation.id,
                text=draft.text,
                assignee=draft.assignee,
                source="ai",
            )
        )
    db.commit()
    return db.execute(_detail_query().where(Conversation.id == conversation_id)).scalar_one()


# --- Tags ---
@router.post("/{conversation_id}/tags", response_model=ConversationDetailOut)
def add_tag(
    conversation_id: str, payload: TagCreate, db: Session = Depends(get_db)
) -> Conversation:
    conversation = _get_conversation(db, conversation_id)
    name = payload.name.strip()
    tag = db.execute(select(Tag).where(Tag.name == name)).scalar_one_or_none()
    if tag is None:
        tag = Tag(name=name)
        db.add(tag)
        db.flush()
    if tag not in conversation.tags:
        conversation.tags.append(tag)
    db.commit()
    return db.execute(_detail_query().where(Conversation.id == conversation_id)).scalar_one()


@router.delete("/{conversation_id}/tags/{tag_id}", response_model=ConversationDetailOut)
def remove_tag(
    conversation_id: str, tag_id: str, db: Session = Depends(get_db)
) -> Conversation:
    conversation = _get_conversation(db, conversation_id)
    tag = db.get(Tag, tag_id)
    if tag is not None and tag in conversation.tags:
        conversation.tags.remove(tag)
        db.commit()
    return db.execute(_detail_query().where(Conversation.id == conversation_id)).scalar_one()


# --- Export ---
@router.get("/{conversation_id}/export")
def export_conversation(
    conversation_id: str, format: str = "md", db: Session = Depends(get_db)
) -> Response:
    conversation = db.execute(
        _detail_query().where(Conversation.id == conversation_id)
    ).scalar_one_or_none()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    slug = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in conversation.title).strip("-")

    if format == "pdf":
        pdf_bytes = to_pdf(conversation)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{slug or "conversation"}.pdf"'},
        )

    markdown = to_markdown(conversation)
    return Response(
        content=markdown,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{slug or "conversation"}.md"'},
    )
