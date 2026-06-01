"""
Planner Agent
Generates task plans from goals using memory context and LLM-driven reasoning.
"""

from __future__ import annotations

import json
import uuid
from typing import Any, Dict, List

from core.agent import BaseAgent
from core.llm.client import LLMClient
from core.memory.store import MemoryStore
from core.task import Task


class PlannerAgent(BaseAgent):
    name = "planner_agent"

    def __init__(self, memory: MemoryStore):
        self.memory = memory
        self.llm = LLMClient()

    def can_handle(self, task: Task) -> bool:
        return task.type in {"plan", "goal", "decompose"}

    def execute(self, task: Task) -> Dict[str, Any]:
        payload = task.payload or {}
        goal = (payload.get("goal") or payload.get("input") or "").strip()

        history = self.memory.last(20)
        if not goal:
            result = {
                "agent": self.name,
                "task_id": task.id,
                "goal": "",
                "plan": [],
                "error": "No goal provided",
            }
            self.memory.write("plan_created", {"goal": "", "plan": [], "error": "No goal provided"})
            return result

        plan = self._create_plan(goal, history)

        self.memory.write("plan_created", {"goal": goal, "plan": plan})

        return {"agent": self.name, "task_id": task.id, "goal": goal, "plan": plan}

    def _create_plan(self, goal: str, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        context_summary = self._summarize_history(history)

        messages = [
            {"role": "system", "content": "You are a planning engine. Output ONLY valid JSON list of tasks."},
            {
                "role": "user",
                "content": f"""
Goal:
{goal}

Context:
{context_summary}

Return a JSON list of tasks in this format:
[{{"type": "llm|tool|train", "payload": {{...}}}}]
""",
            },
        ]

        raw = self.llm.complete(messages)

        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return self._attach_ids(parsed)
        except Exception:
            pass

        return self._attach_ids(
            [
                {"type": "llm", "payload": {"prompt": goal}},
                {"type": "tool", "payload": {"tool": "inspect_context", "args": {"goal": goal}}},
            ]
        )

    def _attach_ids(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        confidence_map = {"llm": 0.8, "tool": 0.9, "train": 0.7}
        attached: List[Dict[str, Any]] = []
        for raw_step in steps:
            if not isinstance(raw_step, dict):
                continue
            step = dict(raw_step)
            step_type = step.get("type")
            if not isinstance(step_type, str) or not step_type.strip():
                continue
            confidence = confidence_map.get(step_type, 0.75)
            step["id"] = str(uuid.uuid4())
            step.setdefault("payload", {})
            step["confidence"] = confidence
            step["risk"] = 1.0 - confidence
            step["priority"] = round(confidence * 10)
            attached.append(step)
        attached.sort(key=lambda item: item.get("priority", 0), reverse=True)
        return attached

    def _summarize_history(self, history: List[Dict[str, Any]]) -> str:
        if not history:
            return "No prior context"

        summaries = []
        for event in history[-5:]:
            event_type = event.get("type", "event")
            data = event.get("data", {})
            if isinstance(data, dict) and data:
                keys = ", ".join(sorted(data.keys())[:3])
                summaries.append(f"{event_type}({keys})")
            else:
                summaries.append(event_type)
        return " | ".join(summaries)
