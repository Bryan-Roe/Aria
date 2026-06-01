"""
Reasoning Agent
Performs explicit multi-step chain-of-thought reasoning on complex questions or
problems, returning a structured trace of intermediate steps and a final
conclusion.  Useful as a deliberative layer before planning or as a standalone
explanation tool.
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
_DEFAULT_NUM_STEPS = 3


class ReasoningAgent(BaseAgent):
    """Produces a multi-step reasoning chain for a given question or problem.

    Accepts tasks of type ``reason``, ``explain``, or ``chain_of_thought``.
    The task payload should contain a ``question`` or ``prompt`` field.  An
    optional ``num_steps`` field controls how many reasoning steps are
    requested (default 3).

    Returns a dict with:

    * ``steps`` (list[str]) — ordered reasoning steps.
    * ``conclusion`` (str) — final answer derived from the chain.
    * ``confidence`` (float 0–1) — self-reported confidence estimate.
    """

    name = "reasoning_agent"

    def __init__(
        self,
        memory: MemoryStore,
        llm: Optional[LLMClient] = None,
    ) -> None:
        self.memory = memory
        self.llm = llm or LLMClient()

    def can_handle(self, task: Task) -> bool:
        return task.type in {"reason", "explain", "chain_of_thought"}

    def execute(self, task: Task) -> Dict[str, Any]:
        payload = task.payload or {}
        question: str = (
            payload.get("question")
            or payload.get("prompt")
            or payload.get("text")
            or ""
        ).strip()
        num_steps: int = max(1, int(payload.get("num_steps", _DEFAULT_NUM_STEPS)))

        if not question:
            result: Dict[str, Any] = {
                "agent": self.name,
                "task_id": task.id,
                "steps": [],
                "conclusion": "No question provided.",
                "confidence": 0.0,
            }
            return result

        reasoning = self._reason(question, num_steps)
        reasoning["agent"] = self.name
        reasoning["task_id"] = task.id

        try:
            self.memory.write("reasoning_completed", reasoning)
        except Exception:
            logger.exception("Memory write failed when storing reasoning trace")

        return reasoning

    def _reason(self, question: str, num_steps: int) -> Dict[str, Any]:
        truncated = question[:_MAX_INPUT_CHARS]
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a chain-of-thought reasoning engine. "
                    "Output ONLY a JSON object with these fields: "
                    '"steps" (list of strings, each a numbered reasoning step), '
                    '"conclusion" (string, the final answer), '
                    '"confidence" (float 0-1).'
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Reason through the following in {num_steps} explicit steps:\n"
                    f"{truncated}"
                ),
            },
        ]

        raw = ""
        try:
            raw = self.llm.complete(messages)
        except Exception:
            logger.exception("LLM client failed during reasoning")

        return self._parse_reasoning(raw)

    def _parse_reasoning(self, raw: str) -> Dict[str, Any]:
        fallback: Dict[str, Any] = {
            "steps": ["Reasoning unavailable"],
            "conclusion": "Could not complete reasoning chain.",
            "confidence": 0.0,
        }

        if not raw or not raw.strip():
            return fallback

        def _extract(data: Any) -> Dict[str, Any] | None:
            if not isinstance(data, dict):
                return None
            if not any(k in data for k in ("steps", "conclusion")):
                return None
            steps = data.get("steps") or []
            if not isinstance(steps, list):
                steps = [str(steps)]
            conclusion = str(data.get("conclusion", "")).strip()
            confidence = float(
                max(0.0, min(1.0, float(data.get("confidence", 0.5))))
            )
            return {
                "steps": [str(s) for s in steps],
                "conclusion": conclusion or "No conclusion reached.",
                "confidence": confidence,
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
