from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Conversation, Speaker
from app.schemas import SpeakerCreate, SpeakerOut, SpeakerUpdate

router = APIRouter(tags=["speakers"])


@router.post("/conversations/{conversation_id}/speakers", response_model=SpeakerOut, status_code=201)
def create_speaker(
    conversation_id: str, payload: SpeakerCreate, db: Session = Depends(get_db)
) -> Speaker:
    if db.get(Conversation, conversation_id) is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    existing = db.execute(
        select(Speaker).where(
            Speaker.conversation_id == conversation_id, Speaker.label == payload.label
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    speaker = Speaker(
        conversation_id=conversation_id,
        label=payload.label,
        display_name=payload.display_name,
        color=payload.color,
    )
    db.add(speaker)
    db.commit()
    db.refresh(speaker)
    return speaker


@router.patch("/speakers/{speaker_id}", response_model=SpeakerOut)
def update_speaker(
    speaker_id: str, payload: SpeakerUpdate, db: Session = Depends(get_db)
) -> Speaker:
    speaker = db.get(Speaker, speaker_id)
    if speaker is None:
        raise HTTPException(status_code=404, detail="Speaker not found")
    if payload.display_name is not None:
        speaker.display_name = payload.display_name
    if payload.color is not None:
        speaker.color = payload.color
    db.commit()
    db.refresh(speaker)
    return speaker


@router.delete("/speakers/{speaker_id}", status_code=204)
def delete_speaker(speaker_id: str, db: Session = Depends(get_db)) -> Response:
    speaker = db.get(Speaker, speaker_id)
    if speaker is not None:
        db.delete(speaker)
        db.commit()
    return Response(status_code=204)
