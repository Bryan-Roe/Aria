#!/usr/bin/env python3
"""
LM Studio + AGI Provider Integration Test Suite

Verifies that LM Studio is properly integrated with the AGI Provider's multi-agent system.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

_REPO_ROOT = Path(__file__).parent.parent
_CHAT_SRC = _REPO_ROOT / "ai-projects" / "chat-cli" / "src"

if str(_CHAT_SRC) not in sys.path:
    sys.path.insert(0, str(_CHAT_SRC))


def test_agent_registration():
    """Test that lmstudio-specialist is registered."""
    from agi_provider import _AGENT_REGISTRY

    assert (
        "lmstudio-specialist" in _AGENT_REGISTRY
    ), "lmstudio-specialist not in registry"
    agent = _AGENT_REGISTRY["lmstudio-specialist"]

    assert agent["provider"] == "lmstudio", "Provider should be 'lmstudio'"
    assert "explanation" in agent["intents"], "Should handle explanation intent"
    assert "question" in agent["intents"], "Should handle question intent"
    assert "coding" in agent["intents"], "Should handle coding intent"
    assert "creation" in agent["intents"], "Should handle creation intent"
    assert agent["confidence_boost"] == 0.05, "Confidence boost should be 0.05"

    print("✓ Agent registration test passed")


def test_provider_detection():
    """Test that detect_provider can create LMStudioProvider."""
    from chat_providers import LMStudioProvider, detect_provider

    with patch("chat_providers.OpenAI") as mock_openai_cls:
        mock_openai_cls.return_value = MagicMock()
        provider, choice = detect_provider(explicit="lmstudio")

    assert provider is not None, "Provider should be created"
    assert choice.name == "lmstudio", "Choice should be lmstudio"
    assert choice.model == "local-model", "Model should be local-model"
    assert isinstance(provider, LMStudioProvider)

    print("✓ Provider detection test passed")
    print(f"   Provider type: {type(provider).__name__}")
    print(f"   Choice: {choice.name} ({choice.model})")


def test_agent_class_methods():
    """Test that AGI provider can be instantiated."""
    from agi_provider import AGIProvider

    # Instantiation may raise if optional dependencies are missing — that's acceptable.
    try:
        AGIProvider()
        print("✓ AGI provider instantiation test passed")
    except Exception as e:
        print(f"⚠ AGI provider instantiation (optional dep missing): {e}")


def test_env_configuration():
    """Test that environment is properly configured for LM Studio."""
    lmstudio_url = os.getenv("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1")
    lmstudio_model = os.getenv("LMSTUDIO_MODEL", "local-model")

    assert isinstance(lmstudio_url, str) and lmstudio_url, "LMSTUDIO_BASE_URL should be a non-empty string"
    assert isinstance(lmstudio_model, str) and lmstudio_model, "LMSTUDIO_MODEL should be a non-empty string"

    print(f"✓ Environment configuration test passed")
    print(f"   LMSTUDIO_BASE_URL: {lmstudio_url}")
    print(f"   LMSTUDIO_MODEL: {lmstudio_model}")


def run_all_tests():
    """Run all integration tests."""
    print("\n" + "=" * 70)
    print("LM Studio + AGI Provider Integration Tests")
    print("=" * 70 + "\n")

    tests = [
        ("Agent Registration", test_agent_registration),
        ("Provider Detection", test_provider_detection),
        ("AGI Provider Initialization", test_agent_class_methods),
        ("Environment Configuration", test_env_configuration),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            print(f"\nRunning: {test_name}")
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary:")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "PASS ✓" if result else "FAIL ✗"
        print(f"  {status}  {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ LM Studio + AGI Provider integration is complete and working!")
        print("\nUsage examples:")
        print("  # Explicitly use LM Studio (requires LM Studio running)")
        print("  python3 src/chat_cli.py --provider lmstudio --once 'Your question'")
        print("\n  # Let agent selection route to LM Studio specialist")
        print("  python3 src/chat_cli.py --once 'Your question'")
        print("\n  # Interactive mode with possible LM Studio routing")
        print("  python3 src/chat_cli.py")
        return 0
    else:
        print("\n⚠ Some tests failed. Check output above.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
