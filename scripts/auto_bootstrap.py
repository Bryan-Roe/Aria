#!/usr/bin/env python
"""Auto Bootstrap Script

Purpose: Provide a single command to quickly validate environment readiness and
all orchestrator configurations without performing heavy training or paid runs.

Features:
- Detect and summarize per-project virtual environments (root, quantum-ai, talk-to-ai, LoRA project)
- Verify presence of key requirement files
- Optionally create missing venvs (skipped in --dry-run mode)
- Run dry-run for AutoTrain and Quantum AutoRun orchestrators
- Aggregate status.json files into one summary artifact
- Fast failure if any job reports missing assets

Usage (PowerShell):
  python .\\scripts\\auto_bootstrap.py --dry-run        # Plan only, no installs
  python .\\scripts\\auto_bootstrap.py                 # Validate + dry-run orchestrators
  python .\\scripts\\auto_bootstrap.py --create-venvs  # Create missing venvs, install minimal deps then dry-runs

Exit codes:
  0 = success / all validated
  1 = validation problems detected (some jobs missing or errors)

Notes:
- Does NOT run paid Azure Quantum jobs (only dry-run)
- Keeps output lightweight for CI usage
- Aggregated summary: data_out/auto_bootstrap/status_summary.json
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_OUT = REPO_ROOT / "data_out" / "auto_bootstrap"
AUTOTRAIN_SCRIPT = REPO_ROOT / "scripts" / "autotrain.py"
QUANTUM_AUTORUN_SCRIPT = REPO_ROOT / "scripts" / "quantum_autorun.py"

PROJECTS = {
    "root": REPO_ROOT / "venv",
    "quantum-ai": REPO_ROOT / "quantum-ai" / "venv",
    "talk-to-ai": REPO_ROOT / "talk-to-ai" / "venv",
    "phi-lora": REPO_ROOT / "AI" / "microsoft_phi-silica-3.6_v1" / "venv",
}

REQUIREMENTS = {
    "root": REPO_ROOT / "requirements.txt",
    "quantum-ai": REPO_ROOT / "quantum-ai" / "requirements.txt",
    "talk-to-ai": REPO_ROOT / "talk-to-ai" / "requirements.txt",
    "phi-lora": REPO_ROOT / "AI" / "microsoft_phi-silica-3.6_v1" / "requirements.txt",
}

PYTHON_EXE = Path(sys.executable)


def _win_python(venv_path: Path) -> Path:
    return venv_path / "Scripts" / "python.exe"


def detect_venv(venv_path: Path) -> Dict[str, Any]:
    py = _win_python(venv_path)
    exists = py.exists()
    return {"path": str(py), "exists": exists}


def create_venv(venv_path: Path) -> Dict[str, Any]:
    py_info = detect_venv(venv_path)
    if py_info["exists"]:
        return {"created": False, **py_info}
    subprocess.check_call([str(PYTHON_EXE), "-m", "venv", str(venv_path)])
    py_info = detect_venv(venv_path)
    return {"created": True, **py_info}


def install_requirements(venv_path: Path, req_file: Path) -> Dict[str, Any]:
    py = _win_python(venv_path)
    if not py.exists():
        return {"installed": False, "error": "venv python missing"}
    if not req_file.exists():
        return {"installed": False, "error": f"requirements file missing: {req_file}"}
    cmd = [str(py), "-m", "pip", "install", "-r", str(req_file)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "installed": proc.returncode == 0,
        "return_code": proc.returncode,
        "stderr": proc.stderr[:500],
    }


def run_orchestrator(script: Path, name: str) -> Dict[str, Any]:
    if not script.exists():
        return {"name": name, "status": "missing_script", "script": str(script)}
    cmd = [str(PYTHON_EXE), str(script), "--dry-run"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    status = "ok" if proc.returncode == 0 else "error"
    # Attempt to parse last JSON object from stdout for richer detail
    detail: List[Any] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                detail.append(json.loads(line))
            except Exception:
                pass
    return {
        "name": name,
        "status": status,
        "script": str(script),
        "return_code": proc.returncode,
        "jobs_parsed": detail,
        "stdout_tail": proc.stdout[-600:],
        "stderr_tail": proc.stderr[-400:],
    }


def aggregate_status(results: Dict[str, Any]) -> None:
    DATA_OUT.mkdir(parents=True, exist_ok=True)
    out_file = DATA_OUT / "status_summary.json"
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"[auto_bootstrap] Summary written: {out_file}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Auto Bootstrap environment + orchestrator validator")
    ap.add_argument("--dry-run", action="store_true", help="Do not create venvs or install deps; just report plan")
    ap.add_argument("--create-venvs", action="store_true", help="Create missing venvs before validation")
    ap.add_argument("--install", action="store_true", help="Install requirements after creating venvs")
    ap.add_argument("--watch", action="store_true", help="Continuously monitor status files (30s refresh)")
    ap.add_argument("--check-training", action="store_true", help="Include training job status in monitoring")
    args = ap.parse_args()

    summary: Dict[str, Any] = {"generated_at": None, "projects": {}, "orchestrators": {}, "problems": []}
    summary["generated_at"] = os.environ.get("SOURCE_DATE_EPOCH") or None

    # Project venv detection / creation
    for pname, venv_path in PROJECTS.items():
        info = detect_venv(venv_path)
        proj_entry = {"venv": info, "requirements": str(REQUIREMENTS[pname])}
        if args.create_venvs and not info["exists"] and not args.dry_run:
            created = create_venv(venv_path)
            proj_entry["venv"] = created
        if args.install and not args.dry_run:
            install_res = install_requirements(venv_path, REQUIREMENTS[pname])
            proj_entry["install"] = install_res
            if not install_res.get("installed"):
                summary["problems"].append(f"Install failed: {pname} -> {install_res.get('error')}")
        summary["projects"][pname] = proj_entry
        if not info["exists"] and not args.dry_run and not args.create_venvs:
            summary["problems"].append(f"Missing venv: {pname}")

    # Orchestrators (always dry-run for speed & safety)
    if not args.dry_run:
        summary["orchestrators"]["autotrain"] = run_orchestrator(AUTOTRAIN_SCRIPT, "autotrain")
        summary["orchestrators"]["quantum_autorun"] = run_orchestrator(QUANTUM_AUTORUN_SCRIPT, "quantum_autorun")
    else:
        summary["orchestrators"] = {"note": "Skipped (dry-run mode)"}

    aggregate_status(summary)

    # Determine exit code
    problems = summary.get("problems", [])
    if any(p for p in problems):
        print("[auto_bootstrap] Problems detected:")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)
    # If orchestrator statuses show error/missing_script
    if not args.dry_run:
        for oc in summary.get("orchestrators", {}).values():
            if isinstance(oc, dict) and oc.get("status") not in ("ok", None):
                print(f"[auto_bootstrap] Orchestrator issue: {oc}")
                sys.exit(1)

    if args.watch:
        print("[auto_bootstrap] Entering watch mode (Ctrl+C to exit)...")
        try:
            while True:
                time.sleep(30)
                # Re-check orchestrator status
                if args.check_training:
                    autotrain_status = REPO_ROOT / "data_out" / "autotrain" / "status.json"
                    if autotrain_status.exists():
                        with autotrain_status.open("r") as f:
                            data = json.load(f)
                            succeeded = sum(1 for j in data.get("jobs", []) if j.get("status") == "succeeded")
                            total = len(data.get("jobs", []))
                            print(f"[watch] AutoTrain: {succeeded}/{total} succeeded")
                print("[watch] Status refreshed. Waiting 30s...")
        except KeyboardInterrupt:
            print("\n[auto_bootstrap] Watch mode stopped")
            sys.exit(0)
    
    print("[auto_bootstrap] Validation complete")
    sys.exit(0)


if __name__ == "__main__":
    main()
