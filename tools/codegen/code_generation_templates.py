"""
Code Generation Templates for Aria

Pre-built templates for common code generation tasks.
Use these as examples for generating your own functions.
"""

# ============================================================================
# TEMPLATE 1: Validation Functions
# ============================================================================

VALIDATION_TEMPLATES = {
    "email": {
        "description": "Validates email address format",
        "parameters": {"email": "str"},
        "returns": {"is_valid": "bool"},
        "example": 'validate_email("user@example.com")',
    },
    "phone": {
        "description": "Validates phone number format (10-15 digits)",
        "parameters": {"phone": "str"},
        "returns": {"is_valid": "bool"},
        "example": 'validate_phone("+1-555-123-4567")',
    },
    "url": {
        "description": "Validates URL format (http/https)",
        "parameters": {"url": "str"},
        "returns": {"is_valid": "bool"},
        "example": 'validate_url("https://example.com/path")',
    },
    "credit_card": {
        "description": "Validates credit card number using Luhn algorithm",
        "parameters": {"card_number": "str"},
        "returns": {"is_valid": "bool"},
        "example": 'validate_credit_card("4532-1111-2222-3333")',
    },
    "password_strength": {
        "description": "Check password strength (length, complexity)",
        "parameters": {"password": "str"},
        "returns": {"strength": "str"},  # 'weak', 'medium', 'strong'
        "example": 'password_strength("MyP@ssw0rd123")',
    },
}


# ============================================================================
# TEMPLATE 2: Text Processing Functions
# ============================================================================

TEXT_PROCESSING_TEMPLATES = {
    "slugify": {
        "description": "Convert text to URL-friendly slug",
        "parameters": {"text": "str"},
        "returns": {"slug": "str"},
        "example": 'slugify("Hello World!")',
    },
    "extract_emails": {
        "description": "Extract all email addresses from text",
        "parameters": {"text": "str"},
        "returns": {"emails": "list"},
        "example": 'extract_emails("Contact: john@example.com or jane@domain.org")',
    },
    "extract_urls": {
        "description": "Extract all URLs from text",
        "parameters": {"text": "str"},
        "returns": {"urls": "list"},
        "example": 'extract_urls("Visit https://example.com for more info")',
    },
    "extract_hashtags": {
        "description": "Extract all hashtags from social media text",
        "parameters": {"text": "str"},
        "returns": {"hashtags": "list"},
        "example": 'extract_hashtags("Love #Python and #AI #ML")',
    },
    "markdown_to_html": {
        "description": "Convert basic markdown to HTML",
        "parameters": {"markdown": "str"},
        "returns": {"html": "str"},
        "example": 'markdown_to_html("# Heading\\n**bold** text")',
    },
    "truncate_text": {
        "description": "Truncate text to length with ellipsis",
        "parameters": {"text": "str", "max_length": "int"},
        "returns": {"truncated": "str"},
        "example": 'truncate_text("Long text here", 10)',
    },
}


# ============================================================================
# TEMPLATE 3: Data Transformation Functions
# ============================================================================

TRANSFORMATION_TEMPLATES = {
    "parse_csv_line": {
        "description": "Parse a CSV line into fields",
        "parameters": {"line": "str", "delimiter": "str"},
        "returns": {"fields": "list"},
        "example": 'parse_csv_line("a,b,c", ",")',
    },
    "parse_query_string": {
        "description": "Parse URL query string into dictionary",
        "parameters": {"query_string": "str"},
        "returns": {"params": "dict"},
        "example": 'parse_query_string("name=John&age=30")',
    },
    "flatten_list": {
        "description": "Flatten nested list to single level",
        "parameters": {"nested_list": "list"},
        "returns": {"flat_list": "list"},
        "example": "flatten_list([[1, 2], [3, [4, 5]]])",
    },
    "group_by": {
        "description": "Group items by key function",
        "parameters": {"items": "list", "key_field": "str"},
        "returns": {"grouped": "dict"},
        "example": 'group_by([{"type":"A","val":1}], "type")',
    },
    "merge_dicts": {
        "description": "Deep merge two dictionaries",
        "parameters": {"dict1": "dict", "dict2": "dict"},
        "returns": {"merged": "dict"},
        "example": 'merge_dicts({"a":1}, {"b":2})',
    },
}


# ============================================================================
# TEMPLATE 4: Mathematical Functions
# ============================================================================

MATH_TEMPLATES = {
    "calculate_average": {
        "description": "Calculate average of numbers",
        "parameters": {"numbers": "list"},
        "returns": {"average": "float"},
        "example": "calculate_average([1, 2, 3, 4, 5])",
    },
    "calculate_median": {
        "description": "Calculate median of numbers",
        "parameters": {"numbers": "list"},
        "returns": {"median": "float"},
        "example": "calculate_median([1, 2, 3, 4, 5])",
    },
    "compound_interest": {
        "description": "Calculate compound interest",
        "parameters": {"principal": "float", "rate": "float", "years": "float"},
        "returns": {"amount": "float"},
        "example": "compound_interest(1000, 5.0, 10)",
    },
    "fibonacci": {
        "description": "Generate Fibonacci sequence",
        "parameters": {"count": "int"},
        "returns": {"sequence": "list"},
        "example": "fibonacci(10)",
    },
    "prime_factors": {
        "description": "Get prime factors of number",
        "parameters": {"number": "int"},
        "returns": {"factors": "list"},
        "example": "prime_factors(24)",
    },
    "gcd": {
        "description": "Greatest common divisor",
        "parameters": {"a": "int", "b": "int"},
        "returns": {"gcd": "int"},
        "example": "gcd(48, 18)",
    },
}


# ============================================================================
# TEMPLATE 5: String Utilities
# ============================================================================

STRING_TEMPLATES = {
    "reverse_string": {
        "description": "Reverse a string",
        "parameters": {"text": "str"},
        "returns": {"reversed": "str"},
        "example": 'reverse_string("Hello")',
    },
    "is_palindrome": {
        "description": "Check if string is palindrome",
        "parameters": {"text": "str"},
        "returns": {"is_palindrome": "bool"},
        "example": 'is_palindrome("racecar")',
    },
    "camel_case": {
        "description": "Convert to camelCase",
        "parameters": {"text": "str"},
        "returns": {"camel_case": "str"},
        "example": 'camel_case("hello world")',
    },
    "snake_case": {
        "description": "Convert to snake_case",
        "parameters": {"text": "str"},
        "returns": {"snake_case": "str"},
        "example": 'snake_case("Hello World")',
    },
    "title_case": {
        "description": "Convert to Title Case",
        "parameters": {"text": "str"},
        "returns": {"title_case": "str"},
        "example": 'title_case("hello world example")',
    },
    "count_occurrences": {
        "description": "Count word occurrences (case insensitive)",
        "parameters": {"text": "str", "word": "str"},
        "returns": {"count": "int"},
        "example": 'count_occurrences("hello hello world", "hello")',
    },
}


# ============================================================================
# TEMPLATE 6: List/Array Operations
# ============================================================================

ARRAY_TEMPLATES = {
    "find_duplicates": {
        "description": "Find duplicate items in list",
        "parameters": {"items": "list"},
        "returns": {"duplicates": "list"},
        "example": "find_duplicates([1, 2, 2, 3, 3, 3])",
    },
    "remove_duplicates": {
        "description": "Remove duplicate items preserving order",
        "parameters": {"items": "list"},
        "returns": {"unique_items": "list"},
        "example": "remove_duplicates([1, 2, 2, 3, 1])",
    },
    "chunks": {
        "description": "Split list into chunks of size n",
        "parameters": {"items": "list", "chunk_size": "int"},
        "returns": {"chunks": "list"},
        "example": "chunks([1, 2, 3, 4, 5], 2)",
    },
    "rotate_list": {
        "description": "Rotate list items by n positions",
        "parameters": {"items": "list", "positions": "int"},
        "returns": {"rotated": "list"},
        "example": "rotate_list([1, 2, 3, 4], 2)",
    },
    "intersect": {
        "description": "Find intersection of two lists",
        "parameters": {"list1": "list", "list2": "list"},
        "returns": {"intersection": "list"},
        "example": "intersect([1, 2, 3], [2, 3, 4])",
    },
}


# ============================================================================
# TEMPLATE 7: Type Checking Functions
# ============================================================================

TYPE_CHECK_TEMPLATES = {
    "is_even": {
        "description": "Check if number is even",
        "parameters": {"number": "int"},
        "returns": {"is_even": "bool"},
        "example": "is_even(4)",
    },
    "is_odd": {
        "description": "Check if number is odd",
        "parameters": {"number": "int"},
        "returns": {"is_odd": "bool"},
        "example": "is_odd(5)",
    },
    "is_prime": {
        "description": "Check if number is prime",
        "parameters": {"number": "int"},
        "returns": {"is_prime": "bool"},
        "example": "is_prime(17)",
    },
    "is_perfect_square": {
        "description": "Check if number is perfect square",
        "parameters": {"number": "float"},
        "returns": {"is_square": "bool"},
        "example": "is_perfect_square(16)",
    },
    "is_numeric": {
        "description": "Check if string contains only numbers",
        "parameters": {"text": "str"},
        "returns": {"is_numeric": "bool"},
        "example": 'is_numeric("12345")',
    },
}


# ============================================================================
# WEBSITE TEMPLATES
# ============================================================================

WEBSITE_TEMPLATES = {
    "portfolio": {
        "description": "Professional portfolio website",
        "pages": ["index.html", "about.html", "portfolio.html", "contact.html"],
        "style": "modern",
    },
    "blog": {
        "description": "Blog with posts and navigation",
        "pages": ["index.html", "post.html", "archive.html", "about.html"],
        "style": "minimal",
    },
    "landing": {
        "description": "Marketing landing page",
        "pages": ["index.html", "pricing.html", "faq.html"],
        "style": "modern",
    },
    "documentation": {
        "description": "API documentation site",
        "pages": [
            "index.html",
            "getting-started.html",
            "api-reference.html",
            "examples.html",
        ],
        "style": "minimal",
    },
    "ecommerce": {
        "description": "Simple ecommerce site",
        "pages": ["index.html", "products.html", "cart.html", "checkout.html"],
        "style": "modern",
    },
}


# ============================================================================
# GENERATION TEMPLATES (Ready to use)
# ============================================================================

ALL_TEMPLATES = {
    "validation": VALIDATION_TEMPLATES,
    "text": TEXT_PROCESSING_TEMPLATES,
    "transform": TRANSFORMATION_TEMPLATES,
    "math": MATH_TEMPLATES,
    "string": STRING_TEMPLATES,
    "array": ARRAY_TEMPLATES,
    "type_check": TYPE_CHECK_TEMPLATES,
}

WEBSITE_TEMPLATES_ALL = WEBSITE_TEMPLATES


# ============================================================================
# UTILITY: List available templates
# ============================================================================


def list_templates():
    """Display all available templates"""
    print("\n📚 CODE GENERATION TEMPLATES")
    print("=" * 60)

    for category, templates in ALL_TEMPLATES.items():
        print(f"\n{category.upper()}:")
        for name, info in templates.items():
            print(f"  • {name:20} - {info['description']}")

    print(f"\n\nWEBSITE TEMPLATES:")
    for name, info in WEBSITE_TEMPLATES_ALL.items():
        print(f"  • {name:20} - {info['description']}")

    print("\n" + "=" * 60)


# ============================================================================
# UTILITY: Get template info
# ============================================================================


def get_template_info(category, name):
    """Get information about a specific template"""
    if category in ALL_TEMPLATES:
        if name in ALL_TEMPLATES[category]:
            return ALL_TEMPLATES[category][name]

    if category == "website" and name in WEBSITE_TEMPLATES_ALL:
        return WEBSITE_TEMPLATES_ALL[name]

    return None


# ============================================================================
# Usage Examples
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "list":
            list_templates()
        elif cmd == "info" and len(sys.argv) > 3:
            info = get_template_info(sys.argv[2], sys.argv[3])
            if info:
                print(f"\nTemplate: {sys.argv[3]}")
                for key, value in info.items():
                    print(f"  {key}: {value}")
            else:
                print("Template not found")
        else:
            print("Usage:")
            print("  python3 code_generation_templates.py list")
            print("  python3 code_generation_templates.py info <category> <name>")
    else:
        list_templates()
