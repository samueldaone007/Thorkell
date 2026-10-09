from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {},
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # Import models so they are registered on Base.metadata before create_all.
    from app import models  # noqa: F401

    settings.storage_dir.mkdir(parents=True, exist_ok=True)

    Base.metadata.create_all(bind=engine)

    with engine.begin() as conn:
        # Full-text search index over transcript segments.
        conn.execute(
            text(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS segment_fts USING fts5(
                    text,
                    segment_id UNINDEXED,
                    conversation_id UNINDEXED,
                    tokenize='porter unicode61'
                )
                """
            )
        )
