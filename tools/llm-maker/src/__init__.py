"""
LLM Maker - Autonomous Tool and Website Creation for LLMs

This package provides components for LLMs to autonomously create,
validate, and execute Python tools in a safe, sandboxed environment,
as well as generate complete websites from natural language descriptions.
"""

from .tool_maker import ToolMaker
from .tool_validator import ToolValidator
from .tool_executor import ToolExecutor
from .tool_registry import ToolRegistry, Tool
from .website_maker import WebsiteMaker, WebsiteValidator

__all__ = [
    "ToolMaker",
    "ToolValidator",
    "ToolExecutor",
    "ToolRegistry",
    "Tool",
    "WebsiteMaker",
    "WebsiteValidator",
]

__version__ = "0.2.0"
