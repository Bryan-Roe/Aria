"""Simple file-backed persistence for AGI reasoning chains.

Provides a minimal, dependency-free JSONL writer that stores reasoning chains and
messages for later auditing or learning. Designed to be optional and robust —
failures are logged but do not affect AGI response generation.
"""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from typing import Any, Dict, List, Optional


class FileAGIPersistence:
    """Append-only JSONL persistence for AGI events.

    Each line written is a compact JSON object with keys:
      - id: unique id for the event
      - ts: epoch timestamp (float)
      - type: one of 'reasoning_chain'|'message'|'other'
      - meta: optional metadata dict
      - chain/message: payload depending on type
    """

    def __init__(self, path: str) -> None:
        self.path = os.path.abspath(path)
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        # touch the file so callers can rely on its existence
        open(self.path, "a", encoding="utf-8").close()
        self._lock = threading.RLock()

    def write_reasoning_chain(self, chain: List[Dict[str, Any]], meta: Optional[Dict[str, Any]] = None) -> str:
        entry = {
            "id": uuid.uuid4().hex,
            "ts": time.time(),
            "type": "reasoning_chain",
            "meta": meta or {},
            "chain": chain,
        }
        self._append(entry)
        return entry["id"]

    def add_reasoning_chain(self, chain: List[Dict[str, Any]]) -> str:
        # Backwards-compatible alias used by some callers
        return self.write_reasoning_chain(chain)

    def add_message(self, message: Dict[str, Any]) -> str:
        entry = {
            "id": uuid.uuid4().hex,
            "ts": time.time(),
            "type": "message",
            "meta": {},
            "message": message,
        }
        self._append(entry)
        return entry["id"]

    def _append(self, entry: Dict[str, Any]) -> None:
        with self._lock:
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, separators=(",", ":"), ensure_ascii=False))
                fh.write("\n")

    def read_last(self, n: int = 10) -> List[Dict[str, Any]]:
        """Return up to the last *n* entries from the file (newest last)."""
        with self._lock:
            with open(self.path, "r", encoding="utf-8") as fh:
                lines = fh.read().splitlines()
        if not lines:
            return []
        selected = lines[-n:]
        out: List[Dict[str, Any]] = []
        for line in selected:
            try:
                out.append(json.loads(line))
            except Exception:
                continue
        return out

    def close(self) -> None:
        # File is opened per-write; nothing to close persistently.
        return
