"""Backfill existing chat JSONL logs into the SQL memory store.

Usage (PowerShell):
  python .\\scripts\\ingest_chat_logs_to_sql.py --logs-dir talk-to-ai\\logs --limit 10

Environment:
  QAI_DB_CONN must be set for inserts to succeed.

Behavior:
  - Each log file becomes (or reuses) a conversation via sp_LogChatConversation.
  - Embeddings are generated for user messages (assistant messages optional with --embed-assistant).
  - Fault-tolerant: failures per message are reported but ingestion continues.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import List

from shared.db_logging import log_chat_message_safe
from shared.chat_memory import generate_embedding, store_embedding


def ingest_file(path: Path, embed_assistant: bool = False) -> dict:  # noqa: ANN001
    session_id = path.stem  # Use filename as session identifier
    stats = {"file": str(path), "messages": 0, "embedded": 0, "errors": 0}
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    msg = json.loads(line)
                except Exception as e:  # noqa: BLE001
                    stats["errors"] += 1
                    print(f"[WARN] Invalid JSON in {path.name}: {e}")
                    continue
                role = msg.get("role")
                content = msg.get("content") or ""
                log_res = log_chat_message_safe(
                    session_id=session_id,
                    provider="backfill",
                    model=None,
                    role=role,
                    content=content,
                )
                if log_res.get("success"):
                    stats["messages"] += 1
                    if role == "user" or (embed_assistant and role == "assistant"):
                        try:
                            emb = generate_embedding(content)
                            if emb:
                                ok = store_embedding(log_res.get("message_id"), emb, model="backfill")
                                if ok:
                                    stats["embedded"] += 1
                        except Exception as e:  # noqa: BLE001
                            stats["errors"] += 1
                            print(f"[WARN] Embedding failed for message: {e}")
                else:
                    stats["errors"] += 1
        return stats
    except Exception as e:  # noqa: BLE001
        stats["errors"] += 1
        print(f"[ERROR] Failed ingest {path}: {e}")
        return stats


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Backfill chat logs into SQL memory store")
    p.add_argument("--logs-dir", default="talk-to-ai/logs", help="Directory containing chat_*.jsonl logs")
    p.add_argument("--limit", type=int, default=0, help="Optional limit of files to ingest")
    p.add_argument("--embed-assistant", action="store_true", help="Also embed assistant messages")
    p.add_argument("--dry-run", action="store_true", help="List files only without ingestion")
    args = p.parse_args(argv)

    if not os.getenv("QAI_DB_CONN"):
        print("[WARN] QAI_DB_CONN not set; ingestion will do nothing.")

    logs_dir = Path(args.logs_dir)
    if not logs_dir.exists():
        print(f"[ERROR] Logs dir not found: {logs_dir}")
        return 2

    files = sorted([p for p in logs_dir.glob("chat_*.jsonl")])
    if args.limit > 0:
        files = files[: args.limit]

    print(f"Found {len(files)} file(s) to ingest.")
    if args.dry_run:
        for f in files:
            print(f"DRY-RUN: {f.name}")
        return 0

    aggregate = {"files": 0, "messages": 0, "embedded": 0, "errors": 0}
    for f in files:
        res = ingest_file(f, embed_assistant=args.embed_assistant)
        aggregate["files"] += 1
        aggregate["messages"] += res["messages"]
        aggregate["embedded"] += res["embedded"]
        aggregate["errors"] += res["errors"]
        print(f"Ingested {f.name}: {res}")

    print(f"Done. Aggregate: {aggregate}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
