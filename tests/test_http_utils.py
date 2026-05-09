"""Test suite for http_utils module.

This test validates HTTP utility functions for validation and file serving.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.http_utils import (create_cors_headers, create_no_cache_headers,
                               serve_static_file, validate_messages,
                               validate_provider_choice)


def test_validate_messages_success():
    """Test that valid messages pass validation."""
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "system", "content": "You are helpful"},
    ]

    is_valid, error = validate_messages(messages)

    assert is_valid is True
    assert error is None
    print("✓ Valid messages pass validation")


def test_validate_messages_empty():
    """Test that empty messages fail validation."""
    is_valid, error = validate_messages([])

    assert is_valid is False
    assert "No messages" in error
    print("✓ Empty messages fail validation")


def test_validate_messages_not_list():
    """Test that non-list input fails validation."""
    is_valid, error = validate_messages("not a list")

    assert is_valid is False
    assert "must be a list" in error
    print("✓ Non-list input fails validation")


def test_validate_messages_missing_role():
    """Test that message without role fails validation."""
    messages = [{"content": "Hello"}]

    is_valid, error = validate_messages(messages)

    assert is_valid is False
    assert "role" in error
    print("✓ Message without role fails validation")


def test_validate_messages_missing_content():
    """Test that message without content fails validation."""
    messages = [{"role": "user"}]

    is_valid, error = validate_messages(messages)

    assert is_valid is False
    assert "content" in error
    print("✓ Message without content fails validation")


def test_validate_messages_invalid_role():
    """Test that message with invalid role fails validation."""
    messages = [{"role": "invalid_role", "content": "Hello"}]

    is_valid, error = validate_messages(messages)

    assert is_valid is False
    assert "invalid role" in error.lower()
    print("✓ Invalid role fails validation")


def test_validate_messages_whitespace_only_content():
    """Test that whitespace-only string content fails validation."""
    messages = [{"role": "user", "content": "   \n\t  "}]

    is_valid, error = validate_messages(messages)

    assert is_valid is False
    assert "whitespace" in error.lower() or "empty" in error.lower()
    print("✓ Whitespace-only content fails validation")


def test_validate_messages_block_content_whitespace_text_fails():
    """Text blocks with only whitespace should fail validation."""
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "   "},
                {
                    "type": "image_url",
                    "image_url": {"url": "https://example.com/img.png"},
                },
            ],
        }
    ]

    is_valid, error = validate_messages(messages)

    assert is_valid is False
    assert "whitespace" in error.lower() or "empty" in error.lower()
    print("✓ Whitespace-only text block content fails validation")


def test_validate_messages_block_content_whitespace_input_text_fails():
    """input_text blocks with only whitespace should fail validation."""
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": "   \n  "},
                {
                    "type": "image_url",
                    "image_url": {"url": "https://example.com/img.png"},
                },
            ],
        }
    ]

    is_valid, error = validate_messages(messages)

    assert is_valid is False
    assert "whitespace" in error.lower() or "empty" in error.lower()
    print("✓ Whitespace-only input_text block content fails validation")


def test_validate_messages_block_content_image_only_passes():
    """Non-text block-only content should pass (e.g., image-only messages)."""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": "https://example.com/img.png"},
                }
            ],
        }
    ]

    is_valid, error = validate_messages(messages)

    assert is_valid is True
    assert error is None
    print("✓ Image-only block content passes validation")


def test_create_cors_headers():
    """Test CORS headers creation."""
    headers = create_cors_headers()

    assert "Access-Control-Allow-Origin" in headers
    assert "Access-Control-Allow-Methods" in headers
    assert "Access-Control-Allow-Headers" in headers
    assert headers["Access-Control-Allow-Origin"] == "*"
    print("✓ CORS headers created correctly")


def test_create_cors_headers_custom():
    """Test CORS headers with custom values."""
    headers = create_cors_headers(
        allow_origin="https://example.com",
        allow_methods="GET, POST",
        allow_headers="X-Custom-Header",
    )

    assert headers["Access-Control-Allow-Origin"] == "https://example.com"
    assert headers["Access-Control-Allow-Methods"] == "GET, POST"
    assert headers["Access-Control-Allow-Headers"] == "X-Custom-Header"
    print("✓ Custom CORS headers created correctly")


def test_create_no_cache_headers():
    """Test no-cache headers creation."""
    headers = create_no_cache_headers()

    assert "Cache-Control" in headers
    assert "no-cache" in headers["Cache-Control"]
    assert "Pragma" in headers
    assert "Expires" in headers
    print("✓ No-cache headers created correctly")


def test_validate_provider_choice_valid():
    """Test that valid provider choices pass validation."""
    for provider in ["auto", "openai", "azure", "local", "lmstudio"]:
        is_valid, error, hints = validate_provider_choice(provider)
        assert is_valid is True, f"Provider {provider} should be valid"
        assert error is None
        assert hints is None

    print("✓ Valid provider choices pass validation")


def test_validate_provider_choice_invalid():
    """Test that invalid provider fails validation."""
    is_valid, error, hints = validate_provider_choice("invalid_provider")

    assert is_valid is False
    assert "Invalid provider" in error
    assert hints is not None
    assert "hint" in hints
    print("✓ Invalid provider fails validation")


def test_validate_provider_choice_lora_without_model():
    """Test that LoRA without model path fails validation."""
    is_valid, error, hints = validate_provider_choice("lora", model_override=None)

    assert is_valid is False
    assert "LoRA" in error
    assert "model path" in error
    assert hints is not None
    print("✓ LoRA without model path fails validation")


def test_validate_provider_choice_lora_with_model():
    """Test that LoRA with model path passes validation."""
    is_valid, error, hints = validate_provider_choice(
        "lora", model_override="/path/to/adapter"
    )

    assert is_valid is True
    assert error is None
    assert hints is None
    print("✓ LoRA with model path passes validation")


def test_serve_static_file_success():
    """Test serving an existing file."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False, encoding="utf-8"
    ) as f:
        f.write("<html><body>Test</body></html>")
        temp_path = Path(f.name)

    try:
        content, status, headers = serve_static_file(
            temp_path, "text/html", use_cache_headers=False
        )

        assert status == 200
        assert "<html>" in content
        assert "Test" in content
        print("✓ Serving existing file works")
    finally:
        os.unlink(temp_path)


def test_serve_static_file_with_cache_headers():
    """Test serving file with cache headers."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".js", delete=False, encoding="utf-8"
    ) as f:
        f.write("console.log('test');")
        temp_path = Path(f.name)

    try:
        content, status, headers = serve_static_file(
            temp_path, "application/javascript", use_cache_headers=True
        )

        assert status == 200
        assert "console.log" in content
        assert "Cache-Control" in headers
        assert "no-cache" in headers["Cache-Control"]
        print("✓ Serving file with cache headers works")
    finally:
        os.unlink(temp_path)


def test_serve_static_file_not_found():
    """Test serving non-existent file."""
    fake_path = Path("/nonexistent/file.html")
    content, status, headers = serve_static_file(fake_path, "text/html")

    assert status == 404
    assert "not found" in content.lower()
    print("✓ Serving non-existent file returns 404")


if __name__ == "__main__":
    print("Testing http_utils module...\n")

    test_validate_messages_success()
    test_validate_messages_empty()
    test_validate_messages_not_list()
    test_validate_messages_missing_role()
    test_validate_messages_missing_content()
    test_validate_messages_invalid_role()
    test_create_cors_headers()
    test_create_cors_headers_custom()
    test_create_no_cache_headers()
    test_validate_provider_choice_valid()
    test_validate_provider_choice_invalid()
    test_validate_provider_choice_lora_without_model()
    test_validate_provider_choice_lora_with_model()
    test_serve_static_file_success()
    test_serve_static_file_with_cache_headers()
    test_serve_static_file_not_found()

    print("\n✅ All http_utils tests passed!")
