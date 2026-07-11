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
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
    REPO_ROOT / "ai-projects" / "lora-training" / "microsoft_phi-silica-3.6_v1" / "scripts" / "train_lora.py"
)

__all__ = ["load_config", "load_jobs", "validate_job", "build_command", "main"]


__all__ = ["load_config", "load_jobs", "validate_job", "build_command", "main"]

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class TrainJob:
    name: str
    runner: str = "hf"
    category: str = "baseline"
    enabled: bool = True
    config: str | None = None
    dataset: str | None = None
    save_dir: str | None = None
    epochs: int = 1
    max_train_samples: int | None = None
    max_eval_samples: int | None = None
    learning_rate: float = 2e-4
    lora_dropout: float = 0.1
    hf_model_id: str | None = None
    device: str = "auto"
    extra_args: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------


def _parse_bool(value: Any, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, int | float):
        return bool(value)
    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"true", "yes", "y", "1", "on"}:
            return True
        if v in {"false", "no", "n", "0", "off"}:
            return False
    return default


def _parse_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        v = value.strip()
        if not v:
            return None
        try:
            return int(v)
        except ValueError:
            return None
    return None


def _parse_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        v = value.strip()
        if not v:
            return None
        try:
            return float(v)
        except ValueError:
            return None
    return None


def _parse_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        s = value.strip()
        return s or None
    return str(value)


def _parse_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            s = _parse_str(item)
            if s:
                out.append(s)
        return out
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return []
        return shlex.split(s)
    return [str(value)]


def _norm_relpath(value: str | None) -> str | None:
    if not value:
        return None

    p = Path(value)
    if p.is_absolute():
        return None

    norm = os.path.normpath(value)
    if norm.startswith("..") or norm == "..":
        return None
    return norm


__all__ = ["load_config", "load_jobs", "validate_job", "build_command", "main"]


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"jobs": []}

    text = path.read_text(encoding="utf-8")

    if yaml is not None:
        data = yaml.safe_load(text) or {}
        if not isinstance(data, dict):
            return {"jobs": []}
        jobs = data.get("jobs", [])
        if not isinstance(jobs, list):
            return {"jobs": []}
        data.setdefault("jobs", jobs)
        return data

    jobs: list[dict[str, Any]] = []
    current: dict[str, Any] = {}

    for line in text.splitlines():
        line = line.rstrip()
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("- name:"):
            if current:
                jobs.append(current)
            current = {"name": stripped.split(":", 1)[1].strip()}
            continue

        if ":" in stripped and current:
            key, _, val = stripped.partition(":")
            current[key.strip()] = val.strip()

    if current:
        jobs.append(current)

    return {"jobs": jobs}


def load_jobs(path: Path) -> list[TrainJob]:
    data = load_config(path)
    raw_jobs = data.get("jobs", [])

    if not isinstance(raw_jobs, list):
        return []

    jobs: list[TrainJob] = []
    for raw in raw_jobs:
        if not isinstance(raw, dict):
            continue

        enabled = _parse_bool(raw.get("enabled"), default=True)
        epochs = _parse_int(raw.get("epochs")) or 1
        if epochs < 1:
            epochs = 1

        learning_rate = _parse_float(raw.get("learning_rate")) or 2e-4
        if learning_rate <= 0:
            learning_rate = 2e-4

        lora_dropout = _parse_float(raw.get("lora_dropout")) or 0.1
        if lora_dropout < 0:
            lora_dropout = 0.0
        if lora_dropout > 1:
            lora_dropout = 1.0

        jobs.append(
            TrainJob(
                name=str(raw.get("name", "unnamed")),
                runner=str(raw.get("runner", "hf")),
                category=str(raw.get("category", "baseline")),
                enabled=enabled,
                config=_norm_relpath(_parse_str(raw.get("config"))),
                dataset=_norm_relpath(_parse_str(raw.get("dataset"))),
                save_dir=_norm_relpath(_parse_str(raw.get("save_dir"))),
                epochs=epochs,
                max_train_samples=_parse_int(raw.get("max_train_samples")),
                max_eval_samples=_parse_int(raw.get("max_eval_samples")),
                learning_rate=learning_rate,
                lora_dropout=lora_dropout,
                hf_model_id=_parse_str(raw.get("hf_model_id")),
                device=str(raw.get("device", "auto")),
                extra_args=_parse_str_list(raw.get("extra_args")),
            )
        )

    return jobs


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_job(job: TrainJob) -> dict[str, Any]:
    missing: list[str] = []

    if not job.dataset:
        missing.append("dataset")
    else:
        dataset_path = REPO_ROOT / job.dataset
        if not dataset_path.exists():
            missing.append(f"dataset path not found: {job.dataset}")

    if job.runner == "hf":
        if not HF_TRAIN_SCRIPT.exists():
            missing.append(f"train script not found: {HF_TRAIN_SCRIPT.relative_to(REPO_ROOT)}")

    if job.config:
        config_path = REPO_ROOT / job.config
        if not config_path.exists():
            missing.append(f"lora config not found: {job.config}")

    if job.save_dir:
        out_dir = REPO_ROOT / job.save_dir
        if out_dir.exists() and not out_dir.is_dir():
            missing.append(f"save_dir is not a directory: {job.save_dir}")

    return {"status": "ok" if not missing else "missing", "missing": missing}


# ---------------------------------------------------------------------------
# Command building
# ---------------------------------------------------------------------------


def build_command(job: TrainJob) -> list[str]:
    py = sys.executable or "python"

    if job.runner == "local":
        local_script = REPO_ROOT / "scripts" / "run_local_lora_training.py"
        return [py, str(local_script), "--job", job.name]

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


def _write_status(payload: dict[str, Any]) -> None:
    DATA_OUT.mkdir(parents=True, exist_ok=True)
    STATUS_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _build_status(jobs_info: list[dict[str, Any]]) -> dict[str, Any]:
    succeeded = sum(1 for j in jobs_info if j.get("status") == "ok")
    failed = sum(1 for j in jobs_info if j.get("status") == "failed")
    skipped = sum(1 for j in jobs_info if j.get("status") == "skipped")
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_jobs": len(jobs_info),
        "succeeded": succeeded,
        "failed": failed,
        "skipped": skipped,
        "running": 0,
        "avg_duration": None,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "jobs": jobs_info,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AutoTrain — LoRA fine-tuning orchestrator")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help=f"Path to YAML config (default: {DEFAULT_CONFIG})",
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate config only; do not execute")
    parser.add_argument("--list", action="store_true", help="Print jobs as JSON and exit")
    parser.add_argument("--run", action="store_true", help="Execute training jobs")
    parser.add_argument("--job", metavar="NAME", help="Filter to a single job by name")

    args = parser.parse_args(argv)

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Config not found: {config_path} — using empty job list", file=sys.stderr)
        jobs: list[TrainJob] = []
    else:
        jobs = load_jobs(config_path)

    if args.job:
        jobs = [j for j in jobs if j.name == args.job]
        if not jobs:
            print(f"No job named '{args.job}' found in config", file=sys.stderr)
            return 1

    if args.list:
        print(json.dumps([vars(j) for j in jobs], indent=2, ensure_ascii=False))
        return 0

    if not (args.dry_run or args.run):
        args.dry_run = True

    print(f"AutoTrain — {len(jobs)} job(s) from {config_path}")

    jobs_info: list[dict[str, Any]] = []
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

        if args.dry_run and not args.run:
            jobs_info.append(
                {
                    "name": job.name,
                    "status": "ok" if validation["status"] == "ok" else "missing",
                    "validation": validation,
                    "dry_run": True,
                }
            )
            continue

        cmd = build_command(job)
        print(f"  → {shlex.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                cwd=str(REPO_ROOT),
                check=False,
            )
        except OSError as e:
            jobs_info.append({"name": job.name, "status": "failed", "error": str(e), "returncode": None})
            continue

        status = "ok" if result.returncode == 0 else "failed"
        jobs_info.append({"name": job.name, "status": status, "returncode": result.returncode})

    status_payload = _build_status(jobs_info)
    _write_status(status_payload)
    print(f"\nStatus written to {STATUS_FILE}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
