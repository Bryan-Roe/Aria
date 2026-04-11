#!/usr/bin/env python3
"""
Practical Examples: LM Studio + AGI Provider

Real-world examples showing how to integrate LM Studio with Aria's
AGI provider for multi-agent reasoning, task decomposition, and
chain-of-thought analysis.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add lmstudio-mcp to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from lmstudio_agi_integration import (
        AGILMStudioRouter, complete_with_lmstudio_routing,
        decompose_task_with_lmstudio, reason_with_lmstudio_chain_of_thought)
except ImportError as e:
    print(f"Error importing integration: {e}")
    sys.exit(1)


def print_section(title):
    """Print a formatted section."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


async def example_1_basic_routing():
    """
    Example 1: Basic LM Studio Routing

    Shows how the router analyzes queries and decides when to use LM Studio.
    """
    print_section("Example 1: Basic LM Studio Routing")

    router = AGILMStudioRouter()

    # Test cases
    test_cases = [
        {
            "name": "Technical Explanation",
            "query": "Explain how transformers work in NLP",
            "analysis": {
                "query": "explain how transformers work",
                "domain": "technical",
                "intent": "explanation",
            },
        },
        {
            "name": "Coding Task",
            "query": "Write a Python decorator for memoization",
            "analysis": {
                "query": "write a python decorator",
                "domain": "technical",
                "intent": "coding",
            },
        },
        {
            "name": "Explicit Local Request",
            "query": "Analyze this code locally, please",
            "analysis": {
                "query": "analyze this code locally",
                "domain": "technical",
                "intent": "explanation",
            },
        },
        {
            "name": "AI Domain",
            "query": "How does reinforcement learning work?",
            "analysis": {
                "query": "how does reinforcement learning work",
                "domain": "ai",
                "intent": "explanation",
            },
        },
    ]

    print("Routing Decision Examples:\n")

    for test in test_cases:
        use_lmstudio = router.should_use_lmstudio(test["analysis"])
        decision = "✓ Route to LM Studio" if use_lmstudio else "✗ Route to fallback"

        print(f"Query: {test['name']}")
        print(f"  Text: {test['query']}")
        print(
            f"  Domain: {test['analysis']['domain']:12} Intent: {test['analysis']['intent']}"
        )
        print(f"  Decision: {decision}\n")


async def example_2_query_analysis():
    """
    Example 2: Query Analysis & Classification

    Shows how AGI provider analyzes queries to determine domain and intent.
    """
    print_section("Example 2: Query Classification")

    # Simulated query analysis results (as AGI provider would do)
    queries = [
        "Explain backpropagation",
        "Debug this Python error",
        "Build a recommendation system",
        "What is quantum entanglement?",
        "Move left and wave",
    ]

    print("Query Classification:\n")

    # Simple domain detection (in real AGI provider, more sophisticated)
    domain_keywords = {
        "technical": ["python", "code", "debug", "error", "function"],
        "ai": ["neural", "backprop", "gradient", "machine learning", "recommendation"],
        "quantum": ["quantum", "entangle", "superposition", "qubit"],
        "aria": ["move", "wave", "dance", "say"],
    }

    for query in queries:
        query_lower = query.lower()
        domain = "general"

        for potential_domain, keywords in domain_keywords.items():
            if any(kw in query_lower for kw in keywords):
                domain = potential_domain
                break

        print(f"Query: {query}")
        print(f"  Domain: {domain}")
        print(f"  Use LM Studio: {'Yes' if domain in ['technical', 'ai'] else 'No'}\n")


async def example_3_task_decomposition():
    """
    Example 3: Task Decomposition

    Shows how complex tasks are broken into subtasks.
    """
    print_section("Example 3: Task Decomposition")

    task = "Implement a chatbot with context-aware responses"
    print(f"Complex Task: {task}\n")

    print("Decomposing with LM Studio...")
    print("(This will attempt to connect to LM Studio)\n")

    try:
        subtasks = await decompose_task_with_lmstudio(task, domain="technical")

        print("Decomposed Subtasks:\n")
        for i, subtask in enumerate(subtasks, 1):
            if isinstance(subtask, dict):
                task_text = subtask.get("task", str(subtask))
            else:
                task_text = str(subtask)

            print(f"  {i}. {task_text}")

        print()

    except Exception as e:
        print(f"Note: Could not decompose (LM Studio may not be running): {e}\n")
        print("Example output would be:")
        print("  1. Design conversation state management")
        print("  2. Implement context tracking system")
        print("  3. Build response generation pipeline")
        print("  4. Add memory/persistence layer")
        print()


async def example_4_reasoning_chain():
    """
    Example 4: Chain-of-Thought Reasoning

    Shows multi-step reasoning analysis.
    """
    print_section("Example 4: Chain-of-Thought Reasoning")

    question = "Why do neural networks have difficulty with long-term dependencies?"
    print(f"Question: {question}\n")

    print("Generating 3-step reasoning chain...")
    print("(Attempting connection to LM Studio)\n")

    try:
        reasoning = await reason_with_lmstudio_chain_of_thought(question, depth=3)

        print("Reasoning Steps:\n")

        for step in reasoning.get("reasoning_steps", []):
            step_num = step.get("number", "?")
            step_name = step.get("step", "Analysis")
            content = step.get("content", "")[:150]

            print(f"  Step {step_num} - {step_name}:")
            print(f"    {content}...")

        print(f"\n  Conclusion:")
        conclusion = reasoning.get("conclusion", "")[:200]
        print(f"    {conclusion}...\n")

    except Exception as e:
        print(
            f"Note: Could not generate reasoning (LM Studio may not be running): {e}\n"
        )
        print("Example reasoning would be:")
        print("  Step 1 - Problem: Gradients vanish as they backpropagate")
        print("  Step 2 - Why: Multiplication by small numbers causes decay")
        print("  Step 3 - Solution: Use LSTMs, residual connections, or attention\n")


async def example_5_multi_agent_workflow():
    """
    Example 5: Multi-Agent Workflow

    Shows how different agents handle different aspects of a task.
    """
    print_section("Example 5: Multi-Agent Workflow")

    workflow_steps = [
        {
            "step": 1,
            "task": "Understand the request",
            "agent": "Query Analyzer",
            "action": "Parse intent and domain",
        },
        {
            "step": 2,
            "task": "Research approach",
            "agent": "LM Studio (Technical)",
            "action": "Explain relevant concepts",
        },
        {
            "step": 3,
            "task": "Plan implementation",
            "agent": "Decomposer",
            "action": "Break into subtasks",
        },
        {
            "step": 4,
            "task": "Implement solution",
            "agent": "Code Specialist / LM Studio",
            "action": "Write code with explanations",
        },
        {
            "step": 5,
            "task": "Review & improve",
            "agent": "Reflection Engine",
            "action": "Check completeness and quality",
        },
    ]

    print("Example: Build a Login System\n")
    print("Workflow:\n")

    for step in workflow_steps:
        print(f"  Step {step['step']}: {step['task']}")
        print(f"    Agent: {step['agent']}")
        print(f"    Action: {step['action']}\n")


async def example_6_fallback_behavior():
    """
    Example 6: Fallback Behavior

    Shows what happens when LM Studio is unavailable.
    """
    print_section("Example 6: Fallback & Resilience")

    print("LM Studio Unavailability Handling:\n")

    scenarios = [
        {
            "scenario": "LM Studio offline",
            "behavior": "✓ Fall back to AGI provider",
            "result": "Request completes, possible slower",
        },
        {
            "scenario": "Network timeout",
            "behavior": "✓ Retry with exponential backoff",
            "result": "Eventually falls back to fallback provider",
        },
        {
            "scenario": "All agents busy",
            "behavior": "✓ Queue request for next available",
            "result": "Request completes when agent available",
        },
        {
            "scenario": "LM Studio re-available",
            "behavior": "✓ Automatic reconnection",
            "result": "Back to fast local inference",
        },
    ]

    for scenario in scenarios:
        print(f"Scenario: {scenario['scenario']}")
        print(f"  Behavior: {scenario['behavior']}")
        print(f"  Result: {scenario['result']}\n")


async def example_7_configuration():
    """
    Example 7: Configuration & Tuning

    Shows how to configure LM Studio + AGI integration.
    """
    print_section("Example 7: Configuration & Tuning")

    print("Configuration Options:\n")

    configs = [
        {
            "setting": "LMSTUDIO_MODEL",
            "default": "local-model",
            "example": "mistral-7b",
            "impact": "Which model to use",
        },
        {
            "setting": "LMSTUDIO_TEMPERATURE",
            "default": "0.7",
            "example": "0.3",
            "impact": "Lower = more deterministic, faster",
        },
        {
            "setting": "LMSTUDIO_MAX_TOKENS",
            "default": "2048",
            "example": "512",
            "impact": "Lower = faster, shorter responses",
        },
        {
            "setting": "AGI reasoning_depth",
            "default": "3",
            "example": "5",
            "impact": "More steps = better reasoning, slower",
        },
    ]

    for config in configs:
        print(f"Setting: {config['setting']}")
        print(f"  Default: {config['default']}")
        print(f"  Example: {config['example']}")
        print(f"  Impact: {config['impact']}\n")

    print("Quick Performance Tuning:\n")

    tuning_tips = [
        "Speed: ↓ temperature, ↓ max_tokens, ↓ reasoning_depth",
        "Quality: ↑ temperature, ↑ max_tokens, ↑ reasoning_depth",
        "Balance: defaults (0.7, 2048, 3) work well",
    ]

    for tip in tuning_tips:
        print(f"  • {tip}")

    print()


async def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("LM Studio + AGI Provider - Practical Examples")
    print("=" * 70)

    await example_1_basic_routing()
    await example_2_query_analysis()
    await example_3_task_decomposition()
    await example_4_reasoning_chain()
    await example_5_multi_agent_workflow()
    await example_6_fallback_behavior()
    await example_7_configuration()

    print("=" * 70)
    print("Examples Complete!")
    print("=" * 70)
    print("\nNext Steps:")
    print("  1. Start LM Studio (https://lmstudio.ai)")
    print("  2. Start MCP server: python lmstudio_mcp_server.py")
    print("  3. Review AGI_PROVIDER_INTEGRATION.md for detailed guide")
    print("  4. Integrate with your AGI provider instance")
    print()


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
