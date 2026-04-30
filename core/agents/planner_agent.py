"""
Planner Agent
Generates task plans from goals using memory context and LLM-style reasoning.
"""

from typing import Dict, Any, List
from core.agent import BaseAgent
from core.task import Task
from core.memory.store import MemoryStore
import uuid


class PlannerAgent(BaseAgent):
    name = "planner_agent"

    def __init__(self, memory: MemoryStore):
        self.memory = memory

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
        """
        LLM-style planning layer (currently deterministic scaffold,
        designed for later model integration).
        """

        if not goal:
            return [{"error": "No goal provided"}]

        context_summary = self._summarize_history(history)

        # Simulated structured reasoning output
        # Future: replace with real LLM JSON schema response
        plan = [
            {
                "id": str(uuid.uuid4()),
                "type": "llm",
                "payload": {
                    "prompt": f"Goal: {goal}\nContext: {context_summary}\n\nProduce solution step output"
                },
            },
            {
                "id": str(uuid.uuid4()),
                "type": "tool",
                "payload": {
                    "tool": "evaluate_output",
                    "args": {"mode": "auto"},
                },
            },
            {
                "id": str(uuid.uuid4()),
                "type": "train",
                "payload": {
                    "signal": "auto_improve",
                },
            },
        ]

        return plan

    def _summarize_history(self, history: List[Dict[str, Any]]) -> str:
        if not history:
            return "No prior context"

        last_events = history[-5:]
        return " | ".join(
            f"{e.get('type', 'event')}" for e in last_events
        )
