#!/usr/bin/env python
"""
Evaluation AutoRun Orchestrator

Automates AI model evaluation runs defined in a YAML config.
Built following the same pattern as autotrain.py and quantum_autorun.py.

Key features:
- Sequential evaluation job execution with validation
- Support for multiple model types: LoRA, Azure OpenAI, local, quantum
- Configurable metrics and output formats
- Dry-run validation with path checking
- Machine-readable JSON status output

Outputs:
- data_out/evaluation_autorun/<job_name>/<timestamp>/results.json
- data_out/evaluation_autorun/<job_name>/<timestamp>/stdout.log
- data_out/evaluation_autorun/<job_name>/last_run.json
- data_out/evaluation_autorun/status.json

Usage examples (PowerShell):
  python .\\scripts\\evaluation_autorun.py --dry-run
  python .\\scripts\\evaluation_autorun.py --job eval_smoke_test
  python .\\scripts\\evaluation_autorun.py --list
  python .\\scripts\\evaluation_autorun.py --job eval_lora_phi35_full
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml  # type: ignore
except Exception:
    raise SystemExit("pyyaml is required. Install with: pip install pyyaml")

# Optional DB logging (safe no-op if not configured)
try:  # noqa: SIM105
    from shared.db_logging import log_evaluation_run_safe  # type: ignore
except Exception:  # noqa: BLE001
    def log_evaluation_run_safe(*_a, **_kw):  # type: ignore
        return {"success": False, "skipped": True}


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_OUT = REPO_ROOT / "data_out" / "evaluation_autorun"

# Evaluation scripts by model type
EVAL_SCRIPTS = {
    "lora": REPO_ROOT / "scripts" / "evaluate_lora_model.py",
    "azure": REPO_ROOT / "scripts" / "evaluate_azure_model.py",
    "openai": REPO_ROOT / "scripts" / "evaluate_openai_model.py",
    "local": REPO_ROOT / "scripts" / "evaluate_local_model.py",
    "quantum": REPO_ROOT / "scripts" / "evaluate_quantum_model.py",
}

# Supported metrics by model type
SUPPORTED_METRICS = {
    "lora": ["accuracy", "bleu", "rouge", "response_time", "token_efficiency", "perplexity"],
    "azure": ["accuracy", "bleu", "rouge", "response_time", "cost_per_token"],
    "openai": ["accuracy", "bleu", "rouge", "response_time", "cost_per_token"],
    "local": ["response_time", "determinism", "rule_coverage"],
    "quantum": ["accuracy", "precision", "recall", "f1_score", "circuit_depth"],
}


@dataclass
class EvalJob:
    name: str
    enabled: bool = True
    model_type: str = "lora"  # "lora" | "azure" | "openai" | "local" | "quantum"
    model_path: Optional[str] = None
    dataset: Optional[str] = None
    max_samples: Optional[int] = None
    metrics: List[str] = field(default_factory=lambda: ["accuracy"])
    output_format: str = "json"  # "json" | "csv" | "markdown"
    save_results: bool = True
    batch_size: Optional[int] = None
    # Azure-specific
    azure_deployment: Optional[str] = None
    # Extra args passthrough
    extra_args: List[str] = field(default_factory=list)


def read_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_jobs(config_path: Path) -> List[EvalJob]:
    raw = read_yaml(config_path)
    jobs: List[EvalJob] = []
    for item in raw.get("jobs", []):
        j = EvalJob(
            name=str(item.get("name")),
            enabled=bool(item.get("enabled", True)),
            model_type=str(item.get("model_type", "lora")),
            model_path=item.get("model_path"),
            dataset=item.get("dataset"),
            max_samples=item.get("max_samples"),
            metrics=list(item.get("metrics", ["accuracy"])),
            output_format=str(item.get("output_format", "json")),
            save_results=bool(item.get("save_results", True)),
            batch_size=item.get("batch_size"),
            azure_deployment=item.get("azure_deployment"),
            extra_args=list(item.get("extra_args", [])),
        )
        if not j.name:
            raise ValueError("Every job requires a 'name'")
        if not j.dataset:
            raise ValueError(f"Job '{j.name}' requires a 'dataset'")
        jobs.append(j)
    return jobs


def _venv_python_default() -> Path:
    # Prefer repo root venv if it exists; else system python
    venv_python = REPO_ROOT / "venv" / "Scripts" / "python.exe"
    return venv_python if venv_python.exists() else Path(sys.executable)


def _venv_python_quantum() -> Path:
    # Use quantum-ai venv for quantum evaluations
    venv_python = REPO_ROOT / "quantum-ai" / "venv" / "Scripts" / "python.exe"
    return venv_python if venv_python.exists() else _venv_python_default()


def build_eval_command(job: EvalJob) -> List[str]:
    # Select appropriate venv based on model type
    if job.model_type == "quantum":
        py = str(_venv_python_quantum())
    else:
        py = str(_venv_python_default())

    # Get evaluation script for model type
    script = EVAL_SCRIPTS.get(job.model_type)
    if not script:
        raise ValueError(f"Unknown model_type: {job.model_type}")

    cmd: List[str] = [py, str(script)]

    # Common args
    cmd += ["--dataset", str(job.dataset)]
    if job.model_path:
        cmd += ["--model", str(job.model_path)]
    if job.max_samples is not None:
        cmd += ["--max-samples", str(job.max_samples)]
    if job.batch_size is not None:
        cmd += ["--batch-size", str(job.batch_size)]

    # Metrics
    for metric in job.metrics:
        cmd += ["--metric", metric]

    # Output format
    cmd += ["--output-format", job.output_format]

    # Azure-specific
    if job.model_type == "azure" and job.azure_deployment:
        cmd += ["--deployment", job.azure_deployment]

    # Results directory
    if job.save_results:
        results_dir = DATA_OUT / job.name
        cmd += ["--save-dir", str(results_dir)]

    # Pass through extra args
    cmd += list(job.extra_args)

    return cmd


def ensure_dirs(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def validate_job(job: EvalJob, parallel: bool = False) -> Dict[str, Any]:
    """Validate job configuration and paths without executing.

    Args:
        job: The evaluation job to validate
        parallel: If True, skip expensive checks for faster batch validation
    """
    missing: List[str] = []
    warnings: List[str] = []

    # Check evaluation script exists
    script = EVAL_SCRIPTS.get(job.model_type)
    if script and not script.exists():
        # Note: Scripts don't exist yet, so we'll create placeholder validation
        warnings.append(f"Evaluation script not yet created: {script}")

    # Check dataset exists
    if job.dataset:
        dataset_path = Path(job.dataset)
        if not dataset_path.exists():
            missing.append(str(dataset_path))

    # Check model path exists (if specified)
    if job.model_path:
        model_path = Path(job.model_path)
        if not model_path.exists():
            missing.append(str(model_path))

    # Validate metrics for model type
    supported = SUPPORTED_METRICS.get(job.model_type, [])
    unsupported = [m for m in job.metrics if m not in supported]
    if unsupported:
        warnings.append(
            f"Unsupported metrics for {job.model_type}: {unsupported}")

    # Check Azure credentials if needed
    if job.model_type == "azure":
        required_vars = ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT"]
        missing_vars = [v for v in required_vars if not os.getenv(v)]
        if missing_vars:
            warnings.append(f"Missing Azure env vars: {missing_vars}")

    result = {
        "status": "validated" if not missing else "missing",
        "missing": missing,
        "warnings": warnings,
    }
    return result


def run_job(job: EvalJob, dry_run: bool = False) -> Dict[str, Any]:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    job_dir = DATA_OUT / job.name / ts
    ensure_dirs(job_dir)
    log_path = job_dir / "stdout.log"
    results_path = job_dir / "results.json"

    cmd = build_eval_command(job)

    result: Dict[str, Any] = {
        "name": job.name,
        "model_type": job.model_type,
        "cmd": cmd,
        "start_time": ts,
        "status": "planned" if dry_run else "running",
        "return_code": None,
        "log": str(log_path),
        "results_file": str(results_path) if job.save_results else None,
        "metrics_computed": job.metrics,
    }

    if dry_run:
        # Validate without execution (fast mode for batch)
        validation = validate_job(job, parallel=True)
        result.update(validation)
        # Check for critical blockers
        if validation.get("missing"):
            result["blocker"] = True
        return result

    # Execute evaluation
    env = os.environ.copy()
    t0 = time.time()

    with log_path.open("w", encoding="utf-8") as logf:
        logf.write(f"$ {' '.join(str(x) for x in cmd)}\n\n")
        logf.flush()
        proc = subprocess.Popen(
            cmd,
            cwd=str(REPO_ROOT),
            env=env,
            stdout=logf,
            stderr=subprocess.STDOUT,
            text=True
        )
        rc = proc.wait()

    duration = time.time() - t0
    result["return_code"] = rc
    result["duration_sec"] = round(duration, 2)
    result["status"] = "succeeded" if rc == 0 else "failed"

    # Try to load results if saved
    if job.save_results and results_path.exists():
        try:
            with results_path.open("r") as f:
                eval_results = json.load(f)
                result["evaluation_summary"] = eval_results.get("summary", {})
        except Exception as e:
            result["evaluation_summary"] = {"error": str(e)}

    # Persist last_run.json
    write_json(DATA_OUT / job.name / "last_run.json", result)
    return result


def collect_status(all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    summary = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_jobs": len(all_results),
        "succeeded": sum(1 for r in all_results if r.get("status") == "succeeded"),
        "failed": sum(1 for r in all_results if r.get("status") == "failed"),
        "validated": sum(1 for r in all_results if r.get("status") == "validated"),
        "missing": sum(1 for r in all_results if r.get("status") == "missing"),
        "jobs": all_results,
    }
    write_json(DATA_OUT / "status.json", summary)
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description="Evaluation AutoRun orchestrator")
    # Default config lives under config/evaluation/ to match other orchestrators
    ap.add_argument("--config", default=str(REPO_ROOT / "config" / "evaluation" / "evaluation_autorun.yaml"),
                    help="Path to evaluation_autorun.yaml")
    ap.add_argument("--job", default=None, help="Run only the named job")
    ap.add_argument("--dry-run", action="store_true",
                    help="Validate and print commands; do not execute")
    ap.add_argument("--list", action="store_true",
                    help="List configured jobs and exit")
    args = ap.parse_args()

    # Initialize optional tracing (best-effort)
    try:
        from shared.tracing import init_tracing

        init_tracing(service_name="evaluation_autorun")
    except Exception as _e:  # pragma: no cover - non-fatal
        logging.debug(f"[tracing] init skipped in evaluation_autorun: {_e}")

    cfg_path = Path(args.config)
    if not cfg_path.exists():
        raise SystemExit(f"Config not found: {cfg_path}")

    jobs = load_jobs(cfg_path)

    # Filter to enabled jobs
    jobs = [j for j in jobs if j.enabled]

    if args.list:
        print(json.dumps([j.__dict__ for j in jobs], indent=2, default=str))
        return

    # Filter to specific job if requested
    if args.job:
        jobs = [j for j in jobs if j.name == args.job]
        if not jobs:
            raise SystemExit(f"Job not found in config: {args.job}")

    ensure_dirs(DATA_OUT)
    results: List[Dict[str, Any]] = []

    for idx, j in enumerate(jobs):
        progress = int(((idx + 1) / len(jobs)) * 100)
        print(
            f"[evaluation_autorun] [{progress}%] Job {idx + 1}/{len(jobs)}: {j.name} (model_type={j.model_type})")
        res = run_job(j, dry_run=args.dry_run)
        results.append(res)
        print(json.dumps(res, indent=2, default=str))

        # DB Logging (only on successful real runs)
        if not args.dry_run and res.get("status") == "succeeded":
            log_info = log_evaluation_run_safe(j, res)
            if log_info.get("success"):
                print(
                    f"[evaluation_autorun] Logged to DB (run_id={log_info.get('run_id')})")
            elif log_info.get("skipped"):
                print("[evaluation_autorun] DB logging skipped (not configured)")
            else:
                print(
                    f"[evaluation_autorun] DB logging failed: {log_info.get('error')}")

    status = collect_status(results)
    print(
        f"\n[evaluation_autorun] Summary: {status['succeeded']}/{status['total_jobs']} succeeded")

    # Non-zero exit if any job failed
    if not args.dry_run and status["failed"] > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
