"""
Aria LLM Client
Unified abstraction layer for future model providers (OpenAI, local, Ollama, etc.).
Currently a lightweight offline simulator returning deterministic JSON outputs.
"""

from __future__ import annotations

import importlib
import json
import os
from typing import Dict, Iterable, List


class LLMClient:
    def __init__(self, model: str = "auto", use_real_provider: bool = False):
        self.model = model
        env_enabled = os.getenv("ARIA_USE_REAL_LLM") == "1"
        self.use_real_provider = bool(use_real_provider or env_enabled)

    def complete(self, messages: List[Dict[str, str]]) -> str:
        """
        Placeholder LLM call.
        Future: integrate real providers + function calling.
        """
        last_user_message = ""
        system_prompt = ""
        for message in reversed(messages):
            if message.get("role") == "user":
                last_user_message = message.get("content", "")
                break

        for message in messages:
            if message.get("role") == "system":
                system_prompt = message.get("content", "")
                break

        if self.use_real_provider:
            real_response = self._complete_with_real_provider(messages)
            if real_response is not None:
                return real_response

        return self._simulate(last_user_message, system_prompt)

    def _complete_with_real_provider(self, messages: List[Dict[str, str]]) -> str | None:
        try:
            module = importlib.import_module("agi_provider")
            if hasattr(module, "create_agi_provider"):
                provider = module.create_agi_provider(model=self.model)
            else:
                provider = module.AGIProvider(model=self.model)
            response = provider.complete(messages, stream=False)
            if isinstance(response, str):
                return response
            if isinstance(response, Iterable):
                return "".join(str(part) for part in response)
        except Exception:
            return None
        return None

    def _simulate(self, prompt: str, system_prompt: str = "") -> str:
        if not prompt:
            return "{}"

        if "goal evolution engine" in system_prompt.lower():
            return json.dumps({"goal": self._goal_from_prompt(prompt)})

        if "planning engine" in system_prompt.lower():
            return json.dumps(
                [
                    {"type": "llm", "payload": {"prompt": self._extract_goal(prompt)}},
                    {
                        "type": "tool",
                        "payload": {"tool": "inspect_context", "args": {"goal": self._extract_goal(prompt)}},
                    },
                ]
            )

        if "summarization engine" in system_prompt.lower():
            excerpt = " ".join(prompt.split())[:200]
            return json.dumps({"summary": f"Summary of: {excerpt}"})

        if "critique engine" in system_prompt.lower():
            return json.dumps({
                "score": 0.75,
                "issues": ["Minor verbosity detected"],
                "suggestions": ["Consider trimming the response for conciseness"],
            })

        if "chain-of-thought reasoning engine" in system_prompt.lower():
            excerpt = " ".join(prompt.split())[:100]
            return json.dumps({
                "steps": [
                    f"1. Identify the core question in: {excerpt}",
                    "2. Break the problem into smaller sub-problems",
                    "3. Evaluate each sub-problem systematically",
                ],
                "conclusion": f"Based on the reasoning above, a well-structured answer can be formed for: {excerpt}",
                "confidence": 0.8,
            })

        if "debate and critical-thinking engine" in system_prompt.lower():
            excerpt = " ".join(prompt.split())[:80]
            return json.dumps({
                "counter_arguments": [
                    f"The claim '{excerpt}' may not hold under different assumptions",
                    "Evidence may be incomplete or biased",
                ],
                "weaknesses": [
                    "Relies on unverified premises",
                    "Does not account for edge cases",
                ],
                "steelman": f"The strongest case for '{excerpt}' rests on its core logic being sound under ideal conditions.",
                "verdict": "The claim has merit but requires stronger evidence and broader scope.",
            })

        return json.dumps(
            {
                "analysis": f"Processed: {prompt}",
                "steps": ["understand_goal", "decompose_task", "execute_solution"],
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
