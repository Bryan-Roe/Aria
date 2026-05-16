"""
Aria LLM Client
Unified abstraction layer for future model providers (OpenAI, local, Ollama, etc.).
Currently a lightweight stub returning structured outputs.
"""

from __future__ import annotations

import json
from typing import Dict, List


class LLMClient:
    def __init__(self, model: str = "auto"):
        self.model = model

    def complete(self, messages: List[Dict[str, str]]) -> str:
        """
        Placeholder LLM call.
        Future: integrate real providers + function calling.
        """
        last_user_message = ""
        system_prompt = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_message = m.get("content", "")
                break

        for m in messages:
            if m.get("role") == "system":
                system_prompt = m.get("content", "")
                break

        return self._simulate(last_user_message, system_prompt)

    def _simulate(self, prompt: str, system_prompt: str = "") -> str:
        if not prompt:
            return "{}"

        if "goal evolution engine" in system_prompt.lower():
            return json.dumps({"goal": self._goal_from_prompt(prompt)})

        if "planning engine" in system_prompt.lower():
            return json.dumps(
                [
                    {
                        "type": "llm",
                        "payload": {
                            "prompt": self._extract_goal(prompt),
                        },
                    }
                ]
            )

        return json.dumps(
            {
                "analysis": f"Processed: {prompt}",
                "steps": [
                    "understand_goal",
                    "decompose_task",
                    "execute_solution",
                ],
                "output": f"Simulated result for: {prompt}",
            }
        )

    def _extract_goal(self, prompt: str) -> str:
        marker = "Goal:"
        if marker in prompt:
            goal_section = prompt.split(marker, 1)[1]
            goal = goal_section.split("Context:", 1)[0].strip()
            if goal:
                return goal
        return prompt.strip()

    def _goal_from_prompt(self, prompt: str) -> str:
        normalized = " ".join(prompt.split())
        if not normalized:
            return "improve system performance"
        return f"Refine runtime behavior based on: {normalized[:120]}"
