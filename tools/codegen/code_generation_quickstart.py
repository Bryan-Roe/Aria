#!/usr/bin/env python3
"""
Code Generation Quick Start for Aria

This script provides an interactive menu for code generation tasks.

Usage:
    python3 code_generation_quickstart.py
"""

import importlib
import subprocess
import sys
import traceback
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

# Add to path
SRC_DIR = Path(__file__).parent / "ai-projects" / "llm-maker" / "src"
sys.path.insert(0, str(SRC_DIR))

templates_module = importlib.import_module("code_generation_templates")

ALL_TEMPLATES = cast(
    dict[str, dict[str, dict[str, Any]]],
    templates_module.ALL_TEMPLATES,
)
WEBSITE_TEMPLATES_ALL = cast(
    dict[str, dict[str, Any]],
    templates_module.WEBSITE_TEMPLATES_ALL,
)
get_template_info = cast(
    Callable[[str, str], dict[str, Any] | None],
    templates_module.get_template_info,
)
list_templates = cast(
    Callable[[], None],
    templates_module.list_templates,
)

MENU_WIDTH = 60


def print_banner():
    """Display welcome banner."""
    print(f"\n╔{'=' * 58}╗")
    print("║  Code Generation Quick Start - Aria Platform           ║")
    print("║  Generate Safe, Validated Code Instantly               ║")
    print(f"╚{'=' * 58}╝\n")


def show_main_menu():
    """Show main menu options."""
    print("\n📝 MAIN MENU")
    print("-" * MENU_WIDTH)
    print("1. View Available Templates")
    print("2. Generate from Template")
    print("3. Run Code Generation Examples")
    print("4. View Documentation")
    print("5. Quick Reference")
    print("0. Exit")
    print()


def show_templates():
    """Show all available templates."""
    list_templates()


def _select_index(prompt: str, item_count: int) -> int | None:
    choice = input(prompt).strip()
    try:
        index = int(choice) - 1
    except ValueError:
        print("Invalid input")
        return None

    if 0 <= index < item_count:
        return index

    print("Invalid selection")
    return None


def _as_text_map(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}

    typed_map: dict[str, str] = {}
    for key, item in value.items():
        typed_map[str(key)] = str(item)
    return typed_map


def _as_text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _print_template_details(template_name: str, info: dict[str, Any]) -> None:
    print(f"\n✨ Selected: {template_name}")
    print("-" * MENU_WIDTH)

    description = str(info.get("description", "No description available."))
    print(f"Description: {description}")

    parameters = _as_text_map(info.get("parameters"))
    if parameters:
        print("\nParameters:")
        for param, param_type in parameters.items():
            print(f"  • {param} ({param_type})")

    returns = _as_text_map(info.get("returns"))
    if returns:
        print("\nReturns:")
        for ret, return_type in returns.items():
            print(f"  • {ret} ({return_type})")

    pages = _as_text_list(info.get("pages"))
    if pages:
        print(f"\nPages: {', '.join(pages)}")

    example = info.get("example")
    if isinstance(example, str):
        print(f"\nExample: {example}")

    print("\n💡 Next Steps:")
    print("   1. Use @llm-maker in Copilot Chat")
    print("   2. Say: 'Generate a function that [description]'")
    print("   3. Review the generated code")
    print("   4. Copy and use in your project")


def generate_from_template():
    """Interactive template-based generation."""
    print("\n📦 TEMPLATE CATEGORIES")
    print("-" * MENU_WIDTH)

    categories = list(ALL_TEMPLATES.keys()) + ["website"]
    for i, cat in enumerate(categories, 1):
        print(f"{i}. {cat.upper()}")

    category_index = _select_index(
        "\nSelect category (number): ",
        len(categories),
    )
    if category_index is None:
        return

    category = categories[category_index]
    if category == "website":
        templates = WEBSITE_TEMPLATES_ALL
    else:
        templates = ALL_TEMPLATES[category]

    print(f"\n📝 {category.upper()} TEMPLATES")
    print("-" * MENU_WIDTH)

    template_names = list(templates.keys())
    for i, name in enumerate(template_names, 1):
        description = str(templates[name].get("description", ""))
        print(f"{i}. {name:20} - {description}")

    template_index = _select_index(
        "\nSelect template (number): ",
        len(template_names),
    )
    if template_index is None:
        return

    template_name = template_names[template_index]
    info = get_template_info(category, template_name)
    if not isinstance(info, dict):
        print("Template details are unavailable")
        return

    _print_template_details(template_name, info)


def run_examples():
    """Run code generation examples."""
    print("\n🚀 RUNNING CODE GENERATION EXAMPLES")
    print("-" * MENU_WIDTH)
    print("\nThis will generate and test real code...\n")

    try:
        result = subprocess.run(
            [sys.executable, "code_generation_examples.py"],
            cwd=Path(__file__).parent,
            capture_output=False,
            check=False,
        )
        return result.returncode == 0
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"Error running examples: {exc}")
        return False


def show_documentation():
    """Show documentation links."""
    print("\n📖 DOCUMENTATION")
    print("-" * MENU_WIDTH)
    print("\n📚 Main Documentation:")
    print("  • .github/CODE_GENERATION_GUIDE.md")
    print("    Complete guide with API reference, examples, troubleshooting")

    print("\n📁 Source Code:")
    print("  • ai-projects/llm-maker/src/tool_maker.py")
    print("    ToolMaker implementation")
    print("  • ai-projects/llm-maker/src/website_maker.py")
    print("    WebsiteMaker implementation")
    print("  • ai-projects/llm-maker/src/tool_validator.py")
    print("    Safety validation system")

    print("\n⚡ Quick Files:")
    print("  • code_generation_templates.py (this directory)")
    print("    Template library with 40+ patterns")
    print("  • code_generation_examples.py (this directory)")
    print("    Working examples for 7 common tasks")

    print("\n🎯 Copilot Integration:")
    print("  • Open VS Code Copilot Chat: Ctrl+Shift+I")
    print("  • Type: @llm-maker Generate a function that [requirement]")
    print("  • Watch code generation happen in real-time")


def show_quick_reference():
    """Show quick reference."""
    print("\n⚡ QUICK REFERENCE")
    print("-" * MENU_WIDTH)

    print("\n1️⃣  GENERATE A PYTHON FUNCTION")
    print("    @llm-maker Generate a function that [what it should do]")
    print("\n    Examples:")
    print("    • @llm-maker Generate a function that validates email addresses")
    print("    • @llm-maker Generate a function that converts degrees to radians")
    print("    • @llm-maker Generate a function that extracts URLs from text")

    print("\n2️⃣  GENERATE A WEBSITE")
    print("    @llm-maker Build a [style] [type] website with pages: [page list]")
    print("\n    Examples:")
    print("    • @llm-maker Build a modern portfolio website with pages:")
    print("      index, about, contact")
    print("    • @llm-maker Build a minimal blog with posts and navigation")
    print("    • @llm-maker Create a landing page for a SaaS product")

    print("\n3️⃣  GENERATE MULTIPLE FUNCTIONS")
    print("    @llm-maker Generate these functions:")
    print("    1. [Function 1 description]")
    print("    2. [Function 2 description]")
    print("    3. [Function 3 description]")

    print("\n4️⃣  BATCH GENERATION")
    print("    python3 code_generation_examples.py  # Run all 7 examples")
    print("    python3 code_generation_templates.py list  # Show templates")

    print("\n❌ NOT ALLOWED (will be rejected):")
    print("    • Functions that import os, sys, subprocess, socket")
    print("    • Functions that use eval, exec, or dynamic code")
    print("    • Functions that access the network or file system")
    print("\n    💡 Why? Safety validation prevents dangerous code generation")

    print("\n✅ WHAT YOU CAN GENERATE:")
    print("    • Data processing and transformation")
    print("    • Validation and checking functions")
    print("    • Mathematical calculations")
    print("    • String and text manipulation")
    print("    • List and array operations")
    print("    • Type checking functions")
    print("    • Complete static websites (HTML/CSS/JS)")


def main():
    """Main interactive menu."""
    print_banner()

    while True:
        show_main_menu()
        choice = input("Enter your choice: ").strip()

        if choice == "1":
            show_templates()
        elif choice == "2":
            generate_from_template()
        elif choice == "3":
            run_examples()
        elif choice == "4":
            show_documentation()
        elif choice == "5":
            show_quick_reference()
        elif choice == "0":
            print("\n👋 Thanks for using Aria Code Generation!")
            print("   Remember: Use @llm-maker in Copilot Chat for interactive generation\n")
            break
        else:
            print("Invalid choice. Please try again.")

        input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except (RuntimeError, ValueError, OSError) as exc:
        print(f"\nError: {exc}")
        traceback.print_exc()
        sys.exit(1)
