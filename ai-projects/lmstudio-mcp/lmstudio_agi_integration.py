#!/usr/bin/env python3
"""
LM Studio Integration with AGI Provider

This module shows how to integrate LM Studio with Aria's AGI (Artificial General
Intelligence) provider, enabling:

1. LM Studio as a specialized agent in the multi-agent routing system
2. Dynamic task decomposition using LM Studio
3. Chain-of-thought reasoning with local models
4. Seamless fallback to/from other providers

The AGI provider analyzes queries, decomposes complex tasks, and routes them to
the most appropriate agent. LM Studio can handle technical, coding, and AI domains.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from lmstudio_agent_integration import (LMStudioAgentClient,
                                        get_lmstudio_agent_client,
                                        get_lmstudio_agent_info)

_logger = logging.getLogger(__name__)

# =============================================================================
# AGI Provider Enhancements
# =============================================================================


def get_lmstudio_agent_registry_entry() -> Dict[str, Any]:
    """
    Get the LM Studio agent entry for the AGI provider's agent registry.

    This can be added to _AGENT_REGISTRY in agi_provider.py like:

    Example:
        from lmstudio_agi_integration import get_lmstudio_agent_registry_entry

        registry = _AGENT_REGISTRY.copy()
        registry["lmstudio-local"] = get_lmstudio_agent_registry_entry()

    Returns:
        dict: Agent registry entry with LM Studio metadata
    """
    return {
        "domains": ["technical", "coding", "ai", "general"],
        "intents": ["explanation", "coding", "question", "creation"],
        "provider": "lmstudio",
        "confidence_boost": 0.05,  # Low default; explicit when needed
        "subtask_templates": [
            "Break down the problem into clear steps",
            "Formulate a solution using local models",
            "Review for correctness and completeness",
            "Optimize for clarity and performance",
        ],
        "description": "Local LM Studio instance — fast, private, no cloud dependencies",
    }


class AGILMStudioRouter:
    """
    Routes AGI provider queries to LM Studio when appropriate.

    Uses query analysis results to determine if LM Studio should handle the task,
    and manages fallback to other providers if LM Studio is unavailable.
    """

    def __init__(self, fallback_provider: Optional[str] = "agi"):
        """
        Initialize the router.

        Args:
            fallback_provider: Provider to use if LM Studio fails (default: "agi")
        """
        self.fallback_provider = fallback_provider
        self.lmstudio_client = None
        self._health_checked = False
        self._healthy = False

    async def ensure_healthy(self) -> bool:
        """
        Check LM Studio health and cache the result.

        Returns:
            bool: True if LM Studio is healthy and available
        """
        if self._health_checked:
            return self._healthy

        try:
            self.lmstudio_client = get_lmstudio_agent_client()
            self._healthy = await self.lmstudio_client.check_health()
            self._health_checked = True
            if self._healthy:
                _logger.info("✓ LM Studio is healthy and available")
            else:
                _logger.warning("✗ LM Studio health check failed")
        except Exception as e:
            _logger.warning(f"LM Studio unavailable: {e}")
            self._healthy = False
            self._health_checked = True

        return self._healthy

    def should_use_lmstudio(self, query_analysis: Dict[str, Any]) -> bool:
        """
        Determine if LM Studio should handle this query based on analysis.

        LM Studio is preferred for:
        - Technical/coding domains
        - Explicit "local" or "offline" requests
        - Privacy-focused queries

        Args:
            query_analysis: Output from AGI provider's _analyze_query()

        Returns:
            bool: True if LM Studio should handle this query
        """
        domain = query_analysis.get("domain", "").lower()
        intent = query_analysis.get("intent", "").lower()
        query = query_analysis.get("query", "").lower()

        # Explicit requests for local/offline
        if any(term in query for term in ["local", "offline", "lmstudio", "private"]):
            return True

        # Technical domains are good matches
        if domain in ["technical", "coding", "ai"]:
            return True

        # Coding and creation intents work well
        if intent in ["coding", "creation"]:
            return True

        return False

    async def route_query(
        self,
        query: str,
        messages: List[Dict[str, str]],
        query_analysis: Dict[str, Any],
    ) -> Optional[str]:
        """
        Route a query to LM Studio if appropriate.

        Args:
            query: The user's query text
            messages: Conversation history
            query_analysis: Query analysis from AGI provider

        Returns:
            str: Response from LM Studio, or None if should use fallback
        """
        # Check if LM Studio is healthy
        is_healthy = await self.ensure_healthy()
        if not is_healthy:
            return None

        # Check if query is suitable for LM Studio
        if not self.should_use_lmstudio(query_analysis):
            return None

        try:
            _logger.info(
                f"Routing to LM Studio: domain={query_analysis.get('domain')}, "
                f"intent={query_analysis.get('intent')}"
            )

            # Use the LM Studio client
            if self.lmstudio_client is None:
                raise RuntimeError("LM Studio client is not initialized")
            response = await self.lmstudio_client.complete(
                messages=messages,
                temperature=0.7,
                max_tokens=2048,
            )
            return response

        except Exception as e:
            _logger.error(f"LM Studio response failed: {e}")
            return None


# =============================================================================
# AGI Provider Enhancement Functions
# =============================================================================


async def complete_with_lmstudio_routing(
    agi_provider: Any,
    messages: List[Dict[str, str]],
    stream: bool = True,
    prefer_lmstudio: bool = False,
) -> str:
    """
    Complete a query using AGI provider with LM Studio routing.

    This function wraps AGI provider completion and routes to LM Studio when
    appropriate, providing a fallback mechanism.

    Args:
        agi_provider: An AGIProvider instance
        messages: Message history
        stream: Whether to stream the response
        prefer_lmstudio: Force LM Studio if available

    Returns:
        str: The response from LM Studio or fallback provider

    Example:
        from agi_provider import AGIProvider
        from lmstudio_agi_integration import complete_with_lmstudio_routing

        agi = AGIProvider()
        response = await complete_with_lmstudio_routing(
            agi,
            messages=[{"role": "user", "content": "Explain Python generators"}],
            prefer_lmstudio=True
        )
        print(response)
    """
    # Create router
    router = AGILMStudioRouter()

    # Get the last user message for analysis
    user_message = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_message = msg.get("content", "")
            break

    if not user_message:
        return "No query provided"

    # Analyze the query
    query_analysis = agi_provider._analyze_query(user_message)

    # Try LM Studio if preferred or recommended
    if prefer_lmstudio or router.should_use_lmstudio(query_analysis):
        result = await router.route_query(user_message, messages, query_analysis)
        if result is not None:
            return result

    # Fallback to AGI provider
    _logger.info("Falling back to AGI provider")
    response = agi_provider.complete(messages, stream=stream)
    if isinstance(response, str):
        return response
    else:
        # Handle streaming response
        return "".join(response)


async def decompose_task_with_lmstudio(
    task: str,
    domain: str = "technical",
) -> List[Dict[str, str]]:
    """
    Decompose a complex task into subtasks, using LM Studio if available.

    This demonstrates multi-agent task decomposition where LM Studio
    participates in breaking down complex requests.

    Args:
        task: The complex task to decompose
        domain: The task domain (technical, coding, ai, etc.)

    Returns:
        list: Subtasks with reasoning

    Example:
        subtasks = await decompose_task_with_lmstudio(
            "Build a neural network for image classification",
            domain="ai"
        )
        for subtask in subtasks:
            print(f"- {subtask['task']}")
    """
    try:
        client = get_lmstudio_agent_client()

        # Decomposition prompt
        decompose_prompt = f"""Decompose this task into clear, sequential subtasks:

Domain: {domain}
Task: {task}

Provide 3-5 subtasks as a JSON array with:
- "task": subtask description
- "dependencies": list of subtask names it depends on
- "complexity": "low", "medium", or "high"

Return only valid JSON."""

        messages = [
            {
                "role": "system",
                "content": "You are a task decomposition expert. Break complex tasks into actionable subtasks.",
            },
            {"role": "user", "content": decompose_prompt},
        ]

        response = await client.complete(messages, max_tokens=1024)

        # Parse JSON response
        try:
            # Extract JSON from response
            import re

            json_match = re.search(r"\[.*\]", response, re.DOTALL)
            if json_match:
                subtasks = json.loads(json_match.group())
                return subtasks
        except (json.JSONDecodeError, AttributeError):
            pass

        # Fallback to simple splitting
        return [
            {"task": line.strip(), "dependencies": [], "complexity": "medium"}
            for line in response.split("\n")
            if line.strip() and line.strip()[0].isdigit()
        ]

    except Exception as e:
        _logger.error(f"Task decomposition failed: {e}")
        return [{"task": task, "dependencies": [], "complexity": "high"}]


async def reason_with_lmstudio_chain_of_thought(
    query: str,
    depth: int = 3,
) -> Dict[str, Any]:
    """
    Generate a chain-of-thought reasoning using LM Studio.

    Demonstrates how LM Studio can participate in multi-step reasoning
    similar to the AGI provider's reasoning chains.

    Args:
        query: The query to reason about
        depth: Number of reasoning steps (1-5)

    Returns:
        dict: Reasoning chain with steps and conclusion

    Example:
        reasoning = await reason_with_lmstudio_chain_of_thought(
            "Why is deep learning effective for NLP?",
            depth=3
        )
        for step in reasoning['reasoning_steps']:
            print(f"Step {step['number']}: {step['content']}")
    """
    try:
        client = get_lmstudio_agent_client()
        depth = max(1, min(depth, 5))  # Clamp to 1-5

        reasoning_prompt = f"""Reason through this question step-by-step with {depth} reasoning steps:

Query: {query}

Format your response as JSON with:
{{
    "reasoning_steps": [
        {{"number": 1, "step": "...", "content": "..."}},
        {{"number": 2, "step": "...", "content": "..."}},
        ...
    ],
    "conclusion": "Final answer"
}}

Be concise but thorough. Return only valid JSON."""

        messages = [
            {
                "role": "system",
                "content": "You are a reasoning expert. Provide clear step-by-step reasoning.",
            },
            {"role": "user", "content": reasoning_prompt},
        ]

        response = await client.complete(messages, temperature=0.3, max_tokens=2048)

        # Parse reasoning
        try:
            import re

            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except (json.JSONDecodeError, AttributeError):
            pass

        # Fallback structure
        return {
            "reasoning_steps": [
                {
                    "number": 1,
                    "step": "Analysis",
                    "content": response[:500],
                }
            ],
            "conclusion": response[-200:] if len(response) > 200 else response,
        }

    except Exception as e:
        _logger.error(f"Reasoning failed: {e}")
        return {
            "reasoning_steps": [],
            "conclusion": f"Unable to reason: {e}",
        }


# =============================================================================
# Integration Examples
# =============================================================================


async def example_basic_routing() -> None:
    """Example: Basic LM Studio routing with AGI provider."""
    print("\n" + "=" * 70)
    print("Example 1: LM Studio Routing with AGI Provider")
    print("=" * 70 + "\n")

    try:
        # This would normally be imported from agi_provider
        # from agi_provider import AGIProvider
        # For demo, we'll just show the interface

        print("Simulated flow:")
        print("  1. Query analyzed: domain=technical, complexity=medium")
        print("  2. LM Studio available: routing to local model")
        print("  3. Response: [from LM Studio]")
        print("  4. Result cached for learning")

    except Exception as e:
        print(f"Error: {e}")


async def example_task_decomposition() -> None:
    """Example: Task decomposition with LM Studio."""
    print("\n" + "=" * 70)
    print("Example 2: Task Decomposition")
    print("=" * 70 + "\n")

    try:
        task = "Implement a transformer attention mechanism from scratch"
        print(f"Complex task: {task}\n")

        print("Decomposing with LM Studio...")
        subtasks = await decompose_task_with_lmstudio(task, domain="ai")

        print("\nSubtasks:")
        for i, subtask in enumerate(subtasks, 1):
            task_desc = subtask.get("task", "Unknown")
            print(f"  {i}. {task_desc}")

    except Exception as e:
        print(f"Error: {e}")


async def example_chain_of_thought() -> None:
    """Example: Chain-of-thought reasoning with LM Studio."""
    print("\n" + "=" * 70)
    print("Example 3: Chain-of-Thought Reasoning")
    print("=" * 70 + "\n")

    try:
        query = "Why does overfitting occur in machine learning?"
        print(f"Query: {query}\n")

        print("Generating reasoning chain...")
        reasoning = await reason_with_lmstudio_chain_of_thought(query, depth=3)

        print("\nReasoning steps:")
        for step in reasoning.get("reasoning_steps", []):
            num = step.get("number", "?")
            step_name = step.get("step", "")
            content = step.get("content", "")[:100]
            print(f"  Step {num} ({step_name}): {content}...")

        print(f"\nConclusion: {reasoning.get('conclusion', 'N/A')[:200]}...")

    except Exception as e:
        print(f"Error: {e}")


async def example_router_decision_logic() -> None:
    """Example: Router decision logic and fallback."""
    print("\n" + "=" * 70)
    print("Example 4: Router Decision Logic")
    print("=" * 70 + "\n")

    router = AGILMStudioRouter()

    # Test different query analyses
    test_cases = [
        {
            "query": "Explain Python generators",
            "analysis": {
                "domain": "technical",
                "intent": "explanation",
                "query": "explain python generators locally",
            },
            "name": "Technical explanation (local mention)",
        },
        {
            "query": "What is quantum computing?",
            "analysis": {
                "domain": "quantum",
                "intent": "explanation",
                "query": "what is quantum computing",
            },
            "name": "Quantum domain (no local mention)",
        },
        {
            "query": "Write me a Python function",
            "analysis": {
                "domain": "technical",
                "intent": "coding",
                "query": "write me a python function",
            },
            "name": "Coding task (good for LM Studio)",
        },
    ]

    print("Router Decision Logic:\n")
    for test in test_cases:
        should_use = router.should_use_lmstudio(test["analysis"])
        decision = "✓ Use LM Studio" if should_use else "✗ Use fallback"
        print(f"  {test['name']}")
        print(
            f"    Domain: {test['analysis']['domain']}, Intent: {test['analysis']['intent']}"
        )
        print(f"    Decision: {decision}\n")


async def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("LM Studio + AGI Provider Integration Examples")
    print("=" * 70)

    await example_basic_routing()
    await example_router_decision_logic()
    await example_task_decomposition()
    await example_chain_of_thought()

    print("\n" + "=" * 70)
    print("Examples Complete")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nExamples interrupted")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
