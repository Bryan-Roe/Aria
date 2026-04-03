"""AutoTrain Orchestrator — LoRA fine-tuning job runner.

Reads training jobs from a YAML config (default: config/training/autotrain.yaml),
validates the configuration, and optionally executes each job.

Usage:
    python scripts/autotrain.py --dry-run              # validate config only
    python scripts/autotrain.py --list                 # list jobs as JSON
    python scripts/autotrain.py --config path/to.yaml  # use custom config
    python scripts/autotrain.py --run                  # execute training jobs
    python scripts/autotrain.py --run --job NAME       # run a single job
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from .config_paths import resolve_config_path
except ImportError:
    from config_paths import resolve_config_path

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = resolve_config_path(REPO_ROOT, "autotrain")
DATA_OUT = REPO_ROOT / "data_out" / "autotrain"
STATUS_FILE = DATA_OUT / "status.json"

HF_TRAIN_SCRIPT = (
    REPO_ROOT / "AI" / "microsoft_phi-silica-3.6_v1" / "scripts" / "train_lora.py"
)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class TrainJob:
    name: str
    runner: str = "hf"
    category: str = "baseline"
    enabled: bool = True
    config: Optional[str] = None
    dataset: Optional[str] = None
    save_dir: Optional[str] = None
    epochs: int = 1
    max_train_samples: Optional[int] = None
    max_eval_samples: Optional[int] = None
    learning_rate: float = 2e-4
    lora_dropout: float = 0.1
    hf_model_id: Optional[str] = None
    device: str = "auto"
    extra_args: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------


def load_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"jobs": []}
    text = path.read_text()
    if yaml is not None:
        return yaml.safe_load(text) or {"jobs": []}
    # Minimal fallback: only supports basic YAML structure (name/runner keys)
    jobs: List[Dict[str, Any]] = []
    current: Dict[str, Any] = {}
    for line in text.splitlines():
        line = line.rstrip()
        if line.strip().startswith("- name:"):
            if current:
                jobs.append(current)
            current = {"name": line.strip().split(":", 1)[1].strip()}
        elif ":" in line and current:
            key, _, val = line.strip().partition(":")
            current[key.strip()] = val.strip()
    if current:
        jobs.append(current)
    return {"jobs": jobs}


def load_jobs(path: Path) -> List[TrainJob]:
    data = load_config(path)
    jobs: List[TrainJob] = []
    for raw in data.get("jobs", []):

        def _get(k, default=None):
            return raw.get(k, default)

        def _int(v):
            try:
                return int(v) if v is not None else None
            except Exception:
                return None

        def _float(v):
            try:
                return float(v) if v is not None else None
            except Exception:
                return None

        jobs.append(
            TrainJob(
                name=str(_get("name", "unnamed")),
                runner=str(_get("runner", "hf")),
                category=str(_get("category", "baseline")),
                enabled=bool(_get("enabled", True)),
                config=_get("config"),
                dataset=_get("dataset"),
                save_dir=_get("save_dir"),
                epochs=_int(_get("epochs")) or 1,
                max_train_samples=_int(_get("max_train_samples")),
                max_eval_samples=_int(_get("max_eval_samples")),
                learning_rate=_float(_get("learning_rate")) or 2e-4,
                lora_dropout=_float(_get("lora_dropout")) or 0.1,
                hf_model_id=_get("hf_model_id"),
                device=str(_get("device", "auto")),
                extra_args=_get("extra_args") or [],
            )
        )
    return jobs


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_job(job: TrainJob) -> Dict[str, Any]:
    missing: List[str] = []

    if not job.dataset:
        missing.append("dataset")
    elif not (REPO_ROOT / job.dataset).exists():
        missing.append(f"dataset path not found: {job.dataset}")

    if job.runner == "hf" and not HF_TRAIN_SCRIPT.exists():
        missing.append(
            f"train script not found: {HF_TRAIN_SCRIPT.relative_to(REPO_ROOT)}"
        )

    if job.config and not (REPO_ROOT / job.config).exists():
        missing.append(f"lora config not found: {job.config}")

    return {"status": "ok" if not missing else "missing", "missing": missing}


# ---------------------------------------------------------------------------
# Command building
# ---------------------------------------------------------------------------


def build_command(job: TrainJob) -> List[str]:
    py = sys.executable or "python"

    if job.runner == "local":
        # Placeholder for a local runner script
        local_script = REPO_ROOT / "scripts" / "run_local_lora_training.py"
        return [py, str(local_script), "--job", job.name]

    # Default: HF trainer
    cmd = [py, str(HF_TRAIN_SCRIPT)]
    if job.hf_model_id:
        cmd.extend(["--model-id", job.hf_model_id])
    if job.dataset:
        cmd.extend(["--dataset", job.dataset])
    if job.save_dir:
        cmd.extend(["--output-dir", str(REPO_ROOT / job.save_dir)])
    if job.config:
        cmd.extend(["--lora-config", job.config])
    cmd.extend(["--epochs", str(job.epochs)])
    if job.max_train_samples is not None:
        cmd.extend(["--max-train-samples", str(job.max_train_samples)])
    if job.max_eval_samples is not None:
        cmd.extend(["--max-eval-samples", str(job.max_eval_samples)])
    cmd.extend(["--learning-rate", str(job.learning_rate)])
    cmd.extend(["--lora-dropout", str(job.lora_dropout)])
    cmd.extend(["--device", job.device])
    if job.extra_args:
        cmd.extend(job.extra_args)
    return cmd


# ---------------------------------------------------------------------------
# Status helpers
# ---------------------------------------------------------------------------


def _write_status(payload: Dict[str, Any]) -> None:
    DATA_OUT.mkdir(parents=True, exist_ok=True)
    STATUS_FILE.write_text(json.dumps(payload, indent=2))


def _build_status(jobs_info: List[Dict[str, Any]]) -> Dict[str, Any]:
    succeeded = sum(1 for j in jobs_info if j.get("status") == "ok")
    failed = sum(1 for j in jobs_info if j.get("status") == "failed")
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_jobs": len(jobs_info),
        "succeeded": succeeded,
        "failed": failed,
        "running": 0,
        "avg_duration": None,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "jobs": jobs_info,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="AutoTrain — LoRA fine-tuning orchestrator"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help=f"Path to YAML config (default: {DEFAULT_CONFIG})",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Validate config only; do not execute"
    )
    parser.add_argument(
        "--list", action="store_true", help="Print jobs as JSON and exit"
    )
    parser.add_argument("--run", action="store_true", help="Execute training jobs")
    parser.add_argument("--job", metavar="NAME", help="Filter to a single job by name")

    args = parser.parse_args(argv)

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"⚠️  Config not found: {config_path} — using empty job list")
        jobs: List[TrainJob] = []
    else:
        jobs = load_jobs(config_path)

    if args.job:
        jobs = [j for j in jobs if j.name == args.job]
        if not jobs:
            print(f"❌ No job named '{args.job}' found in config")
            return 1

    if args.list:
        print(json.dumps([vars(j) for j in jobs], indent=2))
        return 0

    print(f"📋 AutoTrain — {len(jobs)} job(s) from {config_path}")

    jobs_info: List[Dict[str, Any]] = []
    for job in jobs:
        if not job.enabled:
            print(f"  [skip] {job.name} (disabled)")
            jobs_info.append({"name": job.name, "status": "skipped"})
            continue

        validation = validate_job(job)
        if validation["status"] != "ok":
            print(f"  [warn] {job.name}: missing {validation['missing']}")
        else:
            print(f"  [ok]   {job.name} (runner={job.runner}, epochs={job.epochs})")

        if args.dry_run:
            jobs_info.append(
                {
                    "name": job.name,
                    "status": "ok",
                    "validation": validation,
                    "dry_run": True,
                }
            )
            continue

        if args.run:
            cmd = build_command(job)
            print(f"  → {' '.join(cmd[:4])} ...")
            result = subprocess.run(cmd, cwd=str(REPO_ROOT))
            status = "ok" if result.returncode == 0 else "failed"
            jobs_info.append(
                {"name": job.name, "status": status, "returncode": result.returncode}
            )

    status_payload = _build_status(jobs_info)
    _write_status(status_payload)
    print(f"\n📄 Status written to {STATUS_FILE}")

    if not args.dry_run and not args.run and not args.list:
        # Default mode: just dry-run
        print("ℹ️  Use --dry-run to validate, --run to execute, --list to list jobs")

    return 0


if __name__ == "__main__":
    sys.exit(main())
