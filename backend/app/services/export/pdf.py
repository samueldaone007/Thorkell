from __future__ import annotations

import io
import re
from datetime import timezone

from fpdf import FPDF

from app.models import Conversation
from app.services.export.markdown import speaker_name


def _fmt_ts(ms: int) -> str:
    total = max(0, ms) // 1000
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h:d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def _latin(text: str) -> str:
    """Core PDF fonts are latin-1; drop characters they cannot render."""
    return text.encode("latin-1", "replace").decode("latin-1")


class _Doc(FPDF):
    def header(self) -> None:
        pass


def to_pdf(conversation: Conversation) -> bytes:
    pdf = _Doc(unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(18, 18, 18)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(109, 40, 217)  # violet primary
    pdf.multi_cell(0, 9, _latin(conversation.title))
    pdf.ln(1)

    created = conversation.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(107, 114, 128)
    pdf.cell(0, 6, _latin(f"Recorded {created.strftime('%Y-%m-%d %H:%M UTC')}"))
    pdf.ln(8)

    def section(title: str) -> None:
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(26, 11, 46)
        pdf.cell(0, 8, _latin(title))
        pdf.ln(9)

    def body(text: str) -> None:
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(26, 11, 46)
        pdf.multi_cell(0, 6, _latin(text))
        pdf.ln(2)

    if conversation.tags:
        body("Tags: " + ", ".join(t.name for t in conversation.tags))

    if conversation.notes:
        section("Notes")
        body(conversation.notes)

    if conversation.summaries:
        section("Summary")
        body(re.sub(r"[#*_`>]", "", conversation.summaries[0].content))

    if conversation.action_items:
        section("Action items")
        for item in conversation.action_items:
            box = "[x]" if item.done else "[ ]"
            who = f"  (@{item.assignee})" if item.assignee else ""
            body(f"{box} {item.text}{who}")

    section("Transcript")
    transcript = conversation.transcripts[-1] if conversation.transcripts else None
    if transcript is None:
        body("No transcript available.")
    else:
        for seg in transcript.segments:
            who = speaker_name(conversation, seg.speaker_label)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(109, 40, 217)
            pdf.cell(0, 5, _latin(f"{who}  [{_fmt_ts(seg.start_ms)}]"))
            pdf.ln(5)
            pdf.set_font("Helvetica", "", 11)
            pdf.set_text_color(26, 11, 46)
            pdf.multi_cell(0, 6, _latin(seg.text))
            pdf.ln(1)

    out = pdf.output()
    return bytes(out) if not isinstance(out, (bytes, bytearray)) else bytes(out)


def render_pdf(conversation: Conversation) -> io.BytesIO:
    return io.BytesIO(to_pdf(conversation))
