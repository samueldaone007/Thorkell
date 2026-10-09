import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Check, Pencil } from "lucide-react";

import { Badge } from "./ui/Badge";
import { Spinner } from "./ui/Spinner";
import { api, ApiError } from "../lib/api";
import { formatTimestamp, speakerColor } from "../lib/format";
import type { Segment, Speaker, Transcript } from "../lib/types";

interface Props {
  conversationId: string;
  transcript: Transcript;
  speakers: Speaker[];
  onSeek: (ms: number) => void;
  onChanged: () => void;
}

function displayName(label: string | null, speakers: Speaker[]): string {
  if (!label) return "Unknown";
  const speaker = speakers.find((s) => s.label === label);
  return speaker?.display_name || label;
}

export function TranscriptView({ transcript, speakers, onSeek, onChanged }: Props) {
  const queryClient = useQueryClient();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);

  const labels = Array.from(
    new Set([
      ...speakers.map((s) => s.label),
      ...transcript.segments.map((s) => s.speaker_label).filter((l): l is string => !!l),
    ]),
  ).sort();

  const updateSegment = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: { text?: string; speaker_label?: string | null } }) =>
      api.updateSegment(id, payload),
    onSuccess: () => {
      setEditingId(null);
      setError(null);
      onChanged();
      queryClient.invalidateQueries({ queryKey: ["search"] });
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : (err as Error).message),
  });

  const beginEdit = (segment: Segment) => {
    setEditingId(segment.id);
    setDraft(segment.text);
  };

  return (
    <div className="space-y-1">
      {error && <p className="mb-2 text-xs text-red-500">{error}</p>}
      {transcript.segments.map((segment) => {
        const name = displayName(segment.speaker_label, speakers);
        return (
          <div
            key={segment.id}
            className="group flex gap-3 rounded-lg px-2 py-2 hover:bg-muted/60"
          >
            <button
              onClick={() => onSeek(segment.start_ms)}
              className="mt-0.5 shrink-0 font-mono text-xs text-muted-foreground hover:text-primary"
              title="Jump to this point"
            >
              {formatTimestamp(segment.start_ms)}
            </button>

            <div className="min-w-0 flex-1">
              <div className="mb-0.5 flex items-center gap-2">
                <span
                  className="inline-block h-2 w-2 rounded-full"
                  style={{ background: speakerColor(segment.speaker_label) }}
                />
                <select
                  value={segment.speaker_label ?? ""}
                  onChange={(e) =>
                    updateSegment.mutate({
                      id: segment.id,
                      payload: { speaker_label: e.target.value || null },
                    })
                  }
                  className="cursor-pointer appearance-none rounded bg-transparent text-xs font-semibold text-foreground hover:text-primary focus:outline-none"
                  style={{ color: speakerColor(segment.speaker_label) }}
                >
                  <option value="" style={{ color: "inherit" }}>
                    Unknown
                  </option>
                  {labels.map((label) => (
                    <option key={label} value={label} style={{ color: "inherit" }}>
                      {displayName(label, speakers)}
                    </option>
                  ))}
                </select>
                {updateSegment.isPending && updateSegment.variables?.id === segment.id && (
                  <Spinner className="h-3 w-3" />
                )}
              </div>

              {editingId === segment.id ? (
                <div className="flex items-start gap-2">
                  <textarea
                    autoFocus
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    rows={2}
                    className="w-full rounded-md border border-border bg-background px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
                  />
                  <button
                    onClick={() => updateSegment.mutate({ id: segment.id, payload: { text: draft } })}
                    className="text-primary hover:text-primary-hover"
                    title="Save"
                  >
                    <Check size={16} />
                  </button>
                </div>
              ) : (
                <p
                  className="cursor-text text-sm leading-relaxed"
                  onClick={() => beginEdit(segment)}
                  title="Click to edit"
                >
                  {segment.text}
                  <Pencil
                    size={12}
                    className="ml-1 inline opacity-0 transition-opacity group-hover:opacity-40"
                  />
                </p>
              )}
            </div>
          </div>
        );
      })}

      {labels.length === 0 && (
        <div className="flex items-center gap-2 pt-2 text-xs text-muted-foreground">
          <Badge tone="primary">Tip</Badge>
          <span>Add speakers from the panel on the right, then assign them here.</span>
        </div>
      )}
    </div>
  );
}
