import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Plus, Trash2 } from "lucide-react";

import { Button } from "./ui/Button";
import { Card, CardBody, CardHeader, CardTitle } from "./ui/Card";
import { api } from "../lib/api";
import { speakerColor } from "../lib/format";
import type { Speaker } from "../lib/types";

interface Props {
  conversationId: string;
  speakers: Speaker[];
  onChanged: () => void;
}

export function SpeakersPanel({ conversationId, speakers, onChanged }: Props) {
  const [newLabel, setNewLabel] = useState("");
  const [drafts, setDrafts] = useState<Record<string, string>>({});

  const create = useMutation({
    mutationFn: (label: string) => api.createSpeaker(conversationId, { label }),
    onSuccess: () => {
      setNewLabel("");
      onChanged();
    },
  });

  const update = useMutation({
    mutationFn: ({ id, display_name }: { id: string; display_name: string }) =>
      api.updateSpeaker(id, { display_name }),
    onSuccess: onChanged,
  });

  const remove = useMutation({
    mutationFn: (id: string) => api.deleteSpeaker(id),
    onSuccess: onChanged,
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Speakers</CardTitle>
      </CardHeader>
      <CardBody className="space-y-2">
        {speakers.length === 0 && (
          <p className="text-xs text-muted-foreground">
            No speakers yet. Add one to label who said what in the transcript.
          </p>
        )}

        {speakers.map((speaker) => (
          <div key={speaker.id} className="flex items-center gap-2">
            <span
              className="h-3 w-3 shrink-0 rounded-full"
              style={{ background: speakerColor(speaker.label) }}
            />
            <input
              value={drafts[speaker.id] ?? speaker.display_name ?? ""}
              placeholder={speaker.label}
              onChange={(e) => setDrafts((d) => ({ ...d, [speaker.id]: e.target.value }))}
              onBlur={() => {
                const value = drafts[speaker.id];
                if (value !== undefined && value !== (speaker.display_name ?? "")) {
                  update.mutate({ id: speaker.id, display_name: value });
                }
              }}
              className="min-w-0 flex-1 rounded-md border border-transparent bg-transparent px-1 py-0.5 text-sm hover:border-border focus:border-border focus:outline-none"
            />
            <button
              onClick={() => remove.mutate(speaker.id)}
              className="text-muted-foreground hover:text-red-500"
              title="Remove speaker"
            >
              <Trash2 size={14} />
            </button>
          </div>
        ))}

        <form
          className="flex items-center gap-2 pt-1"
          onSubmit={(e) => {
            e.preventDefault();
            if (newLabel.trim()) create.mutate(newLabel.trim());
          }}
        >
          <input
            value={newLabel}
            onChange={(e) => setNewLabel(e.target.value)}
            placeholder="Speaker label"
            className="h-8 min-w-0 flex-1 rounded-md border border-border bg-background px-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
          />
          <Button type="submit" size="sm" variant="secondary" disabled={create.isPending}>
            <Plus size={14} />
          </Button>
        </form>
      </CardBody>
    </Card>
  );
}
