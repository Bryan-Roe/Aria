"""SQLite-backed persistence for AGI reasoning chains.

Provides a compact, thread-safe SQLite adapter with a FileAGIPersistence-compatible
API. Stores events in an append-only `agi_events` table and exposes a small
read_last() method for audit and testing.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
import uuid
from typing import Any, Dict, List, Optional


class SQLiteAGIPersistence:
    """Append-only SQLite persistence for AGI events.

    Table schema: agi_events(id TEXT PRIMARY KEY, ts REAL, type TEXT, meta TEXT, payload TEXT)
    """

    def __init__(self, path: str) -> None:
        self.path = os.path.abspath(path)
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        # Use a single connection with check_same_thread=False; protect with a lock.
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        # Lightweight durability settings for append-only workload
        try:
            self._conn.execute("PRAGMA journal_mode=WAL;")
            self._conn.execute("PRAGMA synchronous=NORMAL;")
        except Exception:
            pass
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agi_events (
                id TEXT PRIMARY KEY,
                ts REAL,
                type TEXT,
                meta TEXT,
                payload TEXT
            )
            """
        )
        self._conn.commit()

    def write_reasoning_chain(self, chain: List[Dict[str, Any]], meta: Optional[Dict[str, Any]] = None) -> str:
        eid = uuid.uuid4().hex
        ts = time.time()
        meta_j = json.dumps(meta or {}, separators=(",", ":"), ensure_ascii=False)
        payload_j = json.dumps(chain, separators=(",", ":"), ensure_ascii=False)
        with self._lock:
            self._conn.execute(
                "INSERT INTO agi_events (id, ts, type, meta, payload) VALUES (?, ?, ?, ?, ?)",
                (eid, ts, "reasoning_chain", meta_j, payload_j),
            )
            self._conn.commit()
        return eid

    def add_reasoning_chain(self, chain: List[Dict[str, Any]]) -> str:
        return self.write_reasoning_chain(chain)

    def add_message(self, message: Dict[str, Any]) -> str:
        eid = uuid.uuid4().hex
        ts = time.time()
        meta_j = json.dumps({}, separators=(",", ":"), ensure_ascii=False)
        payload_j = json.dumps(message, separators=(",", ":"), ensure_ascii=False)
        with self._lock:
            self._conn.execute(
                "INSERT INTO agi_events (id, ts, type, meta, payload) VALUES (?, ?, ?, ?, ?)",
                (eid, ts, "message", meta_j, payload_j),
            )
            self._conn.commit()
        return eid

    def write(self, event_type: str, data: Dict[str, Any]) -> str:
        """Generic write(event_type, data) compatibility method."""
        eid = uuid.uuid4().hex
        ts = time.time()
        meta_j = json.dumps({}, separators=(",", ":"), ensure_ascii=False)
        payload_j = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
        with self._lock:
            self._conn.execute(
                "INSERT INTO agi_events (id, ts, type, meta, payload) VALUES (?, ?, ?, ?, ?)",
                (eid, ts, event_type, meta_j, payload_j),
            )
            self._conn.commit()
        return eid

    def read_last(self, n: int = 10) -> List[Dict[str, Any]]:
        """Return up to the last *n* events (newest last)."""
        with self._lock:
            cur = self._conn.execute(
                "SELECT id, ts, type, meta, payload FROM agi_events ORDER BY ts DESC LIMIT ?",
                (n,),
            )
            rows = cur.fetchall()
        out: List[Dict[str, Any]] = []
        # rows are newest-first; return newest-last to match FileAGIPersistence
        for id, ts, ev_type, meta_j, payload_j in reversed(rows):
            try:
                meta = json.loads(meta_j) if meta_j else {}
            except Exception:
                meta = {}
            try:
                payload = json.loads(payload_j) if payload_j else {}
            except Exception:
                payload = {}
            entry: Dict[str, Any] = {"id": id, "ts": ts, "type": ev_type, "meta": meta}
            if ev_type == "reasoning_chain":
                entry["chain"] = payload
            elif ev_type == "message":
                entry["message"] = payload
            else:
                entry["payload"] = payload
            out.append(entry)
        return out

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass
