"""
Prune AGI persistence backends (SQLite or JSONL).

Usage examples:
  python scripts/agi_persistence_prune.py --sqlite /path/to/agi.db --keep-rows 1000
  python scripts/agi_persistence_prune.py --jsonl /path/to/agi.jsonl --keep-last 1000
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from typing import Dict, Any


def prune_sqlite(path: str, keep_days: int | None = None, keep_rows: int | None = None, dry_run: bool = False) -> Dict[str, Any]:
    path = os.path.abspath(path)
    if not os.path.exists(path):
        print(f"No DB at {path}", file=sys.stderr)
        return {"deleted": 0, "remaining": 0}

    conn = sqlite3.connect(path, check_same_thread=False)
    try:
        cur = conn.execute("SELECT COUNT(*) FROM agi_events")
        total = int((cur.fetchone() or [0])[0] or 0)

        if keep_rows is not None and total > keep_rows:
            to_delete = total - keep_rows
            cur = conn.execute("SELECT id FROM agi_events ORDER BY ts ASC LIMIT ?", (to_delete,))
            ids = [r[0] for r in cur.fetchall()]
            if not dry_run and ids:
                conn.executemany("DELETE FROM agi_events WHERE id = ?", [(i,) for i in ids])
                conn.commit()
            return {"deleted": len(ids), "remaining": total - len(ids)}

        if keep_days is not None:
            cutoff = time.time() - (keep_days * 86400)
            cur = conn.execute("SELECT COUNT(*) FROM agi_events WHERE ts < ?", (cutoff,))
            to_delete = int((cur.fetchone() or [0])[0] or 0)
            if not dry_run and to_delete > 0:
                conn.execute("DELETE FROM agi_events WHERE ts < ?", (cutoff,))
                conn.commit()
            return {"deleted": to_delete, "remaining": total - to_delete}

        return {"deleted": 0, "remaining": total}
    finally:
        conn.close()


def prune_jsonl(path: str, keep_last: int | None = None, dry_run: bool = False) -> Dict[str, Any]:
    path = os.path.abspath(path)
    if not os.path.exists(path):
        print(f"No JSONL at {path}", file=sys.stderr)
        return {"deleted": 0, "remaining": 0}

    with open(path, "r", encoding="utf-8") as fh:
        lines = fh.read().splitlines()

    total = len(lines)
    if keep_last is not None and total > keep_last:
        keep = lines[-keep_last:]
        if not dry_run:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("\n".join(keep) + "\n")
        return {"deleted": total - keep_last, "remaining": keep_last}

    return {"deleted": 0, "remaining": total}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prune AGI persistence backends (SQLite or JSONL).")
    parser.add_argument("--sqlite", help="Path to SQLite AGI DB")
    parser.add_argument("--jsonl", help="Path to JSONL AGI file")
    parser.add_argument("--keep-days", type=int, help="Prune SQLite rows older than DAYS")
    parser.add_argument("--keep-rows", type=int, help="Keep only the newest N rows in SQLite")
    parser.add_argument("--keep-last", type=int, help="Keep only the last N lines in JSONL")
    parser.add_argument("--dry-run", action="store_true", help="Don't modify data, just report")

    args = parser.parse_args(argv)

    try:
        results = {}
        if args.sqlite:
            results["sqlite"] = prune_sqlite(args.sqlite, keep_days=args.keep_days, keep_rows=args.keep_rows, dry_run=args.dry_run)
        if args.jsonl:
            results["jsonl"] = prune_jsonl(args.jsonl, keep_last=args.keep_last, dry_run=args.dry_run)

        print(json.dumps({"status": "ok", "results": results}))
        return 0
    except Exception as e:  # noqa: BLE001 - top-level script should report errors
        print(json.dumps({"status": "error", "error": str(e)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
