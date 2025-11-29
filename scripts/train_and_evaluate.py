#!/usr/bin/env python
"""Train & Evaluate Combined Orchestrator

Runs selected AutoTrain jobs (LoRA fine-tuning) then corresponding evaluation
jobs (eval_<jobName>) defined in evaluation_autorun.yaml. Produces a consolidated
summary ranking models by a primary metric (accuracy → bleu → rouge fallback).

Usage (PowerShell):
  python .\\scripts\\train_and_evaluate.py --jobs phi35_mixed_chat_lr_low,phi35_mixed_chat_lr_high --dry-run
  python .\\scripts\\train_and_evaluate.py --jobs phi35_mixed_chat_lr_low
  python .\\scripts\\train_and_evaluate.py --all-variants   # run all newly added variant jobs

Flags:
    --dry-run         Validate commands only (no training/evaluation execution)
    --jobs            Comma-separated list of job names (must exist in autotrain.yaml)
    --all-variants    Shortcut to run all hyperparameter exploration jobs
    --stop-on-fail    Abort remaining jobs if any training fails
    --skip-existing   Skip training when adapter artifacts already exist (still runs evaluation)

Artifacts:
  data_out/train_and_evaluate/summary.json
  Reuses:
    data_out/autotrain/status.json
    data_out/evaluation_autorun/status.json
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any

REPO_ROOT = Path(__file__).resolve().parents[1]
AUTOTRAIN = REPO_ROOT / "scripts" / "autotrain.py"
EVAL_AUTORUN = REPO_ROOT / "scripts" / "evaluation_autorun.py"
TRAIN_AND_EVAL_OUT = REPO_ROOT / "data_out" / "train_and_evaluate"
AUTOTRAIN_CFG = REPO_ROOT / "autotrain.yaml"
EVAL_CFG = REPO_ROOT / "evaluation_autorun.yaml"

VARIANT_JOBS = [
    "phi35_mixed_chat_lr_low",
    "phi35_mixed_chat_lr_high",
    "phi35_mixed_chat_dropout_low",
    "phi35_mixed_chat_dropout_high",
]


def read_yaml(path: Path) -> Dict[str, Any]:
    import yaml  # type: ignore
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_autotrain_jobs() -> Dict[str, Dict[str, Any]]:
    raw = read_yaml(AUTOTRAIN_CFG)
    jobs = {}
    for j in raw.get("jobs", []):
        if j.get("name"):
            jobs[j["name"]] = j
    return jobs


def load_eval_jobs() -> Dict[str, Dict[str, Any]]:
    raw = read_yaml(EVAL_CFG)
    jobs = {}
    for j in raw.get("jobs", []):
        if j.get("name"):
            jobs[j["name"]] = j
    return jobs


def run_subprocess(cmd: List[str], dry_run: bool) -> Dict[str, Any]:
    if dry_run:
        return {"cmd": cmd, "status": "validated"}
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "cmd": cmd,
        "status": "succeeded" if proc.returncode == 0 else "failed",
        "return_code": proc.returncode,
        "stdout_tail": proc.stdout[-800:],
        "stderr_tail": proc.stderr[-400:],
    }


def extract_eval_metrics(status_json: Path) -> Dict[str, Dict[str, Any]]:
    if not status_json.exists():
        return {}
    try:
        data = json.loads(status_json.read_text(encoding="utf-8"))
        out: Dict[str, Dict[str, Any]] = {}
        for j in data.get("jobs", []):
            name = j.get("name")
            if not name:
                continue
            metrics = j.get("evaluation_summary") or {}
            out[name] = {
                "status": j.get("status"),
                "metrics": metrics,
            }
        return out
    except Exception as e:  # noqa: BLE001
        return {"error": {"message": str(e)}}


def choose_primary_metric(metrics: Dict[str, Any]) -> float | None:
    # Priority: accuracy > bleu > rouge > eval_perplexity (inverse) > None
    for key in ["accuracy", "bleu", "rouge"]:
        v = metrics.get(key)
        if isinstance(v, (int, float)):
            return float(v)
    if "eval_perplexity" in metrics and isinstance(metrics["eval_perplexity"], (int, float)):
        # lower perplexity is better; map to inverted score
        return 1.0 / float(metrics["eval_perplexity"])
    return None


def rank_models(eval_results: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    ranking: List[Dict[str, Any]] = []
    for name, info in eval_results.items():
        if info.get("status") != "succeeded":
            continue
        metrics = info.get("metrics", {})
        score = choose_primary_metric(metrics)
        ranking.append({"name": name, "score": score, "metrics": metrics})
    ranking.sort(key=lambda x: (x["score"] is None, -(x["score"] or 0.0)))
    return ranking


def main() -> None:
    ap = argparse.ArgumentParser(description="Train and evaluate selected AutoTrain jobs")
    ap.add_argument("--jobs", help="Comma-separated list of autotrain job names", default=None)
    ap.add_argument("--all-variants", action="store_true", help="Run all predefined variant jobs")
    ap.add_argument("--dry-run", action="store_true", help="Validate only (no execution)")
    ap.add_argument("--stop-on-fail", action="store_true", help="Abort remaining jobs if a training fails")
    ap.add_argument("--skip-existing", action="store_true", help="Skip training if output artifacts already exist")
    args = ap.parse_args()

    TRAIN_AND_EVAL_OUT.mkdir(parents=True, exist_ok=True)

    autotrain_jobs = load_autotrain_jobs()
    eval_jobs = load_eval_jobs()

    if args.all_variants:
        selected = VARIANT_JOBS
    elif args.jobs:
        selected = [j.strip() for j in args.jobs.split(",") if j.strip()]
    else:
        print("No jobs specified. Use --jobs or --all-variants.")
        sys.exit(1)

    missing = [j for j in selected if j not in autotrain_jobs]
    if missing:
        print(f"Missing jobs in autotrain.yaml: {missing}")
        sys.exit(1)

    training_results: Dict[str, Any] = {}
    evaluation_results: Dict[str, Any] = {}

    # Helper mapping function for training job -> evaluation job name (defined early for skip-existing logic)
    def map_training_to_eval(job_name: str) -> str:
        if job_name.startswith("phi35_mixed_chat_"):
            variant = job_name[len("phi35_mixed_chat_") :]
            if variant.startswith("dropout_"):
                variant = variant.replace("dropout_", "drop_")
            return f"eval_phi35_{variant}"
        if job_name.startswith("qwen25_3b_"):
            variant = job_name[len("qwen25_3b_") :]
            return f"eval_qwen25_{variant}"
        return f"eval_{job_name}"

    # Run training sequentially
    for job in selected:
        eval_job_name_for_skip = map_training_to_eval(job)
        output_dir = None
        if eval_job_name_for_skip in eval_jobs:
            model_path = eval_jobs[eval_job_name_for_skip].get("model_path")
            if model_path:
                output_dir = REPO_ROOT / model_path
        # Skip logic: adapter exists
        if args.skip_existing and output_dir and (output_dir / "lora_adapter").exists():
            # Check for any safetensors file to confirm completeness
            has_weights = any((output_dir / "lora_adapter").glob("*.safetensors"))
            if has_weights:
                print(f"[train_and_evaluate] Skipping existing training for {job} (artifacts found at {output_dir})")
                training_results[job] = {"status": "skipped_existing", "output_dir": str(output_dir)}
                continue
        cmd = [sys.executable, str(AUTOTRAIN), "--job", job]
        if args.dry_run:
            cmd.append("--dry-run")
        print(f"[train_and_evaluate] Training job: {job}")
        res = run_subprocess(cmd, dry_run=args.dry_run)
        training_results[job] = res
        if res["status"] != "succeeded" and not args.dry_run and args.stop_on_fail:
            print(f"[train_and_evaluate] Aborting due to failure in {job}")
            break

    # Run evaluations for successfully trained jobs
    for job in selected:
        t_res = training_results.get(job, {})
        if not args.dry_run and t_res.get("status") not in {"succeeded", "skipped_existing"}:
            continue
        eval_job_name = map_training_to_eval(job)
        if eval_job_name not in eval_jobs:
            print(f"[train_and_evaluate] No matching evaluation job for {job} (expected {eval_job_name})")
            continue
        cmd = [sys.executable, str(EVAL_AUTORUN), "--job", eval_job_name]
        if args.dry_run:
            cmd.append("--dry-run")
        print(f"[train_and_evaluate] Evaluation job: {eval_job_name}")
        res = run_subprocess(cmd, dry_run=args.dry_run)
        evaluation_results[eval_job_name] = res

    # After evaluation runs, parse evaluation status for metrics
    status_file = REPO_ROOT / "data_out" / "evaluation_autorun" / "status.json"
    eval_metrics = extract_eval_metrics(status_file)
    ranking = rank_models(eval_metrics)

    summary = {
        "jobs_trained": selected,
        "training": training_results,
        "evaluation": evaluation_results,
        "evaluation_metrics": eval_metrics,
        "ranking": ranking,
        "dry_run": args.dry_run,
    }
    (TRAIN_AND_EVAL_OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))

    # Non-zero exit if any training failed (in real run)
    if not args.dry_run:
        failed = [j for j, r in training_results.items() if r.get("status") == "failed"]
        if failed:
            print(f"[train_and_evaluate] Training failures: {failed}")
            sys.exit(1)


if __name__ == "__main__":
    main()
