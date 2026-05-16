"""
Goal Evolution Agent
Generates and refines goals based on memory history for autonomous operation.

Improvements:
- Fixed trailing syntax error.
- Accepts an injectable LLM client for testability and decoupling.
- Robust JSON and heuristic parsing with safe fallbacks.
- Added logging and defensive error handling.
- Clearer typing and docstrings; goal length limiting and sanitization.
"""

from typing import Dict, Any, Optional, Sequence
import json

from core.agent import BaseAgent
from core.task import Task
from core.memory.store import MemoryStore
from core.llm.client import LLMClient
import logging
import re

logger = logging.getLogger(__name__)


class GoalEvolutionAgent(BaseAgent):
    """Agent that proposes and refines goals using memory context and an LLM.

    The LLM client may be injected for testing or to swap implementations.
    """

    name = "goal_evolution_agent"

    def __init__(self, memory: MemoryStore, llm: Optional[LLMClient] = None):
        self.memory = memory
        self.llm = llm or LLMClient()

    def can_handle(self, task: Task) -> bool:
        """Return True for tasks related to goal evolution or reflection."""
        return task.type in {"goal_evolve", "new_goal", "reflect"}

    def execute(self, task: Task) -> Dict[str, Any]:
        """Generate or refine a goal based on recent memory history.

        Returns a dict containing the chosen goal and metadata.
        """
        history = self.memory.last(30)
        prompt = self._build_prompt(history)

        messages = [
            {
                "role": "system",
                "content": "You are a goal evolution engine. Output ONLY a JSON object with a single field: goal.",
            },
            {"role": "user", "content": prompt},
        ]

        raw = ""
        try:
            raw = self.llm.complete(messages)
        except Exception as e:
            logger.exception("LLM client failed while generating goal: %s", e)

        goal = self._parse(raw)

        # persist the evolved goal
        try:
            self.memory.write("goal_evolved", {"goal": goal})
        except Exception:
            logger.exception("Memory write failed when storing evolved goal")

        return {
            "agent": self.name,
            "goal": goal,
            "task_id": task.id,
        }

    def _build_prompt(self, history: Sequence[Dict[str, Any]]) -> str:
        if not history:
            return "No history. Generate a simple useful system improvement goal."

        # include the last few event types and short summaries where available
        entries = history[-10:]
        summary_parts = []
        for e in entries:
            t = e.get("type", "event")
            data = e.get("data")
            if isinstance(data, dict):
                short = data.get("goal") or data.get(
                    "message") or data.get("output")
            else:
                short = str(data)[:80] if data is not None else ""
            part = f"{t}: {short}" if short else t
            summary_parts.append(part)

        summary = " | ".join(summary_parts)

        return f"""
Based on system history:
{summary}

Generate the next most useful goal for system improvement, learning, or optimization.
"""

    def _parse(self, raw: str) -> str:
        """Parse the raw LLM output into a single goal string.

        This is defensive: tries strict JSON first, then searches for a JSON object substring,
        then looks for simple 'goal:' markers, and finally falls back to a safe default.
        """
        fallback = "improve system performance"

        if not raw or not raw.strip():
            logger.debug(
                "Empty LLM response for goal evolution; returning fallback")
            return fallback

        # Try strict JSON parse
        try:
            data = json.loads(raw)
            if isinstance(data, dict) and "goal" in data:
                goal = str(data.get("goal", fallback)).strip()
                return self._normalize_goal(goal, fallback)
        except Exception:
            logger.debug(
                "Strict JSON parsing failed for LLM output; attempting substring search")

        # Attempt to find first JSON object in the string
        try:
            match = re.search(r"\{.*?\}", raw, flags=re.S)
            if match:
                candidate = match.group(0)
                data = json.loads(candidate)
                if isinstance(data, dict) and "goal" in data:
                    goal = str(data.get("goal", fallback)).strip()
                    return self._normalize_goal(goal, fallback)
        except Exception:
            logger.debug("JSON substring parsing failed")

        # Look for heuristic 'goal:' pattern
        m = re.search(r"goal\s*[:\-]\s*(.+)", raw, flags=re.I)
        if m:
            goal = m.group(1).strip().strip('\'"')
            return self._normalize_goal(goal, fallback)

        # As a last resort, return a short sanitized excerpt of the raw output
        excerpt = " ".join(raw.split())[:200]
        logger.info("Using raw excerpt as goal fallback: %s", excerpt)
        return self._normalize_goal(excerpt, fallback)

    def _normalize_goal(self, goal: str, fallback: str) -> str:
        """Sanitize and limit the goal text length, return fallback for empty results."""
        if not goal:
            return fallback
        goal = goal.strip()
        # enforce a reasonable maximum length
        if len(goal) > 240:
            goal = goal[:240].rsplit(" ", 1)[0] + "..."
        return goal
