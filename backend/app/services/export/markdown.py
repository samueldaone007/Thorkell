from __future__ import annotations

from datetime import timezone

from app.models import Conversation, Speaker


def _fmt_ts(ms: int) -> str:
    total = max(0, ms) // 1000
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h:d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def speaker_name(conversation: Conversation, label: str | None) -> str:
    if not label:
        return "Unknown"
    for spk in conversation.speakers:
        if spk.label == label and spk.display_name:
            return spk.display_name
    return label


def to_markdown(conversation: Conversation) -> str:
    lines: list[str] = []
    lines.append(f"# {conversation.title}")
    lines.append("")

    created = conversation.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    lines.append(f"*Recorded {created.strftime('%Y-%m-%d %H:%M UTC')}*")

    if conversation.tags:
        lines.append("")
        lines.append("**Tags:** " + ", ".join(f"`{t.name}`" for t in conversation.tags))

    if conversation.notes:
        lines.append("")
        lines.append("## Notes")
        lines.append("")
        lines.append(conversation.notes)

    if conversation.summaries:
        latest = conversation.summaries[0]
        lines.append("")
        lines.append("## Summary")
        lines.append("")
        lines.append(latest.content)

    if conversation.action_items:
        lines.append("")
        lines.append("## Action items")
        lines.append("")
        for item in conversation.action_items:
            box = "x" if item.done else " "
            who = f" — @{item.assignee}" if item.assignee else ""
            lines.append(f"- [{box}] {item.text}{who}")

    lines.append("")
    lines.append("## Transcript")
    lines.append("")

    transcript = conversation.transcripts[-1] if conversation.transcripts else None
    if transcript is None:
        lines.append("_No transcript available._")
    else:
        for seg in transcript.segments:
            who = speaker_name(conversation, seg.speaker_label)
            lines.append(f"**{who}** [{_fmt_ts(seg.start_ms)}]: {seg.text}")

    lines.append("")
    return "\n".join(lines)
