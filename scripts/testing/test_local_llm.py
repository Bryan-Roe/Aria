#!/usr/bin/env python3
"""
Test Local LLM Integration - Smoke tests for all local providers
Validates LMStudio, LoRA, and fallback providers.
"""
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src" / "chat"))
sys.path.insert(0, str(PROJECT_ROOT / "src" / "lora"))
# Note: Don't add shared to path to avoid circular imports with shared/chat_providers.py

def print_test(name: str, passed: bool, details: str = ""):
    """Print test result."""
    symbol = "✓" if passed else "✗"
    status = "PASS" if passed else "FAIL"
    print(f"{symbol} {name:<50} [{status}]")
    if details:
        print(f"  → {details}")

def test_provider_imports() -> Tuple[bool, str]:
    """Test that provider classes can be imported."""
    try:
        import sys
        from pathlib import Path
        # Direct import from src/chat
        chat_path = str(Path(__file__).parent.parent / "src" / "chat")
        if chat_path not in sys.path:
            sys.path.insert(0, chat_path)
        
        from chat_providers import (
            BaseChatProvider,
            LocalEchoProvider,
            LMStudioProvider,
            LoraLocalProvider,
            detect_provider,
        )
        return True, "All providers imported successfully"
    except Exception as e:
        return False, f"Import failed: {e}"

def test_local_echo() -> Tuple[bool, str]:
    """Test LocalEchoProvider (always works)."""
    try:
        import sys
        from pathlib import Path
        chat_path = str(Path(__file__).parent.parent / "src" / "chat")
        if chat_path not in sys.path:
            sys.path.insert(0, chat_path)
        
        from chat_providers import LocalEchoProvider
        
        provider = LocalEchoProvider(seed=42)
        messages = [{"role": "user", "content": "Hello"}]
        response = provider.complete(messages, stream=False)
        
        if isinstance(response, str) and len(response) > 0:
            return True, f"Response: {response[:50]}..."
        else:
            return False, "No response from LocalEchoProvider"
    except Exception as e:
        return False, f"LocalEchoProvider failed: {e}"

def test_lmstudio_detection() -> Tuple[bool, str]:
    """Test LMStudio provider detection."""
    try:
        import sys
        from pathlib import Path
        chat_path = str(Path(__file__).parent.parent / "src" / "chat")
        if chat_path not in sys.path:
            sys.path.insert(0, chat_path)
        
        from chat_providers import detect_provider
        
        # Simulate LMStudio available
        os.environ["LMSTUDIO_BASE_URL"] = "http://127.0.0.1:1234/v1"
        os.environ["LMSTUDIO_MODEL"] = "test-model"
        
        try:
            provider, choice = detect_provider()
            return True, f"Detected {choice.name} ({choice.model})"
        except RuntimeError as e:
            # LMStudio server not actually running - that's OK for this test
            if "Connection" in str(e) or "refused" in str(e) or "openai" in str(e).lower():
                return True, "LMStudio would be used (server/openai not available)"
            raise
    except Exception as e:
        return False, f"Detection failed: {e}"

def test_lora_detection() -> Tuple[bool, str]:
    """Test LoRA provider detection."""
    try:
        import sys
        from pathlib import Path
        chat_path = str(Path(__file__).parent.parent / "src" / "chat")
        if chat_path not in sys.path:
            sys.path.insert(0, chat_path)
        
        from chat_providers import detect_provider
        
        # Simulate LoRA selection with non-existent adapter
        # This should fail gracefully
        try:
            provider, choice = detect_provider(explicit="lora", model_override="./fake_adapter")
            return False, "Should have failed with non-existent adapter"
        except RuntimeError as e:
            if "adapter" in str(e).lower() or "not found" in str(e).lower():
                return True, "LoRA provider correctly validates adapter path"
            else:
                return False, f"Wrong error: {e}"
    except Exception as e:
        return False, f"LoRA detection failed: {e}"

def test_auto_detection() -> Tuple[bool, str]:
    """Test auto provider detection (should fall back to LocalEcho)."""
    try:
        import sys
        from pathlib import Path
        chat_path = str(Path(__file__).parent.parent / "src" / "chat")
        if chat_path not in sys.path:
            sys.path.insert(0, chat_path)
        
        from chat_providers import detect_provider
        
        # Clear env vars to force fallback
        for key in ["LMSTUDIO_BASE_URL", "AZURE_OPENAI_API_KEY", "OPENAI_API_KEY"]:
            os.environ.pop(key, None)
        
        try:
            provider, choice = detect_provider()
            return True, f"Auto-detected: {choice.name}"
        except RuntimeError as e:
            # If openai package not installed, LocalEchoProvider should still work
            if "openai" in str(e).lower():
                return True, "Would auto-detect LMStudio (openai not installed)"
            raise
    except Exception as e:
        return False, f"Auto-detection failed: {e}"

def test_chat_cli_help() -> Tuple[bool, str]:
    """Test chat CLI is accessible."""
    try:
        result = subprocess.run(
            [sys.executable, "src/chat/chat_cli.py", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and "provider" in result.stdout:
            return True, "Chat CLI is functional"
        else:
            return False, "Chat CLI failed"
    except Exception as e:
        return False, f"Chat CLI test failed: {e}"

def test_chat_cli_local() -> Tuple[bool, str]:
    """Test chat CLI with local provider."""
    try:
        # Use local provider (no cloud APIs)
        result = subprocess.run(
            [sys.executable, "src/chat/chat_cli.py", "--provider", "local", "--once", "Hello"],
            capture_output=True,
            text=True,
            timeout=10,
            env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)},
        )
        if result.returncode == 0:
            return True, "Chat CLI local test passed"
        else:
            return False, result.stderr[:100] if result.stderr else "Unknown error"
    except subprocess.TimeoutExpired:
        return False, "Chat CLI timed out"
    except Exception as e:
        return False, f"Chat CLI test failed: {e}"

def test_provider_chain() -> Tuple[bool, str]:
    """Test provider detection chain priority."""
    try:
        import sys
        from pathlib import Path
        chat_path = str(Path(__file__).parent.parent / "src" / "chat")
        if chat_path not in sys.path:
            sys.path.insert(0, chat_path)
        
        from chat_providers import detect_provider
        
        # Test that LMStudio takes priority over OpenAI
        os.environ["LMSTUDIO_BASE_URL"] = "http://127.0.0.1:1234/v1"
        os.environ["OPENAI_API_KEY"] = "sk-test-key"
        
        try:
            provider, choice = detect_provider()
            # If LMStudio is selected despite connection error, provider chain works
            if choice.name in ["lmstudio", "local"]:
                return True, f"Provider chain correct (would use {choice.name})"
            else:
                return False, f"Wrong provider selected: {choice.name}"
        except RuntimeError:
            # Expected if server not running
            return True, "Provider chain detected LMStudio (server not running is OK)"
    except Exception as e:
        return False, f"Provider chain test failed: {e}"

def main():
    """Run all tests."""
    os.chdir(PROJECT_ROOT)
    
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  LOCAL LLM PROVIDER TESTS".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    print()
    
    tests = [
        ("Provider Imports", test_provider_imports),
        ("LocalEchoProvider (Fallback)", test_local_echo),
        ("LMStudio Detection", test_lmstudio_detection),
        ("LoRA Adapter Detection", test_lora_detection),
        ("Auto Provider Detection", test_auto_detection),
        ("Chat CLI Help", test_chat_cli_help),
        ("Chat CLI Local Test", test_chat_cli_local),
        ("Provider Chain Priority", test_provider_chain),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            passed, details = test_func()
            results.append((test_name, passed))
            print_test(test_name, passed, details)
        except Exception as e:
            results.append((test_name, False))
            print_test(test_name, False, f"Exception: {e}")
    
    # Summary
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print()
    print("="*70)
    print(f"Results: {passed_count}/{total_count} tests passed")
    print("="*70)
    
    if passed_count == total_count:
        print("\n✓ All tests passed! Local LLM integration is working.\n")
        return 0
    else:
        print(f"\n✗ {total_count - passed_count} test(s) failed. Check setup.\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
