#!/usr/bin/env python
r"""
Quantum AutoRun Orchestrator

Automates local quantum training runs defined in a YAML config.
Built to mirror scripts/autotrain.py but targeting quantum-ai/train_custom_dataset.py.

Key features:
- Works 100% locally (no Azure required)
- Dry-run validation (no execution) with clear JSON status
- Sequential job execution with per-job run dirs and aggregated status

Outputs:
- data_out/quantum_autorun/<job_name>/<timestamp>/stdout.log
- data_out/quantum_autorun/<job_name>/last_run.json
- data_out/quantum_autorun/status.json

Usage examples (PowerShell):
  python .\\scripts\\quantum_autorun.py --dry-run
  python .\\scripts\\quantum_autorun.py --job heart_quick --dry-run
  python .\\scripts\\quantum_autorun.py --job heart_quick
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path as _Path  # local alias used for dataset name inference
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Optional DB logging (safe no-op if not configured)
try:  # noqa: SIM105
    from shared.db_logging import log_quantum_run_safe  # type: ignore
except Exception:  # noqa: BLE001
    def log_quantum_run_safe(*_a, **_kw):  # type: ignore
        return {"success": False, "skipped": True}

try:
    import yaml  # type: ignore
except Exception as e:  # noqa: BLE001
    raise SystemExit("pyyaml is required. Install with: pip install pyyaml")


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_OUT = REPO_ROOT / "data_out" / "quantum_autorun"
TRAIN_SCRIPT = REPO_ROOT / "quantum-ai" / "train_custom_dataset.py"
AZURE_SUBMIT_SCRIPT = REPO_ROOT / "quantum-ai" / "deploy_to_azure_quantum.py"

# Presets supported by train_custom_dataset.py
KNOWN_PRESETS = {"heart", "ionosphere", "sonar", "banknote"}

# Azure Quantum modes
MODE_LOCAL = "train_custom_dataset"  # Local simulator (default, free)
MODE_AZURE = "azure_hardware"  # Azure Quantum hardware submission


@dataclass
class QJob:
    name: str
    mode: str = "train_custom_dataset"  # "train_custom_dataset" or "azure_hardware"
    enabled: bool = True
    # Data selection (choose one)
    preset: Optional[str] = None
    csv: Optional[str] = None
    label_col: Optional[str] = None
    drop_cols: Optional[str] = None  # comma-separated list
    # Hyperparameters
    n_qubits: Optional[int] = None
    epochs: Optional[int] = None
    batch_size: Optional[int] = None
    learning_rate: Optional[float] = None
    test_size: Optional[float] = None
    # Azure Quantum specific (mode=azure_hardware)
    azure_backend: Optional[str] = None  # e.g., "ionq.simulator", "ionq.qpu"
    azure_shots: Optional[int] = None  # Number of shots for hardware
    azure_confirm_cost: bool = False  # Safety: must be True to submit to paid hardware
    # Extra args passthrough
    extra_args: List[str] = field(default_factory=list)


def read_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_jobs(config_path: Path) -> List[QJob]:
    raw = read_yaml(config_path)
    jobs: List[QJob] = []
    for item in raw.get("jobs", []):
        j = QJob(
            name=str(item.get("name")),
            mode=str(item.get("mode", "train_custom_dataset")),
            enabled=bool(item.get("enabled", True)),
            preset=item.get("preset"),
            csv=item.get("csv"),
            label_col=item.get("label_col"),
            drop_cols=item.get("drop_cols"),
            n_qubits=item.get("n_qubits"),
            epochs=item.get("epochs"),
            batch_size=item.get("batch_size"),
            learning_rate=item.get("learning_rate"),
            test_size=item.get("test_size"),
            azure_backend=item.get("azure_backend"),
            azure_shots=item.get("azure_shots"),
            azure_confirm_cost=bool(item.get("azure_confirm_cost", False)),
            extra_args=list(item.get("extra_args", [])),
        )
        if not j.name:
            raise ValueError("Every job requires a 'name'")
        jobs.append(j)
    return jobs


def _venv_python_default() -> Path:
    """Prefer repo root venv if it exists; else current interpreter."""
    venv_python = REPO_ROOT / "venv" / "Scripts" / "python.exe"
    return venv_python if venv_python.exists() else Path(sys.executable)


def _venv_python_quantum() -> Path:
    """Use project-specific venv with quantum dependencies."""
    venv_python = REPO_ROOT / "quantum-ai" / "venv" / "Scripts" / "python.exe"
    if venv_python.exists():
        return venv_python
    # Fallback to root venv
    return _venv_python_default()


def build_command(job: QJob) -> List[str]:
    py = str(_venv_python_quantum())  # Use quantum venv for training/submission
    
    if job.mode == MODE_AZURE:
        # Azure hardware submission mode
        cmd: List[str] = [py, str(AZURE_SUBMIT_SCRIPT)]
        if job.azure_backend:
            cmd += ["--backend", str(job.azure_backend)]
        if job.azure_shots is not None:
            cmd += ["--shots", str(job.azure_shots)]
        if job.n_qubits is not None:
            cmd += ["--n-qubits", str(job.n_qubits)]
        # Azure submit script expects trained model path or circuit definition
        # For now, pass through extra args which can include --circuit-file, etc.
        cmd += list(job.extra_args)
    else:
        # Local training mode (default)
        cmd: List[str] = [py, str(TRAIN_SCRIPT)]
        # Dataset selection
        if job.preset:
            cmd += ["--preset", str(job.preset)]
        if job.csv:
            cmd += ["--csv", str(job.csv)]
            if job.label_col:
                cmd += ["--label-col", str(job.label_col)]
            if job.drop_cols:
                cmd += ["--drop-cols", str(job.drop_cols)]
        # Hyperparameters
        if job.n_qubits is not None:
            cmd += ["--n-qubits", str(job.n_qubits)]
        if job.epochs is not None:
            cmd += ["--epochs", str(job.epochs)]
        if job.batch_size is not None:
            cmd += ["--batch-size", str(job.batch_size)]
        if job.learning_rate is not None:
            cmd += ["--learning-rate", str(job.learning_rate)]
        if job.test_size is not None:
            cmd += ["--test-size", str(job.test_size)]
        # Extras
        cmd += list(job.extra_args)
    return cmd


def ensure_dirs(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def validate_job(job: QJob) -> Dict[str, Any]:
    """Static validation used during dry-run.

    Checks:
      - Required scripts exist
      - Mode-specific validation
      - Cost confirmation for paid hardware
    """
    problems: List[str] = []
    warnings: List[str] = []
    
    if job.mode == MODE_AZURE:
        # Azure hardware mode validation
        if not AZURE_SUBMIT_SCRIPT.exists():
            problems.append(str(AZURE_SUBMIT_SCRIPT))
        
        # Safety: Check if targeting paid hardware without confirmation
        if job.azure_backend and "simulator" not in job.azure_backend.lower() and "sim" not in job.azure_backend.lower():
            if not job.azure_confirm_cost:
                problems.append(f"COST SAFETY: azure_confirm_cost must be true for paid hardware ({job.azure_backend})")
                warnings.append("Set azure_confirm_cost: true in config to proceed with paid hardware")
        
        if not job.azure_backend:
            warnings.append("No azure_backend specified; will use config default (may be paid hardware!)")
    else:
        # Local training mode validation
        if not TRAIN_SCRIPT.exists():
            problems.append(str(TRAIN_SCRIPT))

        # Mutually exclusive dataset selectors
        if job.preset and job.csv:
            problems.append("Specify either 'preset' or 'csv', not both")
        if not job.preset and not job.csv:
            # Allowed: script will fallback to demo dataset; warn but not error
            pass

        if job.preset and job.preset not in KNOWN_PRESETS:
            problems.append(f"Unknown preset: {job.preset}")

        if job.csv:
            if not Path(job.csv).exists():
                problems.append(str(job.csv))

    status = "validated" if not problems else "missing"
    out = {"status": status}
    if problems:
        out["missing"] = problems
    if warnings:
        out["warnings"] = warnings
    return out


def run_job(job: QJob, dry_run: bool = False) -> Dict[str, Any]:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    job_dir = DATA_OUT / job.name / ts
    ensure_dirs(job_dir)
    log_path = job_dir / "stdout.log"

    cmd = build_command(job)

    # Include a compact snapshot of job parameters for status enrichment
    meta: Dict[str, Any] = {
        "preset": job.preset,
        "csv": job.csv,
        "label_col": job.label_col,
        "drop_cols": job.drop_cols,
        "n_qubits": job.n_qubits,
        "epochs": job.epochs,
        "batch_size": job.batch_size,
        "learning_rate": job.learning_rate,
        "test_size": job.test_size,
    }
    if job.mode == MODE_AZURE:
        meta.update({
            "azure_backend": job.azure_backend,
            "azure_shots": job.azure_shots,
            "azure_confirm_cost": job.azure_confirm_cost,
        })

    result: Dict[str, Any] = {
        "name": job.name,
        "mode": job.mode,
        "cmd": cmd,
        "start_time": ts,
        "status": "planned" if dry_run else "running",
        "return_code": None,
        "log": str(log_path),
        "meta": meta,
    }

    if dry_run:
        v = validate_job(job)
        result.update(v)
        return result

    # Execute
    t0 = time.time()
    with log_path.open("w", encoding="utf-8") as logf:
        logf.write(f"$ {' '.join(str(x) for x in cmd)}\n\n")
        logf.flush()
        proc = subprocess.Popen(cmd, cwd=str(REPO_ROOT), stdout=logf, stderr=subprocess.STDOUT, text=True)
        rc = proc.wait()

    duration = time.time() - t0
    result["return_code"] = rc
    result["duration_sec"] = round(duration, 2)
    result["status"] = "succeeded" if rc == 0 else "failed"

    # Enrich with Azure results if available
    if rc == 0 and job.mode == MODE_AZURE:
        try:
            # Read last lines of log to find results path
            log_text = Path(log_path).read_text(encoding="utf-8", errors="ignore")
            marker = "Results saved to: "
            idx = log_text.rfind(marker)
            if idx != -1:
                start = idx + len(marker)
                # Read path until end-of-line
                end = log_text.find("\n", start)
                out_path = log_text[start:end].strip() if end != -1 else log_text[start:].strip()
                jpath = Path(out_path)
                if jpath.exists():
                    import json as _json
                    with jpath.open("r", encoding="utf-8") as f:
                        j = _json.load(f)
                    # Attach to meta
                    result.setdefault("meta", {})
                    result["meta"]["azure_results_file"] = str(jpath)
                    for k in ("job_id", "counts", "success"):
                        if k in j:
                            result["meta"][f"azure_{k}"] = j[k]
        except Exception as e:  # noqa: BLE001
            # Best-effort enrichment; ignore failures
            result.setdefault("meta", {})
            result["meta"].setdefault("azure_parse_error", str(e))

    # Persist last_run.json for job
    write_json(DATA_OUT / job.name / "last_run.json", result)
    return result


def collect_status(all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Aggregate simple counts by status and latest run info
    counts: Dict[str, int] = {}
    latest: Optional[Dict[str, Any]] = None
    latest_ts: Optional[str] = None
    for r in all_results:
        st = str(r.get("status", "unknown"))
        counts[st] = counts.get(st, 0) + 1
        ts = str(r.get("start_time", ""))
        if ts and (latest_ts is None or ts > latest_ts):
            latest_ts = ts
            latest = {
                "name": r.get("name"),
                "status": st,
                "mode": r.get("mode"),
                "start_time": ts,
                "log": r.get("log"),
            }

    summary = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "jobs": all_results,
        "summary": {
            "counts": counts,
            "latest": latest,
        },
    }
    write_json(DATA_OUT / "status.json", summary)
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description="Quantum AutoRun orchestrator")
    ap.add_argument("--config", default=str(REPO_ROOT / "quantum_autorun.yaml"), help="Path to quantum_autorun.yaml")
    ap.add_argument("--job", default=None, help="Run only the named job")
    ap.add_argument("--dry-run", action="store_true", help="Validate and print commands; do not execute")
    ap.add_argument("--list", action="store_true", help="List configured jobs and exit")
    args = ap.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.exists():
        raise SystemExit(f"Config not found: {cfg_path}")

    jobs = [j for j in load_jobs(cfg_path) if j.enabled]
    if args.list:
        print(json.dumps([j.__dict__ for j in jobs], indent=2))
        return

    # Filter to a specific job if requested
    if args.job:
        jobs = [j for j in jobs if j.name == args.job]
        if not jobs:
            raise SystemExit(f"Job not found in config: {args.job}")

    ensure_dirs(DATA_OUT)
    results: List[Dict[str, Any]] = []
    for j in jobs:
        print(f"[quantum_autorun] Running job: {j.name} (mode={j.mode})")
        res = run_job(j, dry_run=args.dry_run)
        results.append(res)
        print(json.dumps(res, indent=2))

        # === DB Logging (only on successful real runs) ===
        if not args.dry_run and res.get("status") == "succeeded":
            dataset_name = j.preset or (j.csv and _Path(str(j.csv)).stem) or "unknown"
            log_info = log_quantum_run_safe(j, res, dataset_name, res.get("log", ""))
            if log_info.get("success"):
                print(f"[quantum_autorun] Logged quantum run to DB (run_id={log_info.get('run_id')})")
            elif log_info.get("skipped"):
                print("[quantum_autorun] DB logging skipped (QAI_DB_CONN not set)")
            else:
                print(f"[quantum_autorun] DB logging failed: {log_info.get('error')}")

    collect_status(results)
    # Non-zero exit if any job failed during non-dry run
    if not args.dry_run:
        failed = [r for r in results if r.get("status") == "failed"]
        if failed:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
