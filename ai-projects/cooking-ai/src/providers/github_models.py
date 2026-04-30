from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore


class GitHubModelsProvider:
    """OpenAI-compatible provider for GitHub Models.

    Uses the OpenAI Python SDK with a custom base_url.
    Env vars:
      - GITHUB_MODELS_API_KEY or GITHUB_TOKEN
      - GITHUB_MODELS_MODEL (optional; default 'gpt-4o-mini')
      - COOKING_TEMPERATURE (optional; default 0.4)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        base_url: str = "https://models.inference.ai.azure.com",
    ) -> None:
        if OpenAI is None:
            raise RuntimeError(
                "openai package not available. Install with: pip install openai>=1.43.0"
            )
        api_key = (
            api_key or os.getenv("GITHUB_MODELS_API_KEY") or os.getenv("GITHUB_TOKEN")
        )
        if not api_key:
            raise RuntimeError(
                "GitHub Models provider requires GITHUB_MODELS_API_KEY or GITHUB_TOKEN to be set."
            )
        self.model = model or os.getenv("GITHUB_MODELS_MODEL", "gpt-4o-mini")
        self.temperature = 0.4 if temperature is None else float(temperature)
        # Create client with custom base URL
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def complete(self, messages: List[Dict[str, str]], json_mode: bool = False) -> str:
        """Send a chat completion request and return the assistant content."""
        # Some GitHub Models support response_format; if not, rely on prompting.
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": 1024,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        resp = self.client.chat.completions.create(**kwargs)  # type: ignore
        content = resp.choices[0].message.content if resp.choices else ""
        return content or ""
