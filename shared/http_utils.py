"""Common validation and serving utilities for HTTP endpoints.

Provides reusable validation functions and file serving utilities to reduce
duplication across Azure Functions endpoints.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

_LOGGER = logging.getLogger(__name__)


def _is_text_like_block_type(block_type: Any) -> bool:
    """Return True for text block types used by OpenAI-compatible APIs."""
    if not isinstance(block_type, str):
        return False
    normalized = block_type.strip().lower()
    return normalized == "text" or normalized.endswith("_text")


def _has_non_whitespace_text_content(content: Any) -> bool:
    """Return True when content includes valid, non-whitespace text.

    Supports plain string content and OpenAI-style block content lists.
    Non-text blocks are ignored for this specific validation check.
    """
    if isinstance(content, str):
        return bool(content.strip())

    if isinstance(content, list):
        has_text_block = False
        for block in content:
            if not isinstance(block, dict):
                continue
            if not _is_text_like_block_type(block.get("type")):
                continue
            has_text_block = True
            block_text = block.get("text")
            if isinstance(block_text, str) and block_text.strip():
                return True
        # If there were text blocks but none had non-whitespace text, reject.
        if has_text_block:
            return False
        # For block-based content with no text blocks, treat as valid (e.g. image-only).
        return True

    if content is None:
        return False

    return bool(str(content).strip())


def validate_messages(messages: Any) -> Tuple[bool, Optional[str]]:
    """Validate chat messages format.

    Args:
        messages: The messages to validate (should be list of dicts)

    Returns:
        Tuple of (is_valid, error_message)
        - If valid: (True, None)
        - If invalid: (False, "error description")

    Expected format:
        [{"role": "user|assistant|system", "content": "..."}]
    """
    if not messages:
        return False, "No messages provided"

    if not isinstance(messages, list):
        return False, "Messages must be a list"

    for idx, msg in enumerate(messages):
        if not isinstance(msg, dict):
            return False, f"Message {idx} must be a dict"

        if "role" not in msg:
            return False, f"Message {idx} missing 'role' field"

        if "content" not in msg:
            return False, f"Message {idx} missing 'content' field"

        if not _has_non_whitespace_text_content(msg.get("content")):
            return False, (
                f"Message {idx} has empty or whitespace-only content. "
                "Text content must contain non-whitespace text."
            )

        # Validate role is one of the expected values
        valid_roles = {"user", "assistant", "system"}
        roles_str = ", ".join(sorted(valid_roles))
        if msg["role"] not in valid_roles:
            return (
                False,
                f"Message {idx} has invalid role '{msg['role']}'. Expected one of: {roles_str}",
            )

    return True, None


def create_cors_headers(
    allow_origin: str = "*",
    allow_methods: str = "POST, GET, OPTIONS",
    allow_headers: str = "Content-Type",
) -> Dict[str, str]:
    """Create standard CORS headers for HTTP responses.

    Args:
        allow_origin: Allowed origins (default: "*")
        allow_methods: Allowed HTTP methods (default: "POST, GET, OPTIONS")
        allow_headers: Allowed headers (default: "Content-Type")

    Returns:
        Dict of CORS headers
    """
    return {
        "Access-Control-Allow-Origin": allow_origin,
        "Access-Control-Allow-Methods": allow_methods,
        "Access-Control-Allow-Headers": allow_headers,
    }


def create_no_cache_headers() -> Dict[str, str]:
    """Create headers that prevent caching.

    Useful for serving dynamic content that should always be fresh.

    Returns:
        Dict of cache-control headers
    """
    return {
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0",
    }


def validate_provider_choice(
    provider_choice: Optional[str], model_override: Optional[str] = None
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """Validate provider choice and model override.

    Args:
        provider_choice: The requested provider ('auto', 'openai', 'azure', 'local', 'lora')
        model_override: Optional model path/name

    Returns:
        Tuple of (is_valid, error_message, hints)
        - If valid: (True, None, None)
        - If invalid: (False, "error description", {"hint": "...", "key": "value"})
    """
    if not provider_choice:
        return True, None, None

    provider_lower = provider_choice.lower()
    valid_providers = {"auto", "openai", "azure", "local", "lora", "lmstudio"}

    if provider_lower not in valid_providers:
        return (
            False,
            f"Invalid provider '{provider_choice}'",
            {
                "hint": f"Valid providers: {', '.join(sorted(valid_providers))}",
                "requested": provider_choice,
            },
        )

    # LoRA provider requires model path
    if provider_lower == "lora" and not model_override:
        return (
            False,
            "LoRA provider requires model path",
            {
                "hint": "Provide 'model' in request body (e.g., data_out/lora_training/lora_adapter)",
                "provider": provider_choice,
            },
        )

    return True, None, None


def serve_static_file(
    file_path: Path, mimetype: str, use_cache_headers: bool = False
) -> Tuple[Optional[str], int, Dict[str, str]]:
    """Serve a static file with appropriate headers.

    Args:
        file_path: Path to the file to serve
        mimetype: MIME type for the response (e.g., 'text/html', 'application/javascript')
        use_cache_headers: Whether to add no-cache headers (default: False for better caching)

    Returns:
        Tuple of (content, status_code, headers)
        - On success: (file_content, 200, headers_dict)
        - On error: (error_message, error_code, {})

    Example:
        content, status, headers = serve_static_file(
            Path("chat-web/index.html"),
            "text/html",
            use_cache_headers=True
        )
        return func.HttpResponse(content, status_code=status, mimetype=mimetype, headers=headers)
    """
    try:
        if not file_path.exists():
            error_msg = f"File not found: {file_path}"
            if mimetype.startswith("text/html"):
                error_msg = f"<h1>Error</h1><p>{error_msg}</p>"
            elif mimetype.startswith("application/javascript"):
                error_msg = f"// Error: {error_msg}"
            else:
                error_msg = f"Error: {error_msg}"

            return error_msg, 404, {}

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        headers = {}
        if use_cache_headers:
            headers.update(create_no_cache_headers())

        return content, 200, headers

    except Exception as e:
        _LOGGER.error(f"Error serving file {file_path}: {e}")

        error_msg = f"Internal error: {str(e)}"
        if mimetype.startswith("text/html"):
            error_msg = f"<h1>Error</h1><p>{error_msg}</p>"
        elif mimetype.startswith("application/javascript"):
            error_msg = f"// Error: {error_msg}"

        return error_msg, 500, {}
