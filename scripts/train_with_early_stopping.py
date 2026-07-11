"""
Training pipeline with integrated early stopping and plateau detection.
Wraps existing LoRA training with validation monitoring.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments

from shared.early_stopping import EarlyStoppingConfig, EarlyStoppingMonitor

logger = logging.getLogger(__name__)


class TrainingWithEarlyStopping:
    """Wrapper for training with integrated early stopping."""

    def __init__(
        self,
        model_name: str,
        dataset_path: str,
        output_dir: str,
        num_epochs: int = 3,
        batch_size: int = 4,
        learning_rate: float = 1e-4,
        enable_early_stopping: bool = True,
        early_stopping_config: EarlyStoppingConfig | None = None,
    ):

        self.model_name = model_name
        self.dataset_path = dataset_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.num_epochs = num_epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.enable_early_stopping = enable_early_stopping

        # Early stopping config
        self.es_config = early_stopping_config or EarlyStoppingConfig()
        self.es_monitor = EarlyStoppingMonitor(self.es_config, self.output_dir / "early_stopping")

        self.best_model_path = None
        self.training_history = []

    async def train(self) -> tuple[bool, dict[str, Any]]:
        """
        Execute training with early stopping.

        Returns:
            (success: bool, results: dict)
        """
        try:
            logger.info("🚀 Starting training with early stopping enabled")
            logger.info(f"   Model: {self.model_name}")
            logger.info(f"   Dataset: {self.dataset_path}")
            logger.info(f"   Max epochs: {self.num_epochs}")
            logger.info(f"   Early stopping patience: {self.es_config.patience}")

            # Load model and tokenizer
            model = AutoModelForCausalLM.from_pretrained(self.model_name, device_map="auto")
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)

            # Load dataset
            dataset = self._load_dataset()
            train_dataset, val_dataset = self._split_dataset(dataset)

            # Prepare training arguments with validation
            training_args = TrainingArguments(
                output_dir=str(self.output_dir / "checkpoints"),
                num_train_epochs=self.num_epochs,
                per_device_train_batch_size=self.batch_size,
                per_device_eval_batch_size=self.batch_size,
                learning_rate=self.learning_rate,
                evaluation_strategy="epoch",  # Evaluate every epoch
                save_strategy="epoch",
                load_best_model_at_end=False,  # We handle best model ourselves
                save_total_limit=3,
                logging_steps=100,
                report_to="none",
            )

            # Create trainer with custom callback
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=train_dataset,
                eval_dataset=val_dataset,
                callbacks=[self._create_callback()],
            )

            # Training loop with early stopping
            results = await self._training_loop(trainer, model, tokenizer)

            return True, results

        except Exception as e:
            logger.error(f"❌ Training failed: {e}")
            return False, {"error": str(e)}

    def _create_callback(self):
        """Create a Hugging Face callback for monitoring."""
        from transformers import TrainerCallback

        class EarlyStoppingCallback(TrainerCallback):
            def __init__(self, monitor):
                self.monitor = monitor
                self.stop_training = False

            def on_evaluate(self, args, state, control, metrics=None, **kwargs):
                if metrics is None:
                    return

                if "eval_loss" in metrics:
                    epoch = state.epoch or (state.global_step // state.steps_per_epoch)
                    val_loss = metrics["eval_loss"]

                    es_metrics = self.monitor.check(int(epoch), val_loss)

                    if es_metrics.should_stop:
                        logger.warning(f"🛑 {es_metrics.reason}")
                        control.should_training_stop = True

        return EarlyStoppingCallback(self.es_monitor)

    async def _training_loop(self, trainer, model, tokenizer) -> dict[str, Any]:
        """Execute training loop with epoch-by-epoch monitoring."""
        best_results = None

        for epoch in range(self.num_epochs):
            logger.info(f"\n📊 Epoch {epoch + 1}/{self.num_epochs}")

            # Train one epoch
            train_result = trainer.train()

            # Evaluate
            eval_result = trainer.evaluate()
            val_loss = eval_result.get("eval_loss", float("inf"))

            # Check early stopping
            es_metrics = self.es_monitor.check(epoch + 1, val_loss)

            epoch_result = {
                "epoch": epoch + 1,
                "train_loss": train_result.training_loss,
                "val_loss": val_loss,
                "best_loss": es_metrics.best_loss,
                "early_stopping": {"plateau": es_metrics.is_plateau, "reason": es_metrics.reason},
            }

            self.training_history.append(epoch_result)

            if es_metrics.should_stop:
                logger.warning(f"⏹️  Stopping training: {es_metrics.reason}")
                break

            best_results = epoch_result

        # Save final results
        summary = self.es_monitor.get_summary()
        logger.info("\n✅ Training complete!")
        logger.info(f"   Best loss: {summary['best_loss']:.6f} (epoch {summary['best_epoch']})")
        logger.info(f"   Total epochs: {summary['total_epochs_trained']}")

        return {
            "success": True,
            "training_history": self.training_history,
            "early_stopping_summary": summary,
            "best_results": best_results,
        }

    def _load_dataset(self):
        """Load training dataset."""
        from datasets import load_dataset

        if self.dataset_path.endswith(".json"):
            dataset = load_dataset("json", data_files=self.dataset_path)["train"]
        else:
            dataset = load_dataset(self.dataset_path)

        return dataset

    def _split_dataset(self, dataset, val_split: float = 0.1):
        """Split dataset into train/val."""
        split = dataset.train_test_split(test_size=val_split, seed=42)
        return split["train"], split["test"]


async def main():
    """Example usage."""
    trainer = TrainingWithEarlyStopping(
        model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        dataset_path="datasets/chat/conversations.json",
        output_dir="data_out/training_with_early_stopping",
        num_epochs=50,  # Allow many epochs, early stopping will cut it short
        batch_size=4,
        learning_rate=1e-4,
        enable_early_stopping=True,
        early_stopping_config=EarlyStoppingConfig(patience=5, min_delta=0.001, adaptive_patience=True, max_epochs=50),
    )

    success, results = await trainer.train()

    # Save results
    output = Path("data_out/training_with_early_stopping")
    output.mkdir(parents=True, exist_ok=True)

    with open(output / "training_results.json", "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"\n📊 Results saved to {output}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
