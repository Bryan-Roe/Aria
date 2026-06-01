#!/usr/bin/env python3
"""Automate baseline validation for core runtime files.

Checks performed:
- Enumerate Python files under core/
- Parse + compile each file (syntax/import-time compile safety)
- Optionally run a lightweight runtime smoke (`python -m core --cycles 1`)
- Persist machine-readable status to data_out/core_automation/status.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def compile_python_file(path: Path) -> dict[str, Any]:
    try:
        source = path.read_text(encoding="utf-8")
        compile(source, str(path), "exec")
        return {"path": str(path), "status": "ok"}
    except Exception as exc:  # pragma: no cover - defensive and reported via status json
        return {"path": str(path), "status": "failed", "error": str(exc)}


def run_core_smoke(repo_root: Path, timeout_seconds: int) -> dict[str, Any]:
    cmd = [sys.executable, "-m", "core", "--cycles", "1"]
    proc = subprocess.run(  # noqa: S603 - fixed command list, no user interpolation
        cmd,
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
    return {
        "command": " ".join(cmd),
        "returncode": proc.returncode,
        "stdout": proc.stdout[-4000:],
        "stderr": proc.stderr[-4000:],
        "status": "ok" if proc.returncode == 0 else "failed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Automate core/ file validation")
    parser.add_argument(
        "--skip-smoke",
        action="store_true",
        help="Skip the runtime smoke check (`python -m core --cycles 1`).",
    )
    parser.add_argument(
        "--smoke-timeout",
        type=int,
        default=60,
        help="Timeout in seconds for core runtime smoke check (default: 60).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print final JSON status to stdout.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    core_dir = repo_root / "core"
    out_dir = repo_root / "data_out" / "core_automation"
    out_dir.mkdir(parents=True, exist_ok=True)
    status_path = out_dir / "status.json"

    py_files = sorted(core_dir.rglob("*.py"))
    compile_results = [compile_python_file(p) for p in py_files]
    compile_failed = [r for r in compile_results if r["status"] != "ok"]

    smoke_result: dict[str, Any] | None = None
    if not args.skip_smoke:
        smoke_result = run_core_smoke(repo_root, timeout_seconds=max(args.smoke_timeout, 1))

    passed = not compile_failed and (smoke_result is None or smoke_result["status"] == "ok")
    summary = {
        "generated_at": utc_now(),
        "core_dir": str(core_dir),
        "python_files_total": len(py_files),
        "compile_failed": len(compile_failed),
        "compile_results": compile_results,
        "smoke": smoke_result,
        "passed": passed,
    }

    status_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(
            "[core_automation] "
            f"passed={passed} | files={len(py_files)} | compile_failed={len(compile_failed)} "
            f"| status={status_path}"
        )

    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
