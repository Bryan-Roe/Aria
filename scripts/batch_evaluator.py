#!/usr/bin/env python
"""
Batch Evaluator

Parallel evaluation of multiple models with comprehensive result aggregation.

Features:
- Parallel model evaluation (ThreadPoolExecutor)
- Support for multiple model types (LoRA, Azure, OpenAI, Local, Quantum)
- Configurable metrics per model type
- Result aggregation and ranking
- Export to multiple formats
- Comparison reports

Usage examples (PowerShell):
  python .\scripts\batch_evaluator.py --config batch_eval_config.yaml
  python .\scripts\batch_evaluator.py --scan-models --evaluate-all
  python .\scripts\batch_evaluator.py --compare lora azure openai
  python .\scripts\batch_evaluator.py --export markdown --output report.md
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_OUT = REPO_ROOT / "data_out" / "batch_evaluator"


@dataclass
class EvaluationTask:
    """A single model evaluation task."""
    model_id: str
    model_type: str
    model_path: str
    dataset: str
    metrics: List[str]
    max_samples: Optional[int] = None
    batch_size: int = 8


@dataclass
class EvaluationResult:
    """Result from evaluating a model."""
    model_id: str
    model_type: str
    dataset: str
    status: str  # succeeded, failed, timeout
    duration: float
    metrics: Dict[str, float] = field(default_factory=dict)
    error: Optional[str] = None


class BatchEvaluator:
    """Orchestrates parallel model evaluation."""
    
    def __init__(self, max_workers: int = 3):
        self.data_out = DATA_OUT
        self.data_out.mkdir(parents=True, exist_ok=True)
        self.max_workers = max_workers
        self.tasks: List[EvaluationTask] = []
        self.results: List[EvaluationResult] = []
    
    def load_config(self, config_file: Path):
        """Load evaluation tasks from config file."""
        with config_file.open("r") as f:
            config = yaml.safe_load(f)
        
        for task_data in config.get("evaluation_tasks", []):
            task = EvaluationTask(**task_data)
            self.tasks.append(task)
        
        print(f"[batch_eval] Loaded {len(self.tasks)} evaluation tasks")
    
    def scan_models(self) -> List[EvaluationTask]:
        """Scan for trained models and create evaluation tasks."""
        tasks = []
        
        # Scan LoRA models
        lora_dir = DATA_OUT.parent / "lora_training"
        if lora_dir.exists():
            for model_dir in lora_dir.iterdir():
                if model_dir.is_dir() and (model_dir / "adapter_config.json").exists():
                    task = EvaluationTask(
                        model_id=model_dir.name,
                        model_type="lora",
                        model_path=str(model_dir),
                        dataset="datasets/chat/mixed_chat",
                        metrics=["accuracy", "perplexity", "bleu"],
                        max_samples=100
                    )
                    tasks.append(task)
        
        print(f"[batch_eval] Found {len(tasks)} models to evaluate")
        return tasks
    
    def evaluate_model(self, task: EvaluationTask) -> EvaluationResult:
        """Evaluate a single model."""
        print(f"[batch_eval] Evaluating: {task.model_id} ({task.model_type})")
        
        # Build evaluation command
        cmd = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "evaluate_lora_model.py"),
            "--model", task.model_path,
            "--dataset", task.dataset,
            "--max-samples", str(task.max_samples or 1000),
            "--metric", ",".join(task.metrics),
            "--output-format", "json",
            "--save-dir", str(self.data_out / task.model_id)
        ]
        
        t0 = time.time()
        try:
            result = subprocess.run(
                cmd,
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes
            )
            
            duration = time.time() - t0
            
            # Parse results
            result_obj = EvaluationResult(
                model_id=task.model_id,
                model_type=task.model_type,
                dataset=task.dataset,
                status="succeeded" if result.returncode == 0 else "failed",
                duration=duration
            )
            
            # Try to extract metrics from output
            if result.returncode == 0:
                try:
                    # Look for JSON output in stdout
                    for line in result.stdout.splitlines():
                        if line.strip().startswith("{"):
                            data = json.loads(line)
                            if "metrics" in data:
                                result_obj.metrics = data["metrics"]
                                break
                except Exception:
                    pass
            else:
                result_obj.error = result.stderr
            
            return result_obj
        
        except subprocess.TimeoutExpired:
            return EvaluationResult(
                model_id=task.model_id,
                model_type=task.model_type,
                dataset=task.dataset,
                status="timeout",
                duration=1800,
                error="Evaluation timed out after 30 minutes"
            )
        except Exception as e:
            return EvaluationResult(
                model_id=task.model_id,
                model_type=task.model_type,
                dataset=task.dataset,
                status="failed",
                duration=0,
                error=str(e)
            )
    
    def run_parallel(self):
        """Run all evaluation tasks in parallel."""
        print(f"\n[batch_eval] Starting parallel evaluation")
        print(f"[batch_eval] Tasks: {len(self.tasks)}")
        print(f"[batch_eval] Workers: {self.max_workers}\n")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.evaluate_model, task): task
                for task in self.tasks
            }
            
            for future in as_completed(futures):
                task = futures[future]
                try:
                    result = future.result()
                    self.results.append(result)
                    
                    status_icon = "✓" if result.status == "succeeded" else "✗"
                    print(f"{status_icon} {result.model_id}: {result.status} ({result.duration:.1f}s)")
                    
                    if result.metrics:
                        for metric, value in result.metrics.items():
                            print(f"    {metric}: {value:.4f}")
                
                except Exception as e:
                    print(f"✗ {task.model_id}: Exception - {e}")
        
        print(f"\n[batch_eval] Evaluation complete")
        print(f"[batch_eval] Succeeded: {sum(1 for r in self.results if r.status == 'succeeded')}")
        print(f"[batch_eval] Failed: {sum(1 for r in self.results if r.status == 'failed')}")
    
    def aggregate_results(self) -> Dict:
        """Aggregate all evaluation results."""
        succeeded = [r for r in self.results if r.status == "succeeded"]
        failed = [r for r in self.results if r.status != "succeeded"]
        
        # Rank by primary metric (accuracy if available)
        ranked = sorted(
            succeeded,
            key=lambda r: r.metrics.get("accuracy", r.metrics.get("perplexity", 0)),
            reverse=True
        )
        
        return {
            "evaluated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "total_models": len(self.results),
            "succeeded": len(succeeded),
            "failed": len(failed),
            "total_duration": sum(r.duration for r in self.results),
            "best_model": ranked[0].model_id if ranked else None,
            "results": [r.__dict__ for r in self.results],
            "ranking": [
                {"rank": i+1, "model_id": r.model_id, "metrics": r.metrics}
                for i, r in enumerate(ranked)
            ]
        }
    
    def export_markdown(self, output_file: Path):
        """Export results as Markdown report."""
        aggregated = self.aggregate_results()
        
        with output_file.open("w") as f:
            f.write("# Model Evaluation Report\n\n")
            f.write(f"**Generated:** {aggregated['evaluated_at']}\n\n")
            f.write(f"**Total Models:** {aggregated['total_models']}\n")
            f.write(f"**Succeeded:** {aggregated['succeeded']}\n")
            f.write(f"**Failed:** {aggregated['failed']}\n")
            f.write(f"**Total Duration:** {aggregated['total_duration']:.1f}s\n\n")
            
            if aggregated['best_model']:
                f.write(f"**Best Model:** {aggregated['best_model']}\n\n")
            
            # Results table
            f.write("## Evaluation Results\n\n")
            f.write("| Rank | Model | Type | Status | Duration | Metrics |\n")
            f.write("|------|-------|------|--------|----------|----------|\n")
            
            for item in aggregated['ranking']:
                metrics_str = ", ".join(f"{k}={v:.3f}" for k, v in item['metrics'].items())
                f.write(f"| {item['rank']} | {item['model_id']} | - | ✓ | - | {metrics_str} |\n")
            
            # Failed models
            failed = [r for r in self.results if r.status != "succeeded"]
            if failed:
                f.write("\n## Failed Evaluations\n\n")
                for result in failed:
                    f.write(f"- **{result.model_id}**: {result.status}")
                    if result.error:
                        f.write(f" - {result.error}")
                    f.write("\n")
        
        print(f"[batch_eval] Exported Markdown report to: {output_file}")
    
    def export_json(self, output_file: Path):
        """Export results as JSON."""
        aggregated = self.aggregate_results()
        with output_file.open("w") as f:
            json.dump(aggregated, f, indent=2)
        print(f"[batch_eval] Exported JSON to: {output_file}")
    
    def compare_models(self, model_ids: List[str]) -> Dict:
        """Compare specific models side-by-side."""
        comparison = []
        
        for model_id in model_ids:
            result = next((r for r in self.results if r.model_id == model_id), None)
            if result:
                comparison.append(result)
        
        return {
            "models": [r.model_id for r in comparison],
            "comparison": [
                {
                    "model_id": r.model_id,
                    "model_type": r.model_type,
                    "status": r.status,
                    "duration": r.duration,
                    "metrics": r.metrics
                }
                for r in comparison
            ]
        }


def main():
    ap = argparse.ArgumentParser(description="Batch Model Evaluator")
    ap.add_argument("--config", type=Path, help="Load evaluation tasks from config")
    ap.add_argument("--scan-models", action="store_true", help="Scan for trained models")
    ap.add_argument("--evaluate-all", action="store_true", help="Evaluate all scanned models")
    ap.add_argument("--compare", nargs="+", help="Compare specific models")
    ap.add_argument("--export", choices=["json", "markdown", "both"], help="Export results")
    ap.add_argument("--output", type=Path, help="Output file for export")
    ap.add_argument("--max-workers", type=int, default=3, help="Number of parallel workers")
    args = ap.parse_args()
    
    evaluator = BatchEvaluator(max_workers=args.max_workers)
    
    if args.config:
        evaluator.load_config(args.config)
    
    if args.scan_models:
        tasks = evaluator.scan_models()
        if args.evaluate_all:
            evaluator.tasks = tasks
    
    if evaluator.tasks and args.evaluate_all:
        evaluator.run_parallel()
        
        # Auto-save results
        results_file = evaluator.data_out / f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        evaluator.export_json(results_file)
    
    if args.compare:
        comparison = evaluator.compare_models(args.compare)
        print(json.dumps(comparison, indent=2))
    
    if args.export:
        if not args.output:
            args.output = evaluator.data_out / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if args.export in ["json", "both"]:
            json_file = args.output.with_suffix(".json")
            evaluator.export_json(json_file)
        
        if args.export in ["markdown", "both"]:
            md_file = args.output.with_suffix(".md")
            evaluator.export_markdown(md_file)
        
        return
    
    # Default: show help
    if not any([args.config, args.scan_models, args.compare, args.export]):
        ap.print_help()


if __name__ == "__main__":
    main()
