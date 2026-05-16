"""Base agent contract for the Aria core runtime."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from core.task import Task


class BaseAgent(ABC):
    """Minimal interface shared by all runtime agents."""

    name = "base_agent"

    @abstractmethod
    def can_handle(self, task: Task) -> bool:
        """Return whether this agent can execute the task."""

    @abstractmethod
    def execute(self, task: Task) -> Dict[str, Any]:
        """Execute a task and return a structured result."""
