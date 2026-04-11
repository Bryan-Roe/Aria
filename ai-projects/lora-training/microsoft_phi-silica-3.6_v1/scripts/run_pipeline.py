"""
Master Pipeline Orchestrator
Automates the complete training pipeline: optimization → pruning → training → evaluation → RAG
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict


class PipelineOrchestrator:
    """Orchestrates the complete training pipeline"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.results = {}
        self.start_time = time.time()

    def run_full_pipeline(self):
        """Run complete pipeline"""
        print("=" * 60)
        print("ADVANCED TRAINING PIPELINE")
        print("=" * 60)

        steps = [
            ("GPU Optimization", self.step_gpu_optimization),
            ("Data Pruning", self.step_data_pruning),
            ("Model Training", self.step_training),
            ("Model Evaluation", self.step_evaluation),
            ("RAG Setup", self.step_rag_setup),
        ]

        for i, (name, func) in enumerate(steps, 1):
            if not self.config.get(f"skip_{name.lower().replace(' ', '_')}", False):
                print(f"\n{'='*60}")
                print(f"STEP {i}/{len(steps)}: {name}")
                print(f"{'='*60}\n")

                try:
                    result = func()
                    self.results[name] = {"status": "success", "result": result}
                except Exception as e:
                    print(f"❌ Error in {name}: {e}")
                    self.results[name] = {"status": "failed", "error": str(e)}

                    if not self.config.get("continue_on_error", False):
                        print("\n❌ Pipeline stopped due to error")
                        return False
            else:
                print(f"\n⏭️  Skipping: {name}")
                self.results[name] = {"status": "skipped"}

        # Print summary
        self.print_summary()
        return True

    def step_gpu_optimization(self) -> Dict[str, Any]:
        """Step 1: GPU optimization"""
        cmd = [
            sys.executable,
            "scripts/gpu_optimizer.py",
            "--model-size",
            str(self.config.get("model_size_gb", 7.0)),
            "--memory-usage",
            str(self.config.get("memory_usage", 0.8)),
            "--output",
            "data_out/gpu_profile.yaml",
        ]

        if self.config.get("update_config", True):
            cmd.extend(
                [
                    "--update-config",
                    self.config.get("training_config", "lora/lora.yaml"),
                ]
            )

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"GPU optimization failed: {result.stderr}")

        print(result.stdout)
        return {"profile_path": "data_out/gpu_profile.yaml"}

    def step_data_pruning(self) -> Dict[str, Any]:
        """Step 2: Data pruning"""
        input_path = self.config.get("input_dataset")
        if not input_path:
            print("⚠️  No input dataset specified, skipping pruning")
            return {"skipped": True}

        output_path = self.config.get("pruned_dataset", "data/pruned_train.jsonl")

        cmd = [
            sys.executable,
            "scripts/semantic_pruning.py",
            "--input",
            input_path,
            "--output",
            output_path,
            "--similarity-threshold",
            str(self.config.get("similarity_threshold", 0.95)),
            "--quality-threshold",
            str(self.config.get("quality_threshold", 0.3)),
        ]

        if self.config.get("no_embeddings", False):
            cmd.append("--no-embeddings")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"Data pruning failed: {result.stderr}")

        print(result.stdout)
        return {"input_path": input_path, "output_path": output_path}

    def step_training(self) -> Dict[str, Any]:
        """Step 3: Model training"""
        dataset_path = self.config.get("pruned_dataset", "data")
        if not Path(dataset_path).exists():
            dataset_path = self.config.get("input_dataset", "data")

        cmd = [
            sys.executable,
            "scripts/train_lora.py",
            "--dataset",
            dataset_path,
            "--config",
            self.config.get("training_config", "lora/lora.yaml"),
        ]

        # Add optional flags
        if self.config.get("max_train_samples"):
            cmd.extend(["--max-train-samples", str(self.config["max_train_samples"])])

        if self.config.get("no_stream", False):
            cmd.append("--no-stream")

        if self.config.get("dry_run", False):
            cmd.append("--dry-run")

        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd)

        if result.returncode != 0:
            raise RuntimeError("Training failed")

        return {"model_path": self.config.get("model_output", "data_out/lora_training")}

    def step_evaluation(self) -> Dict[str, Any]:
        """Step 4: Model evaluation"""
        model_path = self.config.get("model_output", "data_out/lora_training")
        test_dataset = self.config.get("test_dataset")

        if not test_dataset:
            print("⚠️  No test dataset specified, skipping evaluation")
            return {"skipped": True}

        cmd = [
            sys.executable,
            "scripts/auto_eval.py",
            "--model",
            model_path,
            "--dataset",
            test_dataset,
            "--num-samples",
            str(self.config.get("eval_samples", 100)),
            "--output-name",
            self.config.get("experiment_name", "pipeline_eval"),
        ]

        metrics = self.config.get("eval_metrics", ["perplexity", "inference_time"])
        cmd.extend(["--metrics"] + metrics)

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"Evaluation failed: {result.stderr}")

        print(result.stdout)

        # Parse results
        eval_results = {}
        for line in result.stdout.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                eval_results[key.strip()] = value.strip()

        return eval_results

    def step_rag_setup(self) -> Dict[str, Any]:
        """Step 5: RAG setup"""
        if not self.config.get("rag_docs_path"):
            print("⚠️  No RAG docs path specified, skipping RAG setup")
            return {"skipped": True}

        model_path = self.config.get("model_output", "data_out/lora_training")
        docs_path = self.config.get("rag_docs_path")
        index_path = self.config.get("rag_index_path", "data_out/rag_index")

        cmd = [
            sys.executable,
            "scripts/rag_pipeline.py",
            "--model",
            model_path,
            "--docs",
            docs_path,
            "--index-dir",
            index_path,
        ]

        if self.config.get("rebuild_rag_index", True):
            cmd.append("--rebuild-index")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"RAG setup failed: {result.stderr}")

        print(result.stdout)
        return {"index_path": index_path, "ready": True}

    def print_summary(self):
        """Print pipeline summary"""
        elapsed = time.time() - self.start_time

        print("\n" + "=" * 60)
        print("PIPELINE SUMMARY")
        print("=" * 60)

        for step, result in self.results.items():
            status = result["status"]
            emoji = "✅" if status == "success" else "❌" if status == "failed" else "⏭️"
            print(f"{emoji} {step}: {status.upper()}")

        print(f"\nTotal time: {elapsed:.1f}s ({elapsed/60:.1f}m)")

        # Save results
        results_file = Path("data_out/pipeline_results.json")
        results_file.parent.mkdir(parents=True, exist_ok=True)

        with open(results_file, "w") as f:
            json.dump(
                {
                    "config": self.config,
                    "results": self.results,
                    "elapsed_seconds": elapsed,
                },
                f,
                indent=2,
            )

        print(f"\n📊 Full results saved to: {results_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Master Training Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full pipeline
  python scripts/run_pipeline.py --input-dataset data/train.jsonl --test-dataset data/test.jsonl

  # Quick test (64 samples, no RAG)
  python scripts/run_pipeline.py --input-dataset data/train.jsonl --max-train-samples 64 --skip-rag

  # Production (with RAG)
  python scripts/run_pipeline.py --input-dataset data/train.jsonl --test-dataset data/test.jsonl --rag-docs ../../datasets
        """,
    )

    # Input/Output
    parser.add_argument(
        "--input-dataset", type=str, help="Input training dataset (JSONL)"
    )
    parser.add_argument(
        "--test-dataset", type=str, help="Test dataset for evaluation (JSONL)"
    )
    parser.add_argument(
        "--training-config",
        type=str,
        default="lora/lora.yaml",
        help="Training config file",
    )
    parser.add_argument(
        "--model-output",
        type=str,
        default="data_out/lora_training",
        help="Output directory for trained model",
    )

    # GPU Optimization
    parser.add_argument(
        "--model-size-gb", type=float, default=7.0, help="Model size in GB"
    )
    parser.add_argument(
        "--memory-usage",
        type=float,
        default=0.8,
        help="Target GPU memory usage (0.0-1.0)",
    )
    parser.add_argument(
        "--no-update-config",
        action="store_true",
        help="Don't update training config with GPU optimizations",
    )

    # Data Pruning
    parser.add_argument(
        "--pruned-dataset",
        type=str,
        default="data/pruned_train.jsonl",
        help="Output path for pruned dataset",
    )
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=0.95,
        help="Similarity threshold for pruning",
    )
    parser.add_argument(
        "--quality-threshold",
        type=float,
        default=0.3,
        help="Quality threshold for pruning",
    )
    parser.add_argument(
        "--no-embeddings", action="store_true", help="Skip semantic deduplication"
    )

    # Training
    parser.add_argument(
        "--max-train-samples", type=int, help="Maximum training samples (for testing)"
    )
    parser.add_argument(
        "--no-stream", action="store_true", help="Disable streaming during training"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Dry run (validate config only)"
    )

    # Evaluation
    parser.add_argument(
        "--eval-samples", type=int, default=100, help="Number of samples for evaluation"
    )
    parser.add_argument(
        "--eval-metrics",
        nargs="+",
        default=["perplexity", "inference_time"],
        help="Evaluation metrics",
    )
    parser.add_argument(
        "--experiment-name",
        type=str,
        default="pipeline_eval",
        help="Experiment name for results",
    )

    # RAG
    parser.add_argument("--rag-docs", type=str, help="Path to documents for RAG")
    parser.add_argument(
        "--rag-index-path",
        type=str,
        default="data_out/rag_index",
        help="Path for RAG index",
    )
    parser.add_argument(
        "--no-rebuild-rag-index", action="store_true", help="Don't rebuild RAG index"
    )

    # Pipeline Control
    parser.add_argument(
        "--skip-optimization", action="store_true", help="Skip GPU optimization step"
    )
    parser.add_argument(
        "--skip-pruning", action="store_true", help="Skip data pruning step"
    )
    parser.add_argument(
        "--skip-training", action="store_true", help="Skip training step"
    )
    parser.add_argument(
        "--skip-evaluation", action="store_true", help="Skip evaluation step"
    )
    parser.add_argument("--skip-rag", action="store_true", help="Skip RAG setup step")
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue pipeline even if a step fails",
    )

    args = parser.parse_args()

    # Build config
    config = {
        # I/O
        "input_dataset": args.input_dataset,
        "test_dataset": args.test_dataset,
        "training_config": args.training_config,
        "model_output": args.model_output,
        "pruned_dataset": args.pruned_dataset,
        # GPU
        "model_size_gb": args.model_size_gb,
        "memory_usage": args.memory_usage,
        "update_config": not args.no_update_config,
        # Pruning
        "similarity_threshold": args.similarity_threshold,
        "quality_threshold": args.quality_threshold,
        "no_embeddings": args.no_embeddings,
        # Training
        "max_train_samples": args.max_train_samples,
        "no_stream": args.no_stream,
        "dry_run": args.dry_run,
        # Evaluation
        "eval_samples": args.eval_samples,
        "eval_metrics": args.eval_metrics,
        "experiment_name": args.experiment_name,
        # RAG
        "rag_docs_path": args.rag_docs,
        "rag_index_path": args.rag_index_path,
        "rebuild_rag_index": not args.no_rebuild_rag_index,
        # Control
        "skip_gpu_optimization": args.skip_optimization,
        "skip_data_pruning": args.skip_pruning,
        "skip_model_training": args.skip_training,
        "skip_model_evaluation": args.skip_evaluation,
        "skip_rag_setup": args.skip_rag,
        "continue_on_error": args.continue_on_error,
    }

    # Run pipeline
    orchestrator = PipelineOrchestrator(config)
    success = orchestrator.run_full_pipeline()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
