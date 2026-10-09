export interface Tag {
  id: string;
  name: string;
}

export interface AudioAsset {
  id: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
  duration_ms: number | null;
  created_at: string;
}

export interface Speaker {
  id: string;
  label: string;
  display_name: string | null;
  color: string | null;
}

export interface Segment {
  id: string;
  start_ms: number;
  end_ms: number;
  text: string;
  speaker_label: string | null;
}

export interface Transcript {
  id: string;
  provider: string;
  model: string;
  language: string | null;
  created_at: string;
  segments: Segment[];
}

export interface Summary {
  id: string;
  provider: string;
  model: string;
  content: string;
  created_at: string;
}

export interface ActionItem {
  id: string;
  text: string;
  assignee: string | null;
  done: boolean;
  source: string;
  created_at: string;
}

export type ConversationStatus =
  | "draft"
  | "recorded"
  | "transcribing"
  | "transcribed"
  | "failed";

export interface ConversationSummary {
  id: string;
  title: string;
  status: ConversationStatus;
  duration_ms: number | null;
  language: string | null;
  created_at: string;
  updated_at: string;
  tags: Tag[];
  has_transcript: boolean;
}

export interface ConversationDetail {
  id: string;
  title: string;
  notes: string | null;
  status: ConversationStatus;
  error: string | null;
  duration_ms: number | null;
  language: string | null;
  created_at: string;
  updated_at: string;
  tags: Tag[];
  audio_assets: AudioAsset[];
  transcripts: Transcript[];
  speakers: Speaker[];
  summaries: Summary[];
  action_items: ActionItem[];
}

export interface SearchHit {
  segment_id: string;
  conversation_id: string;
  conversation_title: string;
  start_ms: number;
  end_ms: number;
  speaker_label: string | null;
  text: string;
  snippet: string;
}

export interface SearchResponse {
  query: string;
  hits: SearchHit[];
}

export interface HealthResponse {
  status: string;
  app: string;
  transcription_provider: string;
  summarization_provider: string;
  diarization_provider: string;
  groq_configured: boolean;
}
