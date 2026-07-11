"""
Local AGI provider using the core/llm client as a deterministic, dependency-free
fallback. This provider is intentionally lightweight and avoids importing heavy
chat-cli internals at import time to reduce circular import risk.

It implements a minimal `complete(messages, stream)` contract compatible with
BaseChatProvider consumers.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any


class LocalAGIProvider:
    """Deterministic AGI-like provider backed by core.llm.client.LLMClient.

    - `complete(messages, stream=True)` returns an iterable of string chunks
      when `stream=True`, or a final string when `stream=False`.
    - Uses the simulator's structured JSON output to provide useful chunks.
    """

    def __init__(self, model: str = "local-llm", temperature: float = 0.7, max_output_tokens: int | None = None):
        # Lazy import to avoid heavy startup and circular imports
        try:
            from core.llm.client import LLMClient
        except Exception:
            # Fall back to a tiny shim that returns echoes if the simulator is missing
            LLMClient = None  # type: ignore

        self._llm = LLMClient(model=model) if LLMClient is not None else None
        self.model = model
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens

    def complete(self, messages: list[dict[str, Any]], stream: bool = True) -> Iterable[str] | str:
        # The core LLMClient expects a list of messages with roles 'system'/'user'.
        if self._llm is None:
            text = "[LocalAGI fallback] No simulator available."
            return (c for c in text) if stream else text

        raw = self._llm.complete(messages)

        # The simulator returns JSON strings for structured modes; try to parse.
        try:
            payload = json.loads(raw) if isinstance(raw, str) else raw
        except Exception:
            # Non-JSON fallback — stream characters or return string
            if stream:

                def _char_gen():
                    yield from str(raw)

                return _char_gen()
            return str(raw)

        # If streaming, yield structured dict chunks: analysis, steps, output tokens.
        if stream:

            def _gen():
                try:
                    if isinstance(payload, dict):
                        analysis = payload.get("analysis")
                        if analysis:
                            yield {"type": "analysis", "data": analysis}

                        steps = payload.get("steps")
                        if isinstance(steps, list):
                            for s in steps:
                                # yield step objects directly so consumers can parse easily
                                yield {"type": "step", "data": s}

                        output = payload.get("output")
                        if output:
                            # Stream output by word to create coarser tokens
                            for token in str(output).split():
                                yield {"type": "output", "data": token + " "}
                            return

                    # Generic fallback: yield the payload as a single structured chunk
                    yield {"type": "payload", "data": payload}
                except Exception as exc:
                    yield {"type": "error", "data": str(exc)}

            return _gen()

        # Non-streaming: return the most relevant text field
        if isinstance(payload, dict):
            return payload.get("output") or json.dumps(payload)
        return str(payload)
