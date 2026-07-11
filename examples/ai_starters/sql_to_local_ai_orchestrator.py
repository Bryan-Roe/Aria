"""Run SQL query output through a local model automatically.

This script executes a SQL query against SQLite, PostgreSQL,
or MySQL, formats returned rows as context, and asks a local
model for a summary/analysis.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sqlite3
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from examples.ai_starters.local_model_chat import LocalChatModel


def _load_query(query: str | None, query_file: str | None) -> str:
    if query and query.strip():
        return query.strip()
    if query_file:
        path = Path(query_file)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Query file not found: {path}")
        return path.read_text(encoding="utf-8").strip()
    raise ValueError("Provide --query or --query-file.")


def _connect_sqlite(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _connect_postgres(db_url: str) -> Any:
    try:
        import psycopg2

        return psycopg2.connect(db_url)
    except ImportError:
        try:
            import psycopg

            return psycopg.connect(db_url)
        except ImportError as exc:
            raise RuntimeError("PostgreSQL support requires 'psycopg2' or 'psycopg'.") from exc


def _connect_mysql(db_url: str) -> Any:
    parsed = urlparse(db_url)
    if parsed.scheme not in {"mysql", "mysql+pymysql", "mysql+mysqldb"}:
        raise ValueError("MySQL URL must start with mysql://, mysql+pymysql://, or mysql+mysqldb://")

    conn_kwargs = {
        "host": parsed.hostname or "localhost",
        "user": unquote(parsed.username) if parsed.username else None,
        "passwd": unquote(parsed.password) if parsed.password else None,
        "password": unquote(parsed.password) if parsed.password else None,
        "db": parsed.path.lstrip("/") if parsed.path else None,
        "database": parsed.path.lstrip("/") if parsed.path else None,
        "port": parsed.port or 3306,
    }

    try:
        pymysql = importlib.import_module("pymysql")
        return pymysql.connect(
            host=conn_kwargs["host"],
            user=conn_kwargs["user"],
            password=conn_kwargs["password"],
            database=conn_kwargs["database"],
            port=conn_kwargs["port"],
        )
    except ImportError:
        try:
            mysqldb = importlib.import_module("MySQLdb")
            return mysqldb.connect(
                host=conn_kwargs["host"],
                user=conn_kwargs["user"],
                passwd=conn_kwargs["passwd"],
                db=conn_kwargs["db"],
                port=conn_kwargs["port"],
            )
        except ImportError as exc:
            raise RuntimeError("MySQL support requires 'pymysql' or 'mysqlclient' (MySQLdb).") from exc


def _rows_from_cursor(cursor: Any, max_rows: int) -> list[dict]:
    rows = cursor.fetchmany(max_rows)
    if not rows:
        return []

    if hasattr(cursor, "description") and cursor.description:
        columns = [col[0] for col in cursor.description]
        normalized: list[dict] = []
        for row in rows:
            if isinstance(row, dict):
                normalized.append(row)
            elif hasattr(row, "keys"):
                normalized.append(dict(row))
            else:
                normalized.append(dict(zip(columns, row, strict=False)))
        return normalized

    return [dict(row) for row in rows]


def _fetch_rows(
    db_type: str,
    db_path: str | None,
    db_url: str | None,
    sql: str,
    max_rows: int,
) -> list[dict]:
    if db_type == "sqlite":
        if not db_path:
            raise ValueError("--db-path is required for sqlite.")
        conn = _connect_sqlite(db_path)
    elif db_type == "postgres":
        if not db_url:
            raise ValueError("--db-url is required for postgres.")
        conn = _connect_postgres(db_url)
    elif db_type == "mysql":
        if not db_url:
            raise ValueError("--db-url is required for mysql.")
        conn = _connect_mysql(db_url)
    else:
        raise ValueError(f"Unsupported db_type: {db_type}")

    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        return _rows_from_cursor(cursor, max_rows)
    finally:
        conn.close()


def _rows_to_context(rows: list[dict], max_context_chars: int) -> str:
    if not rows:
        return "No rows returned by query."

    serialized = [json.dumps(row, ensure_ascii=False) for row in rows]
    context = "\n".join(serialized)
    if len(context) > max_context_chars:
        context = context[:max_context_chars]
    return context


def _build_prompt(task: str, sql: str, rows_context: str) -> str:
    return (
        "You are a data analyst. Read SQL context and answer clearly.\n\n"
        f"Task:\n{task}\n\n"
        f"SQL used:\n{sql}\n\n"
        "Rows (JSON per line):\n"
        f"{rows_context}\n\n"
        "Output requirements:\n"
        "1) 3-7 bullet summary\n"
        "2) notable anomalies\n"
        "3) recommended next SQL checks"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=("Execute SQL against sqlite/postgres/mysql and pass rows into a local language model.")
    )
    parser.add_argument(
        "--db-type",
        choices=["sqlite", "postgres", "mysql"],
        default="sqlite",
        help="Database type. Defaults to sqlite.",
    )
    parser.add_argument(
        "--db-path",
        default=None,
        help="Path to SQLite database file (used when --db-type sqlite).",
    )
    parser.add_argument(
        "--db-url",
        default=None,
        help=(
            "Connection URL for postgres/mysql. "
            "Examples: postgresql://user:pass@host:5432/db, "
            "mysql://user:pass@host:3306/db"
        ),
    )
    parser.add_argument(
        "--query",
        default=None,
        help="Inline SQL query string.",
    )
    parser.add_argument(
        "--query-file",
        default=None,
        help="Path to a .sql file.",
    )
    parser.add_argument(
        "--model-name",
        default="distilgpt2",
        help="Local model name for Transformers pipeline.",
    )
    parser.add_argument(
        "--task",
        default="Summarize trends and anomalies in this result set.",
        help="What you want the model to do with the SQL output.",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=100,
        help="Maximum rows to feed into the model context.",
    )
    parser.add_argument(
        "--max-context-chars",
        type=int,
        default=8000,
        help="Hard cap for serialized rows passed to model.",
    )
    parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=220,
        help="Maximum new tokens generated by the model.",
    )
    parser.add_argument(
        "--save-output",
        default=None,
        help="Optional file path to save generated analysis.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sql = _load_query(args.query, args.query_file)
    rows = _fetch_rows(
        db_type=args.db_type,
        db_path=args.db_path,
        db_url=args.db_url,
        sql=sql,
        max_rows=args.max_rows,
    )
    rows_context = _rows_to_context(rows, args.max_context_chars)

    prompt = _build_prompt(args.task, sql, rows_context)
    model = LocalChatModel(model_name=args.model_name)
    response = model.ask(prompt, max_new_tokens=args.max_new_tokens)

    print("=== SQL TO LOCAL AI ANALYSIS ===")
    print(f"Rows used: {len(rows)}")
    print("--------------------------------")
    print(response)

    if args.save_output:
        output_path = Path(args.save_output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(response, encoding="utf-8")
        print(f"\nSaved output to: {output_path}")


if __name__ == "__main__":
    main()
