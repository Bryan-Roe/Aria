"""
Quantum-LLM Concurrent Trainer
==============================

Main training loop that runs quantum circuits in parallel with LLM training.

Features:
- Concurrent quantum circuit execution (background thread)
- Parameter synchronization between quantum and classical threads
- Quantum results fed back as loss feedback to LLM
- Non-blocking circuit submission and result collection
- Metrics tracking (convergence, execution time, resource usage)

Usage:
    trainer = QuantumLLMConcurrentTrainer(dataset, n_epochs=10)
    results = trainer.train()
    print(results.summary())

Author: Quantum AI Workspace
Date: March 2026
"""

import gc
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import torch
import torch.nn as nn
from torch.optim import Adam
from torch.utils.data import DataLoader, TensorDataset

# Add quantum to path
quantum_ai_path = Path(__file__).parent.parent / "quantum"
if str(quantum_ai_path) not in sys.path:
    sys.path.insert(0, str(quantum_ai_path))

try:
    from src.quantum_llm_concurrent_runner import (
        QuantumCircuitRunner,
        QuantumResult,
        QuantumTask,
        SharedParameterSync,
    )
except ImportError:
    from quantum_llm_concurrent_runner import (
        QuantumCircuitRunner,
        QuantumResult,
        QuantumTask,
        SharedParameterSync,
    )

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class ConcurrentTrainingResults:
    """Training results summary."""

    total_epochs: int
    total_loss: float
    avg_loss: float
    quantum_tasks: int
    quantum_feedback_weight: float = 0.1
    execution_time: float = 0.0
    final_metrics: Dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        """Get human-readable summary."""
        return (
            f"Concurrent Quantum-LLM Training Results\n"
            f"========================================\n"
            f"Epochs completed: {self.total_epochs}\n"
            f"Total loss: {self.total_loss:.6f}\n"
            f"Average loss: {self.avg_loss:.6f}\n"
            f"Quantum tasks executed: {self.quantum_tasks}\n"
            f"Quantum feedback weight: {self.quantum_feedback_weight}\n"
            f"Execution time: {self.execution_time:.2f}s\n"
            f"Metrics: {self.final_metrics}\n"
        )


class SimpleLLMModel(nn.Module):
    """Simple LLM-like model for testing concurrent training."""

    def __init__(self, input_dim: int = 16, hidden_dim: int = 32):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
        )
        self.attention = nn.Linear(hidden_dim, hidden_dim)
        self.decoder = nn.Linear(hidden_dim, 2)  # Binary classification
        self.loss_fn = nn.CrossEntropyLoss()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through model."""
        encoded = self.encoder(x)
        attn = torch.sigmoid(self.attention(encoded))
        weighted = encoded * attn
        logits = self.decoder(weighted)
        return logits


class QuantumLLMConcurrentTrainer:
    """
    Concurrent trainer managing quantum and LLM execution in parallel.

    Architecture:
    - Main thread: LLM training loop
    - Background thread: Quantum circuit execution
    - Shared state: Parameter synchronization with atomic locks
    """

    def __init__(
        self,
        dataset: Optional[TensorDataset] = None,
        n_epochs: int = 5,
        batch_size: int = 16,
        learning_rate: float = 0.001,
        n_qubits: int = 4,
        n_layers: int = 2,
        quantum_feedback_weight: float = 0.1,
    ):
        """Initialize concurrent trainer."""
        self.n_epochs = n_epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.n_qubits = n_qubits
        self.n_layers = n_layers
        self.quantum_feedback_weight = quantum_feedback_weight

        # Dataset
        if dataset is None:
            # Create synthetic dataset
            X = torch.randn(100, 16)
            y = torch.randint(0, 2, (100,))
            self.dataset = TensorDataset(X, y)
        else:
            self.dataset = dataset

        self.dataloader = DataLoader(
            self.dataset, batch_size=batch_size, shuffle=True
        )

        # Model setup
        self.model = SimpleLLMModel(input_dim=16, hidden_dim=32)
        self.optimizer = Adam(self.model.parameters(), lr=learning_rate)

        # Quantum runner
        self.quantum_runner = QuantumCircuitRunner(
            n_qubits=n_qubits, n_layers=n_layers
        )

        # Parameter synchronization
        self.param_sync = SharedParameterSync()

        # Metrics
        self.epoch_losses: List[float] = []
        self.quantum_results_collected: int = 0
        
        # Optimization: cache attention weights per epoch
        self._cached_attention: Optional[torch.Tensor] = None

        logger.info(
            f"Initialized QuantumLLMConcurrentTrainer: "
            f"{n_epochs} epochs, {n_qubits}q quantum"
        )

    def train(
        self,
        checkpoint_dir: Optional[Path] = None,
        resume_from: Optional[Path] = None,
    ) -> ConcurrentTrainingResults:
        """
        Run concurrent training loop.
        
        Args:
            checkpoint_dir: Directory to save checkpoints
            resume_from: Path to checkpoint file to resume from
        """
        logger.info("Starting concurrent training...")
        start_time = datetime.now()
        
        # Load checkpoint if resuming
        start_epoch = 0
        if resume_from is not None:
            start_epoch = self._load_checkpoint(resume_from)

        # Start quantum runner
        self.quantum_runner.start()

        try:
            total_loss = 0.0

            for epoch in range(start_epoch, self.n_epochs):
                epoch_loss = 0.0
                batch_count = 0

                # Cache attention weights once per epoch for efficiency
                if epoch % 1 == 0:  # Refresh every epoch
                    self._cached_attention = self.param_sync.get(
                        "attention_weights"
                    )
                
                for batch_idx, (X_batch, y_batch) in enumerate(
                    self.dataloader
                ):
                    # 1. Submit quantum circuit for background execution
                    task_id = f"epoch{epoch}_batch{batch_idx}"
                    self._submit_quantum_circuit(task_id, batch_idx)

                    # 2. Train LLM
                    self.optimizer.zero_grad()
                    logits = self.model(X_batch)
                    loss = self.model.loss_fn(logits, y_batch)

                    # 3. Collect quantum results (non-blocking)
                    quantum_results = self.quantum_runner.get_results()

                    if quantum_results:
                        # Incorporate quantum feedback into loss
                        quantum_loss = self._process_quantum_results(
                            quantum_results
                        )
                        loss = (
                            loss * (1 - self.quantum_feedback_weight)
                            + quantum_loss * self.quantum_feedback_weight
                        )
                        self.quantum_results_collected += len(
                            quantum_results
                        )
                        # Explicit cleanup to help GC
                        del quantum_results

                    # 4. Backprop and update
                    loss.backward()
                    self.optimizer.step()

                    epoch_loss += loss.item()
                    batch_count += 1

                # Log epoch results
                avg_epoch_loss = epoch_loss / batch_count
                self.epoch_losses.append(avg_epoch_loss)
                total_loss += avg_epoch_loss

                quantum_metrics = self.quantum_runner.metrics()
                quantum_completed = quantum_metrics["completed"]
                quantum_submitted = quantum_metrics["submitted"]
                output_pending = quantum_metrics.get("output_pending", 0)
                logger.info(
                    f"Epoch {epoch + 1}/{self.n_epochs} "
                    f"Loss: {avg_epoch_loss:.6f} "
                    f"Q-tasks: {quantum_completed}/{quantum_submitted} "
                    f"(output_pending: {output_pending})"
                )
                
                # Periodic full drain to prevent queue accumulation
                if (epoch + 1) % 10 == 0:
                    drained = self.quantum_runner.get_results(timeout=2.0)
                    if drained:
                        logger.debug(
                            f"Drained {len(drained)} pending quantum results"
                        )
                        self.quantum_results_collected += len(drained)
                        del drained
                
                # Periodic garbage collection to prevent memory buildup
                if (epoch + 1) % 100 == 0:
                    gc.collect()
                    logger.debug("Triggered garbage collection")
                
                # Save checkpoint every 1000 epochs
                if checkpoint_dir and (epoch + 1) % 1000 == 0:
                    self._save_checkpoint(epoch, checkpoint_dir)

        finally:
            # Stop quantum runner and collect remaining results
            logger.info("Waiting for remaining quantum tasks...")
            pending_results = self.quantum_runner.get_results(timeout=5.0)
            if pending_results:
                logger.info(
                    f"Collected {len(pending_results)} pending quantum results"
                )
                self.quantum_results_collected += len(pending_results)

            self.quantum_runner.stop()

        execution_time = (datetime.now() - start_time).total_seconds()

        return ConcurrentTrainingResults(
            total_epochs=self.n_epochs,
            total_loss=total_loss,
            avg_loss=total_loss / self.n_epochs if self.n_epochs > 0 else 0,
            quantum_tasks=self.quantum_results_collected,
            quantum_feedback_weight=self.quantum_feedback_weight,
            execution_time=execution_time,
            final_metrics=self.quantum_runner.metrics(),
        )

    def _submit_quantum_circuit(
        self, task_id: str, batch_idx: int = 0
    ) -> None:
        """Submit a quantum circuit for background execution."""
        # Use cached attention weights instead of cloning every batch
        if batch_idx > 0:
            current_attention = self._cached_attention
        else:
            current_attention = self.param_sync.get("attention_weights")

        task = QuantumTask(
            task_id=task_id,
            circuit_params={
                "device": "default.qubit",
                "params": (
                    current_attention.numpy().flatten()
                    if current_attention is not None
                    else np.random.randn(self.n_layers * self.n_qubits) * 0.1
                ),
            },
            n_qubits=self.n_qubits,
            n_layers=self.n_layers,
            shots=1000,
        )

        self.quantum_runner.submit_circuit(task)

    def _process_quantum_results(
        self, results: List[QuantumResult]
    ) -> torch.Tensor:
        """
        Process quantum circuit results and convert to loss feedback.

        Returns:
            Scalar tensor with quantum loss contribution
        """
        if not results:
            return torch.tensor(0.0)

        successful_results = [r for r in results if r.success]
        if not successful_results:
            return torch.tensor(0.0)

        # Average quantum outputs as loss feedback
        outputs = torch.stack(
            [r.output[0] for r in successful_results if r.output is not None]
        )
        quantum_loss = torch.mean(outputs ** 2)  # MSE-like feedback

        return quantum_loss

    def _save_checkpoint(
        self, epoch: int, checkpoint_dir: Optional[Path] = None
    ) -> None:
        """Save training checkpoint."""
        if checkpoint_dir is None:
            checkpoint_dir = Path(
                "data_out/quantum_llm_concurrent/checkpoints"
            )
        
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        checkpoint_path = checkpoint_dir / f"checkpoint_epoch_{epoch}.pt"
        
        checkpoint = {
            "epoch": epoch,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "epoch_losses": self.epoch_losses,
            "quantum_results_collected": self.quantum_results_collected,
            "n_epochs": self.n_epochs,
            "quantum_feedback_weight": self.quantum_feedback_weight,
        }
        
        torch.save(checkpoint, checkpoint_path)
        logger.info(f"Saved checkpoint to {checkpoint_path}")
    
    def _load_checkpoint(
        self, checkpoint_path: Path
    ) -> int:
        """
        Load training checkpoint and return starting epoch.
        
        Returns:
            Epoch to resume from (checkpoint_epoch + 1)
        """
        if not checkpoint_path.exists():
            logger.warning(f"Checkpoint not found: {checkpoint_path}")
            return 0
        
        checkpoint = torch.load(checkpoint_path)
        
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.epoch_losses = checkpoint.get("epoch_losses", [])
        self.quantum_results_collected = checkpoint.get(
            "quantum_results_collected", 0
        )
        
        resume_epoch = checkpoint["epoch"] + 1
        logger.info(
            f"Loaded checkpoint from {checkpoint_path}, "
            f"resuming from epoch {resume_epoch}"
        )
        return resume_epoch


def main():
    """Run concurrent training example."""
    trainer = QuantumLLMConcurrentTrainer(
        n_epochs=3,
        batch_size=8,
        n_qubits=4,
        n_layers=2,
        quantum_feedback_weight=0.1,
    )

    results = trainer.train()
    print(results.summary())

    return results


if __name__ == "__main__":
    main()
