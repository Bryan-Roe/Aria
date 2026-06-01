"""
Debate Agent
Generates devil's-advocate counter-arguments and challenges for a given
statement, plan, or idea.  Useful for stress-testing proposals, surfacing
blind spots, and strengthening reasoning before commitment.
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


class DebateAgent(BaseAgent):
    """Challenges a claim or plan with structured counter-arguments.

    Accepts tasks of type ``debate``, ``challenge``, or ``stress_test``.
    The task payload should contain a ``claim`` or ``proposal`` or ``text``
    field containing the idea to challenge.  An optional ``steelman``
    boolean (default ``True``) requests a steelmanned version of the
    strongest defence alongside the critiques.

    Returns a dict with:

    * ``counter_arguments`` (list[str]) — objections and opposing points.
    * ``weaknesses`` (list[str]) — identified structural or logical flaws.
    * ``steelman`` (str) — the best-case defence of the original claim
      (included when ``steelman=True``).
    * ``verdict`` (str) — brief overall assessment.
    """

    name = "debate_agent"

    def __init__(
        self,
        memory: MemoryStore,
        llm: Optional[LLMClient] = None,
    ) -> None:
        self.memory = memory
        self.llm = llm or LLMClient()

    def can_handle(self, task: Task) -> bool:
        return task.type in {"debate", "challenge", "stress_test"}

    def execute(self, task: Task) -> Dict[str, Any]:
        payload = task.payload or {}
        claim: str = (
            payload.get("claim")
            or payload.get("proposal")
            or payload.get("text")
            or ""
        ).strip()
        include_steelman: bool = bool(payload.get("steelman", True))

        if not claim:
            result: Dict[str, Any] = {
                "agent": self.name,
                "task_id": task.id,
                "counter_arguments": [],
                "weaknesses": [],
                "steelman": "",
                "verdict": "No claim provided.",
            }
            return result

        debate = self._debate(claim, include_steelman)
        debate["agent"] = self.name
        debate["task_id"] = task.id

        try:
            self.memory.write("debate_completed", debate)
        except Exception:
            logger.exception("Memory write failed when storing debate result")

        return debate

    def _debate(self, claim: str, include_steelman: bool) -> Dict[str, Any]:
        truncated = claim[:_MAX_INPUT_CHARS]
        steelman_instruction = (
            'Include "steelman" (string): the strongest possible defence of the claim. '
            if include_steelman
            else ""
        )
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a debate and critical-thinking engine. "
                    "Output ONLY a JSON object with these fields: "
                    '"counter_arguments" (list of strings), '
                    '"weaknesses" (list of strings), '
                    f'{steelman_instruction}'
                    '"verdict" (string: brief overall assessment).'
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Challenge the following claim or proposal from a devil's advocate "
                    f"perspective:\n{truncated}"
                ),
            },
        ]

        raw = ""
        try:
            raw = self.llm.complete(messages)
        except Exception:
            logger.exception("LLM client failed during debate")

        return self._parse_debate(raw, include_steelman)

    def _parse_debate(self, raw: str, include_steelman: bool) -> Dict[str, Any]:
        fallback: Dict[str, Any] = {
            "counter_arguments": ["Debate unavailable"],
            "weaknesses": [],
            "steelman": "" if not include_steelman else "Steelman unavailable.",
            "verdict": "Could not complete debate analysis.",
        }

        if not raw or not raw.strip():
            return fallback

        def _extract(data: Any) -> Dict[str, Any] | None:
            if not isinstance(data, dict):
                return None
            if not any(k in data for k in ("counter_arguments", "weaknesses", "verdict")):
                return None
            counter = data.get("counter_arguments") or []
            if not isinstance(counter, list):
                counter = [str(counter)]
            weaknesses = data.get("weaknesses") or []
            if not isinstance(weaknesses, list):
                weaknesses = [str(weaknesses)]
            steelman = str(data.get("steelman", "")).strip() if include_steelman else ""
            verdict = str(data.get("verdict", "")).strip()
            return {
                "counter_arguments": [str(c) for c in counter],
                "weaknesses": [str(w) for w in weaknesses],
                "steelman": steelman,
                "verdict": verdict or "No verdict reached.",
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
