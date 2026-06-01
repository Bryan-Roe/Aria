"""
Centralized request validation helpers for function_app.py endpoints.

Usage:
    from shared.request_validator import validate_request, ValidationError

    body, err = validate_request(req, schema={
        "messages": {"type": list, "required": True, "min_length": 1},
        "provider": {"type": str},
        "temperature": {"type": (int, float), "min": 0, "max": 2},
    })
    if err:
        return func.HttpResponse(json.dumps({"error": err}), status_code=400, ...)
"""

from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when request validation fails."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def parse_json_body(req) -> tuple[dict | None, str | None]:
    """Safely parse JSON from an Azure Functions HttpRequest.

    Returns (body_dict, error_message). On success error_message is None.
    """
    try:
        body = req.get_json()
        if not isinstance(body, dict):
            return None, "Request body must be a JSON object"
        return body, None
    except ValueError:
        # Try raw body fallback
        try:
            raw = req.get_body().decode("utf-8")
            if not raw.strip():
                return None, "Empty request body"
            body = json.loads(raw)
            if not isinstance(body, dict):
                return None, "Request body must be a JSON object"
            return body, None
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            return None, f"Invalid JSON: {exc}"


def validate_fields(body: dict, schema: dict[str, dict]) -> str | None:
    """Validate fields in *body* against *schema*.

    Schema format per field:
        "field_name": {
            "type": str | list | int | (int, float),  # expected type(s)
            "required": True,           # field must be present and non-None
            "min_length": 1,            # for str/list — minimum length
            "max_length": 1000,         # for str/list — maximum length
            "min": 0,                   # for numbers — minimum value
            "max": 100,                 # for numbers — maximum value
            "allowed": ["a", "b"],      # allowlist of values
        }

    Returns an error string or None if valid.
    """
    for field, rules in schema.items():
        value = body.get(field)

        # Required check
        if rules.get("required") and value is None:
            return f"Missing required field: {field}"

        if value is None:
            continue  # optional and absent — skip remaining checks

        # Type check
        expected = rules.get("type")
        if expected:
            type_name = expected.__name__ if isinstance(expected, type) else " | ".join(t.__name__ for t in expected)
            # bool is a subclass of int in Python, so isinstance(True, int) is True.
            # Reject bool where it isn't explicitly allowed so numeric fields don't
            # silently accept True/False as 1/0.
            bool_allowed = bool in expected if isinstance(expected, tuple) else expected is bool
            if not isinstance(value, expected) or (isinstance(value, bool) and not bool_allowed):
                return f"Field '{field}' must be {type_name}"

        # Length checks (str / list)
        if isinstance(value, (str, list)):
            min_len = rules.get("min_length")
            if min_len is not None and len(value) < min_len:
                return f"Field '{field}' must have at least {min_len} item(s)"

            max_len = rules.get("max_length")
            if max_len is not None and len(value) > max_len:
                return f"Field '{field}' exceeds max length {max_len}"

        # Numeric range
        if isinstance(value, (int, float)):
            min_val = rules.get("min")
            if min_val is not None and value < min_val:
                return f"Field '{field}' must be >= {min_val}"

            max_val = rules.get("max")
            if max_val is not None and value > max_val:
                return f"Field '{field}' must be <= {max_val}"

        # Allowlist
        allowed = rules.get("allowed")
        if allowed is not None and value not in allowed:
            return f"Field '{field}' must be one of {allowed}"

    return None


def validate_request(req, schema: dict[str, dict]) -> tuple[dict | None, str | None]:
    """Full request validation: parse JSON + field checks.

    Returns (body, error). If error is not None, body may be None.
    """
    body, parse_err = parse_json_body(req)
    if parse_err:
        return None, parse_err

    field_err = validate_fields(body, schema)  # type: ignore[arg-type]
    if field_err:
        return body, field_err

    return body, None


# --- Pre-built schemas for common endpoints ---

CHAT_SCHEMA = {
    "messages": {"type": list, "required": True, "min_length": 1, "max_length": 500},
    "provider": {
        "type": str,
        "allowed": [
            "auto",
            "azure",
            "azure_openai",
            "openai",
            "lmstudio",
            "ollama",
            "lora",
            "agi",
            "quantum",
            "local",
        ],
    },
    "temperature": {"type": (int, float), "min": 0, "max": 2},
    "max_output_tokens": {"type": int, "min": 1, "max": 128000},
    "max_context_tokens": {"type": int, "min": 1, "max": 128000},
    "system_prompt": {"type": str, "max_length": 10000},
}

TTS_SCHEMA = {
    "text": {"type": str, "required": True, "min_length": 1, "max_length": 5000},
    "voice": {"type": str},
    "rate": {"type": str},
}

QUANTUM_JOB_SCHEMA = {
    "circuit_type": {"type": str, "required": True},
    "backend": {"type": str},
    "shots": {"type": int, "min": 1, "max": 100000},
}

SUBSCRIPTION_SCHEMA = {
    "user_id": {"type": str, "required": True, "min_length": 1},
    "tier": {"type": str, "allowed": ["FREE", "PRO", "ENTERPRISE"]},
}


# AGI endpoint schemas (query/messages one-of requirement is enforced in endpoint helpers).
AGI_BASE_SCHEMA = {
    "query": {"type": str, "max_length": 10000},
    "messages": {"type": list, "max_length": 500},
    "model": {"type": str, "max_length": 256},
    "temperature": {"type": (int, float), "min": 0, "max": 2},
    "max_output_tokens": {"type": int, "min": 1, "max": 128000},
    "verbose": {"type": bool},
}

AGI_ANALYZE_SCHEMA = {
    **AGI_BASE_SCHEMA,
}

AGI_REASON_SCHEMA = {
    **AGI_BASE_SCHEMA,
    "goals": {"type": list, "max_length": 10},
    "include_reasoning_summary": {"type": bool},
}

AGI_STREAM_SCHEMA = {
    **AGI_REASON_SCHEMA,
}
