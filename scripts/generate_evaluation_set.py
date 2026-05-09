"""Generate evaluation set from training datasets.

Collects records from JSONL/JSON dataset files, computes content hashes
for deduplication, and produces evaluation-ready datasets.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


def _hash_record(record: Dict[str, Any]) -> str:
    """Compute a deterministic SHA-256 hash for a dataset record."""
    canonical = json.dumps(record, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def collect_training_hashes_and_records(
    dataset_dir: Path,
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Scan a dataset directory for JSONL/JSON files and collect all records.

    For each record, a content hash is computed and attached as a ``hash``
    field.  Returns a tuple of ``(hashes, records)`` where *hashes* is a
    flat list of hash strings and *records* is the list of augmented dicts.

    Args:
        dataset_dir: Directory to scan for ``.json`` and ``.jsonl`` files.

    Returns:
        Tuple of (hash_list, record_list).
    """
    hashes: List[str] = []
    records: List[Dict[str, Any]] = []

    for path in sorted(dataset_dir.iterdir()):
        if path.suffix not in (".json", ".jsonl"):
            continue

        if path.suffix == ".jsonl":
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    rec = json.loads(line)
                    h = _hash_record(rec)
                    rec["hash"] = h
                    hashes.append(h)
                    records.append(rec)
        else:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            # Try JSON array first, fall back to JSONL (one object per line)
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                # Treat as JSONL
                for line in content.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    rec = json.loads(line)
                    h = _hash_record(rec)
                    rec["hash"] = h
                    hashes.append(h)
                    records.append(rec)
                continue
            if isinstance(data, list):
                for rec in data:
                    h = _hash_record(rec)
                    rec["hash"] = h
                    hashes.append(h)
                    records.append(rec)
            elif isinstance(data, dict):
                h = _hash_record(data)
                data["hash"] = h
                hashes.append(h)
                records.append(data)

    return hashes, records
