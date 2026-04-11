#!/usr/bin/env python3
"""
Quick test script for LM Studio MCP Server

Run this to verify your LM Studio connection and test the MCP tools.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from lmstudio_mcp_server import LMStudioClient


async def main():
    """Test LM Studio MCP server."""

    # Get configuration from environment
    base_url = os.getenv("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1")
    model = os.getenv("LMSTUDIO_MODEL", "local-model")

    print("=" * 60)
    print("LM Studio MCP Server Test")
    print("=" * 60)
    print(f"\n📍 Server URL: {base_url}")
    print(f"🤖 Default Model: {model}\n")

    # Create client
    client = LMStudioClient(base_url=base_url, model=model)

    # Test 1: Check connection
    print("Test 1: Connection Check")
    print("-" * 60)
    connected = await client.check_connection()
    if connected:
        print("✅ Successfully connected to LM Studio")
    else:
        print("❌ Failed to connect to LM Studio")
        print("\nTroubleshooting:")
        print("  1. Ensure LM Studio is running")
        print("  2. Check that the local server is enabled")
        print(f"  3. Verify the URL: {base_url}")
        return

    # Test 2: List models
    print("\nTest 2: List Available Models")
    print("-" * 60)
    models_result = await client.list_models()

    if models_result["success"]:
        models = models_result["available_models"]
        print(f"✅ Found {len(models)} model(s):")
        for m in models:
            print(f"   • {m}")
    else:
        print(f"❌ Failed to list models: {models_result['error']}")
        return

    # Test 3: Simple chat completion
    print("\nTest 3: Chat Completion")
    print("-" * 60)

    test_messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant. Keep responses brief.",
        },
        {"role": "user", "content": "What is 2 + 2? Answer in one sentence."},
    ]

    print("Sending message to LM Studio...")
    print(f"Prompt: {test_messages[-1]['content']}\n")

    result = await client.chat_completion(
        messages=test_messages, temperature=0.5, max_tokens=256
    )

    if result["success"]:
        print("✅ Chat completion successful:")
        print(f"\nResponse:\n{result['message']}")
        print(f"\nStop reason: {result['stop_reason']}")
        if "usage" in result:
            usage = result["usage"]
            print(f"\nTokens used:")
            print(f"  • Prompt: {usage.get('prompt_tokens', 'N/A')}")
            print(f"  • Completion: {usage.get('completion_tokens', 'N/A')}")
            print(f"  • Total: {usage.get('total_tokens', 'N/A')}")
    else:
        print(f"❌ Chat completion failed: {result['error']}")

    # Test 4: Server status
    print("\nTest 4: Server Status")
    print("-" * 60)
    status_result = await client.get_server_status()

    if status_result["success"]:
        print("✅ Server Status:")
        print(f"  • Status: {status_result['status']}")
        print(f"  • Loaded models: {status_result['loaded_models']}")
        print(f"  • Current model: {status_result['current_model']}")
    else:
        print(f"❌ Failed to get status: {status_result['error']}")

    # Summary
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Run the MCP server: python lmstudio_mcp_server.py")
    print("  2. Configure in your MCP client")
    print("  3. Use the tools: list_models, chat_completion, server_status")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
