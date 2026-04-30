"""
Tool Agent
Executes registered tools inside the Aria multi-agent runtime.
"""

from typing import Dict, Any, Callable
from core.agent import BaseAgent
from core.task import Task


class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Callable[..., Any]] = {}

    def register(self, name: str, fn: Callable[..., Any]):
        self.tools[name] = fn

    def get(self, name: str):
        return self.tools.get(name)


class ToolAgent(BaseAgent):
    name = "tool_agent"

    def __init__(self, registry: ToolRegistry | None = None):
        self.registry = registry or ToolRegistry()

    def can_handle(self, task: Task) -> bool:
        return task.type in {"tool", "action", "execute"}

    def execute(self, task: Task) -> Dict[str, Any]:
        payload = task.payload or {}
        tool_name = payload.get("tool")
        args = payload.get("args", {})

        tool = self.registry.get(tool_name)

        if not tool:
            return {
                "error": f"Tool not found: {tool_name}",
                "agent": self.name,
                "task_id": task.id,
            }

        try:
            result = tool(**args)
            return {
                "output": result,
                "tool": tool_name,
                "agent": self.name,
                "task_id": task.id,
            }
        except Exception as e:
            return {
                "error": str(e),
                "tool": tool_name,
                "agent": self.name,
                "task_id": task.id,
            }
