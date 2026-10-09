import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Mic, Plus, Clock } from "lucide-react";

import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { Spinner } from "../components/ui/Spinner";
import { RecordDialog } from "../components/RecordDialog";
import { api } from "../lib/api";
import { formatDateTime, formatTimestamp } from "../lib/format";
import type { ConversationStatus } from "../lib/types";

const statusMeta: Record<
  ConversationStatus,
  { label: string; tone: "neutral" | "primary" | "success" | "warning" | "danger" }
> = {
  draft: { label: "Draft", tone: "neutral" },
  recorded: { label: "Recorded", tone: "warning" },
  transcribing: { label: "Transcribing…", tone: "warning" },
  transcribed: { label: "Transcribed", tone: "success" },
  failed: { label: "Failed", tone: "danger" },
};

export function ConversationsPage() {
  const [dialogOpen, setDialogOpen] = useState(false);
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["conversations"],
    queryFn: api.listConversations,
  });

  return (
    <div className="mx-auto max-w-4xl">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Conversations</h1>
          <p className="text-sm text-muted-foreground">
            Record, transcribe and organise your ideas.
          </p>
        </div>
        <Button onClick={() => setDialogOpen(true)}>
          <Plus size={16} />
          New
        </Button>
      </div>

      {isLoading && (
        <div className="flex justify-center py-20 text-muted-foreground">
          <Spinner className="h-6 w-6" />
        </div>
      )}

      {isError && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-600 dark:text-red-400">
          Could not load conversations: {(error as Error).message}
        </div>
      )}

      {data && data.length === 0 && (
        <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed border-border py-20 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/15 text-primary">
            <Mic size={22} />
          </div>
          <div>
            <p className="font-medium">No conversations yet</p>
            <p className="text-sm text-muted-foreground">
              Start by recording a conversation or uploading an audio file.
            </p>
          </div>
          <Button onClick={() => setDialogOpen(true)}>
            <Plus size={16} />
            New conversation
          </Button>
        </div>
      )}

      <div className="grid gap-3">
        {data?.map((conversation) => {
          const meta = statusMeta[conversation.status];
          return (
            <Link
              key={conversation.id}
              to={`/conversations/${conversation.id}`}
              className="group rounded-xl border border-border bg-surface p-4 transition-colors hover:border-primary/50"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <h2 className="truncate font-medium group-hover:text-primary">
                    {conversation.title}
                  </h2>
                  <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
                    <span className="inline-flex items-center gap-1">
                      <Clock size={12} />
                      {conversation.duration_ms
                        ? formatTimestamp(conversation.duration_ms)
                        : formatDateTime(conversation.created_at)}
                    </span>
                    {conversation.tags.map((tag) => (
                      <span
                        key={tag.id}
                        className="rounded-full bg-primary/10 px-2 py-0.5 text-primary"
                      >
                        {tag.name}
                      </span>
                    ))}
                  </div>
                </div>
                <Badge tone={meta.tone}>{meta.label}</Badge>
              </div>
            </Link>
          );
        })}
      </div>

      <RecordDialog open={dialogOpen} onClose={() => setDialogOpen(false)} />
    </div>
  );
}
