"""
Aria LLM Client
Unified abstraction layer for future model providers (OpenAI, local, Ollama, etc.).
Currently a lightweight stub returning structured outputs.
"""

from typing import Dict, Any, List


class LLMClient:
    def __init__(self, model: str = "auto"):
        self.model = model

    def complete(self, messages: List[Dict[str, str]]) -> str:
        """
        Placeholder LLM call.
        Future: integrate real providers + function calling.
        """
        last_user_message = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_message = m.get("content", "")
                break

        return self._simulate(last_user_message)

    def _simulate(self, prompt: str) -> str:
        if not prompt:
            return "{}"

        # Return pseudo-structured response for planner compatibility
        return str({
            "analysis": f"Processed: {prompt}",
            "steps": [
                "understand_goal",
                "decompose_task",
                "execute_solution"
            ],
            "output": f"Simulated result for: {prompt}"
        })
