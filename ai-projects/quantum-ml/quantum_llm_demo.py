#!/usr/bin/env python3
"""
Quantum LLM Comprehensive Demo

Demonstrates all features of the Quantum-Powered LLM module:
- Basic generation and streaming
- Configuration management
- Backend selection
- Circuit caching
- Provider routing
- Error handling
- Observability and metrics

Usage:
    python quantum_llm_demo.py

Requirements:
    - cd /workspaces/Aria
    - pip install -e ai-projects/quantum-ml
"""

import asyncio
import json
import sys
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

import numpy as np
from ai_projects.quantum_ml.src.quantum_llm import (
    CircuitCache,
    QuantumLLMConfig,
    QuantumLLMPipeline,
    QuantumSampler,
)


async def demo_basic_generation():
    """Demo 1: Basic non-streaming generation."""
    print("\n" + "=" * 70)
    print("DEMO 1: Basic Generation")
    print("=" * 70)

    pipeline = QuantumLLMPipeline()

    prompt = "What is quantum computing?"
    print(f"\nPrompt: {prompt}")

    result = await pipeline.generate(prompt)

    print(f"\nResponse: {result['response'][:100]}...")
    print(f"Provider: {result['provider']}")
    print(f"Backend: {result['backend']}")
    print(f"Latency: {result['latency_ms']}ms")
    print(f"Quantum Augmented: {result['quantum_augmented']}")


async def demo_streaming():
    """Demo 2: SSE streaming."""
    print("\n" + "=" * 70)
    print("DEMO 2: Streaming Generation")
    print("=" * 70)

    pipeline = QuantumLLMPipeline()

    prompt = "Tell me about superposition"
    print(f"\nPrompt: {prompt}")
    print("\nStreaming response:")

    async for chunk in pipeline.stream(prompt):
        if "[DONE]" in chunk:
            break
        if "delta" in chunk:
            # Extract delta from SSE format
            try:
                data = json.loads(chunk.split("data: ")[1])
                if "delta" in data:
                    print(data["delta"], end="", flush=True)
            except (IndexError, json.JSONDecodeError):
                pass

    print("\n\n✓ Stream completed")


async def demo_configuration():
    """Demo 3: Custom configuration."""
    print("\n" + "=" * 70)
    print("DEMO 3: Configuration Management")
    print("=" * 70)

    # Create custom config
    config = QuantumLLMConfig(
        backend="classical",
        num_qubits=6,
        shots=256,
        num_layers=3,
        temperature_blend=0.5,
        cache_enabled=True,
        cache_max_size=128,
    )

    print("\nCustom Configuration:")
    print(json.dumps(config.to_dict(), indent=2))

    pipeline = QuantumLLMPipeline(config=config)
    result = await pipeline.generate("Hello!")

    print("\n✓ Generated with custom config")
    print(f"  Backend: {result['backend']}")
    print(f"  Latency: {result['latency_ms']}ms")


async def demo_caching():
    """Demo 4: Circuit caching."""
    print("\n" + "=" * 70)
    print("DEMO 4: Circuit Caching")
    print("=" * 70)

    config = QuantumLLMConfig(cache_enabled=True, cache_max_size=256)
    pipeline = QuantumLLMPipeline(config=config)

    # Generate multiple prompts to populate cache
    prompts = [
        "What is entanglement?",
        "Explain superposition",
        "What is entanglement?",  # Repeat to test cache hit
    ]

    for prompt in prompts:
        print(f"\nGenerating: {prompt[:40]}...")
        await pipeline.generate(prompt)

    # Get cache stats
    status = pipeline.status()
    cache_stats = status["cache"]["stats"]

    print("\n\nCache Statistics:")
    print(json.dumps(cache_stats, indent=2))


def demo_sampler_directly():
    """Demo 5: Using QuantumSampler directly."""
    print("\n" + "=" * 70)
    print("DEMO 5: Direct Sampler Usage")
    print("=" * 70)

    sampler = QuantumSampler(backend="classical", num_qubits=4, shots=512)

    # Sample from logits multiple times
    logits = [10.0, 2.0, 1.0, 0.5]  # Top-k logits from LLM

    print(f"\nLogits: {logits}")
    print("\nSampling 20 times with blend_factor=0.3:")

    samples = []
    for _i in range(20):
        idx = sampler.sample(logits, blend_factor=0.3, seed=None)
        samples.append(idx)

    # Count distribution
    from collections import Counter

    distribution = Counter(samples)
    print(f"Distribution: {dict(distribution)}")

    # Get cache stats
    stats = sampler.cache_stats()
    print(f"\nCache Stats: {stats}")


def demo_circuit_cache_directly():
    """Demo 6: Using CircuitCache directly."""
    print("\n" + "=" * 70)
    print("DEMO 6: Direct CircuitCache Usage")
    print("=" * 70)

    cache = CircuitCache(max_size=10, max_age_seconds=3600)

    # Store some values
    print("\nStoring 5 probability distributions...")
    for i in range(5):
        params = np.array([float(i) * 0.1, float(i) * 0.2])
        probs = np.random.dirichlet([1, 1, 1, 1])  # Random 4-element distribution
        cache.put(params, num_qubits=2, probs=probs)

    # Retrieve and access patterns
    print("Accessing 3 times each...")
    for i in range(3):
        for _j in range(3):
            params = np.array([float(i) * 0.1, float(i) * 0.2])
            cache.get(params, num_qubits=2)

    # Add two more to trigger eviction
    print("Adding 2 more entries (triggers LRU eviction)...")
    for i in range(5, 7):
        params = np.array([float(i) * 0.1, float(i) * 0.2])
        probs = np.random.dirichlet([1, 1, 1, 1])
        cache.put(params, num_qubits=2, probs=probs)

    # Stats
    stats = cache.stats()
    print("\nCache Stats:")
    print(json.dumps({k: v for k, v in stats.items() if k != "size"}, indent=2))
    print(f"Size: {stats['size']}/{stats['max_size']}")


async def demo_status_endpoint():
    """Demo 7: Health check / status endpoint."""
    print("\n" + "=" * 70)
    print("DEMO 7: Health Check / Status Endpoint")
    print("=" * 70)

    pipeline = QuantumLLMPipeline()

    # Generate a few items to populate cache
    for i in range(3):
        await pipeline.generate(f"Query {i}")

    status = pipeline.status()

    print("\nFull Status Response:")
    print(json.dumps(status, indent=2, default=str))


async def demo_error_handling():
    """Demo 8: Error handling."""
    print("\n" + "=" * 70)
    print("DEMO 8: Error Handling")
    print("=" * 70)

    config = QuantumLLMConfig(max_prompt_chars=100)
    pipeline = QuantumLLMPipeline(config=config)

    # Test 1: Oversized prompt
    print("\nTest 1: Oversized prompt")
    try:
        long_prompt = "x" * 1000
        await pipeline.generate(long_prompt)
        print("ERROR: Should have raised ValueError!")
    except ValueError as e:
        print(f"✓ Caught error: {str(e)[:60]}...")

    # Test 2: Empty prompt (should handle gracefully)
    print("\nTest 2: Empty prompt")
    try:
        result = await pipeline.generate("")
        print(f"✓ Handled empty prompt: {result['provider']}")
    except Exception as e:
        print(f"✓ Handled error: {e}")


async def demo_provider_selection():
    """Demo 9: Provider selection."""
    print("\n" + "=" * 70)
    print("DEMO 9: Provider Selection & Routing")
    print("=" * 70)

    pipeline = QuantumLLMPipeline()

    prompts = [
        "Short query",
        "Is this a question?",
        "```python\nprint('code')\n```",
    ]

    print("\nProvider routing for different prompt types:")
    for prompt in prompts:
        result = await pipeline.generate(prompt)
        print(f"  {prompt[:30]:30} → {result['provider']}")


async def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("QUANTUM LLM COMPREHENSIVE DEMO")
    print("=" * 70)

    try:
        # Synchronous demos
        demo_sampler_directly()
        demo_circuit_cache_directly()

        # Asynchronous demos
        await demo_basic_generation()
        await demo_streaming()
        await demo_configuration()
        await demo_caching()
        await demo_status_endpoint()
        await demo_error_handling()
        await demo_provider_selection()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    print("\n" + "=" * 70)
    print("✓ ALL DEMOS COMPLETED SUCCESSFULLY")
    print("=" * 70 + "\n")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
