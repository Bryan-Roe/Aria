"""Generated utility functions for lightweight data validation.

This module is intentionally pure (no filesystem/network side effects)
and safe for reuse in API and CLI layers.
"""

from __future__ import annotations

import re
from typing import Any, Iterable

EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def is_non_empty_string(value: Any) -> bool:
    """Return True if value is a non-empty string after trimming."""
    return isinstance(value, str) and bool(value.strip())


def is_valid_email(value: str) -> bool:
    """Return True when value is a valid-looking email address."""
    if not isinstance(value, str):
        return False
    return bool(EMAIL_PATTERN.match(value.strip()))


def is_valid_slug(value: str) -> bool:
    """Return True for lowercase kebab-case slugs (e.g., 'aria-agent-v1')."""
    if not isinstance(value, str):
        return False
    return bool(SLUG_PATTERN.match(value.strip()))


def in_numeric_range(
    value: Any, minimum: float | None = None, maximum: float | None = None
) -> bool:
    """Return True if numeric value lies within [minimum, maximum] bounds.

    Bounds are inclusive when provided.
    """
    if not isinstance(value, (int, float)):
        return False

    if minimum is not None and value < minimum:
        return False
    if maximum is not None and value > maximum:
        return False
    return True


def required_keys_present(
    record: dict[str, Any], required_keys: Iterable[str]
) -> tuple[bool, list[str]]:
    """Check whether all required keys exist and have non-None values.

    Returns:
        Tuple: (all_present, missing_keys)
    """
    missing = [key for key in required_keys if key not in record or record[key] is None]
    return (len(missing) == 0, missing)


def validate_record_types(
    record: dict[str, Any], expected_types: dict[str, type | tuple[type, ...]]
) -> dict[str, str]:
    """Validate field types and return a mapping of field -> error message.

    Only validates fields that exist in record.
    """
    errors: dict[str, str] = {}

    for field, expected in expected_types.items():
        if field not in record:
            continue

        value = record[field]
        if not isinstance(value, expected):
            if isinstance(expected, tuple):
                expected_name = "|".join(t.__name__ for t in expected)
            else:
                expected_name = expected.__name__
            actual_name = type(value).__name__
            errors[field] = f"expected {expected_name}, got {actual_name}"

    return errors


def pick_validation_errors(
    record: dict[str, Any],
    required_keys: Iterable[str] | None = None,
    expected_types: dict[str, type | tuple[type, ...]] | None = None,
) -> list[str]:
    """Run common validations and return human-readable error list."""
    errors: list[str] = []

    if required_keys is not None:
        ok, missing = required_keys_present(record, required_keys)
        if not ok:
            errors.append(f"missing required keys: {', '.join(missing)}")

    if expected_types is not None:
        type_errors = validate_record_types(record, expected_types)
        for field, message in type_errors.items():
            errors.append(f"{field}: {message}")

    return errors
