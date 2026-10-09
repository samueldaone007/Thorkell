from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ActionItemDraft:
    text: str
    assignee: str | None = None


@dataclass
class SummaryResult:
    provider: str
    model: str
    summary: str
    action_items: list[ActionItemDraft] = field(default_factory=list)


class SummarizationProvider(ABC):
    """Interface for turning a transcript into a summary + action items."""

    name: str = "base"

    @abstractmethod
    async def summarize(self, transcript_text: str, title: str = "") -> SummaryResult:
        raise NotImplementedError
