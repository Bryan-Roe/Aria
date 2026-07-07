"""
Tool Agent
Executes registered tools inside the Aria multi-agent runtime.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from core.agent import BaseAgent
from core.task import Task

_ALLOWED_SCHEMES = {"http", "https"}


class ToolRegistry:
    def __init__(self):
        self.tools: dict[str, Callable[..., Any]] = {}

    def register(self, name: str, fn: Callable[..., Any]):
        if not name or not name.strip():
            raise ValueError("Tool name cannot be empty.")
        self.tools[name] = fn

    def register_remote(self, name: str, url: str, timeout: int = 10, headers: dict[str, str] | None = None) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in _ALLOWED_SCHEMES:
            raise ValueError(f"URL scheme '{parsed.scheme}' is not allowed; use http or https.")

        def _remote_tool(**kwargs: Any) -> Any:
            request = Request(  # noqa: S310 - scheme validated in register_remote()
                url,
                data=json.dumps(kwargs).encode("utf-8"),
                headers={"Content-Type": "application/json", **(headers or {})},
                method="POST",
            )
            with urlopen(request, timeout=timeout) as response:  # noqa: S310
                body = response.read().decode("utf-8")
            try:
                return json.loads(body) if body else None
            except json.JSONDecodeError:
                return body

        self.register(name, _remote_tool)

    def get(self, name: str):
        return self.tools.get(name)

    def unregister(self, name: str) -> None:
        self.tools.pop(name, None)

    def has(self, name: str) -> bool:
        return name in self.tools

    def list_tools(self) -> list[str]:
        return sorted(self.tools)


class ToolAgent(BaseAgent):
    name = "tool_agent"

    def __init__(self, registry: ToolRegistry | None = None):
        self.registry = registry or ToolRegistry()

    def can_handle(self, task: Task) -> bool:
        return task.type in {"tool", "action", "execute"}

    def execute(self, task: Task) -> dict[str, Any]:
        payload = task.payload or {}
        tool_name = payload.get("tool")
        args = payload.get("args", {})

        if not tool_name:
            return {
                "error": "No tool specified",
                "available_tools": self.registry.list_tools(),
                "agent": self.name,
                "task_id": task.id,
            }
        if not isinstance(args, dict):
            return {
                "error": "Tool args must be a dictionary",
                "tool": tool_name,
                "agent": self.name,
                "task_id": task.id,
            }

        tool = self.registry.get(tool_name)

        if not tool:
            return {
                "error": f"Tool not found: {tool_name}",
                "available_tools": self.registry.list_tools(),
                "agent": self.name,
                "task_id": task.id,
            }

        try:
            result = tool(**args)
            return {
                "output": result,
                "tool": tool_name,
                "args": dict(args),
                "agent": self.name,
                "task_id": task.id,
            }
        except Exception as e:
            return {
                "error": str(e),
                "tool": tool_name,
                "args": dict(args),
                "agent": self.name,
                "task_id": task.id,
            }
