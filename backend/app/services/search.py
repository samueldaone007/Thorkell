from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


def index_segment(db: Session, segment_id: str, conversation_id: str, content: str) -> None:
    db.execute(
        text(
            "INSERT INTO segment_fts (text, segment_id, conversation_id) "
            "VALUES (:t, :s, :c)"
        ),
        {"t": content, "s": segment_id, "c": conversation_id},
    )


def remove_segment(db: Session, segment_id: str) -> None:
    db.execute(
        text("DELETE FROM segment_fts WHERE segment_id = :s"), {"s": segment_id}
    )


def remove_conversation(db: Session, conversation_id: str) -> None:
    db.execute(
        text("DELETE FROM segment_fts WHERE conversation_id = :c"), {"c": conversation_id}
    )


def search(db: Session, query: str, limit: int = 50) -> list[dict]:
    """Full-text search across transcript segments using SQLite FTS5.

    Uses a prefix match on the last token so partial words still return hits.
    """
    cleaned = " ".join(t for t in query.replace('"', " ").split() if t)
    if not cleaned:
        return []
    fts_query = f'{cleaned}*'

    rows = db.execute(
        text(
            """
            SELECT f.segment_id        AS segment_id,
                   f.conversation_id   AS conversation_id,
                   snippet(segment_fts, 0, '<mark>', '</mark>', '…', 12) AS snippet,
                   s.start_ms          AS start_ms,
                   s.end_ms            AS end_ms,
                   s.text              AS seg_text,
                   s.speaker_label     AS speaker_label,
                   c.title             AS title
            FROM segment_fts f
            JOIN transcript_segments s ON s.id = f.segment_id
            JOIN conversations c ON c.id = f.conversation_id
            WHERE segment_fts MATCH :q
            ORDER BY rank
            LIMIT :limit
            """
        ),
        {"q": fts_query, "limit": limit},
    ).mappings()

    return [dict(r) for r in rows]
