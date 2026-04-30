"""
LLM Agent
Core reasoning agent for Aria multi-agent runtime.
"""

from typing import Dict, Any
from core.agent import BaseAgent
from core.task import Task


class LLMAgent(BaseAgent):
    name = "llm_agent"

    def __init__(self, model=None):
        self.model = model

    def can_handle(self, task: Task) -> bool:
        return task.type in {"llm", "chat", "reason", "generate"}

    def execute(self, task: Task) -> Dict[str, Any]:
        payload = task.payload or {}
        prompt = payload.get("prompt") or payload.get("message") or ""

        # Minimal placeholder reasoning layer (to be replaced with provider integration)
        response = self._run_llm(prompt)

        return {
            "output": response,
            "agent": self.name,
            "task_id": task.id,
        }

    def _run_llm(self, prompt: str) -> str:
        # Future: integrate OpenAI / local / Ollama / Semantic Kernel
        if not prompt:
            return "No input provided"

        return f"[LLM simulated response]: {prompt}"
