"""Generated utility functions for structured data manipulation.

This module is intentionally pure (no filesystem/network side effects)
and safe for reuse in API and CLI layers.
"""

from __future__ import annotations

from typing import Any, Iterable

MISSING = object()


def deep_get(
    data: dict[str, Any], path: str, default: Any = None, sep: str = "."
) -> Any:
    """Safely retrieve a nested value from a dictionary using a separator path.

    Args:
        data: Source dictionary.
        path: Nested key path (e.g., "user.profile.name").
        default: Value to return if path is missing.
        sep: Path separator.

    Returns:
        The nested value if present, otherwise default.
    """
    if not path:
        return data

    current: Any = data
    for part in path.split(sep):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def flatten_dict(
    data: dict[str, Any], parent_key: str = "", sep: str = "."
) -> dict[str, Any]:
    """Flatten a nested dictionary into path-key form.

    Args:
        data: Nested dictionary.
        parent_key: Prefix key for recursive calls.
        sep: Separator for flattened keys.

    Returns:
        Flattened dictionary.
    """
    items: dict[str, Any] = {}
    for key, value in data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.update(flatten_dict(value, new_key, sep=sep))
        else:
            items[new_key] = value
    return items


def unflatten_dict(data: dict[str, Any], sep: str = ".") -> dict[str, Any]:
    """Convert a flattened dictionary back into nested dictionary form.

    Args:
        data: Flattened dictionary with separator paths.
        sep: Separator used in keys.

    Returns:
        Nested dictionary.
    """
    result: dict[str, Any] = {}
    for flat_key, value in data.items():
        parts = flat_key.split(sep)
        current = result
        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
    return result


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep-merge two dictionaries without mutating inputs.

    Rules:
    - Dict + Dict => recursively merged
    - Otherwise => value from override wins

    Args:
        base: Base dictionary.
        override: Dictionary with overriding values.

    Returns:
        New merged dictionary.
    """
    merged: dict[str, Any] = dict(base)
    for key, value in override.items():
        base_value = merged.get(key, MISSING)
        if isinstance(base_value, dict) and isinstance(value, dict):
            merged[key] = deep_merge(base_value, value)
        else:
            merged[key] = value
    return merged


def unique_by_key(records: Iterable[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    """Keep first record for each distinct key value while preserving order.

    Missing key values are treated as distinct by object identity marker.

    Args:
        records: Iterable of dictionary records.
        key: Record field to deduplicate by.

    Returns:
        Ordered list of unique records by key value.
    """
    seen: set[Any] = set()
    result: list[dict[str, Any]] = []

    for record in records:
        value = record.get(key, MISSING)
        marker = value if value is not MISSING else ("__missing__", id(record))
        if marker in seen:
            continue
        seen.add(marker)
        result.append(record)

    return result


def rekey_dict(
    data: dict[str, Any], mapping: dict[str, str], keep_unmapped: bool = True
) -> dict[str, Any]:
    """Rename dictionary keys according to mapping.

    Args:
        data: Source dictionary.
        mapping: Mapping of old_key -> new_key.
        keep_unmapped: Whether to keep keys not present in mapping.

    Returns:
        Dictionary with remapped keys.
    """
    result: dict[str, Any] = {}
    for key, value in data.items():
        if key in mapping:
            result[mapping[key]] = value
        elif keep_unmapped:
            result[key] = value
    return result


def coalesce(*values: Any, default: Any = None) -> Any:
    """Return first non-None value from arguments.

    Args:
        *values: Candidate values.
        default: Value returned if all candidates are None.

    Returns:
        First non-None value, else default.
    """
    for value in values:
        if value is not None:
            return value
    return default
