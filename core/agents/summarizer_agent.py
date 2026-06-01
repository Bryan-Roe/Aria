"""
Summarizer Agent
Condenses conversation history and event logs into compact summaries for
efficient memory management and context compression.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from core.agent import BaseAgent
from core.llm.client import LLMClient
from core.memory.store import MemoryStore
from core.task import Task

logger = logging.getLogger(__name__)

_MAX_INPUT_CHARS = 4000
_MAX_SUMMARY_LENGTH = 500


class SummarizerAgent(BaseAgent):
    """Summarizes recent memory events or free-form text into a brief digest.

    Accepts tasks of type ``summarize``, ``compress``, or ``condense``.  When
    the task payload includes a ``text`` or ``content`` field that text is
    summarized directly; otherwise the agent fetches the last ``limit`` events
    from memory and summarizes those.

    The produced summary is written back to memory under the ``summary_created``
    event type so that other agents and the knowledge graph can reference it.
    """

    name = "summarizer_agent"

    def __init__(
        self,
        memory: MemoryStore,
        llm: Optional[LLMClient] = None,
    ) -> None:
        self.memory = memory
        self.llm = llm or LLMClient()

    def can_handle(self, task: Task) -> bool:
        return task.type in {"summarize", "compress", "condense"}

    def execute(self, task: Task) -> Dict[str, Any]:
        payload = task.payload or {}
        text: str = payload.get("text") or payload.get("content") or ""
        limit: int = max(1, int(payload.get("limit", 20)))

        if not text.strip():
            events: List[Dict[str, Any]] = self.memory.last(limit)
            if not events:
                summary = "No context to summarize."
            else:
                text = "\n".join(self._format_event(e) for e in events)
                summary = self._summarize(text)
        else:
            summary = self._summarize(text)

        try:
            self.memory.write("summary_created", {"summary": summary})
        except Exception:
            logger.exception("Memory write failed when storing summary")

        return {
            "agent": self.name,
            "task_id": task.id,
            "summary": summary,
        }

    def _summarize(self, text: str) -> str:
        truncated = text[:_MAX_INPUT_CHARS]
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a summarization engine. "
                    'Output ONLY a JSON object with a single field: summary.'
                ),
            },
            {
                "role": "user",
                "content": f"Summarize the following in 2-3 sentences:\n{truncated}",
            },
        ]

        raw = ""
        try:
            raw = self.llm.complete(messages)
        except Exception:
            logger.exception("LLM client failed during summarization")

        return self._parse_summary(raw)

    def _parse_summary(self, raw: str) -> str:
        fallback = "Summary unavailable."

        if not raw or not raw.strip():
            return fallback

        try:
            data = json.loads(raw)
            if isinstance(data, dict) and "summary" in data:
                return str(data["summary"]).strip() or fallback
        except Exception:
            pass

        try:
            match = re.search(r"\{.*?\}", raw, re.S)
            if match:
                data = json.loads(match.group(0))
                if isinstance(data, dict) and "summary" in data:
                    return str(data["summary"]).strip() or fallback
        except Exception:
            pass

        heuristic = re.search(r"summary\s*[:\-]\s*(.+)", raw, re.I)
        if heuristic:
            return heuristic.group(1).strip().strip("'\"")[:_MAX_SUMMARY_LENGTH]

        return raw.strip()[:_MAX_SUMMARY_LENGTH] or fallback

    @staticmethod
    def _format_event(event: Dict[str, Any]) -> str:
        event_type = event.get("type", "event")
        data = event.get("data", "")
        data_str = (
            json.dumps(data, ensure_ascii=False)
            if isinstance(data, (dict, list))
            else str(data)
        )
        return f"{event_type}: {data_str}"
