#!/usr/bin/env python3
"""
LM Studio MCP Integration with Aria AI Agents

This module provides integration between the LM Studio MCP server and
Aria's multi-agent system, allowing agents to dynamically select and use
LM Studio as a provider.

Integration points:
- LM Studio agent in the agent registry
- Agent routing to LM Studio
- Chat completion through agents
- Dynamic model selection
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Generator, Iterable, List, Optional

# Add parent directory to path for imports
_parent = Path(__file__).parent.parent / "lmstudio-mcp"
if str(_parent) not in sys.path:
    sys.path.insert(0, str(_parent))

try:
    from lmstudio_mcp_server import LMStudioClient
except ImportError:
    LMStudioClient = None

_logger = logging.getLogger(__name__)

# =============================================================================
# LM Studio Agent Registry Entry
# =============================================================================

LMSTUDIO_AGENT_ENTRY: Dict[str, Any] = {
    "name": "lmstudio-local",
    "domains": ["technical", "coding", "ai", "general"],
    "intents": ["explanation", "coding", "question", "creation"],
    "provider": "lmstudio",
    "confidence_boost": 0.05,  # Low confidence — falls back to general unless explicitly selected
    "subtask_templates": [
        "Understand the request",
        "Formulate a response using local models",
        "Review for completeness and clarity",
    ],
    "description": "Local LM Studio instance — fast, private, no cloud dependencies",
    "capabilities": {
        "streaming": True,
        "temperature_control": True,
        "token_budgeting": True,
        "model_switching": True,
    },
    "models_hint": "Run 'python -m lmstudio_mcp_server' and check available models",
}

# =============================================================================
# LM Studio Client Factory
# =============================================================================


class LMStudioAgentClient:
    """Wrapper around LMStudioClient for agent integration."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:1234/v1",
        model: str = "local-model",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        """Initialize LM Studio client for agents."""
        if LMStudioClient is None:
            raise RuntimeError(
                "LMStudioClient not available. "
                "Install with: pip install -r ai-projects/lmstudio-mcp/mcp-requirements.txt"
            )

        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = LMStudioClient(
            base_url=base_url,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def complete(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Complete a message sequence and return the response.

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Override temperature, max_tokens, model

        Returns:
            str: The model's response
        """
        model = kwargs.get("model", self.model)
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)

        result = await self._client.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )

        if result.get("success"):
            return result.get("message", "")
        else:
            error = result.get("error", "Unknown error")
            raise RuntimeError(f"LM Studio error: {error}")

    async def stream(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> Generator[str, None, None]:
        """
        Stream completion tokens.

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Override temperature, max_tokens, model

        Yields:
            str: Token chunks from the model
        """
        # Note: Streaming infrastructure is in place in MCP server
        # Implementation depends on MCP client's SSE handling
        model = kwargs.get("model", self.model)
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)

        result = await self._client.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,  # For now, return full response
        )

        if result.get("success"):
            message = result.get("message", "")
            # Simulate streaming by yielding in chunks
            for chunk in message.split():
                yield chunk + " "
        else:
            error = result.get("error", "Unknown error")
            raise RuntimeError(f"LM Studio error: {error}")

    async def list_models(self) -> List[str]:
        """List available models."""
        result = await self._client.list_models()
        if result.get("success"):
            return result.get("available_models", [])
        else:
            raise RuntimeError(f"Failed to list models: {result.get('error')}")

    async def check_health(self) -> bool:
        """Check if LM Studio server is healthy."""
        return await self._client.check_connection()


# =============================================================================
# Factory Functions
# =============================================================================


def get_lmstudio_agent_client() -> LMStudioAgentClient:
    """
    Get an LM Studio client configured from environment variables.

    Returns:
        LMStudioAgentClient: Configured client ready to use

    Raises:
        RuntimeError: If LMStudioClient is not available
    """
    base_url = os.getenv("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1")
    model = os.getenv("LMSTUDIO_MODEL", "local-model")
    temperature = float(os.getenv("LMSTUDIO_TEMPERATURE", "0.7"))
    max_tokens = int(os.getenv("LMSTUDIO_MAX_TOKENS", "2048"))

    return LMStudioAgentClient(
        base_url=base_url,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def register_lmstudio_agent(agent_registry: Dict[str, Dict[str, Any]]) -> None:
    """
    Register LM Studio agent in an agent registry.

    Args:
        agent_registry: The agent registry dict to add LM Studio to

    Usage:
        from agi_provider import _AGENT_REGISTRY
        from lmstudio_agent_integration import register_lmstudio_agent

        register_lmstudio_agent(_AGENT_REGISTRY)
    """
    agent_registry["lmstudio-local"] = LMSTUDIO_AGENT_ENTRY
    _logger.info("Registered LM Studio agent in agent registry")


# =============================================================================
# Agent Selection Helpers
# =============================================================================


def should_use_lmstudio(query: str) -> bool:
    """
    Heuristic to determine if a query should use LM Studio.

    Returns True if:
    - Query explicitly mentions "local" or "lmstudio"
    - Query is about private/offline operation
    - Query is about local models or self-hosted

    Args:
        query: User query text

    Returns:
        bool: Whether to prefer LM Studio
    """
    query_lower = query.lower()

    # Explicit mentions
    if any(term in query_lower for term in ["lmstudio", "local model", "offline"]):
        return True

    # Privacy-focused queries
    if any(
        term in query_lower for term in ["private", "self-hosted", "local", "no cloud"]
    ):
        return True

    return False


def get_lmstudio_agent_info() -> Dict[str, Any]:
    """
    Get information about the LM Studio agent for help/info commands.

    Returns:
        dict: Agent metadata and capabilities
    """
    return {
        **LMSTUDIO_AGENT_ENTRY,
        "status": "available" if LMStudioClient else "unavailable",
        "setup_instructions": (
            "1. Start LM Studio (https://lmstudio.ai)\n"
            "2. Load a model (Mistral 7B recommended)\n"
            "3. Enable Local Server (default: http://127.0.0.1:1234/v1)\n"
            "4. Start MCP server: python -m ai-projects/lmstudio-mcp/lmstudio_mcp_server.py"
        ),
    }


# =============================================================================
# Integration Tests & Examples
# =============================================================================


async def example_direct_usage() -> None:
    """Example: Direct usage of LM Studio agent client."""
    print("\n=== Example 1: Direct LM Studio Usage ===\n")

    try:
        client = get_lmstudio_agent_client()

        # Check connection
        healthy = await client.check_health()
        print(f"✓ Server health: {healthy}")

        # List models
        models = await client.list_models()
        print(f"✓ Available models: {models}")

        # Send a message
        response = await client.complete(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Keep responses brief.",
                },
                {
                    "role": "user",
                    "content": "What is the capital of France?",
                },
            ],
            temperature=0.5,
        )
        print(f"✓ Response: {response}\n")

    except Exception as e:
        print(f"✗ Error: {e}\n")


async def example_agent_integration() -> None:
    """Example: Integration with agent system."""
    print("\n=== Example 2: Agent System Integration ===\n")

    # This shows how it would integrate with the AGI provider
    print("To integrate with AGI agents:")
    print("1. Import this module in agi_provider.py")
    print("2. Call register_lmstudio_agent(_AGENT_REGISTRY)")
    print("3. Agents will automatically route to LM Studio when appropriate")
    print()
    print("Agent metadata:")
    info = get_lmstudio_agent_info()
    print(
        json.dumps(
            {k: v for k, v in info.items() if k != "setup_instructions"}, indent=2
        )
    )
    print()


async def example_model_switching() -> None:
    """Example: Dynamic model switching."""
    print("\n=== Example 3: Dynamic Model Switching ===\n")

    try:
        client = get_lmstudio_agent_client()

        models = await client.list_models()
        if not models:
            print("No models available. Please load a model in LM Studio.")
            return

        print(f"Available models: {models}")

        # Use first available model
        model = models[0]
        print(f"\nUsing model: {model}")

        response = await client.complete(
            messages=[{"role": "user", "content": "Hello!"}],
            model=model,
            temperature=0.3,
        )
        print(f"Response: {response}\n")

    except Exception as e:
        print(f"Error: {e}\n")


async def main():
    """Run integration examples."""
    print("\n" + "=" * 70)
    print("LM Studio MCP Integration Examples")
    print("=" * 70)

    await example_direct_usage()
    await example_agent_integration()
    await example_model_switching()

    print("=" * 70)
    print("Integration Examples Complete")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nExamples interrupted")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
