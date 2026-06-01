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
  python .\\scripts\\batch_evaluator.py --config batch_eval_config.yaml
  python .\\scripts\\batch_evaluator.py --scan-models --evaluate-all
  python .\\scripts\\batch_evaluator.py --compare lora azure openai
  python .\\scripts\\batch_evaluator.py --export markdown --output report.md
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_OUT = REPO_ROOT / "data_out" / "batch_evaluator"

# Add shared directory to path for performance utilities
sys.path.insert(0, str(REPO_ROOT / "shared"))
from performance_utils import find_json_in_output  # noqa: E402


@dataclass
class EvaluationTask:
    """A single model evaluation task."""

    model_id: str
    model_type: str
    model_path: str
    dataset: str
    metrics: list[str]
    max_samples: int | None = None
    batch_size: int = 8


@dataclass
class EvaluationResult:
    """Result from evaluating a model."""

    model_id: str
    model_type: str
    dataset: str = ""
    status: str = "succeeded"  # succeeded, failed, timeout
    duration: float = 0.0
    model_path: str = ""  # Path to the evaluated model
    metrics: dict[str, float] = field(default_factory=dict)
    error: str | None = None


# Backward-compatible alias used by older tests and scripts.
EvalResult = EvaluationResult


class BatchEvaluator:
    """Orchestrates parallel model evaluation."""

    def __init__(self, max_workers: int = 3):
        self.data_out = DATA_OUT
        self.data_out.mkdir(parents=True, exist_ok=True)
        self.max_workers = max_workers
        self.tasks: list[EvaluationTask] = []
        self.results: list[EvaluationResult] = []
        # Performance optimization: cache results lookup by model_id
        self._results_cache: dict[str, EvaluationResult] = {}

    def load_config(self, config_file: Path):
        """Load evaluation tasks from config file."""
        with config_file.open("r") as f:
            config = yaml.safe_load(f)

        # Use list comprehension for better performance
        self.tasks.extend([EvaluationTask(**task_data)
                          for task_data in config.get("evaluation_tasks", [])])

        print(f"[batch_eval] Loaded {len(self.tasks)} evaluation tasks")

    def scan_models(self) -> list[EvaluationTask]:
        """Scan for trained models and create evaluation tasks."""
        # Scan LoRA models - use list comprehension
        lora_dir = DATA_OUT.parent / "lora_training"
        tasks = []
        if lora_dir.exists():
            tasks = [
                EvaluationTask(
                    model_id=model_dir.name,
                    model_type="lora",
                    model_path=str(model_dir),
                    dataset="datasets/chat/mixed_chat",
                    metrics=["accuracy", "perplexity", "bleu"],
                    max_samples=100,
                )
                for model_dir in lora_dir.iterdir()
                if model_dir.is_dir() and (model_dir / "adapter_config.json").exists()
            ]

        print(f"[batch_eval] Found {len(tasks)} models to evaluate")
        return tasks

    def evaluate_model(self, task: EvaluationTask) -> EvaluationResult:
        """Evaluate a single model."""
        print(f"[batch_eval] Evaluating: {task.model_id} ({task.model_type})")

        # Build evaluation command
        cmd = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "evaluate_lora_model.py"),
            "--model",
            task.model_path,
            "--dataset",
            task.dataset,
            "--max-samples",
            str(task.max_samples or 1000),
            "--output-format",
            "json",
            "--save-dir",
            str(self.data_out / task.model_id),
        ]

        # Add metrics (each as separate --metric flag)
        for metric in task.metrics:
            cmd.extend(["--metric", metric])

        t0 = time.time()
        try:
            result = subprocess.run(
                cmd,
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minutes
            )

            duration = time.time() - t0

            # Parse results
            result_obj = EvaluationResult(
                model_id=task.model_id,
                model_type=task.model_type,
                dataset=task.dataset,
                model_path=task.model_path,
                status="succeeded" if result.returncode == 0 else "failed",
                duration=duration,
            )

            # Try to extract metrics from output using optimized utility
            if result.returncode == 0:
                data = find_json_in_output(
                    result.stdout, key="metrics", search_from_end=True, max_lines=50)
                if data and "metrics" in data:
                    result_obj.metrics = data["metrics"]
            else:
                result_obj.error = result.stderr

            return result_obj

        except subprocess.TimeoutExpired:
            return EvaluationResult(
                model_id=task.model_id,
                model_type=task.model_type,
                dataset=task.dataset,
                model_path=task.model_path,
                status="timeout",
                duration=1800,
                error="Evaluation timed out after 30 minutes",
            )
        except Exception as e:
            return EvaluationResult(
                model_id=task.model_id,
                model_type=task.model_type,
                dataset=task.dataset,
                model_path=task.model_path,
                status="failed",
                duration=0,
                error=str(e),
            )

    def run_parallel(self):
        """Run all evaluation tasks in parallel."""
        print("\n[batch_eval] Starting parallel evaluation")
        print(f"[batch_eval] Tasks: {len(self.tasks)}")
        print(f"[batch_eval] Workers: {self.max_workers}\n")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(
                self.evaluate_model, task): task for task in self.tasks}

            for future in as_completed(futures):
                task = futures[future]
                try:
                    result = future.result()
                    self.results.append(result)
                    # Update cache for O(1) lookups
                    self._results_cache[result.model_id] = result

                    # Use ASCII-safe status indicators
                    status_icon = "[OK]" if result.status == "succeeded" else "[FAIL]"
                    print(
                        f"{status_icon} {result.model_id}: {result.status} ({result.duration:.1f}s)")

                    if result.metrics:
                        for metric, value in result.metrics.items():
                            print(f"    {metric}: {value:.4f}")

                except Exception as e:
                    print(f"[ERROR] {task.model_id}: Exception - {e}")

        print("\n[batch_eval] Evaluation complete")
        # Use already classified results from aggregate to avoid redundant passes
        succeeded_count = sum(
            1 for r in self.results if r.status == "succeeded")
        failed_count = len(self.results) - succeeded_count
        print(f"[batch_eval] Succeeded: {succeeded_count}")
        print(f"[batch_eval] Failed: {failed_count}")

    def aggregate_results(self) -> dict[str, Any]:
        """Aggregate all evaluation results.

        Optimized to iterate results only once for classification and metrics.
        """
        succeeded = []
        failed = []
        total_duration = 0.0

        # Single pass through results for classification and duration sum
        for r in self.results:
            total_duration += r.duration
            if r.status == "succeeded":
                succeeded.append(r)
            else:
                failed.append(r)

        # Rank by primary metric (accuracy if available)
        ranked = sorted(
            succeeded,
            key=lambda r: r.metrics.get(
                "accuracy", r.metrics.get("perplexity", 0)),
            reverse=True,
        )

        # Pre-compute ranking list
        ranking = [{"rank": i + 1, "model_id": r.model_id,
                    "metrics": r.metrics} for i, r in enumerate(ranked)]

        return {
            "evaluated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "total_models": len(self.results),
            "succeeded": len(succeeded),
            "failed": len(failed),
            "total_duration": total_duration,
            "best_model": ranked[0].model_id if ranked else None,
            "results": [r.__dict__ for r in self.results],
            "ranking": ranking,
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
            f.write(
                f"**Total Duration:** {aggregated['total_duration']:.1f}s\n\n")

            if aggregated["best_model"]:
                f.write(f"**Best Model:** {aggregated['best_model']}\n\n")

            # Results table
            f.write("## Evaluation Results\n\n")
            f.write("| Rank | Model | Type | Status | Duration | Metrics |\n")
            f.write("|------|-------|------|--------|----------|----------|\n")

            for item in aggregated["ranking"]:
                metrics_str = ", ".join(
                    f"{k}={v:.3f}" for k, v in item["metrics"].items())
                f.write(
                    f"| {item['rank']} | {item['model_id']} | - | ✓ | - | {metrics_str} |\n")

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

    def compare_models(self, model_ids: list[str]) -> dict[str, Any]:
        """Compare specific models side-by-side using fast lookups with fallback."""
        comparison: list[EvaluationResult] = []

        # Primary path: O(1) cache lookup.
        for model_id in model_ids:
            result = self._results_cache.get(model_id)
            if result is not None:
                comparison.append(result)

        # Fallback path for tests/callers that set `self.results` directly.
        if len(comparison) != len(model_ids):
            model_ids_set = set(model_ids)
            seen = {r.model_id for r in comparison}
            for result in self.results:
                if result.model_id in model_ids_set and result.model_id not in seen:
                    comparison.append(result)
                    seen.add(result.model_id)

            # Preserve requested ordering.
            comparison_by_id = {r.model_id: r for r in comparison}
            comparison = [comparison_by_id[mid]
                          for mid in model_ids if mid in comparison_by_id]

        return {
            "models": [r.model_id for r in comparison],
            "comparison": [
                {
                    "model_id": r.model_id,
                    "model_type": r.model_type,
                    "status": r.status,
                    "duration": r.duration,
                    "metrics": r.metrics,
                }
                for r in comparison
            ],
        }

    def promote_best_model(self, target_dir: Path | None = None, dry_run: bool = False) -> dict[str, Any]:
        """
        Promote the best-ranked model to deployed_models/.

        Args:
            target_dir: Target directory (default: deployed_models/)
            dry_run: If True, only show what would be done

        Returns:
            Dict with promotion details (model_id, source, destination, metrics, timestamp)
        """
        if not self.results:
            raise ValueError(
                "No evaluation results available. Run evaluation first.")

        # Get best model from aggregated results
        aggregated = self.aggregate_results()
        best_model_id = aggregated.get("best_model")

        if not best_model_id:
            raise ValueError(
                "No best model found (all evaluations may have failed)")

        # Prefer O(1) cache lookup instead of O(n) linear search, but fall back if needed
        best_result = self._results_cache.get(best_model_id)
        if best_result is None:
            # Fallback to linear search to tolerate transient cache inconsistencies
            best_result = next(
                (r for r in self.results if r.model_id == best_model_id),
                None,
            )
        if best_result is None:
            raise ValueError(
                f"Best model {best_model_id} not found in evaluation results; "
                "this indicates an internal consistency error."
            )

        # Determine target directory
        if target_dir is None:
            target_dir = REPO_ROOT / "deployed_models"

        # Create deployment name with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        deployment_name = f"{best_model_id}_{timestamp}"
        deployment_path = target_dir / deployment_name

        promotion_info = {
            "model_id": best_model_id,
            "source_path": best_result.model_path,
            "deployment_name": deployment_name,
            "deployment_path": str(deployment_path),
            "metrics": best_result.metrics,
            "promoted_at": datetime.now(timezone.utc).isoformat() + "Z",
            "rank": 1,
        }

        if dry_run:
            print(f"[promote] DRY-RUN: Would promote {best_model_id}")
            print(f"[promote]   Source: {best_result.model_path}")
            print(f"[promote]   Target: {deployment_path}")
            print(
                f"[promote]   Metrics: {json.dumps(best_result.metrics, indent=2)}")
            return promotion_info

        # Create deployment directory
        deployment_path.mkdir(parents=True, exist_ok=True)

        # Copy adapter files
        source_path = Path(best_result.model_path)
        import shutil

        for file in source_path.iterdir():
            if file.is_file():
                shutil.copy2(file, deployment_path / file.name)
                print(f"[promote] Copied: {file.name}")

        # Create metadata file
        metadata_file = deployment_path / "promotion_metadata.json"
        with metadata_file.open("w") as f:
            json.dump(promotion_info, f, indent=2)
        print(f"[promote] Created metadata: {metadata_file}")

        # Create symlink to latest
        latest_link = target_dir / "latest"
        if latest_link.exists():
            if latest_link.is_symlink():
                latest_link.unlink()
            else:
                print("[promote] Warning: 'latest' exists but is not a symlink")

        # Create relative symlink on Windows (requires admin or developer mode)
        try:
            latest_link.symlink_to(deployment_name, target_is_directory=True)
            print(
                f"[promote] Updated symlink: {latest_link} -> {deployment_name}")
        except (OSError, NotImplementedError) as e:
            print(f"[promote] Warning: Could not create symlink ({e})")
            # Fallback: write a text file pointing to latest
            with (target_dir / "LATEST.txt").open("w") as f:
                f.write(deployment_name)
            print("[promote] Created LATEST.txt instead")

        print(f"[promote] ✓ Promoted {best_model_id} to {deployment_path}")
        return promotion_info


def main():
    ap = argparse.ArgumentParser(description="Batch Model Evaluator")
    ap.add_argument("--config", type=Path,
                    help="Load evaluation tasks from config")
    ap.add_argument("--scan-models", action="store_true",
                    help="Scan for trained models")
    ap.add_argument("--evaluate-all", action="store_true",
                    help="Evaluate all scanned models")
    ap.add_argument("--compare", nargs="+", help="Compare specific models")
    ap.add_argument(
        "--export", choices=["json", "markdown", "both"], help="Export results")
    ap.add_argument("--output", type=Path, help="Output file for export")
    ap.add_argument("--max-workers", type=int, default=3,
                    help="Number of parallel workers")
    ap.add_argument(
        "--promote-best",
        action="store_true",
        help="Promote best model to deployed_models/",
    )
    ap.add_argument(
        "--promote-target",
        type=Path,
        help="Target directory for promotion (default: deployed_models/)",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry-run mode (show actions without executing)",
    )
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
        results_file = evaluator.data_out / \
            f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        evaluator.export_json(results_file)

        # Auto-promote if requested
        if args.promote_best:
            try:
                promotion_info = evaluator.promote_best_model(
                    target_dir=args.promote_target, dry_run=args.dry_run)
                if not args.dry_run:
                    # Save promotion info
                    promo_file = evaluator.data_out / \
                        f"promotion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    with promo_file.open("w") as f:
                        json.dump(promotion_info, f, indent=2)
                    print(f"[promote] Saved promotion info to: {promo_file}")
            except Exception as e:
                print(f"[promote] Error: {e}", file=sys.stderr)

    if args.compare:
        comparison = evaluator.compare_models(args.compare)
        print(json.dumps(comparison, indent=2))

    if args.export:
        if not args.output:
            args.output = evaluator.data_out / \
                f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

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
