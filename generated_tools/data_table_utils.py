"""Generated utility functions for simple table-style summaries.

This module is intentionally pure (no filesystem/network side effects)
and safe for reuse in API and CLI layers.
"""

from collections import defaultdict
from typing import Any, Iterable


def value_counts(values: Iterable[Any]) -> dict[str, int]:
    """Count occurrences of values using string keys for stable output."""
    counts: dict[str, int] = {}
    for value in values:
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return counts


def count_records_by_key(
    records: Iterable[dict[str, Any]], key: str, missing_label: str = "__missing__"
) -> dict[str, int]:
    """Count records grouped by a chosen field."""
    counts: dict[str, int] = {}
    for record in records:
        label = record.get(key)
        bucket = missing_label if label is None else str(label)
        counts[bucket] = counts.get(bucket, 0) + 1
    return counts


def summarize_numeric_field(
    records: Iterable[dict[str, Any]], key: str
) -> dict[str, float | int | None]:
    """Return count, sum, min, max, and average for a numeric field.

    Non-numeric values are ignored.
    """
    nums: list[float] = []
    for record in records:
        value = record.get(key)
        if isinstance(value, (int, float)):
            nums.append(float(value))

    if not nums:
        return {"count": 0, "sum": 0.0, "min": None, "max": None, "avg": None}

    total = sum(nums)
    return {
        "count": len(nums),
        "sum": total,
        "min": min(nums),
        "max": max(nums),
        "avg": total / len(nums),
    }


def pivot_sum(
    records: Iterable[dict[str, Any]],
    row_key: str,
    col_key: str,
    value_key: str,
    missing_label: str = "__missing__",
) -> dict[str, dict[str, float]]:
    """Create a simple 2D pivot table by summing numeric values."""
    table: defaultdict[str, dict[str, float]] = defaultdict(dict)

    for record in records:
        row = record.get(row_key)
        col = record.get(col_key)
        value = record.get(value_key)
        if not isinstance(value, (int, float)):
            continue

        row_label = missing_label if row is None else str(row)
        col_label = missing_label if col is None else str(col)
        table[row_label][col_label] = table[row_label].get(col_label, 0.0) + float(value)

    result: dict[str, dict[str, float]] = {}
    for row, cols in table.items():
        result[row] = dict(cols)
    return result


def top_n_items(counts: dict[str, int], n: int = 5) -> list[tuple[str, int]]:
    """Return the top N count items sorted by count desc then key asc."""
    if n <= 0:
        return []

    def _sort_key(item: tuple[str, int]) -> tuple[int, str]:
        return (-item[1], item[0])

    return sorted(counts.items(), key=_sort_key)[:n]
