"""
Test different quantum entanglement patterns on the heart disease dataset.
Patterns: linear, circular, full
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

_OPTIONAL_IMPORT_ERROR: Optional[ImportError] = None

try:
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import torch
    from sklearn.decomposition import PCA
    from sklearn.impute import SimpleImputer
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from torch.utils.data import DataLoader, TensorDataset
except ImportError as exc:  # pragma: no cover - environment dependent
    _OPTIONAL_IMPORT_ERROR = exc

if _OPTIONAL_IMPORT_ERROR is not None and "pytest" in sys.modules:
    import pytest

    pytest.skip(
        f"Optional quantum experiment dependencies unavailable: {_OPTIONAL_IMPORT_ERROR}",
        allow_module_level=True,
    )

# Ensure we can import from src/
ROOT = Path(__file__).parent
sys.path.append(str(ROOT / "src"))

try:
    from hybrid_qnn import HybridQNN, QuantumClassicalTrainer  # noqa: E402
except ImportError as exc:  # pragma: no cover - environment dependent
    _OPTIONAL_IMPORT_ERROR = _OPTIONAL_IMPORT_ERROR or exc

if _OPTIONAL_IMPORT_ERROR is not None and "pytest" in sys.modules:
    import pytest

    pytest.skip(
        f"Optional quantum experiment dependencies unavailable: {_OPTIONAL_IMPORT_ERROR}",
        allow_module_level=True,
    )


def load_heart_disease():
    data_path = ROOT.parent / "datasets" / "quantum" / "heart_disease.csv"
    df = pd.read_csv(data_path, header=None, na_values=["?"])

    # Impute
    imputer = SimpleImputer(strategy="median")
    df[df.columns] = imputer.fit_transform(df)

    X = df.iloc[:, :-1].values
    y = df.iloc[:, -1].values
    y = (y > 0).astype(int)

    return X, y


def preprocess(X, y, n_components=4):
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)

    pca = PCA(n_components=n_components, random_state=42)
    X_train_pca = pca.fit_transform(X_train_scaled)
    X_val_pca = pca.transform(X_val_scaled)

    return (X_train_pca, X_val_pca, y_train, y_val)


def run_experiment(entanglement: str, epochs=12, batch_size=16, lr=0.001):
    X, y = load_heart_disease()
    X_train, X_val, y_train, y_val = preprocess(X, y, n_components=4)

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
        hidden_dim=16,
        n_qubits=4,
        n_quantum_layers=2,
        entanglement=entanglement,
        output_dim=2,
        dropout=0.2,
    )

    trainer = QuantumClassicalTrainer(model, learning_rate=lr, device="cpu")
    trainer.train(train_loader, val_loader, num_epochs=epochs)

    return trainer


def main():
    if _OPTIONAL_IMPORT_ERROR is not None:
        print(f"Missing optional experiment dependencies: {_OPTIONAL_IMPORT_ERROR}")
        return 1

    print("=" * 70)
    print("  TEST ENTANGLEMENT PATTERNS (Heart Disease)")
    print("=" * 70)

    patterns = ["linear", "circular", "full"]
    histories = {}

    for p in patterns:
        print(f"\n⚛️ Running pattern: {p}")
        trainer = run_experiment(p, epochs=12)
        histories[p] = {
            "train_loss": trainer.train_losses,
            "val_acc": trainer.val_accuracies,
            "val_loss": trainer.val_losses,
        }
        print(f"   Final Val Acc: {trainer.val_accuracies[-1]*100:.2f}%")

    # Plot
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    axes[0].set_title("Validation Accuracy by Epoch")
    axes[1].set_title("Training Loss by Epoch")

    for p in patterns:
        axes[0].plot(
            range(1, len(histories[p]["val_acc"]) + 1),
            [a * 100 for a in histories[p]["val_acc"]],
            label=p,
        )
        axes[1].plot(
            range(1, len(histories[p]["train_loss"]) + 1),
            histories[p]["train_loss"],
            label=p,
        )

    axes[0].set_xlabel("Epoch")
    axes[1].set_xlabel("Epoch")
    axes[0].set_ylabel("Accuracy (%)")
    axes[1].set_ylabel("Loss")
    for ax in axes:
        ax.grid(alpha=0.3)
        ax.legend()

    results_dir = ROOT / "results"
    results_dir.mkdir(exist_ok=True)
    plot_path = results_dir / "entanglement_patterns_comparison.png"
    plt.tight_layout()
    plt.savefig(plot_path, dpi=300)
    print(f"\n📊 Saved comparison plot: {plot_path}")

    # Markdown report
    md = []
    md.append("# Entanglement Pattern Comparison (Heart Disease)")
    md.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md.append("\n## Summary")
    for p in patterns:
        md.append(
            f"- {p.title()}: Final Val Acc = {histories[p]['val_acc'][-1]*100:.2f}%"
        )

    report_path = results_dir / "entanglement_patterns_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"✅ Saved report: {report_path}")

    print("\nDone.")


if __name__ == "__main__":
    main()
