"""
Goal Evolution Agent
Generates and refines goals based on memory history for autonomous operation.
"""

from typing import Dict, Any
from core.agent import BaseAgent
from core.task import Task
from core.memory.store import MemoryStore
from core.llm.client import LLMClient
import json


class GoalEvolutionAgent(BaseAgent):
    name = "goal_evolution_agent"

    def __init__(self, memory: MemoryStore):
        self.memory = memory
        self.llm = LLMClient()

    def can_handle(self, task: Task) -> bool:
        return task.type in {"goal_evolve", "new_goal", "reflect"}

    def execute(self, task: Task) -> Dict[str, Any]:
        history = self.memory.last(30)

        prompt = self._build_prompt(history)

        messages = [
            {
                "role": "system",
                "content": "You are a goal evolution engine. Output ONLY a JSON object with a single field: goal."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        raw = self.llm.complete(messages)

        goal = self._parse(raw)

        self.memory.write("goal_evolved", {"goal": goal})

        return {
            "agent": self.name,
            "goal": goal,
            "task_id": task.id
        }

    def _build_prompt(self, history):
        if not history:
            return "No history. Generate a simple useful system improvement goal."

        summary = " | ".join(e.get("type", "event") for e in history[-10:])

        return f"""
Based on system history:
{summary}

Generate the next most useful goal for system improvement, learning, or optimization.
"""

    def _parse(self, raw: str) -> str:
        try:
            data = json.loads(raw)
            return data.get("goal", "improve system")
        except Exception:
            return "improve system performance"
""