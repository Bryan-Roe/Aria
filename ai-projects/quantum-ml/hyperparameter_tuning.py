"""
Hyperparameter tuning for HybridQNN on Heart Disease dataset.

NOTE: This is a simplified/quick version for the Heart Disease dataset.
For comprehensive hyperparameter optimization across multiple datasets,
use hyperparameter_optimization.py instead.

Supports a quick mode for small grids to keep runs fast.
"""

import itertools
import json
import sys
from datetime import datetime
from pathlib import Path

import torch
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, TensorDataset

# Import model code
ROOT = Path(__file__).parent
sys.path.append(str(ROOT / "src"))
from dataset_loader import load_dataset, preprocess_for_qubits  # noqa: E402
from hybrid_qnn import HybridQNN, QuantumClassicalTrainer  # noqa: E402


def load_heart_disease():
    """Load heart disease dataset - wrapper for backward compatibility"""
    X, y, _ = load_dataset("heart_disease")
    return X, y


def preprocess(X, y, n_components=4):
    """Preprocess data - wrapper using shared preprocess_for_qubits"""
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    X_train, X_val, scaler, pca = preprocess_for_qubits(X_train, X_val, n_components)

    return (X_train, X_val, y_train, y_val)


def train_eval(config, X_train, X_val, y_train, y_val):
    batch_size = config["batch_size"]
    lr = config["learning_rate"]
    n_layers = config["n_quantum_layers"]
    hidden_dim = config["hidden_dim"]

    X_train_t = torch.tensor(X_train, dtype=torch.float32)
    y_train_t = torch.tensor(y_train, dtype=torch.long)
    X_val_t = torch.tensor(X_val, dtype=torch.float32)
    y_val_t = torch.tensor(y_val, dtype=torch.long)

    train_ds = TensorDataset(X_train_t, y_train_t)
    val_ds = TensorDataset(X_val_t, y_val_t)

    train_loader = DataLoader(
        train_ds, batch_size=batch_size, shuffle=True, drop_last=True
    )
    val_loader = DataLoader(
        val_ds, batch_size=batch_size, shuffle=False, drop_last=False
    )

    model = HybridQNN(
        input_dim=4,
        hidden_dim=hidden_dim,
        n_qubits=4,
        n_quantum_layers=n_layers,
        entanglement="linear",
        output_dim=2,
        dropout=0.2,
    )

    trainer = QuantumClassicalTrainer(model, learning_rate=lr, device="cpu")
    trainer.train(train_loader, val_loader, num_epochs=config["epochs"])

    best_val_acc = max(trainer.val_accuracies) if trainer.val_accuracies else 0.0

    return {
        "config": config,
        "best_val_acc": float(best_val_acc),
        "final_val_acc": (
            float(trainer.val_accuracies[-1]) if trainer.val_accuracies else 0.0
        ),
        "final_val_loss": float(trainer.val_losses[-1]) if trainer.val_losses else 0.0,
        "history": {
            "train_loss": [float(x) for x in trainer.train_losses],
            "val_acc": [float(x) for x in trainer.val_accuracies],
            "val_loss": [float(x) for x in trainer.val_losses],
        },
    }


def main(quick=True):
    print("=" * 70)
    print("  HYPERPARAMETER TUNING (Heart Disease)")
    print("=" * 70)

    # Load and preprocess
    X, y = load_heart_disease()
    X_train, X_val, y_train, y_val = preprocess(X, y, n_components=4)

    # Define grids
    if quick:
        learning_rates = [1e-3]
        batch_sizes = [16]
        n_layers_list = [1, 2]
        hidden_dims = [16]
        epochs = 10
    else:
        learning_rates = [1e-3, 5e-4]
        batch_sizes = [8, 16]
        n_layers_list = [1, 2, 3]
        hidden_dims = [16, 32]
        epochs = 15

    grid = list(
        itertools.product(learning_rates, batch_sizes, n_layers_list, hidden_dims)
    )
    print(f"Total trials: {len(grid)}")

    results = []
    best = None

    for i, (lr, bs, nl, hd) in enumerate(grid, 1):
        config = {
            "learning_rate": lr,
            "batch_size": bs,
            "n_quantum_layers": nl,
            "hidden_dim": hd,
            "epochs": epochs,
        }
        print(f"\nTrial {i}/{len(grid)}: {config}")
        res = train_eval(config, X_train, X_val, y_train, y_val)
        results.append(res)
        if best is None or res["best_val_acc"] > best["best_val_acc"]:
            best = res
        print(f"   Best Val Acc (this run): {res['best_val_acc']*100:.2f}%")

    # Save results
    results_dir = ROOT / "results"
    results_dir.mkdir(exist_ok=True)
    out_path = results_dir / "hyperparameter_tuning_results.json"
    best_path = results_dir / "hyperparameter_best_config.json"

    with open(out_path, "w") as f:
        json.dump(
            {"timestamp": datetime.now().isoformat(), "results": results}, f, indent=2
        )

    with open(best_path, "w") as f:
        json.dump(best, f, indent=2)

    print("\n" + "=" * 70)
    print("  ✅ TUNING COMPLETE")
    print("=" * 70)
    print(f"Best Validation Accuracy: {best['best_val_acc']*100:.2f}%")
    print(f"Best Config: {best['config']}")
    print(f"Saved results: {out_path}")
    print(f"Saved best config: {best_path}")


if __name__ == "__main__":
    main(quick=True)
