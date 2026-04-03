"""Generated utility functions for text and list/data processing.

This module is intentionally pure (no filesystem/network side effects)
and safe for reuse in API and CLI layers.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Iterable


def normalize_whitespace(text: str) -> str:
    """Collapse repeated whitespace and trim the result.

    Args:
        text: Input text.

    Returns:
        Text with internal whitespace collapsed to single spaces.
    """
    return re.sub(r"\s+", " ", text).strip()


def extract_emails(text: str) -> list[str]:
    """Extract unique email addresses from text while preserving order.

    Args:
        text: Source text that may contain email addresses.

    Returns:
        Ordered list of distinct email addresses.
    """
    pattern = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    seen: set[str] = set()
    result: list[str] = []
    for match in pattern.findall(text):
        if match not in seen:
            seen.add(match)
            result.append(match)
    return result


def chunk_list(items: list[Any], chunk_size: int) -> list[list[Any]]:
    """Split a list into chunks.

    Args:
        items: List to split.
        chunk_size: Positive chunk size.

    Returns:
        List of sub-lists, each at most chunk_size elements.

    Raises:
        ValueError: If chunk_size <= 0.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]


def group_records_by_key(
    records: Iterable[dict[str, Any]], key: str
) -> dict[str, list[dict[str, Any]]]:
    """Group dict records by a chosen key.

    Missing/None keys are grouped under "__missing__".

    Args:
        records: Iterable of dictionary records.
        key: Field name to group on.

    Returns:
        Mapping from key value to list of records.
    """
    grouped: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for rec in records:
        value = rec.get(key)
        bucket = "__missing__" if value is None else str(value)
        grouped[bucket].append(rec)
    return dict(grouped)


def rolling_average(values: list[float], window_size: int) -> list[float]:
    """Compute rolling average over numeric values.

    Args:
        values: Input numeric series.
        window_size: Positive rolling window size.

    Returns:
        List where each element is the mean of the current window.
        Length is max(0, len(values) - window_size + 1).

    Raises:
        ValueError: If window_size <= 0.
    """
    if window_size <= 0:
        raise ValueError("window_size must be > 0")
    if len(values) < window_size:
        return []

    result: list[float] = []
    window_sum = sum(values[:window_size])
    result.append(window_sum / window_size)

    for i in range(window_size, len(values)):
        window_sum += values[i] - values[i - window_size]
        result.append(window_sum / window_size)

    return result
