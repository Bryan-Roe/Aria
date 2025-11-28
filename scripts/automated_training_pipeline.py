#!/usr/bin/env python
"""
Automated Multi-Model Training & Azure ML Pipeline

Convenience wrapper to:
  1. Optionally generate synthetic data via auto_data_train.py (phi + qwen)
  2. Run sequential quick ultrafast LoRA trainings for specified models
  3. Produce an aggregated summary file with run IDs, rankings & synthetic entries
  4. Emit Azure ML command job spec (optional) for remote execution

Why this script?
  - Single entry point for frequent iterative tuning
  - Avoid manual flag repetition
  - Ready for future cron / scheduler integration (Task Scheduler / CI)
  - Provides Azure ML job spec emission without direct submission

Usage Examples (PowerShell):
  # Quick both models with evaluation
  python .\scripts\automated_training_pipeline.py --quick

  # Phi only, 300 samples, cleanup checkpoints, rank by post perplexity
  python .\scripts\automated_training_pipeline.py --models phi --samples 300 --cleanup --ranking-metric post_perplexity

  # Qwen only, skip evaluation
  python .\scripts\automated_training_pipeline.py --models qwen --no-eval

  # Generate data only (no training)
  python .\scripts\automated_training_pipeline.py --generate-only --samples 200

  # Emit Azure ML job spec (no training)
  python .\scripts\automated_training_pipeline.py --azure-ml-spec --quick --models phi,qwen --generate-only

Summary Output:
  data_out/automated_training/summary_<timestamp>.json
Azure ML Spec Output:
  .azureml/job_<run_label>.yaml
"""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SUMMARY_DIR = REPO_ROOT / "data_out" / "automated_training"
AUTO_DATA_SCRIPT = REPO_ROOT / "scripts" / "auto_data_train.py"
STATUS_FILE = REPO_ROOT / "data_out" / "parallel_training" / "status.json"

DEFAULT_MIN_SAMPLES_GUARD = 50


def run_cmd(cmd: List[str]) -> int:
    print(f"\n$ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=str(REPO_ROOT)).returncode


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Automated multi-model LoRA training & Azure ML wrapper")
    # Core workflow
    ap.add_argument("--quick", action="store_true", help="Use quick mode (100 samples) for synthetic generation")
    ap.add_argument("--samples", type=int, default=None, help="Total synthetic samples to generate (overrides --quick)")
    ap.add_argument("--models", type=str, default="phi,qwen", help="Comma list of models: phi, qwen")
    ap.add_argument("--no-eval", action="store_true", help="Disable evaluation and sample generation")
    ap.add_argument("--cleanup", action="store_true", help="Cleanup intermediate checkpoints post-run")
    ap.add_argument("--ranking-metric", choices=["perplexity_improvement", "post_perplexity", "diversity_avg", "combined_improvement", "distinct_diversity"], default="perplexity_improvement", help="Ranking metric used during status aggregation (distinct_diversity alias of diversity_avg)")
    ap.add_argument("--min-train-samples", type=int, default=DEFAULT_MIN_SAMPLES_GUARD, help="Skip training if train samples below threshold")
    ap.add_argument("--generate-only", action="store_true", help="Only generate data (no training)")
    ap.add_argument("--output-name", type=str, default=None, help="Optional run name suffix")
    # Azure ML integration hooks
    ap.add_argument("--azure-ml-spec", action="store_true", help="Emit Azure ML command job specification YAML (no submission)")
    ap.add_argument("--azure-ml-compute", type=str, default="cpu-cluster", help="Azure ML compute target name (default: cpu-cluster)")
    ap.add_argument("--azure-ml-experiment", type=str, default="lora-autotrain", help="Experiment name for Azure ML job")
    ap.add_argument("--azure-ml-env-name", type=str, default="auto-training-env", help="Azure ML environment name")
    ap.add_argument("--azure-ml-image", type=str, default="mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu20.04", help="Base container image for AML environment")
    ap.add_argument("--force-azure-ml", action="store_true", help="Overwrite existing Azure ML spec/env files if present")
    return ap.parse_args()


def build_base_flags(args: argparse.Namespace) -> List[str]:
    flags: List[str] = []
    if args.quick and not args.samples:
        flags.append("--quick")
    if args.samples:
        flags += ["--samples", str(args.samples)]
    flags += ["--min-train-samples", str(args.min_train_samples)]
    if getattr(args, "no_eval", False):
        flags.append("--no-eval")
    if args.cleanup:
        flags.append("--cleanup")
    if args.ranking_metric:
        flags += ["--ranking-metric", args.ranking_metric]
    return flags


def _count_dataset_samples(ds_root: Path) -> Dict[str, int]:
    """Count samples in dataset files efficiently using binary mode.
    
    Uses buffered binary read for faster line counting compared to text mode.
    """
    train = test = 0
    if ds_root.is_dir():
        for name, key in [("train.jsonl", "train"), ("train.json", "train"), ("test.jsonl", "test"), ("test.json", "test")]:
            f = ds_root / name
            if f.exists():
                # Use binary mode with buffer for efficient line counting
                count = 0
                with f.open("rb") as fh:
                    buf_size = 65536
                    read_f = fh.read
                    buf = read_f(buf_size)
                    while buf:
                        count += buf.count(b'\n')
                        buf = read_f(buf_size)
                if key == "train":
                    train += count
                else:
                    test += count
    return {"train": train, "test": test}


def emit_azure_ml_spec(args: argparse.Namespace, selected_models: List[str], run_label: str, base_flags: List[str]) -> Path:
    """Generate Azure ML command job spec + environment.yml (no submission)."""
    aml_dir = REPO_ROOT / ".azureml"
    aml_dir.mkdir(exist_ok=True)
    env_file = aml_dir / "environment.yml"
    job_file = aml_dir / f"job_{run_label}.yaml"
    if args.force_azure_ml or not env_file.exists():
        # Valid conda environment file (channels before dependencies)
        env_contents = f"""name: {args.azure_ml_env_name}
channels:
  - defaults
  - conda-forge
dependencies:
  - python=3.11
  - pip
  - pip:
    - -r requirements.txt
"""
        with env_file.open("w", encoding="utf-8") as ef:
            ef.write(env_contents)
    # Build remote command
    cmd_parts = ["python", "scripts/automated_training_pipeline.py", "--models", ",".join(selected_models)] + base_flags
    if args.generate_only and "--generate-only" not in cmd_parts:
        cmd_parts.append("--generate-only")
    # Exclude --azure-ml-spec flag to avoid nested spec emission
    command_line = " ".join(cmd_parts)
    # Emit YAML job spec
    job_yaml_str = (
        """$schema: https://azuremlschemas.azureedge.net/latest/commandJob.schema.json
command: {command_line}
code: .
display_name: automated-training-{run_label}
experiment_name: {experiment}
compute: azureml:{compute}
environment:
  image: {image}
  conda_file: {conda_file}
  name: {env_name}
resources:
  instance_count: 1
identity:
  type: managed
description: Auto-generated Azure ML job spec for multi-model LoRA training wrapper
tags:
  generator: automated_training_pipeline
  models: {models}
"""
    ).format(
        command_line=command_line,
        run_label=run_label,
        experiment=args.azure_ml_experiment,
        compute=args.azure_ml_compute,
        image=args.azure_ml_image,
        conda_file=env_file.name,
        env_name=args.azure_ml_env_name,
        models=",".join(selected_models),
    )
    with job_file.open("w", encoding="utf-8") as jf:
        jf.write(job_yaml_str)
    # Placeholder .env for user to fill in Azure ML workspace specifics
    env_placeholder = REPO_ROOT / ".env"
    if not env_placeholder.exists():
        with env_placeholder.open("w", encoding="utf-8") as pf:
            pf.write(
                "AZURE_ML_SUBSCRIPTION_ID=__REPLACE__\n"
                "AZURE_ML_RESOURCE_GROUP=__REPLACE__\n"
                "AZURE_ML_WORKSPACE=__REPLACE__\n"
                f"AZURE_ML_COMPUTE_TARGET={args.azure_ml_compute}\n"
                f"AZURE_ML_EXPERIMENT_NAME={args.azure_ml_experiment}\n"
                f"AZURE_ML_ENV_NAME={args.azure_ml_env_name}\n"
            )
    else:
        # Append missing Azure ML placeholders if .env already exists
        try:
            existing_env = env_placeholder.read_text(encoding="utf-8")
            additions = []
            placeholder_map = {
                "AZURE_ML_SUBSCRIPTION_ID": "__REPLACE__",
                "AZURE_ML_RESOURCE_GROUP": "__REPLACE__",
                "AZURE_ML_WORKSPACE": "__REPLACE__",
                "AZURE_ML_COMPUTE_TARGET": args.azure_ml_compute,
                "AZURE_ML_EXPERIMENT_NAME": args.azure_ml_experiment,
                "AZURE_ML_ENV_NAME": args.azure_ml_env_name,
            }
            for key, val in placeholder_map.items():
                if f"{key}=" not in existing_env:
                    additions.append(f"{key}={val}")
            if additions:
                with env_placeholder.open("a", encoding="utf-8") as pf:
                    pf.write("\n# Azure ML placeholders added automatically\n" + "\n".join(additions) + "\n")
        except Exception:
            pass
    print(f"[azureml] Spec written: {job_file} (env: {env_file})")
    return job_file


def main() -> int:
    args = parse_args()
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    run_label = args.output_name or f"multi_{timestamp}"

    selected_models = [m.strip() for m in args.models.split(',') if m.strip()]
    valid_models = {"phi", "qwen", "tinyllama"}
    for m in selected_models:
        if m not in valid_models:
            print(f"Invalid model specified: {m}. Valid: phi,qwen,tinyllama")
            return 1

    base_flags = build_base_flags(args)
    all_runs: List[Dict[str, Any]] = []
    try:
        with STATUS_FILE.open("r", encoding="utf-8") as f:
            baseline_status = json.load(f)
        baseline_ids = [r.get("run_id") for r in baseline_status.get("runs", []) if r.get("run_id")]
    except Exception:
        baseline_ids = []

    for model in selected_models:
        print("\n" + "=" * 70)
        print(f"  AUTOMATED MODEL RUN: {model}")
        print("=" * 70)
        cmd = [sys.executable, str(AUTO_DATA_SCRIPT), "--model", model, "--no-repo"] + base_flags
        if args.generate_only:
            cmd += ["--train-mode", "none"]
        rc = run_cmd(cmd)
        if rc != 0:
            print(f"[wrapper] Warning: model run for {model} exited with code {rc}")
        post_ids: List[str] = []
        latest_run = None
        if STATUS_FILE.exists():
            try:
                with STATUS_FILE.open("r", encoding="utf-8") as f:
                    status_obj = json.load(f)
                runs_list = status_obj.get("runs", [])
                post_ids = [r.get("run_id") for r in runs_list if r.get("run_id")]
                if runs_list:
                    latest_run = runs_list[-1]
            except Exception as e:
                print(f"[wrapper] Status parse error: {e}")
        new_run_detected = bool(set(post_ids) - set(baseline_ids))
        if args.generate_only or not new_run_detected:
            ds_path = REPO_ROOT / "datasets" / "chat" / "auto_generated"
            counts = _count_dataset_samples(ds_path)
            synthetic_job = {
                "name": f"{model}_generate_only_{timestamp}",
                "status": "skipped",
                "reason": "generate_only_mode",
                "dataset_path": str(ds_path),
                "dataset_train_samples": counts["train"],
                "dataset_test_samples": counts["test"],
            }
            all_runs.append({
                "model": model,
                "run_id": None,
                "jobs": [synthetic_job],
                "ranking": None,
                "timestamp": timestamp,
                "training_skipped": True,
            })
        else:
            all_runs.append({
                "model": model,
                "run_id": latest_run.get("run_id"),
                "jobs": latest_run.get("jobs"),
                "ranking": latest_run.get("job_ranking"),
                "timestamp": latest_run.get("timestamp"),
                "training_skipped": False,
            })
        baseline_ids = post_ids

    summary_path = SUMMARY_DIR / f"summary_{run_label}.json"
    # Extract per-model evaluation metrics (graceful if missing)
    model_metrics: List[Dict[str, Any]] = []
    for r in all_runs:
        if r.get("training_skipped"):
            continue
        jobs = r.get("jobs") or []
        # Each run here corresponds to a single job produced by auto_data_train
        for job in jobs:
            eval_block = (job or {}).get("evaluation") or {}
            diversity_block = (eval_block.get("diversity") or {})
            if not eval_block:
                continue
            entry = {
                "model": r.get("model"),
                "run_id": r.get("run_id"),
                "pre_perplexity": eval_block.get("pre_eval_perplexity"),
                "post_perplexity": eval_block.get("post_eval_perplexity"),
                "distinct_1": diversity_block.get("distinct_1"),
                "distinct_2": diversity_block.get("distinct_2"),
            }
            # Compute diversity avg if both present
            d1 = entry["distinct_1"]
            d2 = entry["distinct_2"]
            if isinstance(d1, (int, float)) and isinstance(d2, (int, float)):
                entry["diversity_avg"] = (d1 + d2) / 2.0
            # Derive perplexity improvement if possible
            pre = entry["pre_perplexity"]
            post = entry["post_perplexity"]
            if isinstance(pre, (int, float)) and isinstance(post, (int, float)) and pre > 0:
                entry["perplexity_improvement"] = (pre - post) / pre
            model_metrics.append(entry)

    summary_doc = {
        "run_label": run_label,
        "created_at": timestamp,
        "models": selected_models,
        "no_eval": args.no_eval,
        "cleanup": args.cleanup,
        "ranking_metric": args.ranking_metric,
        "generate_only": args.generate_only,
        "runs": all_runs,
        "model_metrics": model_metrics or None,
        "azure_ml_spec_emitted": args.azure_ml_spec,
        "best_model": None,
    }

    def _select_best_model(metrics: List[Dict[str, Any]], ranking_metric: str) -> Dict[str, Any] | None:
        if not metrics:
            return None
        # Helper extraction with safe defaults
        def diversity(entry: Dict[str, Any]) -> float | None:
            return entry.get("diversity_avg")
        def improvement(entry: Dict[str, Any]) -> float | None:
            return entry.get("perplexity_improvement")
        def post_ppl(entry: Dict[str, Any]) -> float | None:
            return entry.get("post_perplexity")

        ranking = ranking_metric
        filtered = [m for m in metrics if post_ppl(m) is not None]
        if ranking in ("perplexity_improvement", "combined_improvement"):
            # If combined_improvement requested but missing diversity, treat div=0
            if ranking == "combined_improvement":
                for m in filtered:
                    div = diversity(m) or 0.0
                    imp = improvement(m) or 0.0
                    m["combined_improvement"] = 0.7 * imp + 0.3 * div
                filtered = [m for m in filtered if m.get("combined_improvement") is not None]
                key = lambda x: x.get("combined_improvement", -1)
            else:
                filtered = [m for m in filtered if improvement(m) is not None]
                key = lambda x: improvement(x)
            candidate = max(filtered, key=key) if filtered else None
            if candidate:
                return {
                    "model": candidate.get("model"),
                    "run_id": candidate.get("run_id"),
                    "metric": ranking,
                    "score": candidate.get(ranking) if ranking == "combined_improvement" else improvement(candidate),
                    "post_perplexity": post_ppl(candidate),
                    "pre_perplexity": candidate.get("pre_perplexity"),
                    "diversity_avg": diversity(candidate),
                }
            return None
        elif ranking in ("diversity_avg", "distinct_diversity"):
            filtered = [m for m in metrics if diversity(m) is not None]
            candidate = max(filtered, key=lambda x: diversity(x)) if filtered else None
            if candidate:
                return {
                    "model": candidate.get("model"),
                    "run_id": candidate.get("run_id"),
                    "metric": ranking,
                    "score": diversity(candidate),
                    "post_perplexity": post_ppl(candidate),
                    "pre_perplexity": candidate.get("pre_perplexity"),
                    "perplexity_improvement": improvement(candidate),
                }
            return None
        elif ranking == "post_perplexity":
            candidate = min(filtered, key=lambda x: post_ppl(x)) if filtered else None
            if candidate:
                return {
                    "model": candidate.get("model"),
                    "run_id": candidate.get("run_id"),
                    "metric": ranking,
                    "score": post_ppl(candidate),
                    "pre_perplexity": candidate.get("pre_perplexity"),
                    "perplexity_improvement": improvement(candidate),
                    "diversity_avg": diversity(candidate),
                }
            return None
        # Fallback unknown metric: choose lowest post perplexity
        candidate = min(filtered, key=lambda x: post_ppl(x)) if filtered else None
        if candidate:
            return {
                "model": candidate.get("model"),
                "run_id": candidate.get("run_id"),
                "metric": "post_perplexity_fallback",
                "score": post_ppl(candidate),
                "pre_perplexity": candidate.get("pre_perplexity"),
                "perplexity_improvement": improvement(candidate),
                "diversity_avg": diversity(candidate),
            }
        return None

    summary_doc["best_model"] = _select_best_model(model_metrics, args.ranking_metric)
    with summary_path.open("w", encoding="utf-8") as sf:
        json.dump(summary_doc, sf, indent=2)
    print(f"\n[wrapper] Summary written: {summary_path}")
    if args.azure_ml_spec:
        emit_azure_ml_spec(args, selected_models, run_label, base_flags)
    print(f"[wrapper] Models processed: {', '.join(selected_models)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
