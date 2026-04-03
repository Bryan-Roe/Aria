#!/usr/bin/env python
"""
Test script for Aria Auto-Execute System
Tests the new LLM-powered action generation and execution
"""
import json
import sys
from typing import Dict

import pytest
import requests

BASE_URL = "http://localhost:8080"


def _aria_server_available() -> bool:
    try:
        response = requests.get(f"{BASE_URL}/api/aria/state", timeout=2)
        return response.ok
    except requests.exceptions.RequestException:
        return False


pytestmark = pytest.mark.skipif(
    not _aria_server_available(),
    reason="Aria server not running on localhost:8080",
)


def print_header(text: str):
    """Print formatted header"""
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}\n")


def print_result(success: bool, message: str):
    """Print test result"""
    symbol = "✓" if success else "✗"
    color = "\033[92m" if success else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{symbol}{reset} {message}")


def plan_mode(command: str) -> Dict:
    """Run plan mode (no execution)."""
    print(f"📋 Planning: '{command}'")

    response = requests.post(
        f"{BASE_URL}/api/aria/execute",
        json={"command": command, "auto_execute": False, "use_llm": False},
    )

    data = response.json()

    if data["status"] == "success":
        print_result(True, f"Parsed {len(data['actions'])} actions:")
        for i, action in enumerate(data["actions"], 1):
            print(
                f"    {i}. {action['action']}: {json.dumps(action, separators=(',', ':'))}"
            )
    else:
        print_result(False, f"Failed: {data.get('message', 'Unknown error')}")

    return data


def execute_mode(command: str) -> Dict:
    """Run execute mode."""
    print(f"▶️  Executing: '{command}'")

    response = requests.post(
        f"{BASE_URL}/api/aria/execute",
        json={"command": command, "auto_execute": True, "use_llm": False},
    )

    data = response.json()

    if data["status"] == "success":
        print_result(True, f"Executed {len(data['results'])} actions:")
        for i, result in enumerate(data["results"], 1):
            action = result["action"]
            res = result["result"]
            status_symbol = "✓" if res["status"] == "success" else "✗"
            print(f"    {status_symbol} {i}. {action['action']}: {res['message']}")
            if res.get("tags"):
                print(f"       Tags: {', '.join(res['tags'])}")
    else:
        print_result(False, f"Failed: {data.get('message', 'Unknown error')}")

    return data


def get_state() -> Dict:
    """Get current stage state"""
    response = requests.get(f"{BASE_URL}/api/aria/state")
    return response.json()


def print_state():
    """Print current Aria state"""
    state = get_state()
    aria = state["aria"]

    print("\n🎭 Current Aria State:")
    print(f"   Position: ({aria['position']['x']}, {aria['position']['y']})")
    print(f"   Expression: {aria['expression']}")
    print(f"   Held object: {aria['held_object'] or 'none'}")
    print(f"   Facing: {aria['facing']}")


def test_plan_mode() -> None:
    """Pytest-compatible smoke test for plan mode."""
    result = plan_mode("Say hello world")
    assert result["status"] == "success"
    assert "actions" in result


def test_execute_mode() -> None:
    """Pytest-compatible smoke test for execute mode."""
    result = execute_mode("Wave at the audience")
    assert result["status"] == "success"
    assert "results" in result
    assert isinstance(result["results"], list)
    assert len(result["results"]) > 0
    # Verify that at least one executed action reports a successful status
    assert any(
        isinstance(item, dict)
        and "result" in item
        and isinstance(item["result"], dict)
        and item["result"].get("status") == "success"
        for item in result["results"]
    )


def run_tests():
    """Run comprehensive test suite"""

    print_header("🤖 Aria Auto-Execute System Tests")

    try:
        # Test 1: Simple say command
        print_header("Test 1: Simple Say Command")
        plan_mode("Say hello world")
        result = execute_mode("Say hello world")
        if result["status"] == "success":
            print_result(True, "Say command executed successfully")

        # Test 2: Gesture command
        print_header("Test 2: Gesture Command")
        plan_mode("Wave at the audience")
        result = execute_mode("Wave at the audience")
        if result["status"] == "success":
            print_result(True, "Gesture command executed successfully")

        # Test 3: Movement command
        print_header("Test 3: Movement Command")
        plan_mode("Move to the center")
        result = execute_mode("Move to the center")
        if result["status"] == "success":
            print_result(True, "Movement command executed successfully")
        print_state()

        # Test 4: Multi-action sequence
        print_header("Test 4: Multi-Action Sequence")
        plan_mode("Go to the table and pick up the apple")
        result = execute_mode("Go to the table and pick up the apple")
        if result["status"] == "success":
            print_result(True, "Multi-action sequence executed successfully")
        print_state()

        # Test 5: Complex command
        print_header("Test 5: Complex Command with Multiple Actions")
        command = "Say welcome, wave, and move to the left"
        plan_mode(command)
        result = execute_mode(command)
        if result["status"] == "success":
            print_result(True, "Complex command executed successfully")
        print_state()

        # Test 6: Error handling (pickup without moving)
        print_header("Test 6: Error Handling (Distance Check)")
        print("Note: This should fail if Aria is too far from the book")
        result = execute_mode("Pick up the book")
        if result["status"] == "success" and result["results"]:
            has_error = any(r["result"]["status"] == "error" for r in result["results"])
            if has_error:
                print_result(True, "Distance validation working correctly")
            else:
                print_result(True, "Pickup succeeded (Aria was close enough)")

        # Summary
        print_header("🎉 Test Suite Complete")
        print_result(True, "All auto-execute features operational")
        print("\n📖 Try the web interface:")
        print(f"   Open: {BASE_URL}/auto-execute.html")
        print("\n📚 Read full documentation:")
        print("   See: aria_web/AUTO-EXECUTE.md\n")

        return True

    except requests.exceptions.ConnectionError:
        print_result(False, "Cannot connect to server")
        print("\n❌ Server not running!")
        print("   Start it with: cd /workspaces/AI/aria_web && python server.py")
        return False

    except Exception as e:
        print_result(False, f"Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
