#!/usr/bin/env python
"""
AutoTrain Orchestrator

Lightweight runner to automate model fine-tuning jobs defined in a YAML config.

Goals:
- Zero external services required (works fully offline)
- Sequential job execution with clear logs and machine-readable status
- Supports two runners:
  - hf: calls AI/microsoft_phi-silica-3.6_v1/scripts/train_lora.py (full HF stack)
  - local: calls scripts/run_local_lora_training.py (streamlined local runner)

Outputs:
- data_out/autotrain/<job_name>/<timestamp>/stdout.log        (verbatim process output)
- data_out/autotrain/<job_name>/last_run.json                 (last run metadata)
- data_out/autotrain/status.json                              (summary of all jobs)

Usage examples (PowerShell):
  python .\scripts\autotrain.py --dry-run
  python .\scripts\autotrain.py --job phi36_mixed_chat
  python .\scripts\autotrain.py --job phi36_mixed_chat --reinstall  # when using local runner
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Optional DB logging (safe no-op if not configured)
try:  # noqa: SIM105
    from shared.db_logging import log_lora_run_safe  # type: ignore
except Exception:  # noqa: BLE001
    def log_lora_run_safe(*_a, **_kw):  # type: ignore
        return {"success": False, "skipped": True}

try:
    import yaml  # type: ignore
except Exception as e:  # noqa: BLE001
    raise SystemExit("pyyaml is required. Install with: pip install pyyaml")


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_OUT = REPO_ROOT / "data_out" / "autotrain"
HF_TRAIN_SCRIPT = REPO_ROOT / "AI" / "microsoft_phi-silica-3.6_v1" / "scripts" / "train_lora.py"
LOCAL_RUNNER = REPO_ROOT / "scripts" / "run_local_lora_training.py"


@dataclass
class Job:
    name: str
    runner: str = "hf"  # "hf" | "local"
    dataset: Optional[str] = None
    config: Optional[str] = None
    save_dir: Optional[str] = None
    # Optional overrides
    learning_rate: Optional[float] = None
    lora_dropout: Optional[float] = None
    epochs: Optional[int] = None
    max_train_samples: Optional[int] = None
    max_eval_samples: Optional[int] = None
    seed: Optional[int] = None
    hf_model_id: Optional[str] = None
    # Local runner specific
    reinstall: bool = False
    extra_args: List[str] = field(default_factory=list)


def read_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_jobs(config_path: Path) -> List[Job]:
    raw = read_yaml(config_path)
    jobs: List[Job] = []
    for item in raw.get("jobs", []):
        j = Job(
            name=str(item.get("name")),
            runner=str(item.get("runner", "hf")),
            dataset=item.get("dataset"),
            config=item.get("config"),
            save_dir=item.get("save_dir"),
            learning_rate=item.get("learning_rate"),
            lora_dropout=item.get("lora_dropout"),
            epochs=item.get("epochs"),
            max_train_samples=item.get("max_train_samples"),
            max_eval_samples=item.get("max_eval_samples"),
            seed=item.get("seed"),
            hf_model_id=item.get("hf_model_id"),
            reinstall=bool(item.get("reinstall", False)),
            extra_args=list(item.get("extra_args", [])),
        )
        if not j.name:
            raise ValueError("Every job requires a 'name'")
        jobs.append(j)
    return jobs


def _powershell_exe() -> str:
    # Use Windows PowerShell if present for .ps1 convenience; otherwise default to python invocation only
    return os.environ.get("ComSpec", "powershell.exe")


def _venv_python_default() -> Path:
    # Prefer repo root venv if it exists; else system python
    venv_python = REPO_ROOT / "venv" / "Scripts" / "python.exe"
    return venv_python if venv_python.exists() else Path(sys.executable)


def _venv_python_ml() -> Path:
    # Use project-specific venv with ML dependencies
    venv_python = REPO_ROOT / "AI" / "microsoft_phi-silica-3.6_v1" / "venv" / "Scripts" / "python.exe"
    if venv_python.exists():
        return venv_python
    # Fallback to root venv
    return _venv_python_default()


def build_hf_command(job: Job) -> List[str]:
    py = str(_venv_python_ml())  # Use ML venv for HF training
    cmd: List[str] = [py, str(HF_TRAIN_SCRIPT)]
    # Dataset/config
    if job.config:
        cmd += ["--config", str(job.config)]
    if job.dataset:
        cmd += ["--dataset", str(job.dataset)]
    # Overrides
    if job.hf_model_id:
        cmd += ["--hf-model-id", str(job.hf_model_id)]
    if job.learning_rate is not None:
        cmd += ["--learning-rate", str(job.learning_rate)]
    if job.lora_dropout is not None:
        cmd += ["--lora-dropout", str(job.lora_dropout)]
    if job.epochs is not None:
        cmd += ["--epochs", str(job.epochs)]
    if job.max_train_samples is not None:
        cmd += ["--max-train-samples", str(job.max_train_samples)]
    if job.max_eval_samples is not None:
        cmd += ["--max-eval-samples", str(job.max_eval_samples)]
    if job.seed is not None:
        cmd += ["--seed", str(job.seed)]
    if job.save_dir:
        cmd += ["--save-dir", str(job.save_dir)]
    # Pass through any extra args
    cmd += list(job.extra_args)
    return cmd


def build_local_command(job: Job) -> List[str]:
    py = str(_venv_python_default())
    cmd: List[str] = [py, str(LOCAL_RUNNER)]
    # Local runner args are different
    if job.config:
        # local runner expects bare filename under local_train; but allow full path too
        cfg = Path(job.config)
        cfg_name = cfg.name
        cmd += ["--config", cfg_name]
    if job.max_train_samples is not None:
        cmd += ["--max-samples", str(job.max_train_samples)]
    if job.epochs is not None:
        cmd += ["--epochs", str(job.epochs)]
    if job.reinstall:
        cmd += ["--reinstall"]
    # NOTE: dataset path is controlled by the local config file
    cmd += list(job.extra_args)
    return cmd


def ensure_dirs(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def run_job(job: Job, dry_run: bool = False) -> Dict[str, Any]:
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    job_dir = DATA_OUT / job.name / ts
    ensure_dirs(job_dir)
    log_path = job_dir / "stdout.log"

    env = os.environ.copy()
    if job.hf_model_id:
        env.setdefault("HF_MODEL_ID", str(job.hf_model_id))

    if job.runner == "local":
        cmd = build_local_command(job)
    else:
        cmd = build_hf_command(job)

    result: Dict[str, Any] = {
        "name": job.name,
        "runner": job.runner,
        "cmd": cmd,
        "start_time": ts,
        "status": "planned" if dry_run else "running",
        "return_code": None,
        "log": str(log_path),
        "output_dir": None,
    }

    if dry_run:
        # Validate script presence and dataset paths
        missing: List[str] = []
        if job.runner == "local" and not LOCAL_RUNNER.exists():
            missing.append(str(LOCAL_RUNNER))
        if job.runner == "hf" and not HF_TRAIN_SCRIPT.exists():
            missing.append(str(HF_TRAIN_SCRIPT))
        if job.dataset:
            dp = Path(job.dataset)
            if not dp.exists():
                missing.append(str(dp))
        result["status"] = "validated" if not missing else "missing"
        if missing:
            result["missing"] = missing
        return result

    t0 = time.time()
    with log_path.open("w", encoding="utf-8") as logf:
        logf.write(f"$ {' '.join(str(x) for x in cmd)}\n\n")
        logf.flush()
        proc = subprocess.Popen(cmd, cwd=str(REPO_ROOT), env=env, stdout=logf, stderr=subprocess.STDOUT, text=True)
        rc = proc.wait()

    duration = time.time() - t0
    result["return_code"] = rc
    result["duration_sec"] = round(duration, 2)
    result["status"] = "succeeded" if rc == 0 else "failed"

    # Guess output directory if specified on job
    if job.save_dir:
        result["output_dir"] = str(Path(job.save_dir))

    # Persist last_run.json for job
    write_json(DATA_OUT / job.name / "last_run.json", result)
    return result


def collect_status(all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    summary = {
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "jobs": all_results,
    }
    write_json(DATA_OUT / "status.json", summary)
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description="AutoTrain orchestrator")
    ap.add_argument("--config", default=str(REPO_ROOT / "autotrain.yaml"), help="Path to autotrain.yaml")
    ap.add_argument("--job", default=None, help="Run only the named job")
    ap.add_argument("--dry-run", action="store_true", help="Validate and print commands; do not execute")
    ap.add_argument("--list", action="store_true", help="List configured jobs and exit")
    ap.add_argument("--reinstall", action="store_true", help="Force reinstall for local runner jobs (alias to job.reinstall)")
    args = ap.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.exists():
        raise SystemExit(f"Config not found: {cfg_path}")

    jobs = load_jobs(cfg_path)
    if args.list:
        print(json.dumps([j.__dict__ for j in jobs], indent=2))
        return

    # Filter to a specific job if requested
    if args.job:
        jobs = [j for j in jobs if j.name == args.job]
        if not jobs:
            raise SystemExit(f"Job not found in config: {args.job}")

    # Apply global flag
    if args.reinstall:
        for j in jobs:
            if j.runner == "local":
                j.reinstall = True

    ensure_dirs(DATA_OUT)
    results: List[Dict[str, Any]] = []
    for j in jobs:
        print(f"[autotrain] Running job: {j.name} (runner={j.runner})")
        res = run_job(j, dry_run=args.dry_run)
        results.append(res)
        # Make it easier to view what happens in CI/logs
        print(json.dumps(res, indent=2))

        # === DB Logging (only on successful real runs) ===
        if not args.dry_run and res.get("status") == "succeeded":
            log_info = log_lora_run_safe(j, res)
            if log_info.get("success"):
                print(f"[autotrain] Logged LoRA run to DB (run_id={log_info.get('run_id')})")
            elif log_info.get("skipped"):
                print("[autotrain] DB logging skipped (QAI_DB_CONN not set)")
            else:
                print(f"[autotrain] DB logging failed: {log_info.get('error')}")

    collect_status(results)
    # Non-zero exit if any job failed during non-dry run
    if not args.dry_run:
        failed = [r for r in results if r.get("status") == "failed"]
        if failed:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
