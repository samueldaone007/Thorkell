import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Download,
  FileText,
  Sparkles,
  Trash2,
  Wand2,
} from "lucide-react";

import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { Input, Textarea } from "../components/ui/Input";
import { Card, CardBody, CardHeader, CardTitle } from "../components/ui/Card";
import { Spinner } from "../components/ui/Spinner";
import { TranscriptView } from "../components/TranscriptView";
import { SpeakersPanel } from "../components/SpeakersPanel";
import { SummaryPanel } from "../components/SummaryPanel";
import { ActionItemsPanel } from "../components/ActionItemsPanel";
import { api, ApiError } from "../lib/api";
import { formatDateTime, formatTimestamp } from "../lib/format";

export function ConversationPage() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const audioRef = useRef<HTMLAudioElement>(null);

  const [title, setTitle] = useState("");
  const [notes, setNotes] = useState("");
  const [tagInput, setTagInput] = useState("");
  const [banner, setBanner] = useState<string | null>(null);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["conversation", id],
    queryFn: () => api.getConversation(id),
    refetchInterval: (query) =>
      query.state.data?.status === "transcribing" ? 2000 : false,
  });

  useEffect(() => {
    if (data) {
      setTitle(data.title);
      setNotes(data.notes ?? "");
    }
  }, [data]);

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["conversation", id] });
    queryClient.invalidateQueries({ queryKey: ["conversations"] });
  };

  const transcribe = useMutation({
    mutationFn: () => api.transcribe(id),
    onMutate: () => setBanner(null),
    onSuccess: invalidate,
    onError: async (err) => {
      setBanner(err instanceof ApiError ? err.message : (err as Error).message);
      invalidate();
      await queryClient.refetchQueries({ queryKey: ["conversation", id] });
    },
  });

  const summarize = useMutation({
    mutationFn: () => api.summarize(id),
    onSuccess: invalidate,
    onError: (err) => setBanner(err instanceof ApiError ? err.message : (err as Error).message),
  });

  const saveTitle = useMutation({
    mutationFn: (value: string) => api.updateConversation(id, { title: value }),
    onSuccess: invalidate,
  });

  const saveNotes = useMutation({
    mutationFn: (value: string) => api.updateConversation(id, { notes: value }),
    onSuccess: invalidate,
  });

  const addTag = useMutation({
    mutationFn: (name: string) => api.addTag(id, name),
    onSuccess: () => {
      setTagInput("");
      invalidate();
    },
  });

  const removeTag = useMutation({
    mutationFn: (tagId: string) => api.removeTag(id, tagId),
    onSuccess: invalidate,
  });

  const remove = useMutation({
    mutationFn: () => api.deleteConversation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      navigate("/");
    },
  });

  const audioAsset = data?.audio_assets.at(-1);
  const transcript = data?.transcripts.at(-1);
  const busy = transcribe.isPending || summarize.isPending;

  const seek = useMemo(
    () => (ms: number) => {
      const el = audioRef.current;
      if (!el) return;
      el.currentTime = ms / 1000;
      void el.play();
    },
    [],
  );

  if (isLoading) {
    return (
      <div className="flex justify-center py-20 text-muted-foreground">
        <Spinner className="h-6 w-6" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="mx-auto max-w-3xl rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-600 dark:text-red-400">
        Could not load conversation: {(error as Error)?.message}
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <div>
        <Link
          to="/"
          className="mb-3 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft size={14} />
          Back to conversations
        </Link>

        <div className="flex flex-wrap items-start justify-between gap-3">
          <Input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            onBlur={() => title !== data.title && saveTitle.mutate(title)}
            className="h-auto max-w-2xl border-none bg-transparent px-0 text-2xl font-semibold focus-visible:ring-0"
          />
          <div className="flex items-center gap-2">
            <a href={api.exportUrl(id, "md")} download>
              <Button variant="secondary" size="sm">
                <FileText size={15} />
                Markdown
              </Button>
            </a>
            <a href={api.exportUrl(id, "pdf")} download>
              <Button variant="secondary" size="sm">
                <Download size={15} />
                PDF
              </Button>
            </a>
            <Button
              variant="ghost"
              size="icon"
              title="Delete conversation"
              onClick={() => {
                if (confirm("Delete this conversation and its recording?")) remove.mutate();
              }}
            >
              <Trash2 size={16} />
            </Button>
          </div>
        </div>

        <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          <Badge tone={data.status === "failed" ? "danger" : data.status === "transcribed" ? "success" : "neutral"}>
            {data.status}
          </Badge>
          <span>{formatDateTime(data.created_at)}</span>
          {data.duration_ms != null && <span>· {formatTimestamp(data.duration_ms)}</span>}
          {data.language && <span>· {data.language}</span>}
          {transcript && <span>· {transcript.provider}/{transcript.model}</span>}
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-1.5">
          {data.tags.map((tag) => (
            <span
              key={tag.id}
              className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary"
            >
              {tag.name}
              <button
                onClick={() => removeTag.mutate(tag.id)}
                className="hover:text-primary-hover"
                aria-label={`Remove ${tag.name}`}
              >
                ×
              </button>
            </span>
          ))}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (tagInput.trim()) addTag.mutate(tagInput.trim());
            }}
          >
            <input
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              placeholder="+ tag"
              className="w-24 rounded-full border border-dashed border-border bg-transparent px-2 py-0.5 text-xs focus:outline-none focus:ring-1 focus:ring-ring"
            />
          </form>
        </div>
      </div>

      {banner && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-600 dark:text-red-400">
          {banner}
        </div>
      )}

      {audioAsset && (
        <Card>
          <CardBody className="space-y-2">
            <audio ref={audioRef} controls src={api.audioUrl(id, audioAsset.id)} className="w-full" />
            <div className="flex flex-wrap gap-2">
              <Button
                onClick={() => transcribe.mutate()}
                disabled={busy || data.status === "transcribing"}
              >
                {data.status === "transcribing" ? <Spinner /> : <Wand2 size={15} />}
                {transcript ? "Re-transcribe" : "Transcribe"}
              </Button>
              <Button
                variant="secondary"
                onClick={() => summarize.mutate()}
                disabled={busy || !transcript}
              >
                {summarize.isPending ? <Spinner /> : <Sparkles size={15} />}
                Summarize &amp; extract actions
              </Button>
            </div>
          </CardBody>
        </Card>
      )}

      <div className="grid gap-5 lg:grid-cols-3">
        <div className="space-y-5 lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Transcript</CardTitle>
            </CardHeader>
            <CardBody>
              {transcript ? (
                <TranscriptView
                  conversationId={id}
                  transcript={transcript}
                  speakers={data.speakers}
                  onSeek={seek}
                  onChanged={invalidate}
                />
              ) : (
                <p className="py-6 text-center text-sm text-muted-foreground">
                  No transcript yet. Record audio, then click “Transcribe”.
                </p>
              )}
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Notes</CardTitle>
            </CardHeader>
            <CardBody>
              <Textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                onBlur={() => notes !== (data.notes ?? "") && saveNotes.mutate(notes)}
                placeholder="Add your own notes and ideas…"
                rows={5}
              />
            </CardBody>
          </Card>
        </div>

        <div className="space-y-5">
          <SummaryPanel conversationId={id} summary={data.summaries[0]} onChanged={invalidate} />
          <ActionItemsPanel conversationId={id} items={data.action_items} onChanged={invalidate} />
          <SpeakersPanel conversationId={id} speakers={data.speakers} onChanged={invalidate} />
        </div>
      </div>
    </div>
  );
}
