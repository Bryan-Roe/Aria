"""
Hypothesis Agent
Generates structured, testable hypotheses from patterns observed in memory
events.  Useful for surfacing causal theories about system behaviour, failure
modes, or improvement opportunities so they can be validated by subsequent
planning or experiment cycles.
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
_DEFAULT_LIMIT = 20


class HypothesisAgent(BaseAgent):
    """Derives testable hypotheses from recent memory events or a supplied observation.

    Accepts tasks of type ``hypothesize``, ``infer``, or ``generate_hypothesis``.
    When the task payload includes an ``observation`` or ``text`` field that
    text is used as the input; otherwise the agent fetches the last ``limit``
    events from memory and derives hypotheses from those.

    Returns a dict with:

    * ``hypotheses`` (list[dict]) — each entry has ``statement`` (str),
      ``rationale`` (str), and ``testable`` (bool).
    * ``summary`` (str) — a brief narrative of the hypothesised patterns.

    The result is also written to memory as a ``hypothesis_generated`` event.
    """

    name = "hypothesis_agent"

    def __init__(
        self,
        memory: MemoryStore,
        llm: Optional[LLMClient] = None,
    ) -> None:
        self.memory = memory
        self.llm = llm or LLMClient()

    def can_handle(self, task: Task) -> bool:
        return task.type in {"hypothesize", "infer", "generate_hypothesis"}

    def execute(self, task: Task) -> Dict[str, Any]:
        payload = task.payload or {}
        observation: str = (
            payload.get("observation") or payload.get("text") or ""
        ).strip()
        limit: int = max(1, int(payload.get("limit", _DEFAULT_LIMIT)))

        if not observation:
            events: List[Dict[str, Any]] = self.memory.last(limit)
            if not events:
                return {
                    "agent": self.name,
                    "task_id": task.id,
                    "hypotheses": [],
                    "summary": "No observations available to hypothesize from.",
                }
            observation = self._format_events(events)

        result = self._hypothesize(observation)
        result["agent"] = self.name
        result["task_id"] = task.id

        try:
            self.memory.write("hypothesis_generated", result)
        except Exception:
            logger.exception("Memory write failed when storing hypotheses")

        return result

    def _hypothesize(self, observation: str) -> Dict[str, Any]:
        truncated = observation[:_MAX_INPUT_CHARS]
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a hypothesis generation engine. "
                    "Output ONLY a JSON object with these fields: "
                    '"hypotheses" (list of objects, each with "statement" (str), '
                    '"rationale" (str), "testable" (bool)), '
                    '"summary" (str: one-sentence narrative of the patterns).'
                ),
            },
            {
                "role": "user",
                "content": (
                    "Based on the following observations, generate 2–4 testable "
                    f"hypotheses about system behaviour or improvement opportunities:\n{truncated}"
                ),
            },
        ]

        raw = ""
        try:
            raw = self.llm.complete(messages)
        except Exception:
            logger.exception("LLM client failed during hypothesis generation")

        return self._parse(raw)

    def _parse(self, raw: str) -> Dict[str, Any]:
        fallback: Dict[str, Any] = {
            "hypotheses": [
                {
                    "statement": "Hypothesis generation failed: no valid response from LLM",
                    "rationale": "",
                    "testable": False,
                }
            ],
            "summary": "Could not generate hypotheses.",
        }

        if not raw or not raw.strip():
            return fallback

        def _extract(data: Any) -> Dict[str, Any] | None:
            if not isinstance(data, dict):
                return None
            if "hypotheses" not in data:
                return None
            hypotheses = data.get("hypotheses") or []
            if not isinstance(hypotheses, list):
                return None
            cleaned: List[Dict[str, Any]] = []
            for h in hypotheses:
                if not isinstance(h, dict):
                    continue
                cleaned.append(
                    {
                        "statement": str(h.get("statement", "")).strip(),
                        "rationale": str(h.get("rationale", "")).strip(),
                        "testable": bool(h.get("testable", False)),
                    }
                )
            summary = str(data.get("summary", "")).strip()
            return {
                "hypotheses": cleaned,
                "summary": summary or "No summary provided.",
            }

        try:
            result = _extract(json.loads(raw))
            if result is not None:
                return result
        except Exception:
            pass

        try:
            match = re.search(r"\{.*?\}", raw, re.S)
            if match:
                result = _extract(json.loads(match.group(0)))
                if result is not None:
                    return result
        except Exception:
            pass

        return fallback

    @staticmethod
    def _format_events(events: List[Dict[str, Any]]) -> str:
        parts: List[str] = []
        for e in events:
            event_type = e.get("type", "event")
            data = e.get("data", "")
            data_str = (
                json.dumps(data, ensure_ascii=False)
                if isinstance(data, (dict, list))
                else str(data)
            )
            parts.append(f"{event_type}: {data_str}")
        return "\n".join(parts)
