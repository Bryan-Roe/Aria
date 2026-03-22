#!/usr/bin/env python3
"""
Test the autonomous code agent with a simple dry-run.

This script verifies the agent is working correctly without modifying the repo.
"""

import sys
import subprocess
from pathlib import Path

if "pytest" in sys.modules:
    import pytest

    pytestmark = pytest.mark.skip(
        reason="script-style autonomous-agent smoke test is environment-dependent"
    )

REPO_ROOT = Path(__file__).parent.parent


def test_agent():
    """Run a simple test task."""
    print("=" * 70)
    print("AUTONOMOUS CODE AGENT - TEST RUN")
    print("=" * 70)
    print()

    print("Testing agent with dry-run (no file modifications)...")
    print()

    # Run a simple dry-run task
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "autonomous_code_agent.py"),
        "--task", "Add comprehensive docstrings to the LocalLLMClient class",
        # Use echo mode for testing (doesn't require LLM running)
        "--llm-type", "echo",
        "--dry-run",
        "--skip-tests",
    ]

    print(f"Command: {' '.join(cmd)}")
    print()

    try:
        result = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            timeout=60,
        )

        print()
        print("=" * 70)
        if result.returncode == 0:
            print("✓ Agent test PASSED")
        else:
            print("✗ Agent test FAILED")
        print("=" * 70)

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("✗ Agent test TIMEOUT (took too long)")
        return False
    except Exception as e:
        print(f"✗ Agent test ERROR: {e}")
        return False


if __name__ == "__main__":
    success = test_agent()
    sys.exit(0 if success else 1)
