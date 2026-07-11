"""
Early stopping with plateau detection for training pipelines.
Monitors validation loss and triggers stopping on performance degradation.
"""

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class EarlyStoppingMetrics:
    """Tracks validation metrics and stopping decisions."""

    epoch: int
    validation_loss: float
    best_loss: float
    epochs_without_improvement: int
    is_plateau: bool = False
    should_stop: bool = False
    checkpoint_saved: bool = False
    reason: str = ""


@dataclass
class EarlyStoppingConfig:
    """Configuration for early stopping behavior."""

    patience: int = 5  # Stop after N epochs without improvement
    min_delta: float = 0.001  # Minimum loss improvement to count as progress
    check_frequency: int = 1  # Check every N epochs
    save_best_model: bool = True
    warmup_epochs: int = 2  # Don't stop before this many epochs
    plateau_threshold: float = 0.0005  # Loss delta below this = plateau
    adaptive_patience: bool = True  # Increase patience if training is slow to converge
    max_epochs: int = 200  # Absolute maximum epochs regardless of plateau


class EarlyStoppingMonitor:
    """Monitor validation loss and decide when to stop training."""

    def __init__(self, config: EarlyStoppingConfig, output_dir: Path):
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.best_loss = float("inf")
        self.best_epoch = 0
        self.epochs_without_improvement = 0
        self.validation_history: list[float] = []
        self.metrics_history: list[EarlyStoppingMetrics] = []
        self.effective_patience = config.patience

    def check(self, epoch: int, validation_loss: float) -> EarlyStoppingMetrics:
        """
        Check if training should stop based on validation loss.

        Args:
            epoch: Current epoch number
            validation_loss: Validation loss for this epoch

        Returns:
            EarlyStoppingMetrics with stopping decision
        """
        self.validation_history.append(validation_loss)

        # Check if this is improvement
        improvement = self.best_loss - validation_loss
        is_improvement = improvement > self.config.min_delta

        if is_improvement:
            self.best_loss = validation_loss
            self.best_epoch = epoch
            self.epochs_without_improvement = 0
            logger.info(f"✓ Epoch {epoch}: Loss improved to {validation_loss:.6f} (delta: {improvement:.6f})")
        else:
            self.epochs_without_improvement += 1
            logger.info(
                f"⚠ Epoch {epoch}: No improvement (patience: "
                f"{self.epochs_without_improvement}/{self.effective_patience})"
            )

        # Detect plateau
        is_plateau = self._detect_plateau()

        # Determine stopping decision
        should_stop = False
        reason = ""
        checkpoint_saved = False

        if epoch < self.config.warmup_epochs:
            logger.debug(f"Warmup phase ({epoch}/{self.config.warmup_epochs}), no stopping")
        elif epoch >= self.config.max_epochs:
            should_stop = True
            reason = f"Reached maximum epochs ({self.config.max_epochs})"
            logger.warning(reason)
        elif self.epochs_without_improvement >= self.effective_patience:
            should_stop = True
            reason = f"Plateau detected: {self.epochs_without_improvement} epochs without improvement"
            logger.warning(reason)

        # Save best model if stopping
        if should_stop and self.config.save_best_model and is_improvement:
            checkpoint_saved = True
            logger.info(f"💾 Saving best model checkpoint (epoch {self.best_epoch}, loss: {self.best_loss:.6f})")

        # Adaptive patience: increase if converging slowly
        if self.config.adaptive_patience and len(self.validation_history) > 10:
            convergence_rate = self._estimate_convergence_rate()
            if convergence_rate < 0.001:  # Very slow convergence
                old_patience = self.effective_patience
                self.effective_patience = min(self.config.patience * 2, 15)
                if old_patience != self.effective_patience:
                    logger.info(f"📈 Slow convergence detected, patience increased to {self.effective_patience}")

        metrics = EarlyStoppingMetrics(
            epoch=epoch,
            validation_loss=validation_loss,
            best_loss=self.best_loss,
            epochs_without_improvement=self.epochs_without_improvement,
            is_plateau=is_plateau,
            should_stop=should_stop,
            checkpoint_saved=checkpoint_saved,
            reason=reason,
        )

        self.metrics_history.append(metrics)
        self._save_metrics()

        return metrics

    def _detect_plateau(self) -> bool:
        """Detect if loss is in a plateau (very small changes)."""
        if len(self.validation_history) < 3:
            return False

        # Check last 3 epochs for plateau pattern
        last_deltas = [
            abs(self.validation_history[-1] - self.validation_history[-2]),
            abs(self.validation_history[-2] - self.validation_history[-3]),
        ]

        return all(delta < self.config.plateau_threshold for delta in last_deltas)

    def _estimate_convergence_rate(self) -> float:
        """Estimate how quickly loss is improving (lower = slower)."""
        if len(self.validation_history) < 10:
            return 1.0

        # Average improvement rate over last 10 epochs
        recent = self.validation_history[-10:]
        total_improvement = recent[0] - recent[-1]
        avg_improvement_per_epoch = total_improvement / 10

        return max(avg_improvement_per_epoch, 0.0)

    def _save_metrics(self):
        """Save metrics history to JSON for monitoring."""
        metrics_file = self.output_dir / "early_stopping_metrics.json"

        metrics_data = {
            "config": asdict(self.config),
            "summary": {
                "best_loss": self.best_loss,
                "best_epoch": self.best_epoch,
                "current_epochs_without_improvement": self.epochs_without_improvement,
                "effective_patience": self.effective_patience,
                "total_epochs": len(self.validation_history),
            },
            "history": [asdict(m) for m in self.metrics_history],
        }

        with open(metrics_file, "w") as f:
            json.dump(metrics_data, f, indent=2)

    def get_summary(self) -> dict:
        """Get summary of early stopping session."""
        return {
            "best_loss": self.best_loss,
            "best_epoch": self.best_epoch,
            "total_epochs_trained": len(self.validation_history),
            "epochs_without_improvement": self.epochs_without_improvement,
            "was_plateau_detected": any(m.is_plateau for m in self.metrics_history),
            "stopping_reason": self.metrics_history[-1].reason if self.metrics_history else "None",
        }
