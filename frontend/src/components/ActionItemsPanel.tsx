import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Plus, Trash2 } from "lucide-react";

import { Button } from "./ui/Button";
import { Card, CardBody, CardHeader, CardTitle } from "./ui/Card";
import { api } from "../lib/api";
import { cn } from "../lib/utils";
import type { ActionItem } from "../lib/types";

interface Props {
  conversationId: string;
  items: ActionItem[];
  onChanged: () => void;
}

export function ActionItemsPanel({ conversationId, items, onChanged }: Props) {
  const [text, setText] = useState("");

  const create = useMutation({
    mutationFn: (value: string) => api.createActionItem(conversationId, { text: value }),
    onSuccess: () => {
      setText("");
      onChanged();
    },
  });

  const toggle = useMutation({
    mutationFn: ({ id, done }: { id: string; done: boolean }) =>
      api.updateActionItem(id, { done }),
    onSuccess: onChanged,
  });

  const remove = useMutation({
    mutationFn: (id: string) => api.deleteActionItem(id),
    onSuccess: onChanged,
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Action items</CardTitle>
      </CardHeader>
      <CardBody className="space-y-2">
        {items.length === 0 && (
          <p className="text-xs text-muted-foreground">
            No action items yet. Generate them from the transcript or add your own.
          </p>
        )}

        {items.map((item) => (
          <div key={item.id} className="group flex items-start gap-2">
            <input
              type="checkbox"
              checked={item.done}
              onChange={() => toggle.mutate({ id: item.id, done: !item.done })}
              className="mt-0.5 h-4 w-4 accent-primary"
            />
            <div className="min-w-0 flex-1">
              <p className={cn("text-sm", item.done && "text-muted-foreground line-through")}>
                {item.text}
              </p>
              {item.assignee && (
                <span className="text-xs text-muted-foreground">@{item.assignee}</span>
              )}
            </div>
            <button
              onClick={() => remove.mutate(item.id)}
              className="text-muted-foreground opacity-0 transition-opacity hover:text-red-500 group-hover:opacity-100"
              title="Delete"
            >
              <Trash2 size={14} />
            </button>
          </div>
        ))}

        <form
          className="flex items-center gap-2 pt-1"
          onSubmit={(e) => {
            e.preventDefault();
            if (text.trim()) create.mutate(text.trim());
          }}
        >
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Add an action item"
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
