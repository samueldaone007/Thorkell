import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Search as SearchIcon } from "lucide-react";

import { Input } from "../components/ui/Input";
import { Spinner } from "../components/ui/Spinner";
import { api } from "../lib/api";
import { formatTimestamp, speakerColor } from "../lib/format";

function useDebounced<T>(value: T, delay = 300): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), delay);
    return () => window.clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

function safeSnippet(snippet: string): string {
  return snippet
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/&lt;mark&gt;/g, '<mark class="mark-hit">')
    .replace(/&lt;\/mark&gt;/g, "</mark>");
}

export function SearchPage() {
  const [query, setQuery] = useState("");
  const debounced = useDebounced(query.trim());

  const { data, isFetching } = useQuery({
    queryKey: ["search", debounced],
    queryFn: () => api.search(debounced),
    enabled: debounced.length > 0,
  });

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="mb-1 text-2xl font-semibold">Search</h1>
      <p className="mb-5 text-sm text-muted-foreground">
        Find ideas and phrases across every transcript.
      </p>

      <div className="relative">
        <SearchIcon
          size={16}
          className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
        />
        <Input
          autoFocus
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search transcripts…"
          className="pl-9"
        />
        {isFetching && (
          <Spinner className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
        )}
      </div>

      <div className="mt-5 space-y-2">
        {debounced.length === 0 && (
          <p className="py-10 text-center text-sm text-muted-foreground">
            Start typing to search across all conversations.
          </p>
        )}

        {data?.hits.map((hit) => (
          <Link
            key={hit.segment_id}
            to={`/conversations/${hit.conversation_id}`}
            className="block rounded-xl border border-border bg-surface p-4 transition-colors hover:border-primary/50"
          >
            <div className="mb-1 flex items-center justify-between gap-2 text-xs text-muted-foreground">
              <span className="truncate font-medium text-foreground">
                {hit.conversation_title}
              </span>
              <span className="font-mono">{formatTimestamp(hit.start_ms)}</span>
            </div>
            {hit.speaker_label && (
              <span
                className="text-xs font-semibold"
                style={{ color: speakerColor(hit.speaker_label) }}
              >
                {hit.speaker_label}
              </span>
            )}
            <p
              className="mt-0.5 text-sm leading-relaxed"
              dangerouslySetInnerHTML={{ __html: safeSnippet(hit.snippet) }}
            />
          </Link>
        ))}

        {data && data.hits.length === 0 && debounced.length > 0 && (
          <p className="py-10 text-center text-sm text-muted-foreground">
            No matches for “{debounced}”.
          </p>
        )}
      </div>
    </div>
  );
}
