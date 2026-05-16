"""Agent registry for the Aria core runtime."""

from __future__ import annotations

from typing import Iterable, List

from core.agent import BaseAgent


class AgentRegistry:
    """Simple in-memory registry for core agents."""

    def __init__(self) -> None:
        self._agents: List[BaseAgent] = []

    def register(self, agent: BaseAgent) -> BaseAgent:
        """Register an agent, replacing any previous instance with the same name."""
        self._agents = [existing for existing in self._agents if existing.name != agent.name]
        self._agents.append(agent)
        return agent

    def get_agents(self) -> List[BaseAgent]:
        """Return registered agents in registration order."""
        return list(self._agents)

    def get(self, name: str) -> BaseAgent | None:
        """Return a registered agent by name."""
        for agent in self._agents:
            if agent.name == name:
                return agent
        return None

    def names(self) -> Iterable[str]:
        """Return agent names."""
        return [agent.name for agent in self._agents]
