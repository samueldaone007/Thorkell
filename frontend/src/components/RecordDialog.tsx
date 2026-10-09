import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { Mic, Square, Pause, Play, Upload } from "lucide-react";

import { Button } from "./ui/Button";
import { Dialog } from "./ui/Dialog";
import { Input } from "./ui/Input";
import { Spinner } from "./ui/Spinner";
import { api, ApiError } from "../lib/api";
import { formatTimestamp } from "../lib/format";
import { useRecorder } from "../hooks/useRecorder";
import { cn } from "../lib/utils";

type Mode = "record" | "upload";

export function RecordDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const recorder = useRecorder();

  const [mode, setMode] = useState<Mode>("record");
  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [autoTranscribe, setAutoTranscribe] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const reset = () => {
    setTitle("");
    setFile(null);
    setError(null);
    setSaving(false);
  };

  const close = () => {
    reset();
    onClose();
  };

  const save = async () => {
    setError(null);
    setSaving(true);
    try {
      let blob: Blob | null = null;
      let filename = "recording.webm";

      if (mode === "record") {
        if (recorder.state !== "idle") {
          blob = await recorder.stop();
        }
        if (!blob) throw new Error("No recording captured");
        const ext = blob.type.includes("ogg") ? "ogg" : blob.type.includes("mp4") ? "mp4" : "webm";
        filename = `recording.${ext}`;
      } else {
        if (!file) throw new Error("Choose an audio file first");
        blob = file;
        filename = file.name;
      }

      const conversation = await api.createConversation({ title: title.trim() || undefined });
      await api.uploadAudio(conversation.id, blob, filename);

      queryClient.invalidateQueries({ queryKey: ["conversations"] });

      if (autoTranscribe) {
        api.transcribe(conversation.id).catch(() => {
          /* errors are surfaced on the conversation page */
        });
      }

      navigate(`/conversations/${conversation.id}`);
      close();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : (err as Error).message);
      setSaving(false);
    }
  };

  const recording = recorder.state !== "idle";

  return (
    <Dialog open={open} onClose={close} title="New conversation">
      <div className="space-y-4">
        <div className="inline-flex rounded-lg border border-border bg-muted p-0.5">
          {(["record", "upload"] as Mode[]).map((m) => (
            <button
              key={m}
              disabled={recording}
              onClick={() => setMode(m)}
              className={cn(
                "flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium capitalize transition-colors disabled:opacity-50",
                mode === m ? "bg-surface text-foreground shadow-sm" : "text-muted-foreground",
              )}
            >
              {m === "record" ? <Mic size={15} /> : <Upload size={15} />}
              {m}
            </button>
          ))}
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-muted-foreground">
            Title (optional)
          </label>
          <Input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Q3 planning brainstorm"
            maxLength={500}
          />
        </div>

        {mode === "record" ? (
          <div className="flex flex-col items-center gap-3 rounded-xl border border-border bg-muted/50 py-6">
            <button
              onClick={() => {
                if (recorder.state === "idle") recorder.start().catch(() => undefined);
                else if (recorder.state === "recording") recorder.pause();
                else recorder.resume();
              }}
              className={cn(
                "flex h-16 w-16 items-center justify-center rounded-full bg-primary text-primary-foreground transition-transform hover:scale-105",
                recorder.state === "recording" && "animate-pulse-ring",
              )}
            >
              {recorder.state === "recording" ? (
                <Pause size={26} />
              ) : recorder.state === "paused" ? (
                <Play size={26} />
              ) : (
                <Mic size={26} />
              )}
            </button>
            <div className="font-mono text-lg tabular-nums">
              {formatTimestamp(recorder.elapsedMs)}
            </div>
            <div className="text-xs text-muted-foreground">
              {recorder.state === "idle"
                ? "Tap to start recording"
                : recorder.state === "paused"
                  ? "Paused — tap to resume"
                  : "Recording… tap to pause"}
            </div>
            {recorder.error && <p className="text-xs text-red-500">{recorder.error}</p>}
          </div>
        ) : (
          <label className="flex cursor-pointer flex-col items-center gap-2 rounded-xl border border-dashed border-border bg-muted/50 py-6 text-sm text-muted-foreground hover:border-primary">
            <Upload size={22} />
            {file ? file.name : "Click to choose an audio file"}
            <input
              ref={fileInputRef}
              type="file"
              accept="audio/*"
              className="hidden"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </label>
        )}

        <label className="flex items-center gap-2 text-sm text-muted-foreground">
          <input
            type="checkbox"
            checked={autoTranscribe}
            onChange={(e) => setAutoTranscribe(e.target.checked)}
            className="h-4 w-4 accent-primary"
          />
          Transcribe automatically after saving
        </label>

        {error && <p className="text-sm text-red-500">{error}</p>}

        <div className="flex justify-end gap-2 pt-1">
          <Button variant="ghost" onClick={close} disabled={saving}>
            Cancel
          </Button>
          <Button onClick={save} disabled={saving}>
            {saving ? <Spinner /> : <Square size={15} />}
            Save conversation
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
