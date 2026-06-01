"""SQLite backend for persistent MemoryStore events."""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Dict, List

Event = Dict[str, Any]


class SQLiteMemoryBackend:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_table()

    def _create_table(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                epoch REAL NOT NULL,
                type TEXT NOT NULL,
                data TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def write(self, event: Event) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO events (id, timestamp, epoch, type, data) VALUES (?, ?, ?, ?, ?)",
            (
                event["id"],
                event["timestamp"],
                event["epoch"],
                event["type"],
                json.dumps(event["data"]),
            ),
        )
        self._conn.commit()

    def load_all(self) -> List[Event]:
        cursor = self._conn.execute("SELECT id, timestamp, epoch, type, data FROM events ORDER BY epoch ASC")
        events: List[Event] = []
        for row in cursor.fetchall():
            events.append(
                {
                    "id": row[0],
                    "timestamp": row[1],
                    "epoch": row[2],
                    "type": row[3],
                    "data": json.loads(row[4]),
                }
            )
        return events
