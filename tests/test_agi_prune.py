"""
Tests for agi_persistence_prune utility.
"""

import json
import time
import sys
from pathlib import Path

# Ensure repo root on path
REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.agi_persistence_sqlite import SQLiteAGIPersistence
import scripts.agi_persistence_prune as prune_mod


def test_prune_jsonl(tmp_path):
    path = tmp_path / "a.jsonl"
    # create 5 lines
    with open(path, "w", encoding="utf-8") as fh:
        for i in range(5):
            fh.write(json.dumps({"i": i, "ts": time.time()}) + "\n")

    res = prune_mod.prune_jsonl(str(path), keep_last=2, dry_run=False)
    assert res["remaining"] == 2
    assert res["deleted"] == 3
    # file now has 2 lines
    with open(path, "r", encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    assert len(lines) == 2


def test_prune_sqlite_by_rows(tmp_path):
    db_path = tmp_path / "agi.db"
    backend = SQLiteAGIPersistence(str(db_path))
    ids = []
    for i in range(5):
        ids.append(backend.write("message", {"i": i}))

    # make first 3 rows old by setting ts backwards
    old_ts = time.time() - (86400 * 30)
    with backend._lock:
        for idx in range(3):
            backend._conn.execute("UPDATE agi_events SET ts = ? WHERE id = ?", (old_ts, ids[idx]))
        backend._conn.commit()

    res = prune_mod.prune_sqlite(str(db_path), keep_rows=2, dry_run=False)
    assert res["remaining"] == 2
    assert res["deleted"] == 3

    backend.close()
