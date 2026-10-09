import type {
  ActionItem,
  AudioAsset,
  ConversationDetail,
  ConversationSummary,
  HealthResponse,
  SearchResponse,
  Segment,
  Speaker,
  Tag,
} from "./types";

const API_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? "/api";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, init);
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      if (body?.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* ignore */
    }
    throw new ApiError(response.status, detail);
  }
  if (response.status === 204) return undefined as T;
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) return (await response.json()) as T;
  return (await response.text()) as unknown as T;
}

function json(body: unknown): RequestInit {
  return {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  };
}

export const api = {
  health: () => request<HealthResponse>("/health"),

  listConversations: () => request<ConversationSummary[]>("/conversations"),

  getConversation: (id: string) => request<ConversationDetail>(`/conversations/${id}`),

  createConversation: (payload: { title?: string; notes?: string }) =>
    request<ConversationDetail>("/conversations", json(payload)),

  updateConversation: (id: string, payload: { title?: string; notes?: string }) =>
    request<ConversationDetail>(`/conversations/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  deleteConversation: (id: string) =>
    request<void>(`/conversations/${id}`, { method: "DELETE" }),

  uploadAudio: async (id: string, blob: Blob, filename: string) => {
    const form = new FormData();
    form.append("file", blob, filename);
    return request<ConversationDetail>(`/conversations/${id}/audio`, {
      method: "POST",
      body: form,
    });
  },

  audioUrl: (conversationId: string, assetId: string) =>
    `${API_URL}/conversations/${conversationId}/audio/${assetId}`,

  transcribe: (id: string) =>
    request<ConversationDetail>(`/conversations/${id}/transcribe`, { method: "POST" }),

  summarize: (id: string) =>
    request<ConversationDetail>(`/conversations/${id}/summarize`, { method: "POST" }),

  addTag: (id: string, name: string) =>
    request<ConversationDetail>(`/conversations/${id}/tags`, json({ name })),

  removeTag: (id: string, tagId: string) =>
    request<ConversationDetail>(`/conversations/${id}/tags/${tagId}`, { method: "DELETE" }),

  listTags: () => request<Tag[]>("/tags"),

  updateSegment: (segmentId: string, payload: { text?: string; speaker_label?: string | null }) =>
    request<Segment>(`/segments/${segmentId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  bulkAssignSpeaker: (segmentIds: string[], speakerLabel: string | null) =>
    request<Segment[]>("/segments/bulk-speaker", json({ segment_ids: segmentIds, speaker_label: speakerLabel })),

  createSpeaker: (conversationId: string, payload: { label: string; display_name?: string; color?: string }) =>
    request<Speaker>(`/conversations/${conversationId}/speakers`, json(payload)),

  updateSpeaker: (speakerId: string, payload: { display_name?: string; color?: string }) =>
    request<Speaker>(`/speakers/${speakerId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  deleteSpeaker: (speakerId: string) =>
    request<void>(`/speakers/${speakerId}`, { method: "DELETE" }),

  createActionItem: (conversationId: string, payload: { text: string; assignee?: string }) =>
    request<ActionItem>(`/conversations/${conversationId}/action-items`, json(payload)),

  updateActionItem: (itemId: string, payload: { text?: string; assignee?: string | null; done?: boolean }) =>
    request<ActionItem>(`/action-items/${itemId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  deleteActionItem: (itemId: string) =>
    request<void>(`/action-items/${itemId}`, { method: "DELETE" }),

  search: (q: string) => request<SearchResponse>(`/search?q=${encodeURIComponent(q)}`),

  exportUrl: (id: string, format: "md" | "pdf") => `${API_URL}/conversations/${id}/export?format=${format}`,
};

export type { AudioAsset };
