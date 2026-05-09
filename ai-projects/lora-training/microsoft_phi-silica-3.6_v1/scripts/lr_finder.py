"""
Learning Rate Finder
Automatically find optimal learning rate using the LR range test
"""

import json
from pathlib import Path
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import numpy as np
import torch
from torch.utils.data import DataLoader
from transformers import AutoModelForCausalLM, AutoTokenizer


class LearningRateFinder:
    """
    Implement Leslie Smith's Learning Rate Range Test
    https://arxiv.org/abs/1506.01186
    """

    def __init__(
        self,
        model: AutoModelForCausalLM,
        optimizer: torch.optim.Optimizer,
        criterion: torch.nn.Module,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
    ):
        self.model = model
        self.optimizer = optimizer
        self.criterion = criterion
        self.device = device

        # Store initial state
        self.initial_state = {
            "model": model.state_dict(),
            "optimizer": optimizer.state_dict(),
        }

        self.results_dir = Path("data_out/lr_finder")
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def range_test(
        self,
        train_loader: DataLoader,
        start_lr: float = 1e-7,
        end_lr: float = 10.0,
        num_iter: int = 100,
        smooth_f: float = 0.05,
        diverge_th: float = 5.0,
    ) -> Dict[str, Any]:
        """
        Perform LR range test

        Args:
            train_loader: Training data loader
            start_lr: Starting learning rate
            end_lr: Ending learning rate
            num_iter: Number of iterations
            smooth_f: Smoothing factor for losses
            diverge_th: Threshold for stopping (multiplier of best loss)

        Returns:
            Dictionary with results
        """
        print("Starting Learning Rate Range Test...")
        print(f"Range: {start_lr} to {end_lr}")
        print(f"Iterations: {num_iter}")

        # Prepare
        self.model.train()
        lrs = []
        losses = []
        best_loss = float("inf")
        avg_loss = 0.0
        beta = smooth_f

        # Create LR schedule
        def lr_lambda(x: float) -> float:
            return float(np.exp(x * np.log(end_lr / start_lr) / (num_iter - 1)))

        # Run test
        data_iterator = iter(train_loader)
        for iteration in range(num_iter):
            # Get batch
            try:
                batch = next(data_iterator)
            except StopIteration:
                data_iterator = iter(train_loader)
                batch = next(data_iterator)

            # Update LR
            lr = start_lr * lr_lambda(iteration)
            for param_group in self.optimizer.param_groups:
                param_group["lr"] = lr

            # Forward pass
            inputs = {k: v.to(self.device) for k, v in batch.items() if k != "labels"}
            labels = (
                batch["labels"].to(self.device)
                if "labels" in batch
                else inputs["input_ids"]
            )

            outputs = self.model(**inputs, labels=labels)
            loss = outputs.loss

            # Backward pass
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

            # Record
            lrs.append(lr)
            losses.append(loss.item())

            # Smooth loss
            avg_loss = beta * avg_loss + (1 - beta) * loss.item()
            smoothed_loss = avg_loss / (1 - beta ** (iteration + 1))

            # Track best loss
            if smoothed_loss < best_loss:
                best_loss = smoothed_loss

            # Check for divergence
            if smoothed_loss > diverge_th * best_loss:
                print(f"\nStopping early at iteration {iteration} (loss diverged)")
                break

            # Progress
            if (iteration + 1) % 10 == 0:
                print(
                    f"Iteration {iteration + 1}/{num_iter} | LR: {lr:.2e} | Loss: {smoothed_loss:.4f}"
                )

        # Restore initial state
        self.model.load_state_dict(self.initial_state["model"])
        self.optimizer.load_state_dict(self.initial_state["optimizer"])

        # Analyze results
        results = self._analyze_results(lrs, losses, smooth_f)

        # Create visualization
        self._create_plot(lrs, losses, results["suggested_lr"])

        # Save results
        self._save_results(results)

        return results

    def _analyze_results(
        self, lrs: List[float], losses: List[float], smooth_f: float
    ) -> Dict[str, Any]:
        """Analyze LR finder results"""
        # Smooth losses
        smoothed_losses = []
        avg_loss = 0.0
        beta = smooth_f

        for i, loss in enumerate(losses):
            avg_loss = beta * avg_loss + (1 - beta) * loss
            smoothed_loss = avg_loss / (1 - beta ** (i + 1))
            smoothed_losses.append(smoothed_loss)

        # Find minimum loss
        min_loss_idx = np.argmin(smoothed_losses)
        min_loss_lr = lrs[min_loss_idx]

        # Find steepest gradient (maximum negative slope)
        gradients = np.gradient(smoothed_losses)
        steepest_idx = np.argmin(gradients)
        steepest_lr = lrs[steepest_idx]

        # Suggest LR (typically 1/10th of LR at steepest gradient)
        suggested_lr = steepest_lr / 10

        # Alternative: Use LR at minimum loss divided by 10-20
        alt_suggested_lr = min_loss_lr / 10

        return {
            "suggested_lr": suggested_lr,
            "alternative_lr": alt_suggested_lr,
            "min_loss_lr": min_loss_lr,
            "steepest_gradient_lr": steepest_lr,
            "min_loss": smoothed_losses[min_loss_idx],
            "all_lrs": lrs,
            "all_losses": losses,
            "smoothed_losses": smoothed_losses,
        }

    def _create_plot(self, lrs: List[float], losses: List[float], suggested_lr: float):
        """Create LR finder plot"""
        try:
            plt.figure(figsize=(10, 6))
            plt.plot(lrs, losses, label="Loss", alpha=0.3)

            # Smooth losses for better visualization
            from scipy.ndimage import uniform_filter1d

            smoothed = uniform_filter1d(losses, size=min(10, len(losses)))
            plt.plot(lrs, smoothed, label="Smoothed Loss", linewidth=2)

            # Mark suggested LR
            plt.axvline(
                suggested_lr,
                color="r",
                linestyle="--",
                label=f"Suggested LR: {suggested_lr:.2e}",
            )

            plt.xscale("log")
            plt.xlabel("Learning Rate")
            plt.ylabel("Loss")
            plt.title("Learning Rate Finder")
            plt.legend()
            plt.grid(True, alpha=0.3)

            plot_path = self.results_dir / "lr_finder_plot.png"
            plt.savefig(plot_path, dpi=150, bbox_inches="tight")
            plt.close()

            print(f"\n✓ Plot saved to {plot_path}")

        except ImportError:
            print("⚠ matplotlib not available, skipping plot")
        except Exception as e:
            print(f"⚠ Error creating plot: {e}")

    def _save_results(self, results: Dict[str, Any]):
        """Save LR finder results"""
        # Remove large arrays for JSON
        save_results = results.copy()
        save_results.pop("all_lrs", None)
        save_results.pop("all_losses", None)
        save_results.pop("smoothed_losses", None)

        output_file = self.results_dir / "lr_finder_results.json"
        with open(output_file, "w") as f:
            json.dump(save_results, f, indent=2)

        print(f"✓ Results saved to {output_file}")
        print("\n📊 Recommended Learning Rates:")
        print(f"  Primary suggestion: {results['suggested_lr']:.2e}")
        print(f"  Alternative: {results['alternative_lr']:.2e}")
        print(f"  LR at min loss: {results['min_loss_lr']:.2e}")


def main():
    """CLI for LR finder"""
    import argparse

    parser = argparse.ArgumentParser(description="Learning Rate Finder")
    parser.add_argument("--model", type=str, required=True, help="Model path")
    parser.add_argument("--dataset", type=str, required=True, help="Dataset path")
    parser.add_argument("--start-lr", type=float, default=1e-7, help="Starting LR")
    parser.add_argument("--end-lr", type=float, default=10.0, help="Ending LR")
    parser.add_argument(
        "--num-iter", type=int, default=100, help="Number of iterations"
    )
    parser.add_argument("--batch-size", type=int, default=1, help="Batch size")

    args = parser.parse_args()

    print("Loading model and dataset...")

    # Load model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = AutoModelForCausalLM.from_pretrained(args.model).to(device)
    tokenizer = AutoTokenizer.from_pretrained(args.model)

    # Load dataset (simplified)
    # In practice, you'd load and prepare your actual dataset
    print(
        "Note: Using simplified dataset loading. Integrate with your actual data pipeline."
    )

    # Create optimizer
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    criterion = torch.nn.CrossEntropyLoss()

    # Run LR finder
    lr_finder = LearningRateFinder(model, optimizer, criterion, device)

    # You would pass your actual train_loader here
    print("\nTo use LR finder in your training script:")
    print("```python")
    print("from scripts.lr_finder import LearningRateFinder")
    print("")
    print("lr_finder = LearningRateFinder(model, optimizer, criterion)")
    print("results = lr_finder.range_test(train_loader)")
    print("suggested_lr = results['suggested_lr']")
    print("```")


if __name__ == "__main__":
    main()
