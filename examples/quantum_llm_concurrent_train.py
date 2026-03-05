"""
Quantum-LLM Concurrent Training Example
========================================

Demonstrates concurrent quantum circuit execution during LLM training.

This example trains a simple LLM-like model while quantum circuits execute
in parallel, with quantum results fed back as loss feedback.

Usage:
    # Basic run (3 epochs, local simulation)
    python examples/quantum_llm_concurrent_train.py

    # Custom parameters
    python examples/quantum_llm_concurrent_train.py --epochs 5 --batch-size 8

    # With quantum feedback
    python examples/quantum_llm_concurrent_train.py \
        --epochs 10 --quantum-weight 0.2 --n-qubits 4

Requirements:
    - torch
    - numpy
    - pennylane
    - quantum_llm_concurrent (scripts/)

Author: Quantum AI Workspace
Date: March 2026
"""

import argparse
import logging
import sys
from pathlib import Path

# Add scripts to path
scripts_path = Path(__file__).parent.parent / "scripts"
if str(scripts_path) not in sys.path:
    sys.path.insert(0, str(scripts_path))

try:
    from quantum_llm_concurrent import (
        QuantumLLMConcurrentTrainer,
        ConcurrentTrainingResults,
    )
except ImportError as e:
    print(f"Error importing trainer: {e}")
    print(f"Make sure quantum_llm_concurrent.py is in {scripts_path}")
    sys.exit(1)


def run_example(
    n_epochs: int = 3,
    batch_size: int = 16,
    learning_rate: float = 0.001,
    n_qubits: int = 4,
    n_layers: int = 2,
    quantum_weight: float = 0.1,
    verbose: bool = True,
    checkpoint_dir: Path = None,
    resume_from: Path = None,
) -> ConcurrentTrainingResults:
    """
    Run concurrent quantum-LLM training example.

    Args:
        n_epochs: Number of training epochs
        batch_size: Training batch size
        learning_rate: Adam learning rate
        n_qubits: Number of qubits in quantum circuits
        n_layers: Number of quantum circuit layers
        quantum_weight: Weight of quantum feedback (0-1)
        verbose: Print detailed logs
        checkpoint_dir: Directory to save checkpoints
        resume_from: Path to checkpoint to resume from

    Returns:
        Training results summary
    """
    if verbose:
        print("\n" + "=" * 60)
        print("Quantum-LLM Concurrent Training Example")
        print("=" * 60)
        print("Configuration:")
        print(f"  Epochs: {n_epochs}")
        print(f"  Batch size: {batch_size}")
        print(f"  Learning rate: {learning_rate}")
        print(f"  Quantum qubits: {n_qubits}")
        print(f"  Quantum layers: {n_layers}")
        print(f"  Quantum feedback weight: {quantum_weight}")
        if checkpoint_dir:
            print(f"  Checkpoint dir: {checkpoint_dir}")
        if resume_from:
            print(f"  Resume from: {resume_from}")
        print("=" * 60 + "\n")

    # Initialize trainer
    trainer = QuantumLLMConcurrentTrainer(
        dataset=None,  # Uses synthetic dataset
        n_epochs=n_epochs,
        batch_size=batch_size,
        learning_rate=learning_rate,
        n_qubits=n_qubits,
        n_layers=n_layers,
        quantum_feedback_weight=quantum_weight,
    )

    # Run training
    try:
        results = trainer.train(
            checkpoint_dir=checkpoint_dir,
            resume_from=resume_from,
        )
        if verbose:
            print("\n" + "=" * 60)
            print(results.summary())
            print("=" * 60)
        else:
            print(results.summary())
        return results
    except KeyboardInterrupt:
        print("\nTraining interrupted by user")
        return None
    except Exception as e:
        print(f"Error during training: {e}")
        raise


def main():
    """Parse arguments and run example."""
    parser = argparse.ArgumentParser(
        description="Quantum-LLM Concurrent Training Example"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=3,
        help="Number of training epochs (default: 3)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="Training batch size (default: 16)",
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=0.001,
        help="Learning rate (default: 0.001)",
    )
    parser.add_argument(
        "--n-qubits",
        type=int,
        default=4,
        help="Number of qubits (default: 4)",
    )
    parser.add_argument(
        "--n-layers",
        type=int,
        default=2,
        help="Number of circuit layers (default: 2)",
    )
    parser.add_argument(
        "--quantum-weight",
        type=float,
        default=0.1,
        help="Weight of quantum feedback (0-1), default: 0.1",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose output",
    )
    parser.add_argument(
        "--checkpoint-dir",
        type=str,
        default=None,
        help="Directory to save checkpoints (saves every 1000 epochs)",
    )
    parser.add_argument(
        "--resume-from",
        type=str,
        default=None,
        help="Path to checkpoint file to resume training from",
    )

    args = parser.parse_args()

    # Validate quantum weight
    if not 0 <= args.quantum_weight <= 1:
        print("Error: --quantum-weight must be between 0 and 1")
        sys.exit(1)
    
    # Parse path arguments
    checkpoint_dir = Path(args.checkpoint_dir) if args.checkpoint_dir else None
    resume_from = Path(args.resume_from) if args.resume_from else None

    # Quiet mode should suppress per-epoch logs while preserving summary.
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
        logging.getLogger("quantum_llm_concurrent").setLevel(
            logging.WARNING
        )
        logging.getLogger(
            "src.quantum_llm_concurrent_runner"
        ).setLevel(logging.WARNING)

    # Run training
    results = run_example(
        n_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        n_qubits=args.n_qubits,
        n_layers=args.n_layers,
        quantum_weight=args.quantum_weight,
        verbose=not args.quiet,
        checkpoint_dir=checkpoint_dir,
        resume_from=resume_from,
    )

    return results


if __name__ == "__main__":
    main()
