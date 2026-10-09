from __future__ import annotations

import json

import httpx

from app.config import get_settings
from app.services.summarization.base import (
    ActionItemDraft,
    SummarizationProvider,
    SummaryResult,
)

SYSTEM_PROMPT = (
    "You are an assistant that helps a team capture ideas from recorded "
    "conversations. Given a transcript, produce a concise summary and a list "
    "of concrete action items. Respond ONLY with valid JSON matching this "
    'schema: {"summary": string, "action_items": [{"text": string, '
    '"assignee": string|null}]}. Write the summary in Markdown with a short '
    "overview followed by key points and any notable ideas. Use a bullet list. "
    "If there are no action items, return an empty array."
)


class GroqSummarizationProvider(SummarizationProvider):
    name = "groq"

    def __init__(self) -> None:
        self.settings = get_settings()
        if not self.settings.groq_api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Add it to backend/.env or set "
                "SUMMARIZATION_PROVIDER=none."
            )

    async def summarize(self, transcript_text: str, title: str = "") -> SummaryResult:
        url = f"{self.settings.groq_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.settings.groq_api_key}",
            "Content-Type": "application/json",
        }
        user_prompt = f"Conversation title: {title or 'Untitled'}\n\nTranscript:\n{transcript_text}"

        body = {
            "model": self.settings.groq_chat_model,
            "temperature": 0.3,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        }

        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(url, headers=headers, json=body)

        if resp.status_code >= 400:
            raise RuntimeError(f"Groq summarization failed ({resp.status_code}): {resp.text}")

        content = resp.json()["choices"][0]["message"]["content"]
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Model returned invalid JSON: {content!r}") from exc

        items = [
            ActionItemDraft(text=str(item.get("text", "")).strip(), assignee=item.get("assignee"))
            for item in parsed.get("action_items", [])
            if str(item.get("text", "")).strip()
        ]

        return SummaryResult(
            provider=self.name,
            model=self.settings.groq_chat_model,
            summary=str(parsed.get("summary", "")).strip(),
            action_items=items,
        )
