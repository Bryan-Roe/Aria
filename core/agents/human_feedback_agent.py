"""Human feedback agent for recording operator guidance and optional bus broadcasts."""

from __future__ import annotations

from typing import Any, Dict, Optional

from core.agent import BaseAgent
from core.bus import AgentBus
from core.memory.store import MemoryStore
from core.task import Task


class HumanFeedbackAgent(BaseAgent):
    name = "human_feedback_agent"

    def __init__(self, memory: MemoryStore, bus: Optional[AgentBus] = None) -> None:
        self.memory = memory
        self.bus = bus

    def can_handle(self, task: Task) -> bool:
        return task.type in {"human_feedback", "feedback", "review"}

    def execute(self, task: Task) -> Dict[str, Any]:
        payload = task.payload or {}
        message = payload.get("message") or payload.get("feedback") or ""
        rating = payload.get("rating")
        event = {
            "message": message,
            "rating": rating,
            "source": payload.get("source", "human"),
        }
        event_id = self.memory.write("human_feedback", event)
        if self.bus is not None:
            self.bus.publish("human_feedback", {"task_id": task.id, "event_id": event_id, **event})
        return {
            "agent": self.name,
            "task_id": task.id,
            "status": "recorded",
            "event_id": event_id,
            "feedback": event,
        }
