from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import TranscriptSegment
from app.schemas import BulkSpeakerAssign, SegmentOut, SegmentUpdate
from app.services import search as search_service

router = APIRouter(prefix="/segments", tags=["segments"])


@router.patch("/{segment_id}", response_model=SegmentOut)
def update_segment(
    segment_id: str, payload: SegmentUpdate, db: Session = Depends(get_db)
) -> TranscriptSegment:
    segment = db.get(TranscriptSegment, segment_id)
    if segment is None:
        raise HTTPException(status_code=404, detail="Segment not found")

    if payload.text is not None and payload.text != segment.text:
        segment.text = payload.text
        transcript = segment.transcript
        search_service.remove_segment(db, segment.id)
        search_service.index_segment(db, segment.id, transcript.conversation_id, segment.text)

    if "speaker_label" in payload.model_fields_set:
        segment.speaker_label = payload.speaker_label

    db.commit()
    db.refresh(segment)
    return segment


@router.post("/bulk-speaker", response_model=list[SegmentOut])
def bulk_assign_speaker(
    payload: BulkSpeakerAssign, db: Session = Depends(get_db)
) -> list[TranscriptSegment]:
    segments = (
        db.query(TranscriptSegment).filter(TranscriptSegment.id.in_(payload.segment_ids)).all()
    )
    for segment in segments:
        segment.speaker_label = payload.speaker_label
    db.commit()
    return segments
