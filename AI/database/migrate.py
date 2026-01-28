#!/usr/bin/env python3
"""
QAI Database Migration Runner

Applies SQL schema (tables, migrations, stored procedures, views) using
configured connection (env vars: QAI_SQL_URL preferred, else QAI_DB_CONN for ODBC).

Supported vendors:
- Azure SQL / SQL Server (mssql)
- Best-effort for SQLite/PostgreSQL/MySQL for generic migrations (limited)

Usage:
  python database/migrate.py --all
  python database/migrate.py --init     # tables only
  python database/migrate.py --sp       # stored procedures only
  python database/migrate.py --views    # views only
  python database/migrate.py --migrations
  python database/migrate.py --dry-run  # show plan only

Notes:
- Splits batches on lines containing only "GO" (case-insensitive) for MSSQL.
- Gracefully skips statements that fail (prints warning) to avoid blocking.
- Creates QAI_QueryMetrics (query tracking) for MSSQL when QAI_ENABLE_QUERY_TRACKING=true.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

from typing import List, Tuple

# Reuse shared SQL engine for URL resolution and engine creation
try:
    from shared.sql_engine import get_engine, resolve_sql_url
    from sqlalchemy import text
except Exception:
    get_engine = None  # type: ignore
    resolve_sql_url = lambda: None  # type: ignore
    text = None  # type: ignore

REPO_ROOT = Path(__file__).resolve().parents[1]
DB_DIR = REPO_ROOT / "database"

TABLES_DIR = DB_DIR / "Tables"
SP_DIR = DB_DIR / "StoredProcedures"
VIEWS_DIR = DB_DIR / "Views"
MIGRATIONS_DIR = DB_DIR / "migrations"

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def _split_batches(sql: str) -> List[str]:
    """Split SQL into batches separated by GO lines.

    MSSQL uses GO as a batch separator. SQLAlchemy doesn't handle GO,
    so we split manually. Lines containing only GO (case-insensitive, with
    optional whitespace) mark boundaries.
    """
    batches: List[str] = []
    current: List[str] = []
    for line in sql.splitlines():
        if re.match(r"^\s*GO\s*$", line, flags=re.IGNORECASE):
            if current:
                batches.append("\n".join(current).strip())
                current = []
        else:
            current.append(line)
    if current:
        batches.append("\n".join(current).strip())
    return [b for b in batches if b]


def _read_sql(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _vendor_name(engine) -> str:
    try:
        return getattr(engine.dialect, "name", "unknown")
    except Exception:
        return "unknown"


def _exec_batch(conn, batch: str, file_path: Path) -> Tuple[bool, str | None]:
    try:
        conn.execute(text(batch))
        return True, None
    except Exception as e:
        return False, f"{file_path.name}: {e}"


# ----------------------------------------------------------------------------
# QAI_QueryMetrics (vendor-specific creation)
# ----------------------------------------------------------------------------

def _ensure_query_metrics_mssql(conn) -> None:
    create_sql = (
        "IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name='QAI_QueryMetrics')\n"
        "BEGIN\n"
        "    CREATE TABLE dbo.QAI_QueryMetrics (\n"
        "        id BIGINT IDENTITY(1,1) PRIMARY KEY,\n"
        "        query_hash VARCHAR(64) NOT NULL,\n"
        "        sql_snippet NVARCHAR(500),\n"
        "        vendor VARCHAR(50),\n"
        "        execution_time_ms DECIMAL(10,2),\n"
        "        executed_at DATETIME2 DEFAULT SYSUTCDATETIME()\n"
        "    );\n"
        "    CREATE INDEX idx_query_hash ON dbo.QAI_QueryMetrics (query_hash);\n"
        "    CREATE INDEX idx_executed_at ON dbo.QAI_QueryMetrics (executed_at);\n"
        "END\n"
    )
    conn.execute(text(create_sql))


# ----------------------------------------------------------------------------
# Application routines
# ----------------------------------------------------------------------------

def _apply_dir(conn, path: Path, vendor: str, split_go: bool = True) -> Tuple[int, int]:
    """Apply all .sql files in a directory, return (applied_count, errors_count)."""
    applied = 0
    errors = 0
    files = sorted([p for p in path.glob("*.sql")])
    for file in files:
        sql = _read_sql(file)
        batches = _split_batches(sql) if split_go else [sql]
        for batch in batches:
            ok, err = _exec_batch(conn, batch, file)
            if ok:
                applied += 1
            else:
                errors += 1
                print(f"[migrate] WARN: {err}")
    return applied, errors


def _load_local_settings_env() -> None:
    """Load env vars from local.settings.json (Values) if present."""
    settings_path = REPO_ROOT / "local.settings.json"
    if not settings_path.exists():
        return
    try:
        import json
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        values = data.get("Values", {}) or {}
        for k, v in values.items():
            if isinstance(v, str):
                # Do not override existing env vars
                os.environ.setdefault(k, v)
    except Exception:
        # best effort only
        pass


def _ensure_sql_url_env() -> None:
    """Ensure QAI_SQL_URL is set, building from QAI_DB_CONN and adding driver if missing."""
    if os.getenv("QAI_SQL_URL"):
        return
    conn = os.getenv("QAI_DB_CONN")
    if not conn:
        return
    # Add default driver if not specified
    if "Driver=" not in conn and "driver=" not in conn:
        conn = f"Driver={{ODBC Driver 18 for SQL Server}};" + conn
    try:
        from shared.sql_engine import _build_url_from_odbc  # type: ignore
        os.environ["QAI_SQL_URL"] = _build_url_from_odbc(conn)
    except Exception:
        # Fallback simple builder
        import urllib.parse as _up
        os.environ["QAI_SQL_URL"] = f"mssql+pyodbc:///?odbc_connect={_up.quote_plus(conn)}"


def run_migrations(plan: List[str], dry_run: bool = False) -> int:
    # Load env from local.settings.json (if present) and synthesize URL
    _load_local_settings_env()
    _ensure_sql_url_env()

    if dry_run:
        print("[migrate] Dry run: planned steps:")
        for step in plan:
            print(f"  - {step}")
        return 0

    url = resolve_sql_url() if resolve_sql_url else None
    if not url:
        print("[migrate] No SQL URL/connection configured (QAI_SQL_URL or QAI_DB_CONN).")
        return 2
    engine = get_engine() if get_engine else None
    if engine is None:
        print("[migrate] Failed to create SQL engine. Ensure SQLAlchemy and driver are installed.")
        return 2
    vendor = _vendor_name(engine)
    print(f"[migrate] Using database vendor: {vendor} url={engine.url}")

    errors_total = 0
    with engine.begin() as conn:
        # Optional: query tracking table for MSSQL
        if os.getenv("QAI_ENABLE_QUERY_TRACKING", "false").lower() == "true" and vendor == "mssql":
            try:
                _ensure_query_metrics_mssql(conn)
                print("[migrate] Ensured QAI_QueryMetrics (MSSQL)")
            except Exception as e:
                errors_total += 1
                print(f"[migrate] WARN: failed to ensure QAI_QueryMetrics: {e}")

        # Apply plan
        for step in plan:
            if step == "tables" and TABLES_DIR.exists():
                applied, errors = _apply_dir(conn, TABLES_DIR, vendor, split_go=True)
                print(f"[migrate] Tables applied: {applied}, errors: {errors}")
                errors_total += errors
            elif step == "migrations" and MIGRATIONS_DIR.exists():
                # For MSSQL, skip generic SQLite-style 002 file and rely on ensured table above
                for file in sorted(MIGRATIONS_DIR.glob("*.sql")):
                    if vendor == "mssql" and file.name == "002_query_performance_tracking.sql":
                        print("[migrate] Skipping 002_query_performance_tracking.sql for MSSQL (handled by ensure)")
                        continue
                    sql = _read_sql(file)
                    batches = _split_batches(sql)
                    for batch in batches:
                        ok, err = _exec_batch(conn, batch, file)
                        if not ok:
                            errors_total += 1
                            print(f"[migrate] WARN: {err}")
                print("[migrate] Migrations applied.")
            elif step == "procedures" and SP_DIR.exists():
                applied, errors = _apply_dir(conn, SP_DIR, vendor, split_go=True)
                print(f"[migrate] Stored procedures applied: {applied}, errors: {errors}")
                errors_total += errors
            elif step == "views" and VIEWS_DIR.exists():
                applied, errors = _apply_dir(conn, VIEWS_DIR, vendor, split_go=True)
                print(f"[migrate] Views applied: {applied}, errors: {errors}")
                errors_total += errors

    return 0 if errors_total == 0 else 1


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="QAI SQL migration runner")
    parser.add_argument("--all", action="store_true", help="Apply tables, migrations, procedures, views")
    parser.add_argument("--init", action="store_true", help="Apply tables only")
    parser.add_argument("--migrations", action="store_true", help="Apply migrations only")
    parser.add_argument("--sp", "--procedures", dest="procedures", action="store_true", help="Apply stored procedures only")
    parser.add_argument("--views", action="store_true", help="Apply views only")
    parser.add_argument("--dry-run", action="store_true", help="Print plan without executing")

    args = parser.parse_args(argv)

    plan: List[str] = []
    if args.all or not any([args.init, args.migrations, args.procedures, args.views]):
        plan = ["tables", "migrations", "procedures", "views"]
    else:
        if args.init:
            plan.append("tables")
        if args.migrations:
            plan.append("migrations")
        if args.procedures:
            plan.append("procedures")
        if args.views:
            plan.append("views")

    return run_migrations(plan, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
