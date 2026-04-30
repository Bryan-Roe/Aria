"""
Aria Intelligent Router
Scores agents dynamically and selects best execution target.
"""

from typing import Dict, Any, List
from core.task import Task
from core.registry import AgentRegistry


class TaskRouter:
    def __init__(self, registry: AgentRegistry):
        self.registry = registry

    def route(self, task: Task) -> Dict[str, Any]:
        candidates = []

        for agent in self.registry.get_agents():
            score = self._score(agent, task)
            if score > 0:
                candidates.append((score, agent))

        if not candidates:
            return {
                "agent": None,
                "result": {"error": "No suitable agent found"},
            }

        candidates.sort(key=lambda x: x[0], reverse=True)
        best_score, best_agent = candidates[0]

        result = best_agent.execute(task)

        return {
            "agent": best_agent.name,
            "score": best_score,
            "result": result,
        }

    def _score(self, agent, task: Task) -> float:
        """
        Default scoring model:
        - 1.0 if agent can handle task
        - +0.5 if task type strongly matches agent domain
        """

        base = 0.0

        if hasattr(agent, "can_handle") and agent.can_handle(task):
            base = 1.0
        else:
            return 0.0

        # lightweight heuristics
        if task.type in {"llm", "chat", "reason"} and agent.name == "llm_agent":
            base += 0.5

        if task.type in {"tool", "execute", "action"} and agent.name == "tool_agent":
            base += 0.5

        if task.type in {"train", "feedback", "evaluate"} and agent.name == "training_agent":
            base += 0.5

        return base
