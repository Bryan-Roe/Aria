#!/usr/bin/env python
"""
Auto Bootstrap - Environment and orchestrator validation utility.

Validates the repository environment, checks configuration files,
and runs dry-run validations for autotrain and quantum orchestrators.
Writes a summary to data_out/auto_bootstrap/status_summary.json.

Usage:
    python scripts/auto_bootstrap.py
    python scripts/auto_bootstrap.py --skip-orchestrators
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_OUT = REPO_ROOT / "data_out" / "auto_bootstrap"


def _write_status(summary: dict) -> None:
    DATA_OUT.mkdir(parents=True, exist_ok=True)
    out_file = DATA_OUT / "status_summary.json"
    with open(out_file, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"📄 Status written to {out_file}")


def check_python_version() -> dict:
    major, minor = sys.version_info[:2]
    ok = major == 3 and minor >= 10
    return {
        "status": "ok" if ok else "warn",
        "python_version": f"{major}.{minor}.{sys.version_info[2]}",
        "detail": "ok" if ok else f"Python 3.10+ recommended, got {major}.{minor}",
    }


def check_requirements() -> dict:
    req_file = REPO_ROOT / "requirements.txt"
    if not req_file.exists():
        return {"status": "missing", "detail": "requirements.txt not found"}
    lines = [
        l.strip()
        for l in req_file.read_text().splitlines()
        if l.strip() and not l.startswith("#")
    ]
    return {"status": "ok", "requirement_count": len(lines)}


def check_critical_configs() -> dict:
    configs = [
        "config/training/autotrain.yaml",
        "config/quantum/quantum_autorun.yaml",
    ]
    missing = []
    for c in configs:
        if not (REPO_ROOT / c).exists():
            missing.append(c)
    return {
        "status": "ok" if not missing else "missing",
        "missing_configs": missing,
    }


def check_critical_scripts() -> dict:
    scripts = [
        "scripts/autotrain.py",
        "scripts/quantum_autorun.py",
        "scripts/test_runner.py",
        "scripts/fast_validate.py",
        "scripts/ci_orchestrator.py",
    ]
    missing = [s for s in scripts if not (REPO_ROOT / s).exists()]
    return {
        "status": "ok" if not missing else "missing",
        "missing_scripts": missing,
    }


def run_orchestrator_dry_run(script: str, name: str) -> dict:
    script_path = REPO_ROOT / script
    if not script_path.exists():
        return {"status": "skipped", "detail": f"{script} not found"}
    t0 = time.monotonic()
    try:
        result = subprocess.run(
            [sys.executable, str(script_path), "--dry-run"],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(REPO_ROOT),
        )
        elapsed = round(time.monotonic() - t0, 2)
        ok = result.returncode == 0
        return {
            "status": "ok" if ok else "failed",
            "returncode": result.returncode,
            "elapsed_s": elapsed,
            "stdout_tail": result.stdout[-500:] if result.stdout else "",
            "stderr_tail": result.stderr[-300:] if result.stderr else "",
        }
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "elapsed_s": 120}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Auto bootstrap — env and orchestrator validation"
    )
    parser.add_argument(
        "--skip-orchestrators",
        action="store_true",
        help="Skip orchestrator dry-run steps",
    )
    args = parser.parse_args()

    print("🚀 Auto Bootstrap — environment and orchestrator validation")
    started = datetime.now(timezone.utc).isoformat()

    checks: dict = {}
    checks["python"] = check_python_version()
    checks["requirements"] = check_requirements()
    checks["configs"] = check_critical_configs()
    checks["scripts"] = check_critical_scripts()

    for name, result in checks.items():
        icon = "✓" if result.get("status") == "ok" else "⚠"
        print(f"  {icon} {name}: {result}")

    orchestrators: dict = {}
    if not args.skip_orchestrators:
        print("\n🔄 Running orchestrator dry-runs...")
        orchestrators["autotrain"] = run_orchestrator_dry_run(
            "scripts/autotrain.py", "autotrain"
        )
        orchestrators["quantum_autorun"] = run_orchestrator_dry_run(
            "scripts/quantum_autorun.py", "quantum_autorun"
        )
        for name, result in orchestrators.items():
            icon = "✓" if result.get("status") == "ok" else "⚠"
            print(
                f"  {icon} {name}: {result.get('status')} ({result.get('elapsed_s', 'n/a')}s)"
            )

    critical_failed = any(
        v.get("status") not in ("ok", "warn", "skipped")
        for v in {**checks, **orchestrators}.values()
    )

    summary = {
        "status": "failed" if critical_failed else "ok",
        "started": started,
        "completed": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "orchestrators": orchestrators,
    }

    _write_status(summary)

    if critical_failed:
        print("\n❌ Bootstrap completed with failures")
        return 1

    print("\n✅ Bootstrap completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
