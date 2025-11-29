#!/usr/bin/env python
"""Minimal SQL migration runner for QAI.

Discovers .sql files under database/migrations/ and applies them sequentially
using the unified SQLAlchemy engine (shared.sql_engine).

Idempotent: records applied migrations in QAI_Migrations table.
Graceful degradation: exits with success if no engine or no migrations.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parents[1]
import sys as _sys
_sys.path.insert(0, str(REPO_ROOT))
from shared.sql_engine import get_engine, resolve_sql_url  # type: ignore
from sqlalchemy import text  # type: ignore
MIGRATIONS_DIR = REPO_ROOT / "database" / "migrations"


def discover_migrations() -> List[Path]:
    if not MIGRATIONS_DIR.exists():
        return []
    return sorted(p for p in MIGRATIONS_DIR.glob("*.sql") if p.is_file())


def ensure_meta_table(engine) -> None:  # noqa: ANN001
    vendor = getattr(engine.dialect, "name", "unknown")
    if vendor == "sqlite":
        ddl = "CREATE TABLE IF NOT EXISTS QAI_Migrations (id TEXT PRIMARY KEY, applied_at TEXT)"
    elif vendor in {"postgresql", "postgres"}:
        ddl = "CREATE TABLE IF NOT EXISTS QAI_Migrations (id VARCHAR(200) PRIMARY KEY, applied_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP)"
    elif vendor == "mysql":
        ddl = (
            "CREATE TABLE IF NOT EXISTS QAI_Migrations (id VARCHAR(200) PRIMARY KEY, "
            "applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP)"
        )
    else:  # SQL Server
        ddl = (
            "IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name='QAI_Migrations') "
            "BEGIN CREATE TABLE dbo.QAI_Migrations (id NVARCHAR(200) NOT NULL PRIMARY KEY, applied_at DATETIME2 DEFAULT SYSUTCDATETIME()) END"
        )
    with engine.begin() as conn:
        conn.execute(text(ddl))


def already_applied(engine) -> set:  # noqa: ANN001
    with engine.connect() as conn:
        try:
            rows = conn.execute(text("SELECT id FROM QAI_Migrations")).fetchall()
            return {r[0] for r in rows}
        except Exception:
            return set()


def apply_migration(engine, path: Path) -> bool:
    sql = path.read_text(encoding="utf-8")
    with engine.begin() as conn:
        conn.execute(text(sql))
        conn.execute(text("INSERT INTO QAI_Migrations (id, applied_at) VALUES (:id, :ts)"), {"id": path.name, "ts": datetime.now(timezone.utc).isoformat()})
    return True


def main() -> int:
    url = resolve_sql_url()
    if not url:
        print("[sql_migrate] No SQL URL resolved (QAI_SQL_URL or QAI_DB_CONN). Nothing to do.")
        return 0
    engine = get_engine()
    if not engine:
        print("[sql_migrate] Engine unavailable.")
        return 0
    ensure_meta_table(engine)
    applied = already_applied(engine)
    all_migs = discover_migrations()
    to_apply = [m for m in all_migs if m.name not in applied]
    print(f"[sql_migrate] Found {len(all_migs)} migration(s); {len(applied)} already applied; {len(to_apply)} pending.")
    if not to_apply:
        print("[sql_migrate] No pending migrations.")
        return 0
    for mig in to_apply:
        try:
            apply_migration(engine, mig)
            print(f"[sql_migrate] Applied {mig.name}")
        except Exception as e:  # noqa: BLE001
            print(f"[sql_migrate] FAILED {mig.name}: {e}")
            return 1
    print(f"[sql_migrate] Completed {len(to_apply)} migration(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
