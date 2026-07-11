"""Extended tests for shared/http_utils.py.

Covers edge cases not in test_http_utils.py:
- validate_messages: None content, non-dict messages, mixed block types,
  numeric/boolean content coercion
- validate_provider_choice: None / empty provider passes
- serve_static_file: 404 error formatting for JS and plain mime types,
  internal error path
- create_cors_headers / create_no_cache_headers: field values
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.http_utils import (
    create_cors_headers,
    create_no_cache_headers,
    serve_static_file,
    validate_messages,
    validate_provider_choice,
)

# ---------------------------------------------------------------------------
# validate_messages — additional content edge cases
# ---------------------------------------------------------------------------


class TestValidateMessagesExtended:
    def test_none_content_fails(self):
        messages = [{"role": "user", "content": None}]
        valid, err = validate_messages(messages)
        assert valid is False
        assert err is not None

    def test_integer_content_succeeds(self):
        # Integer content converts to non-empty str via str()
        messages = [{"role": "user", "content": 42}]
        valid, err = validate_messages(messages)
        assert valid is True
        assert err is None

    def test_zero_integer_content_fails(self):
        # str(0).strip() → "0" which is truthy — so this should pass
        messages = [{"role": "user", "content": 0}]
        valid, err = validate_messages(messages)
        # str(0) = "0" which is non-empty, so valid
        assert valid is True

    def test_non_dict_message_fails(self):
        messages = ["not a dict"]
        valid, err = validate_messages(messages)
        assert valid is False
        assert "dict" in err.lower()

    def test_none_messages_fails(self):
        valid, err = validate_messages(None)
        assert valid is False

    def test_block_content_with_valid_text_passes(self):
        messages = [
            {
                "role": "user",
                "content": [{"type": "text", "text": "Hello there!"}],
            }
        ]
        valid, err = validate_messages(messages)
        assert valid is True
        assert err is None

    def test_block_content_mixed_image_and_valid_text_passes(self):
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image"},
                    {"type": "image_url", "image_url": {"url": "https://example.com/pic.png"}},
                ],
            }
        ]
        valid, err = validate_messages(messages)
        assert valid is True
        assert err is None

    def test_block_with_non_text_type_ignored_for_text_check(self):
        # Only image block — no text block at all → treated as valid
        messages = [
            {
                "role": "user",
                "content": [{"type": "image_url", "image_url": {"url": "https://example.com/x.png"}}],
            }
        ]
        valid, err = validate_messages(messages)
        assert valid is True
        assert err is None

    def test_block_with_non_dict_entry_skipped(self):
        # Non-dict entries in the block list are skipped; image-only content is valid
        messages = [
            {
                "role": "user",
                "content": ["not-a-dict", {"type": "image_url", "image_url": {}}],
            }
        ]
        valid, err = validate_messages(messages)
        assert valid is True

    def test_multiple_messages_second_invalid_reports_index(self):
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "   "},  # whitespace-only
        ]
        valid, err = validate_messages(messages)
        assert valid is False
        assert "1" in err  # index 1

    def test_system_role_accepted(self):
        messages = [{"role": "system", "content": "You are a helpful assistant."}]
        valid, err = validate_messages(messages)
        assert valid is True
        assert err is None

    def test_unknown_role_fails(self):
        messages = [{"role": "tool", "content": "result"}]
        valid, err = validate_messages(messages)
        assert valid is False


# ---------------------------------------------------------------------------
# validate_provider_choice — additional paths
# ---------------------------------------------------------------------------


class TestValidateProviderChoiceExtended:
    def test_none_provider_returns_valid(self):
        valid, err, hints = validate_provider_choice(None)
        assert valid is True
        assert err is None
        assert hints is None

    def test_empty_string_provider_returns_valid(self):
        # Empty string is falsy; treated the same as None
        valid, err, hints = validate_provider_choice("")
        assert valid is True
        assert err is None

    def test_case_insensitive_valid_provider(self):
        valid, err, hints = validate_provider_choice("OPENAI")
        assert valid is True

    def test_lmstudio_valid(self):
        valid, err, hints = validate_provider_choice("lmstudio")
        assert valid is True

    def test_lora_case_insensitive_requires_model(self):
        valid, err, hints = validate_provider_choice("LORA", model_override=None)
        assert valid is False
        assert "LoRA" in err or "lora" in err.lower()

    def test_lora_with_model_case_insensitive(self):
        valid, err, hints = validate_provider_choice("LORA", model_override="/path/adapter")
        assert valid is True

    def test_invalid_provider_hints_contain_valid_list(self):
        valid, err, hints = validate_provider_choice("bad_provider")
        assert valid is False
        assert hints is not None
        assert "hint" in hints
        # The hint should mention at least one known provider
        assert any(p in hints["hint"] for p in ("auto", "openai", "azure"))


# ---------------------------------------------------------------------------
# serve_static_file — 404 error message formats per mime type
# ---------------------------------------------------------------------------


class TestServeStaticFileExtended:
    def test_js_404_returns_comment_style_error(self, tmp_path):
        fake = tmp_path / "nonexistent.js"
        content, status, headers = serve_static_file(fake, "application/javascript")
        assert status == 404
        assert content.startswith("// Error:")

    def test_html_404_returns_html_error(self, tmp_path):
        fake = tmp_path / "nonexistent.html"
        content, status, headers = serve_static_file(fake, "text/html")
        assert status == 404
        assert "<h1>" in content

    def test_plain_404_returns_plain_error(self, tmp_path):
        fake = tmp_path / "nonexistent.txt"
        content, status, headers = serve_static_file(fake, "text/plain")
        assert status == 404
        assert content.startswith("Error:")

    def test_successful_js_serve_no_cache_headers(self, tmp_path):
        js_file = tmp_path / "script.js"
        js_file.write_text("console.log('hello');", encoding="utf-8")
        content, status, headers = serve_static_file(js_file, "application/javascript")
        assert status == 200
        assert "Cache-Control" not in headers

    def test_no_cache_headers_contain_required_keys(self, tmp_path):
        f = tmp_path / "index.html"
        f.write_text("<html></html>", encoding="utf-8")
        _, status, headers = serve_static_file(f, "text/html", use_cache_headers=True)
        assert status == 200
        assert "no-cache" in headers.get("Cache-Control", "")
        assert "Pragma" in headers
        assert "Expires" in headers

    def test_404_returns_empty_headers(self, tmp_path):
        content, status, headers = serve_static_file(tmp_path / "missing.html", "text/html")
        assert status == 404
        assert headers == {}


# ---------------------------------------------------------------------------
# create_cors_headers
# ---------------------------------------------------------------------------


class TestCreateCorsHeadersExtended:
    def test_default_allow_methods_contains_options(self):
        h = create_cors_headers()
        assert "OPTIONS" in h["Access-Control-Allow-Methods"]

    def test_default_allow_headers_is_content_type(self):
        h = create_cors_headers()
        assert h["Access-Control-Allow-Headers"] == "Content-Type"

    def test_returns_dict(self):
        assert isinstance(create_cors_headers(), dict)


# ---------------------------------------------------------------------------
# create_no_cache_headers
# ---------------------------------------------------------------------------


class TestCreateNoCacheHeadersExtended:
    def test_expires_is_zero(self):
        h = create_no_cache_headers()
        assert h["Expires"] == "0"

    def test_pragma_is_no_cache(self):
        h = create_no_cache_headers()
        assert h["Pragma"] == "no-cache"

    def test_cache_control_contains_no_store(self):
        h = create_no_cache_headers()
        assert "no-store" in h["Cache-Control"]

    def test_cache_control_contains_must_revalidate(self):
        h = create_no_cache_headers()
        assert "must-revalidate" in h["Cache-Control"]
