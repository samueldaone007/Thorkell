from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Tags ---
class TagOut(ORMModel):
    id: str
    name: str


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)


# --- Audio ---
class AudioAssetOut(ORMModel):
    id: str
    filename: str
    mime_type: str
    size_bytes: int
    duration_ms: int | None = None
    created_at: datetime


# --- Speakers ---
class SpeakerOut(ORMModel):
    id: str
    label: str
    display_name: str | None = None
    color: str | None = None


class SpeakerCreate(BaseModel):
    label: str = Field(min_length=1, max_length=64)
    display_name: str | None = Field(default=None, max_length=120)
    color: str | None = Field(default=None, max_length=16)


class SpeakerUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=120)
    color: str | None = Field(default=None, max_length=16)


# --- Segments ---
class SegmentOut(ORMModel):
    id: str
    start_ms: int
    end_ms: int
    text: str
    speaker_label: str | None = None


class SegmentUpdate(BaseModel):
    text: str | None = None
    speaker_label: str | None = Field(default=None, max_length=64)


class BulkSpeakerAssign(BaseModel):
    segment_ids: list[str]
    speaker_label: str | None = Field(default=None, max_length=64)


# --- Transcript ---
class TranscriptOut(ORMModel):
    id: str
    provider: str
    model: str
    language: str | None = None
    created_at: datetime
    segments: list[SegmentOut] = []


# --- Summary / Action items ---
class SummaryOut(ORMModel):
    id: str
    provider: str
    model: str
    content: str
    created_at: datetime


class ActionItemOut(ORMModel):
    id: str
    text: str
    assignee: str | None = None
    done: bool
    source: str
    created_at: datetime


class ActionItemCreate(BaseModel):
    text: str = Field(min_length=1)
    assignee: str | None = None


class ActionItemUpdate(BaseModel):
    text: str | None = None
    assignee: str | None = None
    done: bool | None = None


# --- Conversations ---
class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    notes: str | None = None


class ConversationUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    notes: str | None = None


class ConversationSummaryOut(ORMModel):
    id: str
    title: str
    status: str
    duration_ms: int | None = None
    language: str | None = None
    created_at: datetime
    updated_at: datetime
    tags: list[TagOut] = []
    has_transcript: bool = False


class ConversationDetailOut(ORMModel):
    id: str
    title: str
    notes: str | None = None
    status: str
    error: str | None = None
    duration_ms: int | None = None
    language: str | None = None
    created_at: datetime
    updated_at: datetime
    tags: list[TagOut] = []
    audio_assets: list[AudioAssetOut] = []
    transcripts: list[TranscriptOut] = []
    speakers: list[SpeakerOut] = []
    summaries: list[SummaryOut] = []
    action_items: list[ActionItemOut] = []


# --- Search ---
class SearchHit(BaseModel):
    segment_id: str
    conversation_id: str
    conversation_title: str
    start_ms: int
    end_ms: int
    speaker_label: str | None = None
    text: str
    snippet: str


class SearchResponse(BaseModel):
    query: str
    hits: list[SearchHit]
