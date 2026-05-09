#!/usr/bin/env python3
"""
Code Generation Quick Start for Aria

This script provides an interactive menu for code generation tasks.

Usage:
    python3 code_generation_quickstart.py
"""

import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent / "ai-projects" / "llm-maker" / "src"))

from code_generation_templates import (ALL_TEMPLATES, WEBSITE_TEMPLATES_ALL,
                                       get_template_info, list_templates)


def print_banner():
    """Display welcome banner"""
    print("\n" + "╔" + "=" * 58 + "╗")
    print("║  Code Generation Quick Start - Aria Platform           ║")
    print("║  Generate Safe, Validated Code Instantly              ║")
    print("╚" + "=" * 58 + "╝\n")


def show_main_menu():
    """Show main menu options"""
    print("\n📝 MAIN MENU")
    print("-" * 60)
    print("1. View Available Templates")
    print("2. Generate from Template")
    print("3. Run Code Generation Examples")
    print("4. View Documentation")
    print("5. Quick Reference")
    print("0. Exit")
    print()


def show_templates():
    """Show all available templates"""
    list_templates()


def generate_from_template():
    """Interactive template-based generation"""
    print("\n📦 TEMPLATE CATEGORIES")
    print("-" * 60)

    categories = list(ALL_TEMPLATES.keys()) + ["website"]

    for i, cat in enumerate(categories, 1):
        print(f"{i}. {cat.upper()}")

    category_choice = input("\nSelect category (number): ").strip()

    try:
        idx = int(category_choice) - 1
        if 0 <= idx < len(categories):
            category = categories[idx]

            if category == "website":
                templates = WEBSITE_TEMPLATES_ALL
            else:
                templates = ALL_TEMPLATES[category]

            print(f"\n📝 {category.upper()} TEMPLATES")
            print("-" * 60)

            template_list = list(templates.keys())
            for i, name in enumerate(template_list, 1):
                desc = templates[name]["description"]
                print(f"{i}. {name:20} - {desc}")

            template_choice = input("\nSelect template (number): ").strip()
            template_idx = int(template_choice) - 1

            if 0 <= template_idx < len(template_list):
                template_name = template_list[template_idx]
                info = get_template_info(category, template_name)

                print(f"\n✨ Selected: {template_name}")
                print("-" * 60)
                print(f"Description: {info['description']}")

                if "parameters" in info:
                    print(f"\nParameters:")
                    for param, ptype in info["parameters"].items():
                        print(f"  • {param} ({ptype})")
                    print(f"\nReturns:")
                    for ret, rtype in info["returns"].items():
                        print(f"  • {ret} ({rtype})")

                if "pages" in info:
                    print(f"\nPages: {', '.join(info['pages'])}")

                if "example" in info:
                    print(f"\nExample: {info['example']}")

                print("\n💡 Next Steps:")
                print("   1. Use @llm-maker in Copilot Chat")
                print("   2. Say: 'Generate a function that [description]'")
                print("   3. Review the generated code")
                print("   4. Copy and use in your project")

            else:
                print("Invalid selection")
        else:
            print("Invalid selection")
    except ValueError:
        print("Invalid input")


def run_examples():
    """Run code generation examples"""
    print("\n🚀 RUNNING CODE GENERATION EXAMPLES")
    print("-" * 60)
    print("\nThis will generate and test real code...\n")

    try:
        import subprocess

        result = subprocess.run(
            [sys.executable, "code_generation_examples.py"],
            cwd=Path(__file__).parent,
            capture_output=False,
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error running examples: {e}")
        return False


def show_documentation():
    """Show documentation links"""
    print("\n📖 DOCUMENTATION")
    print("-" * 60)
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
    """Show quick reference"""
    print("\n⚡ QUICK REFERENCE")
    print("-" * 60)

    print("\n1️⃣  GENERATE A PYTHON FUNCTION")
    print(
        """
    @llm-maker Generate a function that [what it should do]

    Examples:
    • @llm-maker Generate a function that validates email addresses
    • @llm-maker Generate a function that converts degrees to radians
    • @llm-maker Generate a function that extracts URLs from text
    """
    )

    print("\n2️⃣  GENERATE A WEBSITE")
    print(
        """
    @llm-maker Build a [style] [type] website with pages: [page list]

    Examples:
    • @llm-maker Build a modern portfolio website with pages: index, about, contact
    • @llm-maker Build a minimal blog with posts and navigation
    • @llm-maker Create a landing page for a SaaS product
    """
    )

    print("\n3️⃣  GENERATE MULTIPLE FUNCTIONS")
    print(
        """
    @llm-maker Generate these functions:
    1. [Function 1 description]
    2. [Function 2 description]
    3. [Function 3 description]
    """
    )

    print("\n4️⃣  BATCH GENERATION")
    print(
        """
    python3 code_generation_examples.py    # Run all 7 examples
    python3 code_generation_templates.py list    # Show templates
    """
    )

    print("\n❌ NOT ALLOWED (will be rejected):")
    print(
        """
    • Functions that import os, sys, subprocess, socket
    • Functions that use eval, exec, or dynamic code
    • Functions that access the network or file system

    💡 Why? Safety validation prevents dangerous code generation
    """
    )

    print("\n✅ WHAT YOU CAN GENERATE:")
    print(
        """
    • Data processing and transformation
    • Validation and checking functions
    • Mathematical calculations
    • String and text manipulation
    • List and array operations
    • Type checking functions
    • Complete static websites (HTML/CSS/JS)
    """
    )


def main():
    """Main interactive menu"""
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
            print(
                "   Remember: Use @llm-maker in Copilot Chat for interactive generation\n"
            )
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
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
