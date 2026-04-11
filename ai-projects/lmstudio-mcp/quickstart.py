#!/usr/bin/env python3
"""
Quick Start Guide for LM Studio MCP Server

This script helps you get the LM Studio MCP server up and running quickly.
"""

import os
import subprocess
import sys
from pathlib import Path


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def print_step(number, text):
    """Print a numbered step."""
    print(f"📍 Step {number}: {text}")
    print("-" * 70)


def check_python():
    """Check if Python 3 is available."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required. Found: {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor} detected")
    return True


def check_lmstudio():
    """Check if LM Studio is running."""
    try:
        import asyncio

        import httpx

        async def check():
            async with httpx.AsyncClient(timeout=5) as client:
                try:
                    response = await client.get("http://127.0.0.1:1234/v1/models")
                    return response.status_code == 200
                except Exception:
                    return False

        result = asyncio.run(check())
        if result:
            print("✅ LM Studio is running on localhost:1234")
        else:
            print("❌ LM Studio not detected on localhost:1234")
            print("   Run LM Studio and enable the local server in the UI")
        return result
    except ImportError:
        print("⚠️  Cannot check LM Studio (httpx not installed yet)")
        return None
    except Exception as e:
        print(f"⚠️  Cannot check LM Studio: {e}")
        return None


def install_dependencies():
    """Install required dependencies."""
    script_dir = Path(__file__).parent
    requirements_file = script_dir / "mcp-requirements.txt"

    if not requirements_file.exists():
        print(f"❌ {requirements_file} not found")
        return False

    print(f"Installing dependencies from {requirements_file}...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_file), "-q"]
        )
        print("✅ Dependencies installed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False


def run_tests():
    """Run the test suite."""
    script_dir = Path(__file__).parent
    test_file = script_dir / "test_lmstudio_mcp.py"

    if not test_file.exists():
        print(f"❌ {test_file} not found")
        return False

    print(f"Running tests from {test_file}...")
    try:
        subprocess.check_call([sys.executable, str(test_file)])
        return True
    except subprocess.CalledProcessError:
        print("❌ Tests failed")
        return False


def show_next_steps():
    """Show next steps for the user."""
    script_dir = Path(__file__).parent

    print_header("What's Next?")

    print("1️⃣  Run the MCP Server:")
    print(f"   cd {script_dir}")
    print("   python lmstudio_mcp_server.py")
    print()

    print("2️⃣  Or use the startup script:")
    print(f"   {script_dir}/run.sh")
    print(f"   {script_dir}/run.sh --test")
    print(f"   {script_dir}/run.sh --model mistral-7b")
    print()

    print("3️⃣  Configure environment variables:")
    print("   export LMSTUDIO_BASE_URL=http://127.0.0.1:1234/v1")
    print("   export LMSTUDIO_MODEL=mistral-7b")
    print("   python lmstudio_mcp_server.py")
    print()

    print("4️⃣  Use with MCP client (e.g., GitHub Copilot):")
    print("   Point your MCP client to the stdio channel of this process")
    print()

    print("5️⃣  Reference Documentation:")
    print(f"   • README.md - Full documentation")
    print(f"   • CONFIG_EXAMPLES.md - Configuration examples")
    print(f"   • test_lmstudio_mcp.py - Test the connection")
    print()


def main():
    """Run the quick start wizard."""
    print_header("LM Studio MCP Server - Quick Start Wizard")

    # Step 1: Check Python
    print_step(1, "Check Python Installation")
    if not check_python():
        return False
    print()

    # Step 2: Check LM Studio
    print_step(2, "Check LM Studio Connection")
    lmstudio_status = check_lmstudio()
    if lmstudio_status is False:
        print("⚠️  Process continuing, but LM Studio needs to be running")
    print()

    # Step 3: Install Dependencies
    print_step(3, "Install Dependencies")
    if not install_dependencies():
        return False
    print()

    # Step 4: Run Tests
    print_step(4, "Run Tests")
    if not run_tests():
        print("❌ Tests failed, but you can still try running the server")
    print()

    # Show next steps
    show_next_steps()

    print_header("✅ Quick Start Complete!")
    print("You're ready to use the LM Studio MCP Server!\n")

    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
