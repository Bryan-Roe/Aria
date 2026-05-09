"""
Quick Start Example for LLM Maker
Demonstrates creating and using tools
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tool_executor import ToolExecutor
from tool_maker import ToolMaker
from tool_registry import ToolRegistry


def main():
    """Run quick start examples"""
    print("=" * 60)
    print("LLM Maker - Quick Start")
    print("=" * 60)
    print()

    # Initialize components
    print("Initializing components...")
    maker = ToolMaker()
    registry = ToolRegistry()
    executor = ToolExecutor()
    print("✓ Components initialized")
    print()

    # Example 1: Create a simple math tool
    print("Example 1: Creating a Fibonacci calculator...")
    print("-" * 60)

    tool = maker.create_tool(
        name="calculate_fibonacci",
        description="Calculate the nth Fibonacci number",
        parameters={"n": "int"},
        return_type="int",
        examples=[
            {"input": {"n": 0}, "output": 0},
            {"input": {"n": 1}, "output": 1},
            {"input": {"n": 10}, "output": 55},
        ],
    )

    if tool:
        print(f"✓ Tool created: {tool.name}")
        print(f"  Description: {tool.description}")
        print(f"  Validated: {tool.validated}")
        print()

        # Register the tool
        tool_id = registry.register(tool)
        print(f"✓ Tool registered with ID: {tool_id}")
        print()

        # Execute the tool
        print("Testing tool execution:")
        for n in [0, 1, 5, 10]:
            result = executor.execute(tool.code, tool.name, {"n": n})
            if result["success"]:
                print(f"  F({n}) = {result['result']}")
            else:
                print(f"  Error for F({n}): {result['error']}")
        print()
    else:
        print("✗ Failed to create tool")
        print()

    # Example 2: Create a string processing tool
    print("Example 2: Creating a text analyzer...")
    print("-" * 60)

    tool2 = maker.create_tool(
        name="count_words",
        description="Count the number of words in text",
        parameters={"text": "str"},
        return_type="int",
    )

    if tool2:
        print(f"✓ Tool created: {tool2.name}")
        tool_id2 = registry.register(tool2)
        print(f"✓ Tool registered with ID: {tool_id2}")
        print()

        # Test it
        test_text = "The quick brown fox jumps over the lazy dog"
        result = executor.execute(tool2.code, tool2.name, {"text": test_text})
        if result["success"]:
            print(f"  Text: '{test_text}'")
            print(f"  Word count: {result['result']}")
        print()
    else:
        print("✗ Failed to create tool")
        print()

    # Show registry statistics
    print("Registry Statistics:")
    print("-" * 60)
    stats = registry.get_stats()
    print(f"  Total tools: {stats['total_tools']}")
    print(f"  Validated tools: {stats['validated_tools']}")
    print(f"  Total executions: {stats['total_executions']}")
    print()

    # List all tools
    print("Registered Tools:")
    print("-" * 60)
    tools = registry.list_tools()
    for t in tools:
        print(f"  - {t.name}: {t.description}")
        print(f"    Executions: {t.execution_count}")
    print()

    print("=" * 60)
    print("Quick start complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
