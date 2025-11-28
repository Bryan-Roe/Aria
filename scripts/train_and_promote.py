#!/usr/bin/env python
"""
Automated Training & Promotion Pipeline

Combines training, evaluation, and promotion into a single automated workflow.

Features:
- Train model with configurable hyperparameters
- Automatic evaluation with metrics
- Best model promotion to deployed_models/
- Optional notification/webhook on completion
- Comprehensive logging and status tracking

Usage:
    python scripts/train_and_promote.py --quick
    python scripts/train_and_promote.py --dataset datasets/chat/mixed_chat --epochs 3
    python scripts/train_and_promote.py --config training_config.yaml --auto-promote
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_OUT = REPO_ROOT / "data_out" / "train_and_promote"


def log(msg: str, level: str = "INFO"):
    """Log message with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")


def run_training(
    dataset: str,
    max_train_samples: int,
    max_eval_samples: int,
    epochs: int,
    device: str = "auto",
    additional_args: List[str] = None
) -> Dict[str, Any]:
    """Run LoRA training."""
    log("Starting training phase...")
    
    cmd = [
        sys.executable,
        str(REPO_ROOT / "AI" / "microsoft_phi-silica-3.6_v1" / "scripts" / "train_lora.py"),
        "--dataset", dataset,
        "--max-train-samples", str(max_train_samples),
        "--max-eval-samples", str(max_eval_samples),
        "--epochs", str(epochs),
        "--device", device
    ]
    
    if additional_args:
        cmd.extend(additional_args)
    
    log(f"Training command: {' '.join(cmd)}")
    
    t0 = time.time()
    result = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    duration = time.time() - t0
    
    if result.returncode == 0:
        log(f"Training succeeded in {duration:.1f}s", "SUCCESS")
        return {
            "status": "success",
            "duration": duration,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    else:
        log(f"Training failed after {duration:.1f}s", "ERROR")
        log(f"Error: {result.stderr}", "ERROR")
        return {
            "status": "failed",
            "duration": duration,
            "error": result.stderr
        }


def run_evaluation_and_promotion(
    max_workers: int = 1,
    promote: bool = True,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Run batch evaluation and optional promotion."""
    log("Starting evaluation phase...")
    
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "batch_evaluator.py"),
        "--scan-models",
        "--evaluate-all",
        "--max-workers", str(max_workers)
    ]
    
    if promote:
        cmd.append("--promote-best")
    
    if dry_run:
        cmd.append("--dry-run")
    
    t0 = time.time()
    result = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    duration = time.time() - t0
    
    if result.returncode == 0:
        log(f"Evaluation succeeded in {duration:.1f}s", "SUCCESS")
        
        # Parse results
        results_dir = REPO_ROOT / "data_out" / "batch_evaluator"
        latest_results = sorted(results_dir.glob("results_*.json"))[-1] if results_dir.exists() else None
        
        eval_data = {}
        if latest_results:
            with latest_results.open("r") as f:
                eval_data = json.load(f)
        
        return {
            "status": "success",
            "duration": duration,
            "stdout": result.stdout,
            "results": eval_data
        }
    else:
        log(f"Evaluation failed after {duration:.1f}s", "ERROR")
        return {
            "status": "failed",
            "duration": duration,
            "error": result.stderr
        }


def save_pipeline_report(
    training_result: Dict,
    eval_result: Dict,
    config: Dict,
    output_file: Path
):
    """Save comprehensive pipeline report."""
    report = {
        "pipeline_run": {
            "started_at": datetime.now().isoformat(),
            "config": config
        },
        "training": training_result,
        "evaluation": eval_result,
        "summary": {
            "training_status": training_result.get("status"),
            "evaluation_status": eval_result.get("status"),
            "total_duration": training_result.get("duration", 0) + eval_result.get("duration", 0),
            "best_model": eval_result.get("results", {}).get("best_model"),
            "promotion_successful": "promoted_at" in eval_result.get("results", {})
        }
    }
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w") as f:
        json.dump(report, f, indent=2)
    
    log(f"Pipeline report saved to: {output_file}")


def send_notification(webhook_url: str, report: Dict):
    """Send completion notification (optional)."""
    try:
        import requests
        
        summary = report["summary"]
        message = f"""
Training Pipeline Complete

Training: {summary['training_status']}
Evaluation: {summary['evaluation_status']}
Duration: {summary['total_duration']:.1f}s
Best Model: {summary.get('best_model', 'N/A')}
"""
        
        response = requests.post(webhook_url, json={"text": message})
        log(f"Notification sent: {response.status_code}")
    except Exception as e:
        log(f"Notification failed: {e}", "WARNING")


def main():
    ap = argparse.ArgumentParser(description="Automated Training & Promotion Pipeline")
    
    # Quick presets
    ap.add_argument("--quick", action="store_true", help="Quick training (64 samples, 1 epoch)")
    ap.add_argument("--standard", action="store_true", help="Standard training (500 samples, 3 epochs)")
    ap.add_argument("--full", action="store_true", help="Full training (all samples, 5 epochs)")
    
    # Training config
    ap.add_argument("--dataset", default="datasets/chat/mixed_chat", help="Training dataset path")
    ap.add_argument("--max-train-samples", type=int, help="Max training samples")
    ap.add_argument("--max-eval-samples", type=int, help="Max evaluation samples")
    ap.add_argument("--epochs", type=int, help="Training epochs")
    ap.add_argument("--device", default="auto", help="Device (auto, cuda, cpu)")
    ap.add_argument("--learning-rate", type=float, help="Learning rate")
    ap.add_argument("--batch-size", type=int, help="Batch size")
    
    # Evaluation config
    ap.add_argument("--skip-eval", action="store_true", help="Skip evaluation phase")
    ap.add_argument("--auto-promote", action="store_true", help="Automatically promote best model")
    ap.add_argument("--max-workers", type=int, default=1, help="Parallel evaluation workers")
    ap.add_argument("--dry-run", action="store_true", help="Dry-run promotion")
    
    # Pipeline config
    ap.add_argument("--config", type=Path, help="Load config from YAML")
    ap.add_argument("--output", type=Path, help="Output report path")
    ap.add_argument("--webhook", help="Webhook URL for completion notification")
    
    args = ap.parse_args()
    
    # Load config from file if provided
    config = {}
    if args.config:
        with args.config.open("r") as f:
            config = yaml.safe_load(f)
    
    # Apply presets
    if args.quick:
        config.update({
            "max_train_samples": 64,
            "max_eval_samples": 16,
            "epochs": 1
        })
    elif args.standard:
        config.update({
            "max_train_samples": 500,
            "max_eval_samples": 100,
            "epochs": 3
        })
    elif args.full:
        config.update({
            "max_train_samples": None,  # All samples
            "max_eval_samples": None,
            "epochs": 5
        })
    
    # Override with CLI args
    if args.dataset:
        config["dataset"] = args.dataset
    if args.max_train_samples is not None:
        config["max_train_samples"] = args.max_train_samples
    if args.max_eval_samples is not None:
        config["max_eval_samples"] = args.max_eval_samples
    if args.epochs is not None:
        config["epochs"] = args.epochs
    if args.device:
        config["device"] = args.device
    
    # Build additional training args
    additional_args = []
    if args.learning_rate:
        additional_args.extend(["--learning-rate", str(args.learning_rate)])
    if args.batch_size:
        additional_args.extend(["--train-batch-size", str(args.batch_size)])
    
    # Defaults
    config.setdefault("max_train_samples", 64)
    config.setdefault("max_eval_samples", 16)
    config.setdefault("epochs", 1)
    config.setdefault("device", "auto")
    
    log("=" * 60)
    log("AUTOMATED TRAINING & PROMOTION PIPELINE")
    log("=" * 60)
    log(f"Config: {json.dumps(config, indent=2)}")
    log("=" * 60)
    
    # Phase 1: Training
    training_result = run_training(
        dataset=config["dataset"],
        max_train_samples=config["max_train_samples"],
        max_eval_samples=config["max_eval_samples"],
        epochs=config["epochs"],
        device=config["device"],
        additional_args=additional_args
    )
    
    if training_result["status"] != "success":
        log("Training failed, aborting pipeline", "ERROR")
        sys.exit(1)
    
    # Phase 2: Evaluation & Promotion
    eval_result = {}
    if not args.skip_eval:
        eval_result = run_evaluation_and_promotion(
            max_workers=args.max_workers,
            promote=args.auto_promote,
            dry_run=args.dry_run
        )
        
        if eval_result["status"] != "success":
            log("Evaluation failed", "ERROR")
    else:
        log("Skipping evaluation phase (--skip-eval)")
    
    # Save report
    output_file = args.output or (DATA_OUT / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    save_pipeline_report(training_result, eval_result, config, output_file)
    
    # Send notification if configured
    if args.webhook and eval_result:
        with output_file.open("r") as f:
            report = json.load(f)
        send_notification(args.webhook, report)
    
    log("=" * 60)
    log("PIPELINE COMPLETE", "SUCCESS")
    log("=" * 60)
    
    if eval_result.get("results", {}).get("best_model"):
        log(f"Best Model: {eval_result['results']['best_model']}")
        latest_txt = REPO_ROOT / "deployed_models" / "LATEST.txt"
        if latest_txt.exists():
            with latest_txt.open("r") as f:
                latest = f.read().strip()
            log(f"Deployed to: deployed_models/{latest}")


if __name__ == "__main__":
    main()
