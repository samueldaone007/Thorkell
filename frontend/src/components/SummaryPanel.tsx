import { Sparkles } from "lucide-react";

import { Card, CardBody, CardHeader, CardTitle } from "./ui/Card";
import type { Summary } from "../lib/types";

function MarkdownLite({ content }: { content: string }) {
  const lines = content.split("\n");
  return (
    <div className="space-y-1.5 text-sm">
      {lines.map((line, i) => {
        const trimmed = line.trim();
        if (!trimmed) return <div key={i} className="h-1" />;
        if (trimmed.startsWith("### "))
          return <p key={i} className="font-semibold">{inline(trimmed.slice(4))}</p>;
        if (trimmed.startsWith("## "))
          return <p key={i} className="font-semibold">{inline(trimmed.slice(3))}</p>;
        if (trimmed.startsWith("# "))
          return <p key={i} className="font-semibold">{inline(trimmed.slice(2))}</p>;
        if (/^[-*]\s+/.test(trimmed))
          return (
            <p key={i} className="flex gap-2">
              <span className="text-primary">•</span>
              <span>{inline(trimmed.replace(/^[-*]\s+/, ""))}</span>
            </p>
          );
        return <p key={i}>{inline(trimmed)}</p>;
      })}
    </div>
  );
}

function inline(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) =>
    part.startsWith("**") && part.endsWith("**") ? (
      <strong key={i}>{part.slice(2, -2)}</strong>
    ) : (
      <span key={i}>{part}</span>
    ),
  );
}

export function SummaryPanel({ summary }: { conversationId: string; summary?: Summary; onChanged: () => void }) {
  return (
    <Card>
      <CardHeader className="flex items-center gap-2">
        <Sparkles size={15} className="text-primary" />
        <CardTitle>Summary</CardTitle>
      </CardHeader>
      <CardBody>
        {summary ? (
          <MarkdownLite content={summary.content} />
        ) : (
          <p className="text-xs text-muted-foreground">
            No summary yet. Use “Summarize &amp; extract actions” above the transcript.
          </p>
        )}
      </CardBody>
    </Card>
  );
}
