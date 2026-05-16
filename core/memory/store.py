"""
Aria Memory Store

Provides a small, thread-safe in-memory event store used by agents for shared
context during planning and execution.

Improvements over the original simple list-based store:
- Thread-safety (RLock) for concurrent access.
- Optional bounded storage via collections.deque(maxlen=...).
- Event IDs (UUID) for direct lookup.
- ISO8601 UTC timestamps plus epoch seconds.
- Flexible query API (filter by type, time range, limit, reverse).
- Defensive copying of user-provided data to avoid accidental mutation.
- Utility methods: get, clear, to_list, len, iteration.
"""

from collections import deque
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional
import threading
import uuid


Event = Dict[str, Any]


def _now_utc() -> datetime:
    """Return current time in UTC (timezone-aware)."""
    return datetime.now(timezone.utc)


class MemoryStore:
    """
    Thread-safe in-memory event store.

    Parameters
    - max_events: Optional maximum number of events to retain. If provided,
      the store will drop oldest events once the capacity is reached.
    """

    def __init__(self, max_events: Optional[int] = None) -> None:
        self._lock = threading.RLock()
        # deque provides efficient appends and optional bounded length
        self._events: deque[Event] = deque(maxlen=max_events) if max_events else deque()

    def write(self, event_type: str, data: Mapping[str, Any], timestamp: Optional[datetime] = None) -> str:
        """
        Append a new event to the store.

        Returns the event id (hex UUID string).
        The stored event has keys: id, timestamp (ISO8601 str UTC), epoch (float seconds), type, data.
        The provided `data` is deep-copied to avoid external mutation.
        """
        ts = (timestamp.astimezone(timezone.utc) if timestamp else _now_utc())
        event: Event = {
            "id": uuid.uuid4().hex,
            "timestamp": ts.isoformat(),
            "epoch": ts.timestamp(),
            "type": str(event_type),
            "data": deepcopy(dict(data)),
        }
        with self._lock:
            self._events.append(event)
        return event["id"]

    def query(
        self,
        event_type: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
        reverse: bool = False,
    ) -> List[Event]:
        """
        Query events with optional filters.

        - event_type: filter events with matching type (exact match).
        - since / until: timezone-aware datetimes used to filter by epoch (inclusive).
        - limit: maximum number of events to return (applied after filters).
        - reverse: if True, iterate from newest to oldest (useful with limit).

        Returned events are shallow copies of the stored events (data dict remains a deepcopy from write).
        """
        # Normalize timestamps to epoch floats for comparisons
        since_epoch = since.astimezone(timezone.utc).timestamp() if since else None
        until_epoch = until.astimezone(timezone.utc).timestamp() if until else None

        with self._lock:
            events_snapshot = list(self._events)

        iterable: Iterable[Event] = reversed(events_snapshot) if reverse else events_snapshot

        results: List[Event] = []
        for e in iterable:
            if event_type is not None and e.get("type") != event_type:
                continue
            epoch = float(e.get("epoch", 0))
            if since_epoch is not None and epoch < since_epoch:
                continue
            if until_epoch is not None and epoch > until_epoch:
                continue
            # Provide a shallow copy to avoid callers mutating internal structures
            results.append(e.copy())
            if limit is not None and len(results) >= limit:
                break

        return results

    def last(self, n: int = 10) -> List[Event]:
        """
        Return the last `n` events (newest last). If n <= 0, returns an empty list.
        """
        if n <= 0:
            return []
        with self._lock:
            slice_events = list(self._events)[-n:]
            return [e.copy() for e in slice_events]

    def get(self, event_id: str) -> Optional[Event]:
        """
        Return an event by its id or None if not found.
        """
        with self._lock:
            for e in self._events:
                if e.get("id") == event_id:
                    return e.copy()
        return None

    def clear(self, event_type: Optional[str] = None) -> int:
        """
        Clear events from the store.

        - If event_type is None: clears all events.
        - If event_type is provided: removes only events of that type.

        Returns the number of removed events.
        """
        with self._lock:
            original_len = len(self._events)
            if event_type is None:
                self._events.clear()
                return original_len
            # Rebuild deque without matching events while preserving maxlen
            maxlen = self._events.maxlen
            new_events = [e for e in self._events if e.get("type") != event_type]
            self._events = deque(new_events, maxlen=maxlen)
            return original_len - len(self._events)

    def to_list(self) -> List[Event]:
        """
        Return a snapshot list of all events (shallow copies).
        """
        with self._lock:
            return [e.copy() for e in self._events]

    def __len__(self) -> int:
        with self._lock:
            return len(self._events)

    def __iter__(self):
        """
        Iterate over events from oldest to newest. Yields shallow copies.
        """
        with self._lock:
            snapshot = list(self._events)
        for e in snapshot:
            yield e.copy()
