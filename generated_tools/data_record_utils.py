"""Generated utility functions for record-oriented data transformations.

This module is intentionally pure (no filesystem/network side effects)
and safe for reuse in API and CLI layers.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable


def select_fields(
    records: Iterable[dict[str, Any]], fields: Iterable[str]
) -> list[dict[str, Any]]:
    """Return records containing only selected fields.

    Missing fields are skipped from individual output records.
    """
    field_list = list(fields)
    return [{k: rec[k] for k in field_list if k in rec} for rec in records]


def drop_fields(
    records: Iterable[dict[str, Any]], fields: Iterable[str]
) -> list[dict[str, Any]]:
    """Return records with specified fields removed."""
    drop = set(fields)
    return [{k: v for k, v in rec.items() if k not in drop} for rec in records]


def rename_fields(
    records: Iterable[dict[str, Any]], mapping: dict[str, str]
) -> list[dict[str, Any]]:
    """Rename keys according to mapping for each record."""
    out: list[dict[str, Any]] = []
    for rec in records:
        out.append({mapping.get(k, k): v for k, v in rec.items()})
    return out


def filter_records(
    records: Iterable[dict[str, Any]], predicate: Callable[[dict[str, Any]], bool]
) -> list[dict[str, Any]]:
    """Keep records where predicate(record) is True."""
    return [rec for rec in records if predicate(rec)]


def map_field(
    records: Iterable[dict[str, Any]],
    field: str,
    transform: Callable[[Any], Any],
    skip_missing: bool = True,
) -> list[dict[str, Any]]:
    """Apply transform to a specific field across records.

    Args:
        records: Source record iterable.
        field: Target field name.
        transform: Callable transforming the field value.
        skip_missing: If False, missing fields raise KeyError.
    """
    out: list[dict[str, Any]] = []
    for rec in records:
        copy = dict(rec)
        if field not in copy:
            if skip_missing:
                out.append(copy)
                continue
            raise KeyError(f"Missing field: {field}")
        copy[field] = transform(copy[field])
        out.append(copy)
    return out


def deduplicate_records(
    records: Iterable[dict[str, Any]], keys: Iterable[str]
) -> list[dict[str, Any]]:
    """Deduplicate records using tuple of key values, preserving first occurrence."""
    key_list = list(keys)
    seen: set[tuple[Any, ...]] = set()
    out: list[dict[str, Any]] = []

    for rec in records:
        signature = tuple(rec.get(k) for k in key_list)
        if signature in seen:
            continue
        seen.add(signature)
        out.append(rec)

    return out


def sort_records(
    records: Iterable[dict[str, Any]],
    key: str,
    descending: bool = False,
    missing_last: bool = True,
) -> list[dict[str, Any]]:
    """Sort records by a field with stable handling for missing values."""

    def sort_key(rec: dict[str, Any]) -> tuple[int, int, Any]:
        has_key = key in rec and rec.get(key) is not None
        if has_key:
            value = rec.get(key)
            # Normalize by broad comparable buckets to avoid mixed-type errors.
            # 0: numeric, 1: string, 2: fallback repr for all other types.
            if isinstance(value, (int, float)):
                return (0, 0, float(value))
            if isinstance(value, str):
                return (0, 1, value)
            return (0, 2, repr(value))
        return (1 if missing_last else -1, 3, "")

    return sorted(records, key=sort_key, reverse=descending)


def aggregate_sum(
    records: Iterable[dict[str, Any]], group_key: str, value_key: str
) -> dict[str, float]:
    """Group by group_key and sum numeric value_key per group.

    Non-numeric or missing value_key entries are ignored.
    """
    out: dict[str, float] = {}
    for rec in records:
        group = rec.get(group_key)
        value = rec.get(value_key)
        if group is None or not isinstance(value, (int, float)):
            continue
        label = str(group)
        out[label] = out.get(label, 0.0) + float(value)
    return out
