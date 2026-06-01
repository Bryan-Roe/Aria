"""Repository automation agents.

Deterministic, dependency-light agents that inspect the repository and report
structured results. See :mod:`scripts.agents.base` for the shared framework.
"""

from __future__ import annotations

from scripts.agents.base import (
    AgentResult,
    AutomationAgent,
    get_registered_agents,
    iter_source_files,
    register,
)

__all__ = [
    "AgentResult",
    "AutomationAgent",
    "get_registered_agents",
    "iter_source_files",
    "register",
]
