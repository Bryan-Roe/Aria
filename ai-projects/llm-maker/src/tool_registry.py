"""
Tool Registry - Manages tool lifecycle and storage
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class Tool:
    """Represents a generated tool"""

    id: str
    name: str
    description: str
    code: str
    parameters: Dict[str, str]
    return_type: str
    created_at: str
    validated: bool = False
    execution_count: int = 0
    last_executed: Optional[str] = None
    examples: List[Dict[str, Any]] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "Tool":
        """Create from dictionary"""
        return cls(**data)


class ToolRegistry:
    """Registry for managing generated tools"""

    def __init__(self, tools_dir: Optional[Path] = None):
        """
        Initialize tool registry

        Args:
            tools_dir: Directory to store tools (default: ./tools)
        """
        self.tools_dir = tools_dir or Path("./tools")
        self.tools_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.tools_dir / "index.json"
        self._tools: Dict[str, Tool] = {}
        self._load_index()

    def _load_index(self):
        """Load tool index from disk"""
        if self.index_file.exists():
            try:
                with open(self.index_file, "r") as f:
                    index = json.load(f)
                    for tool_data in index.get("tools", []):
                        tool = Tool.from_dict(tool_data)
                        self._tools[tool.id] = tool
                logger.info(f"Loaded {len(self._tools)} tools from registry")
            except Exception as e:
                logger.error(f"Failed to load tool index: {e}")
                self._tools = {}

    def _save_index(self):
        """Save tool index to disk"""
        try:
            index = {
                "version": "1.0",
                "tools": [tool.to_dict() for tool in self._tools.values()],
                "count": len(self._tools),
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
            with open(self.index_file, "w") as f:
                json.dump(index, f, indent=2)
            logger.debug(f"Saved {len(self._tools)} tools to registry")
        except Exception as e:
            logger.error(f"Failed to save tool index: {e}")

    def register(self, tool: Tool) -> str:
        """
        Register a new tool

        Args:
            tool: Tool to register

        Returns:
            Tool ID
        """
        if not tool.id:
            tool.id = str(uuid4())

        if not tool.created_at:
            tool.created_at = datetime.now(timezone.utc).isoformat()

        self._tools[tool.id] = tool
        self._save_index()

        # Save tool code to separate file
        tool_file = self.tools_dir / f"{tool.id}.py"
        with open(tool_file, "w") as f:
            f.write(f"# Tool: {tool.name}\n")
            f.write(f"# ID: {tool.id}\n")
            f.write(f"# Created: {tool.created_at}\n\n")
            f.write(tool.code)

        logger.info(f"Registered tool '{tool.name}' with ID {tool.id}")
        return tool.id

    def get(self, tool_id: str) -> Optional[Tool]:
        """
        Get a tool by ID

        Args:
            tool_id: Tool ID

        Returns:
            Tool or None if not found
        """
        return self._tools.get(tool_id)

    def get_by_name(self, name: str) -> Optional[Tool]:
        """
        Get a tool by name

        Args:
            name: Tool name

        Returns:
            Tool or None if not found
        """
        for tool in self._tools.values():
            if tool.name == name:
                return tool
        return None

    def list_tools(self, tags: Optional[List[str]] = None) -> List[Tool]:
        """
        List all registered tools

        Args:
            tags: Optional filter by tags

        Returns:
            List of tools
        """
        tools = list(self._tools.values())

        if tags:
            tools = [t for t in tools if any(tag in t.tags for tag in tags)]

        return sorted(tools, key=lambda t: t.created_at, reverse=True)

    def delete(self, tool_id: str) -> bool:
        """
        Delete a tool

        Args:
            tool_id: Tool ID

        Returns:
            True if deleted, False if not found
        """
        if tool_id not in self._tools:
            return False

        tool = self._tools.pop(tool_id)
        self._save_index()

        # Delete tool file
        tool_file = self.tools_dir / f"{tool_id}.py"
        if tool_file.exists():
            tool_file.unlink()

        logger.info(f"Deleted tool '{tool.name}' (ID: {tool_id})")
        return True

    def update_stats(self, tool_id: str):
        """
        Update tool execution statistics

        Args:
            tool_id: Tool ID
        """
        if tool_id in self._tools:
            tool = self._tools[tool_id]
            tool.execution_count += 1
            tool.last_executed = datetime.now(timezone.utc).isoformat()
            self._save_index()

    def search(self, query: str) -> List[Tool]:
        """
        Search tools by name or description

        Args:
            query: Search query

        Returns:
            List of matching tools
        """
        query_lower = query.lower()
        results = []

        for tool in self._tools.values():
            if (
                query_lower in tool.name.lower()
                or query_lower in tool.description.lower()
            ):
                results.append(tool)

        return results

    def get_stats(self) -> Dict[str, Any]:
        """
        Get registry statistics

        Returns:
            Dictionary with statistics
        """
        total_executions = sum(t.execution_count for t in self._tools.values())
        validated_count = sum(1 for t in self._tools.values() if t.validated)

        return {
            "total_tools": len(self._tools),
            "validated_tools": validated_count,
            "total_executions": total_executions,
            "most_used": (
                max(
                    self._tools.values(), key=lambda t: t.execution_count, default=None
                ).name
                if self._tools
                else None
            ),
            "registry_path": str(self.tools_dir),
        }
