"""
Planner Agent
Generates task plans from goals using memory context and LLM-driven reasoning.
"""

from typing import Dict, Any, List
from core.agent import BaseAgent
from core.task import Task
from core.memory.store import MemoryStore
from core.llm.client import LLMClient
import uuid
import json


class PlannerAgent(BaseAgent):
    name = "planner_agent"

    def __init__(self, memory: MemoryStore):
        self.memory = memory
        self.llm = LLMClient()

    def can_handle(self, task: Task) -> bool:
        return task.type in {"plan", "goal", "decompose"}

    def execute(self, task: Task) -> Dict[str, Any]:
        payload = task.payload or {}
        goal = payload.get("goal") or payload.get("input") or ""

        history = self.memory.last(20)

        plan = self._create_plan(goal, history)

        self.memory.write("plan_created", {
            "goal": goal,
            "plan": plan,
        })

        return {
            "agent": self.name,
            "task_id": task.id,
            "goal": goal,
            "plan": plan,
        }

    def _create_plan(self, goal: str, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not goal:
            return [{"error": "No goal provided"}]

        context_summary = self._summarize_history(history)

        messages = [
            {
                "role": "system",
                "content": "You are a planning engine. Output ONLY valid JSON list of tasks."
            },
            {
                "role": "user",
                "content": f"""
Goal:
{goal}

Context:
{context_summary}

Return a JSON list of tasks in this format:
[{{"type": "llm|tool|train", "payload": {{...}}}}]
"""
            }
        ]

        raw = self.llm.complete(messages)

        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return self._attach_ids(parsed)
        except Exception:
            pass

        # fallback
        return [
            {
                "id": str(uuid.uuid4()),
                "type": "llm",
                "payload": {"prompt": goal},
            }
        ]

    def _attach_ids(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out = []
        for s in steps:
            s["id"] = str(uuid.uuid4())
            out.append(s)
        return out

    def _summarize_history(self, history: List[Dict[str, Any]]) -> str:
        if not history:
            return "No prior context"

        return " | ".join(e.get("type", "event") for e in history[-5:])
