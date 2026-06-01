"""Generated utility functions for datetime parsing and range handling.

This module is intentionally pure (no filesystem/network side effects)
and safe for reuse in API and CLI layers.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterable


def parse_iso_datetime(value: str, default_tz_utc: bool = True) -> datetime:
    """Parse an ISO-like datetime string into a datetime object.

    Supports:
    - 'YYYY-MM-DDTHH:MM:SS'
    - 'YYYY-MM-DDTHH:MM:SS.ssssss'
    - trailing 'Z' as UTC

    Args:
        value: Input datetime string.
        default_tz_utc: If True, attach UTC tzinfo when parsed datetime is naive.

    Returns:
        Parsed datetime.

    Raises:
        ValueError: If the value cannot be parsed.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError("value must be a non-empty string")

    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"

    dt = datetime.fromisoformat(raw)
    if default_tz_utc and dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def parse_iso_date(value: str) -> date:
    """Parse an ISO date string (YYYY-MM-DD)."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("value must be a non-empty string")
    return date.fromisoformat(value.strip())


def to_utc_iso(dt: datetime, include_microseconds: bool = False) -> str:
    """Convert datetime to UTC ISO-8601 string ending with 'Z'."""
    if not isinstance(dt, datetime):
        raise ValueError("dt must be a datetime instance")

    target = dt
    if target.tzinfo is None:
        target = target.replace(tzinfo=timezone.utc)
    else:
        target = target.astimezone(timezone.utc)

    if include_microseconds:
        return target.isoformat().replace("+00:00", "Z")

    return target.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def date_range(start: date, end: date, inclusive: bool = True) -> list[date]:
    """Generate a date list between start and end.

    Args:
        start: Start date.
        end: End date.
        inclusive: Include end date when True.

    Returns:
        List of dates in ascending order.

    Raises:
        ValueError: If end < start.
    """
    if not isinstance(start, date) or not isinstance(end, date):
        raise ValueError("start and end must be date instances")
    if end < start:
        raise ValueError("end must be >= start")

    total_days = (end - start).days
    limit = total_days + 1 if inclusive else total_days
    return [start + timedelta(days=i) for i in range(limit)]


def is_within_datetime_window(
    value: datetime,
    start: datetime | None = None,
    end: datetime | None = None,
) -> bool:
    """Check if datetime falls within [start, end] inclusive.

    If start or end is None, that side is considered unbounded.
    Naive datetimes are treated as UTC for comparison consistency.
    """
    if not isinstance(value, datetime):
        return False

    def _to_utc(d: datetime | None) -> datetime | None:
        if d is None:
            return None
        if d.tzinfo is None:
            return d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc)

    v = _to_utc(value)
    s = _to_utc(start)
    e = _to_utc(end)

    if s is not None and v < s:
        return False
    if e is not None and v > e:
        return False
    return True


def bucket_datetimes_by_day(values: Iterable[datetime]) -> dict[str, list[datetime]]:
    """Bucket datetimes by UTC day key (YYYY-MM-DD)."""
    buckets: dict[str, list[datetime]] = {}

    for item in values:
        if not isinstance(item, datetime):
            continue
        normalized = item if item.tzinfo is not None else item.replace(tzinfo=timezone.utc)
        utc_dt = normalized.astimezone(timezone.utc)
        key = utc_dt.date().isoformat()
        buckets.setdefault(key, []).append(item)

    return buckets


def sort_datetimes(values: Iterable[datetime], descending: bool = False) -> list[datetime]:
    """Return datetimes sorted by absolute UTC instant.

    Naive datetimes are interpreted as UTC.
    Invalid (non-datetime) values are ignored.
    """
    normalized: list[datetime] = []
    for value in values:
        if not isinstance(value, datetime):
            continue
        if value.tzinfo is None:
            normalized.append(value.replace(tzinfo=timezone.utc))
        else:
            normalized.append(value.astimezone(timezone.utc))

    return sorted(normalized, reverse=descending)
