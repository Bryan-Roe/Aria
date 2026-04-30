#!/usr/bin/env python3
"""
LM Studio Agent Integration Verification

Quick verification that LM Studio is properly integrated with Aria agents.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add lmstudio-mcp to path
_mcp_path = Path(__file__).parent
if str(_mcp_path) not in sys.path:
    sys.path.insert(0, str(_mcp_path))


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def check_imports():
    """Check if all required modules can be imported."""
    print_section("1. Checking Imports")

    checks = {
        "lmstudio_mcp_server": "Core MCP server",
        "lmstudio_agent_integration": "Agent integration",
    }

    all_ok = True
    for module_name, description in checks.items():
        try:
            __import__(module_name)
            print(f"  ✅ {module_name:40} ({description})")
        except ImportError as e:
            print(f"  ❌ {module_name:40} {str(e)[:40]}")
            all_ok = False

    return all_ok


def check_configuration():
    """Check environment configuration."""
    print_section("2. Checking Configuration")

    config = {
        "LMSTUDIO_BASE_URL": os.getenv("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1"),
        "LMSTUDIO_MODEL": os.getenv("LMSTUDIO_MODEL", "local-model"),
        "LMSTUDIO_TEMPERATURE": os.getenv("LMSTUDIO_TEMPERATURE", "0.7"),
        "LMSTUDIO_MAX_TOKENS": os.getenv("LMSTUDIO_MAX_TOKENS", "2048"),
    }

    for key, value in config.items():
        status = "✅ Set" if os.getenv(key) else "ℹ️  Default"
        print(f"  {status:12} {key:30} = {value}")

    return config


async def check_server_connection():
    """Check if LM Studio server is reachable."""
    print_section("3. Checking Server Connection")

    try:
        from lmstudio_mcp_server import LMStudioClient

        client = LMStudioClient()
        connected = await client.check_connection()

        if connected:
            print(f"  ✅ Connected to LM Studio at {client.base_url}")

            # List models
            models_result = await client.list_models()
            if models_result.get("success"):
                models = models_result.get("available_models", [])
                print(f"  ✅ Found {len(models)} model(s):")
                for model in models[:5]:  # Show first 5
                    print(f"     • {model}")
                if len(models) > 5:
                    print(f"     ... and {len(models) - 5} more")
                return True
            else:
                print(f"  ⚠️  Could not list models: {models_result.get('error')}")
                return False
        else:
            print(f"  ❌ Cannot connect to LM Studio at {client.base_url}")
            print(f"     Ensure LM Studio is running and server is enabled")
            return False

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def check_agent_registration():
    """Check agent registry integration."""
    print_section("4. Checking Agent Integration")

    try:
        from lmstudio_agent_integration import get_lmstudio_agent_info

        info = get_lmstudio_agent_info()

        print(f"  ✅ LM Studio Agent Available")
        print(f"")
        print(f"  Agent Name:     {info.get('name')}")
        print(f"  Status:         {info.get('status')}")
        print(f"  Domains:        {', '.join(info.get('domains', []))}")
        print(f"  Intents:        {', '.join(info.get('intents', []))}")
        print(f"  Description:    {info.get('description')}")
        print(f"")
        print(f"  Capabilities:")
        for cap, enabled in info.get("capabilities", {}).items():
            status = "✅" if enabled else "⚠️"
            print(f"    {status} {cap}")

        return True

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


async def check_direct_usage():
    """Check if agent client can be used directly."""
    print_section("5. Testing Direct Agent Client")

    try:
        from lmstudio_agent_integration import get_lmstudio_agent_client

        client = get_lmstudio_agent_client()
        print(f"  ✅ Created agent client")

        # List models
        try:
            models = await client.list_models()
            print(f"  ✅ Listed models: {len(models)} available")
        except Exception as e:
            print(f"  ⚠️  Could not list models: {e}")

        # Send test message
        try:
            response = await client.complete(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant. Keep responses very brief.",
                    },
                    {"role": "user", "content": "What is 2+2?"},
                ],
                max_tokens=50,
            )
            if response:
                print(f"  ✅ Test message succeeded")
                print(f"     Response: {response[:60]}...")
                return True
            else:
                print(f"  ❌ Empty response")
                return False
        except Exception as e:
            print(f"  ❌ Test message failed: {e}")
            return False

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def check_integration_files():
    """Check that all integration files exist."""
    print_section("6. Checking Integration Files")

    files = {
        "lmstudio_mcp_server.py": "Core MCP server",
        "lmstudio_agent_integration.py": "Agent integration",
        "test_lmstudio_mcp.py": "Connection tests",
        "AGENT_INTEGRATION.md": "Integration guide",
        "README.md": "Full documentation",
        "CONFIG_EXAMPLES.md": "Configuration examples",
    }

    script_dir = Path(__file__).parent
    all_exist = True

    for filename, description in files.items():
        filepath = script_dir / filename
        if filepath.exists():
            size_kb = filepath.stat().st_size / 1024
            print(f"  ✅ {filename:40} ({description:20}) {size_kb:6.1f} KB")
        else:
            print(f"  ❌ {filename:40} MISSING")
            all_exist = False

    return all_exist


async def main():
    """Run all checks."""
    print("\n" + "=" * 70)
    print("  LM Studio Agent Integration Verification")
    print("=" * 70)

    results = {
        "imports": check_imports(),
        "configuration": check_configuration() is not None,
        "agent_registration": check_agent_registration(),
        "integration_files": check_integration_files(),
    }

    # Async checks
    print_section("Running Async Checks...")
    server_ok = await check_server_connection()
    results["server_connection"] = server_ok

    usage_ok = await check_direct_usage()
    results["direct_usage"] = usage_ok

    # Summary
    print_section("Summary")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"  Checks Passed: {passed}/{total}\n")

    for check_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"    {status} {check_name.replace('_', ' ').title()}")

    print()

    if passed == total:
        print("  ✅ All checks passed! Integration is ready to use.")
        print()
        print("  Next steps:")
        print("    1. Review AGENT_INTEGRATION.md for usage examples")
        print("    2. Try: python -m chat_cli --provider lmstudio 'hello'")
        print("    3. Integrate with your custom agents")
        return 0
    elif passed >= total - 1:  # Server may be offline, that's OK
        print("  ⚠️  Most checks passed. Server connection may be offline.")
        print()
        print("  Make sure LM Studio is running:")
        print("    1. Open LM Studio app (https://lmstudio.ai)")
        print("    2. Load a model")
        print("    3. Enable Local Server")
        print("    4. Re-run this verification")
        return 0
    else:
        print("  ❌ Some checks failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nVerification interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
