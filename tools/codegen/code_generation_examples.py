#!/usr/bin/env python3
"""
Code Generation Examples for Aria

This module provides working examples of using the ToolMaker and WebsiteMaker
code generation systems in the Aria project.

Usage:
    python3 code_generation_examples.py
"""

import sys
from pathlib import Path

# Add Aria projects to path
sys.path.insert(0, str(Path(__file__).parent / "ai-projects" / "llm-maker" / "src"))

from tool_maker import ToolMaker
from website_maker import WebsiteMaker


def example_1_email_validator():
    """Example 1: Generate an email validation function"""
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Email Validator Function")
    print("=" * 60)

    maker = ToolMaker()
    code = maker.create_tool(
        "validate_email",
        "Validates if a string is a valid email address using regex",
        {"email": "str"},
        {"is_valid": "bool"},
    )

    print("\nGenerated Code:")
    print(code)

    # Use the generated function
    namespace = {}
    exec(code, namespace)
    validate_email = namespace["validate_email"]

    print("\nTest Results:")
    test_emails = [
        "user@example.com",
        "invalid.email@",
        "test@domain.co.uk",
        "no-at-sign.com",
    ]

    for email in test_emails:
        result = validate_email(email)
        print(f"  {email:25} → {result}")

    return code


def example_2_csv_parser():
    """Example 2: Generate a CSV line parser"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: CSV Line Parser")
    print("=" * 60)

    maker = ToolMaker()
    code = maker.create_tool(
        "parse_csv_line",
        "Parse a CSV line into individual field values, handling quoted strings",
        {"line": "str", "delimiter": "str"},
        {"fields": "list"},
    )

    print("\nGenerated Code:")
    print(code)

    # Use the generated function
    namespace = {}
    exec(code, namespace)
    parse_csv_line = namespace["parse_csv_line"]

    print("\nTest Results:")
    test_lines = [
        "John,Doe,john@example.com",
        'Jane,"Smith, Jr.",jane@example.com',
        "Alice|Bob|Charlie",
    ]

    for line in test_lines:
        delimiter = "|" if "|" in line else ","
        result = parse_csv_line(line, delimiter)
        print(f"  Input: {line}")
        print(f"  Output: {result}\n")

    return code


def example_3_slug_generator():
    """Example 3: Generate a URL slug generator"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: URL Slug Generator")
    print("=" * 60)

    maker = ToolMaker()
    code = maker.create_tool(
        "slugify",
        "Convert a title string to a URL-friendly slug (lowercase, hyphens)",
        {"title": "str"},
        {"slug": "str"},
    )

    print("\nGenerated Code:")
    print(code)

    # Use the generated function
    namespace = {}
    exec(code, namespace)
    slugify = namespace["slugify"]

    print("\nTest Results:")
    test_titles = [
        "Hello World Blog Post",
        "Python 3.9 Release Notes",
        "How to Build APIs in 2026!",
        "Machine Learning & AI Trends",
    ]

    for title in test_titles:
        slug = slugify(title)
        print(f"  '{title}' → '{slug}'")

    return code


def example_4_compound_interest():
    """Example 4: Generate a financial calculator"""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Compound Interest Calculator")
    print("=" * 60)

    maker = ToolMaker()
    code = maker.create_tool(
        "compound_interest",
        "Calculate compound interest for savings",
        {
            "principal": "float",
            "annual_rate": "float",
            "years": "float",
            "compounds_per_year": "int",
        },
        {"final_amount": "float"},
    )

    print("\nGenerated Code:")
    print(code)

    # Use the generated function
    namespace = {}
    exec(code, namespace)
    compound_interest = namespace["compound_interest"]

    print("\nTest Results:")
    scenarios = [
        (1000, 5.0, 10, 12),  # $1000 at 5% for 10 years, monthly compounding
        (5000, 7.5, 5, 4),  # $5000 at 7.5% for 5 years, quarterly
        (10000, 3.0, 20, 1),  # $10000 at 3% for 20 years, annually
    ]

    for principal, rate, years, compounds in scenarios:
        amount = compound_interest(principal, rate, years, compounds)
        print(
            f"  ${principal:>7.0f} @ {rate:>4.1f}% for {years:>2.0f} years → ${amount:>10.2f}"
        )

    return code


def example_5_text_statistics():
    """Example 5: Generate text analysis function"""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Text Statistics Analyzer")
    print("=" * 60)

    maker = ToolMaker()
    code = maker.create_tool(
        "analyze_text",
        "Analyze text and return word count, character count, and average word length",
        {"text": "str"},
        {"word_count": "int", "char_count": "int", "avg_word_length": "float"},
    )

    print("\nGenerated Code:")
    print(code[:400] + "..." if len(code) > 400 else code)

    # Use the generated function
    namespace = {}
    exec(code, namespace)
    analyze_text = namespace["analyze_text"]

    print("\nTest Results:")
    sample_texts = [
        "Hello world",
        "The quick brown fox jumps over the lazy dog",
        "Aria is an interactive AI character platform with quantum ML integration",
    ]

    for text in sample_texts:
        stats = analyze_text(text)
        print(f"  Text: '{text}'")
        print(
            f"  Words: {stats['word_count']}, Chars: {stats['char_count']}, Avg Length: {stats['avg_word_length']:.2f}\n"
        )

    return code


def example_6_simple_website():
    """Example 6: Generate a simple website"""
    print("\n" + "=" * 60)
    print("EXAMPLE 6: Simple Static Website")
    print("=" * 60)

    maker = WebsiteMaker()
    result = maker.create_website(
        "example-site",
        ["index.html", "about.html"],
        "A simple portfolio website with navigation",
    )

    print("\nGenerated Files:")
    for filename in result["files"].keys():
        content = result["files"][filename]
        print(f"  ✓ {filename:20} ({len(content):>6} bytes)")

    print("\nGenerated Content Sample (index.html):")
    index_content = result["files"].get("index.html", "")
    print(index_content[:300] + "..." if len(index_content) > 300 else index_content)

    return result


def example_7_batch_generation():
    """Example 7: Generate multiple functions in batch"""
    print("\n" + "=" * 60)
    print("EXAMPLE 7: Batch Function Generation")
    print("=" * 60)

    maker = ToolMaker()
    functions = [
        (
            "celsius_to_fahrenheit",
            "Convert Celsius to Fahrenheit",
            {"celsius": "float"},
            {"fahrenheit": "float"},
        ),
        ("is_prime", "Check if a number is prime", {"n": "int"}, {"is_prime": "bool"}),
        (
            "reverse_list",
            "Reverse a list of items",
            {"items": "list"},
            {"reversed": "list"},
        ),
    ]

    generated = {}
    for name, desc, params, returns in functions:
        print(f"\nGenerating {name}...", end=" ")
        code = maker.create_tool(name, desc, params, returns)
        generated[name] = code
        print("✓")

        namespace = {}
        exec(code, namespace)
        func = namespace[name]

        if name == "celsius_to_fahrenheit":
            print(f"  Test: 0°C = {func(0):.1f}°F")
        elif name == "is_prime":
            print(f"  Test: is_prime(17) = {func(17)}")
        elif name == "reverse_list":
            print(f"  Test: reverse([1,2,3]) = {func([1,2,3])}")

    return generated


def main():
    """Run all code generation examples"""
    print("\n╔" + "=" * 58 + "╗")
    print("║  Code Generation Examples for Aria Platform             ║")
    print("║  Using ToolMaker and WebsiteMaker                       ║")
    print("╚" + "=" * 58 + "╝")

    try:
        # Run examples
        example_1_email_validator()
        example_2_csv_parser()
        example_3_slug_generator()
        example_4_compound_interest()
        example_5_text_statistics()
        example_6_simple_website()
        example_7_batch_generation()

        print("\n" + "=" * 60)
        print("All examples completed successfully! ✓")
        print("=" * 60)
        print("\nNext Steps:")
        print("  1. Review generated code quality")
        print("  2. Test in your application")
        print("  3. Use @llm-maker agent in Copilot Chat for interactive generation")
        print("  4. Check .github/CODE_GENERATION_GUIDE.md for full documentation")
        print()

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
