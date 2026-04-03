"""
Quantum LLM Quick Start Example
================================

Complete example demonstrating quantum-enhanced LLM training.

Usage:
    python quantum_llm_quickstart.py --mode quick
    python quantum_llm_quickstart.py --mode full --config my_config.yaml
    python quantum_llm_quickstart.py --mode monitor
    python quantum_llm_quickstart.py --mode generate --prompt "Hello"

Author: Quantum AI Workspace
Date: March 9, 2026
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Any, Optional

# Lazily initialized runtime dependencies. This keeps `--help` fast and avoids
# importing heavy ML modules unless an execution mode actually needs them.
torch = None  # type: ignore[assignment]
TORCH_AVAILABLE: Optional[bool] = None
TORCH_IMPORT_ERROR: Optional[Exception] = None

# Placeholders for lazily imported runtime classes/functions. These are updated
# by `_load_runtime_dependencies()` before any training/generation path uses
# them, while still allowing `--help` and monitor mode to avoid heavy imports.
IntegratedQuantumLLM: Any = None
QuantumLLMConfig: Any = None
QuantumLLMSystem: Any = None
CharacterTokenizer: Any = None
DatasetBuilder: Any = None
TextDataset: Any = None
create_train_val_split: Any = None

# Ensure src modules are importable when running from repository root.
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Lazily imported quantum LLM components.
INTEGRATED_AVAILABLE: Optional[bool] = None
DATASETS_AVAILABLE: Optional[bool] = None
INTEGRATED_IMPORT_ERROR: Optional[Exception] = None
DATASETS_IMPORT_ERROR: Optional[Exception] = None


def _load_runtime_dependencies(
    *, load_torch: bool = True, load_integrated: bool = True, load_datasets: bool = True
) -> None:
    """Load heavy runtime dependencies on-demand."""
    global torch
    global TORCH_AVAILABLE, TORCH_IMPORT_ERROR
    global INTEGRATED_AVAILABLE, INTEGRATED_IMPORT_ERROR
    global DATASETS_AVAILABLE, DATASETS_IMPORT_ERROR

    if load_torch and TORCH_AVAILABLE is None:
        try:
            import torch as _torch

            torch = _torch  # type: ignore[assignment]
            TORCH_AVAILABLE = True
            TORCH_IMPORT_ERROR = None
        except ModuleNotFoundError as exc:
            torch = None  # type: ignore[assignment]
            TORCH_AVAILABLE = False
            TORCH_IMPORT_ERROR = exc

    if load_integrated and INTEGRATED_AVAILABLE is None:
        try:
            from src.quantum_llm_integrated import (IntegratedQuantumLLM,
                                                    QuantumLLMConfig,
                                                    QuantumLLMSystem)

            globals().update(
                {
                    "IntegratedQuantumLLM": IntegratedQuantumLLM,
                    "QuantumLLMConfig": QuantumLLMConfig,
                    "QuantumLLMSystem": QuantumLLMSystem,
                }
            )
            INTEGRATED_AVAILABLE = True
            INTEGRATED_IMPORT_ERROR = None
        except ImportError as exc:
            INTEGRATED_AVAILABLE = False
            INTEGRATED_IMPORT_ERROR = exc

    if load_datasets and DATASETS_AVAILABLE is None:
        try:
            from src.quantum_llm_datasets import (CharacterTokenizer,
                                                  DatasetBuilder, TextDataset,
                                                  create_train_val_split)

            globals().update(
                {
                    "CharacterTokenizer": CharacterTokenizer,
                    "DatasetBuilder": DatasetBuilder,
                    "TextDataset": TextDataset,
                    "create_train_val_split": create_train_val_split,
                }
            )
            DATASETS_AVAILABLE = True
            DATASETS_IMPORT_ERROR = None
        except ImportError as exc:
            DATASETS_AVAILABLE = False
            DATASETS_IMPORT_ERROR = exc


logger = logging.getLogger(__name__)

DEFAULT_QUANTUM_QUICKSTART_OUTPUT_DIR = Path("data_out/quantum_llm_quickstart")
DEFAULT_QUANTUM_FULL_OUTPUT_DIR = Path("data_out/quantum_llm_full")


def _resolve_generate_model_path(
    model_path: Optional[str], output_dir: Optional[str]
) -> Optional[Path]:
    """Resolve model path for generate mode.

    Priority:
      1) Explicit --model path (must exist)
      2) Auto-detected checkpoints under --output-dir (or default dirs)

    Returns:
      Path to a discovered model checkpoint, or None if not found.
    """
    if model_path:
        explicit_path = Path(model_path).expanduser()
        return explicit_path if explicit_path.exists() else None

    candidate_roots: list[Path] = []
    if output_dir:
        candidate_roots.append(Path(output_dir))

    candidate_roots.extend(
        [DEFAULT_QUANTUM_QUICKSTART_OUTPUT_DIR, DEFAULT_QUANTUM_FULL_OUTPUT_DIR]
    )

    candidate_relative_paths = [
        Path("final_model.pt"),
        Path("model.pt"),
        Path("best_model.pt"),
        Path("training") / "final_model.pt",
    ]

    for root in candidate_roots:
        for rel in candidate_relative_paths:
            candidate = root / rel
            if candidate.exists():
                return candidate

    return None


def _ensure_torch_available(context: str) -> bool:
    """Ensure torch is available before running training/inference paths."""
    _load_runtime_dependencies(
        load_torch=True, load_integrated=False, load_datasets=False
    )

    if TORCH_AVAILABLE:
        return True

    logger.error("❌ PyTorch is required for %s mode", context)
    if TORCH_IMPORT_ERROR is not None:
        logger.error("   Import error: %s", TORCH_IMPORT_ERROR)
    logger.error("   Install dependency: pip install torch")
    return False


def quick_start_example():
    """
    Quick start: Minimal quantum LLM training example.
    """
    logger.info("=" * 80)
    logger.info("QUANTUM LLM QUICK START")
    logger.info("=" * 80)

    if not _ensure_torch_available("quick"):
        return

    if not INTEGRATED_AVAILABLE or not DATASETS_AVAILABLE:
        logger.error("Required components not available")
        logger.error(
            f"Integrated: {INTEGRATED_AVAILABLE}, Datasets: {DATASETS_AVAILABLE}"
        )
        return

    # Step 1: Create configuration
    logger.info("Step 1: Creating configuration...")
    config = QuantumLLMConfig()
    config.config.update(
        {
            "vocab_size": 256,
            "d_model": 64,
            "n_heads": 2,
            "n_layers": 2,
            "n_qubits": 2,
            "max_seq_length": 128,
            "batch_size": 4,
            "num_epochs": 2,
            "learning_rate": 1e-3,
            "output_dir": "data_out/quantum_llm_quickstart",
            "enable_curriculum": True,
            "enable_dashboard": True,
        }
    )

    # Step 2: Create tokenizer
    logger.info("Step 2: Creating tokenizer...")
    tokenizer = CharacterTokenizer(vocab_size=config["vocab_size"])

    # Step 3: Create sample dataset
    logger.info("Step 3: Creating sample dataset...")
    sample_texts = [
        "Quantum computing harnesses quantum mechanics to process information.",
        "Machine learning algorithms learn patterns from data.",
        "Language models understand and generate natural language text.",
        "Quantum circuits use qubits and quantum gates for computation.",
        "Neural networks consist of interconnected layers of artificial neurons.",
        "Superposition allows quantum bits to exist in multiple states.",
        "Training deep learning models requires large datasets and computing power.",
        "Entanglement creates correlations between quantum particles.",
        "Natural language processing enables computers to understand human language.",
        "Quantum advantage emerges when quantum algorithms outperform classical ones.",
    ] * 10  # Repeat for more training data

    dataset = TextDataset(
        texts=sample_texts,
        tokenizer=tokenizer,
        max_seq_length=config["max_seq_length"],
        stride=64,
    )

    train_dataset, val_dataset = create_train_val_split(dataset, val_ratio=0.1)
    logger.info(f"Train size: {len(train_dataset)}, Val size: {len(val_dataset)}")

    # Step 4: Initialize quantum LLM system
    logger.info("Step 4: Initializing quantum LLM system...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    system = QuantumLLMSystem(config, device=device)

    # Step 5: Start training
    logger.info("Step 5: Starting training...")
    logger.info(
        f"Model parameters: {sum(p.numel() for p in system.model.parameters()):,}"
    )

    start_time = time.time()
    system.train(train_dataset, val_dataset)
    training_time = time.time() - start_time

    # Step 6: Results
    logger.info("=" * 80)
    logger.info("TRAINING COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Training time: {training_time:.2f}s")
    logger.info(f"Output directory: {system.output_dir}")

    # Step 7: Generate report
    logger.info("Step 7: Generating final report...")
    system.generate_report()

    logger.info("✅ Quick start complete!")
    logger.info(f"📁 Check results in: {system.output_dir}")

    return system, tokenizer


def full_training_example(config_path: Optional[Path] = None):
    """
    Full training: Complete quantum LLM training with all features.
    """
    logger.info("=" * 80)
    logger.info("QUANTUM LLM FULL TRAINING")
    logger.info("=" * 80)

    if not _ensure_torch_available("full"):
        return

    if not INTEGRATED_AVAILABLE or not DATASETS_AVAILABLE:
        logger.error("Required components not available")
        return

    # Load configuration
    if config_path and Path(config_path).exists():
        config = QuantumLLMConfig(config_path)
        logger.info(f"Configuration loaded from: {config_path}")
    else:
        # Use default configuration
        config = QuantumLLMConfig()
        config.config.update(
            {
                "vocab_size": 256,
                "d_model": 128,
                "n_heads": 4,
                "n_layers": 4,
                "n_qubits": 4,
                "max_seq_length": 512,
                "batch_size": 16,
                "num_epochs": 10,
                "learning_rate": 1e-4,
                "output_dir": "data_out/quantum_llm_full",
                "enable_multi_scale_attention": True,
                "enable_adaptive_entanglement": True,
                "enable_circuit_caching": True,
                "enable_curriculum": True,
                "enable_dashboard": True,
                "optimization_level": 2,
            }
        )

    # Create tokenizer
    tokenizer = CharacterTokenizer(vocab_size=config["vocab_size"])

    # Load datasets
    # Try to find datasets in the workspace
    datasets_dir = Path("datasets")
    available_datasets = []

    if datasets_dir.exists():
        for category in ["chat", "quantum", "massive_quantum"]:
            category_dir = datasets_dir / category
            if category_dir.exists():
                for file in category_dir.glob("*.json"):
                    available_datasets.append(file)

    if available_datasets:
        logger.info(f"Found {len(available_datasets)} dataset files")
        # Use first available dataset
        dataset = DatasetBuilder.auto_detect_and_load(
            available_datasets[0],
            tokenizer,
            config["max_seq_length"],
        )
    else:
        logger.info("No datasets found, using sample data")
        sample_texts = [
            "The quantum language model combines quantum computing with natural language processing.",
            "Training involves curriculum learning with progressive quantum integration.",
            "Circuit optimization reduces execution time through caching and compilation.",
            "Multi-scale attention captures information at different granularities.",
            "Adaptive entanglement routing selects optimal quantum circuit topology.",
        ] * 50

        dataset = TextDataset(
            texts=sample_texts,
            tokenizer=tokenizer,
            max_seq_length=config["max_seq_length"],
        )

    train_dataset, val_dataset = create_train_val_split(dataset, val_ratio=0.1)

    # Initialize system
    device = "cuda" if torch.cuda.is_available() else "cpu"
    system = QuantumLLMSystem(config, device=device)

    # Save configuration
    config_save_path = Path(config["output_dir"]) / "config.yaml"
    config.save(config_save_path)

    # Train
    logger.info("Starting full training pipeline...")
    system.train(train_dataset, val_dataset)

    # Generate comprehensive report
    system.generate_report()

    logger.info("✅ Full training complete!")
    logger.info(f"📁 Results: {system.output_dir}")

    return system, tokenizer


def monitor_training(output_dir: Path):
    """
    Monitor an ongoing or completed training session.
    """
    logger.info("=" * 80)
    logger.info("QUANTUM LLM TRAINING MONITOR")
    logger.info("=" * 80)

    output_dir = Path(output_dir)

    # Check for dashboard data
    dashboard_path = output_dir / "dashboard" / "dashboard.json"
    if dashboard_path.exists():
        import json

        with open(dashboard_path) as f:
            dashboard_data = json.load(f)

        logger.info("Dashboard Data:")
        logger.info(f"  Timestamp: {dashboard_data.get('timestamp', 'N/A')}")

        metrics = dashboard_data.get("metrics_summary", {})
        logger.info(f"  Loss (MA): {metrics.get('moving_avg_loss', 'N/A'):.4f}")
        logger.info(
            f"  Perplexity (MA): {metrics.get('moving_avg_perplexity', 'N/A'):.2f}"
        )
        logger.info(f"  Loss Trend: {metrics.get('loss_trend', 'N/A')}")

        alerts = dashboard_data.get("recent_alerts", [])
        logger.info(f"  Recent Alerts: {len(alerts)}")
    else:
        logger.warning(f"Dashboard not found: {dashboard_path}")

    # Check for training report
    report_path = output_dir / "training" / "training_report.json"
    if report_path.exists():
        import json

        with open(report_path) as f:
            report = json.load(f)

        logger.info("Training Report:")
        logger.info(f"  Total Stages: {report.get('total_stages', 'N/A')}")
        logger.info(f"  Total Time: {report.get('total_time', 'N/A'):.2f}s")
        logger.info(f"  Best Loss: {report.get('best_loss', 'N/A'):.4f}")
    else:
        logger.warning(f"Training report not found: {report_path}")

    logger.info("=" * 80)


def generate_text(
    model_path: Path, tokenizer: CharacterTokenizer, prompt: str, max_length: int = 100
):
    """
    Generate text using trained quantum LLM.
    """
    logger.info("=" * 80)
    logger.info("QUANTUM LLM TEXT GENERATION")
    logger.info("=" * 80)

    if not _ensure_torch_available("generate"):
        return

    if not INTEGRATED_AVAILABLE:
        logger.error("Integrated components not available")
        return

    # Load model
    checkpoint = torch.load(model_path, map_location="cpu")
    config = QuantumLLMConfig()
    config.config = checkpoint["config"]

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = IntegratedQuantumLLM(config).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    logger.info(f"Model loaded from: {model_path}")
    logger.info(f"Prompt: {prompt}")

    # Encode prompt
    input_ids = (
        torch.tensor(tokenizer.encode(prompt, add_special_tokens=False))
        .unsqueeze(0)
        .to(device)
    )

    # Generate
    generated_ids = input_ids[0].tolist()

    with torch.no_grad():
        for _ in range(max_length):
            # Forward pass
            outputs = model(input_ids)

            # Get next token
            next_token_logits = outputs[0, -1, :]
            next_token_id = torch.argmax(next_token_logits).item()

            generated_ids.append(next_token_id)

            # Update input
            input_ids = torch.tensor([generated_ids]).to(device)

            # Stop at EOS
            if next_token_id == tokenizer.eos_id:
                break

    # Decode
    generated_text = tokenizer.decode(generated_ids)

    logger.info("=" * 80)
    logger.info("GENERATED TEXT:")
    logger.info("=" * 80)
    logger.info(generated_text)
    logger.info("=" * 80)

    return generated_text


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Quantum LLM Quick Start Examples")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["quick", "full", "monitor", "generate"],
        default="quick",
        help="Execution mode",
    )
    parser.add_argument("--config", type=str, help="Path to configuration YAML")
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory to monitor (and auto-discover model checkpoints for generate mode)",
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Path to trained model (optional in generate mode if checkpoint auto-discovery succeeds)",
    )
    parser.add_argument("--prompt", type=str, default="Hello", help="Generation prompt")
    parser.add_argument(
        "--max-length", type=int, default=100, help="Max generation length"
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Check dependencies by mode. Monitoring can run without model dependencies.
    if args.mode in {"quick", "full", "generate"}:
        if not _ensure_torch_available(args.mode):
            return

        _load_runtime_dependencies(
            load_torch=True, load_integrated=True, load_datasets=True
        )

        if not INTEGRATED_AVAILABLE:
            logger.error("❌ Integrated components not available")
            logger.error("   Make sure quantum_llm_integrated.py is importable")
            if INTEGRATED_IMPORT_ERROR is not None:
                logger.error("   Import error: %s", INTEGRATED_IMPORT_ERROR)
            return

        if not DATASETS_AVAILABLE:
            logger.error("❌ Dataset utilities not available")
            logger.error("   Make sure quantum_llm_datasets.py is importable")
            if DATASETS_IMPORT_ERROR is not None:
                logger.error("   Import error: %s", DATASETS_IMPORT_ERROR)
            return

    # Execute requested mode
    if args.mode == "quick":
        system, tokenizer = quick_start_example()

    elif args.mode == "full":
        config_path = Path(args.config) if args.config else None
        system, tokenizer = full_training_example(config_path)

    elif args.mode == "monitor":
        output_dir = (
            Path(args.output_dir)
            if args.output_dir
            else Path("data_out/quantum_llm_quickstart")
        )
        monitor_training(output_dir)

    elif args.mode == "generate":
        if args.max_length <= 0:
            logger.error("--max-length must be > 0")
            return

        resolved_model_path = _resolve_generate_model_path(args.model, args.output_dir)
        if resolved_model_path is None:
            logger.error("No model checkpoint found for generate mode")
            logger.error(
                "Provide --model <path> or ensure one of these files exists under --output-dir (or defaults): "
                "final_model.pt, model.pt, best_model.pt, training/final_model.pt"
            )
            logger.error(
                "Tip: run quick training first: python quantum_llm_quickstart.py --mode quick"
            )
            return

        if not args.model:
            logger.info(f"Auto-selected model checkpoint: {resolved_model_path}")

        # Need tokenizer
        tokenizer = CharacterTokenizer(vocab_size=256)

        generate_text(
            model_path=resolved_model_path,
            tokenizer=tokenizer,
            prompt=args.prompt,
            max_length=args.max_length,
        )


if __name__ == "__main__":
    main()
