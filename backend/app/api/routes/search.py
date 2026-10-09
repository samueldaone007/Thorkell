from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import SearchHit, SearchResponse
from app.services import search as search_service

router = APIRouter(tags=["search"])


@router.get("/search", response_model=SearchResponse)
def search(
    q: str = Query("", min_length=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> SearchResponse:
    if not q.strip():
        return SearchResponse(query=q, hits=[])
    rows = search_service.search(db, q, limit=limit)
    hits = [
        SearchHit(
            segment_id=row["segment_id"],
            conversation_id=row["conversation_id"],
            conversation_title=row["title"],
            start_ms=row["start_ms"],
            end_ms=row["end_ms"],
            speaker_label=row["speaker_label"],
            text=row["seg_text"],
            snippet=row["snippet"],
        )
        for row in rows
    ]
    return SearchResponse(query=q, hits=hits)
