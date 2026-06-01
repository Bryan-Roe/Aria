"""
Reflection Agent
Produces structured meta-learning insights from autonomous execution cycle
outcomes stored in memory.  Unlike goal evolution (which proposes the *next*
goal), reflection looks *backward* to extract lessons learned, patterns
across multiple cycles, and concrete behavioural adjustments that the system
should apply going forward.
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
_DEFAULT_CYCLE_LIMIT = 10


class ReflectionAgent(BaseAgent):
    """Extracts meta-learning insights from past cycle outcomes.

    Accepts tasks of type ``reflect``, ``retrospect``, or ``meta_learn``.
    The agent fetches the most recent ``cycle_limit`` ``cycle_completed``
    events from memory (or falls back to the last ``cycle_limit`` general
    events if none exist) and synthesises lessons and adjustments.

    Returns a dict with:

    * ``lessons`` (list[str]) — key takeaways extracted from past cycles.
    * ``patterns`` (list[str]) — recurring trends or failure modes.
    * ``adjustments`` (list[str]) — concrete behavioural changes recommended.
    * ``overall`` (str) — one-sentence executive summary.

    The result is written back to memory as a ``reflection_completed`` event.
    """

    name = "reflection_agent"

    def __init__(
        self,
        memory: MemoryStore,
        llm: Optional[LLMClient] = None,
    ) -> None:
        self.memory = memory
        self.llm = llm or LLMClient()

    def can_handle(self, task: Task) -> bool:
        return task.type in {"reflect", "retrospect", "meta_learn"}

    def execute(self, task: Task) -> Dict[str, Any]:
        payload = task.payload or {}
        cycle_limit: int = max(1, int(payload.get("cycle_limit", _DEFAULT_CYCLE_LIMIT)))

        # Prefer cycle_completed events; fall back to recent general events.
        cycles: List[Dict[str, Any]] = self.memory.query(event_type="cycle_completed", limit=cycle_limit)
        if not cycles:
            cycles = self.memory.last(cycle_limit)

        if not cycles:
            return {
                "agent": self.name,
                "task_id": task.id,
                "lessons": [],
                "patterns": [],
                "adjustments": [],
                "overall": "No cycle history available for reflection.",
            }

        history_text = self._format_cycles(cycles)
        result = self._reflect(history_text)
        result["agent"] = self.name
        result["task_id"] = task.id

        try:
            self.memory.write("reflection_completed", result)
        except Exception:
            logger.exception("Memory write failed when storing reflection")

        return result

    def _reflect(self, history: str) -> Dict[str, Any]:
        truncated = history[:_MAX_INPUT_CHARS]
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a meta-learning reflection engine. "
                    "Output ONLY a JSON object with these fields: "
                    '"lessons" (list of strings: key takeaways from past cycles), '
                    '"patterns" (list of strings: recurring trends or failure modes), '
                    '"adjustments" (list of strings: concrete behavioural changes to adopt), '
                    '"overall" (string: one-sentence executive summary).'
                ),
            },
            {
                "role": "user",
                "content": (
                    "Analyse the following autonomous execution history and produce "
                    f"structured meta-learning insights:\n{truncated}"
                ),
            },
        ]

        raw = ""
        try:
            raw = self.llm.complete(messages)
        except Exception:
            logger.exception("LLM client failed during reflection")

        return self._parse(raw)

    def _parse(self, raw: str) -> Dict[str, Any]:
        fallback: Dict[str, Any] = {
            "lessons": ["Reflection unavailable"],
            "patterns": [],
            "adjustments": [],
            "overall": "Could not complete reflection.",
        }

        if not raw or not raw.strip():
            return fallback

        def _extract(data: Any) -> Dict[str, Any] | None:
            if not isinstance(data, dict):
                return None
            if not any(k in data for k in ("lessons", "patterns", "adjustments", "overall")):
                return None

            def _to_list(val: Any) -> List[str]:
                if isinstance(val, list):
                    return [str(item) for item in val]
                if val:
                    return [str(val)]
                return []

            return {
                "lessons": _to_list(data.get("lessons")),
                "patterns": _to_list(data.get("patterns")),
                "adjustments": _to_list(data.get("adjustments")),
                "overall": str(data.get("overall", "")).strip() or "No summary provided.",
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
    def _format_cycles(cycles: List[Dict[str, Any]]) -> str:
        parts: List[str] = []
        for i, cycle in enumerate(cycles, start=1):
            data = cycle.get("data", {})
            if isinstance(data, dict):
                goal = data.get("goal", "unknown")
                executed = data.get("executed_steps", "?")
                skipped = data.get("skipped_steps", "?")
                assessment = data.get("self_assessment", {})
                score = assessment.get("score", "N/A") if isinstance(assessment, dict) else "N/A"
                parts.append(f"Cycle {i}: goal={goal}, " f"executed={executed}, skipped={skipped}, score={score}")
            else:
                parts.append(f"Cycle {i}: {json.dumps(data, ensure_ascii=False)[:200]}")
        return "\n".join(parts)
