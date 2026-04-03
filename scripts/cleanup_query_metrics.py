"""Cleanup query metrics utility with SQL injection prevention."""

from __future__ import annotations

import re


def _validate_table_name(name: str) -> str:
    """Validate a SQL table name to prevent SQL injection.

    Only allows names matching ``[A-Za-z_][A-Za-z0-9_]*``.

    Args:
        name: The table name to validate.

    Returns:
        The validated table name (unchanged).

    Raises:
        ValueError: If the name contains invalid characters or is empty.
    """
    if not name or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ValueError(f"Invalid table name: {name!r}")
    return name
