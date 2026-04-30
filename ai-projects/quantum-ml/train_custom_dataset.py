r"""
Train Quantum AI on Your Custom Dataset
======================================

Free-first training pipeline with CLI support for CSVs and built-in presets.
Works 100% locally using simulators (no Azure required). Use this script to
train on your own data without changing code.

Examples (PowerShell):

    # Preset datasets (from datasets/quantum/*.csv)
    python .\train_custom_dataset.py --preset heart --epochs 5 --batch-size 16
    python .\train_custom_dataset.py --preset ionosphere --epochs 5

    # Custom CSV
    python .\train_custom_dataset.py --csv ..\datasets\quantum\banknote.csv `
            --label-col class --epochs 5 --n-qubits 4

Notes:
- Binary or multiclass labels are supported. String labels are auto-encoded.
- Features are standardized and dimension-matched to n_qubits via PCA/padding.

Author: Quantum AI System
Date: November 1, 2025
"""

import os
import sys

# Fix Windows console encoding for emoji support
if os.name == "nt":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

import json

import matplotlib.pyplot as plt
import torch
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from src.hybrid_qnn import HybridQNN, QuantumClassicalTrainer
from torch.utils.data import DataLoader, TensorDataset


def _infer_label_column(df: pd.DataFrame, provided: str | None) -> str:
    """Infer the label/target column if not provided.
    Tries common names, else uses the last column.
    """
    if provided:
        if provided not in df.columns:
            raise ValueError(
                f"Label column '{provided}' not in CSV columns: {list(df.columns)}"
            )
        return provided
    candidates = ["label", "target", "class", "y", "diagnosis", "outcome"]
    for c in candidates:
        if c in df.columns:
            return c
    # Fallback: last column
    return df.columns[-1]


def _encode_labels(y: pd.Series) -> np.ndarray:
    """Encode labels to integer class indices starting at 0.
    - If numeric, cast to int when safe; ensure non-negative contiguous classes.
    - If strings/objects, factorize to 0..K-1.
    """
    if pd.api.types.is_numeric_dtype(y):
        # If binary but not 0/1, normalize to 0/1
        uniq = np.unique(y.dropna())
        if len(uniq) == 2 and set(uniq) != {0, 1}:
            mapping = {uniq.min(): 0, uniq.max(): 1}
            y_enc = y.map(mapping).astype(int).values
        else:
            y_enc = y.astype(int).values
        # Shift to start at 0
        minv = y_enc.min()
        if minv < 0:
            y_enc = y_enc - minv
        return y_enc
    else:
        vals, enc = pd.factorize(y.astype(str))
        return vals


def load_csv_dataset(
    csv_path: str | Path,
    label_col: str | None = None,
    drop_cols: list[str] | None = None,
    handle_missing: str = "auto",
) -> tuple[np.ndarray, np.ndarray]:
    """Load a dataset from CSV.

    Args:
        csv_path: Path to CSV file
        label_col: Column name of the label/target (auto-infer if None)
        drop_cols: Columns to drop before processing
        handle_missing: 'auto' -> treat '?', 'NA', '', 'NaN' as missing

    Returns:
        (X, y) numpy arrays
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    na_values = ["?", "NA", "", "NaN"] if handle_missing == "auto" else None
    df = pd.read_csv(csv_path, na_values=na_values)

    # Drop columns if requested
    if drop_cols:
        missing = [c for c in drop_cols if c not in df.columns]
        if missing:
            raise ValueError(f"Drop columns not found in CSV: {missing}")
        df = df.drop(columns=drop_cols)

    # Determine label column
    y_col = _infer_label_column(df, label_col)
    y = df[y_col]
    X = df.drop(columns=[y_col])

    # Impute missing values in features if needed
    if X.isnull().any().any():
        imputer = SimpleImputer(strategy="median")
        X = pd.DataFrame(imputer.fit_transform(X), columns=X.columns)

    y_enc = _encode_labels(y)
    return X.values, y_enc


def load_preset_dataset(name: str) -> tuple[np.ndarray, np.ndarray]:
    """Load a preset dataset from datasets/quantum/*.csv.

    Presets: heart, ionosphere, sonar, banknote
    """
    base = Path(__file__).parent.parent / "datasets" / "quantum"
    presets = {
        "heart": base / "heart_disease.csv",
        "ionosphere": base / "ionosphere.csv",
        "sonar": base / "sonar.csv",
        "banknote": base / "banknote.csv",
    }
    if name not in presets:
        raise ValueError(f"Unknown preset '{name}'. Choose from {list(presets)}")

    path = presets[name]
    if name == "heart":
        # Special handling for heart disease (binary from multi-class 0..4)
        df = pd.read_csv(path, na_values=["?"])
        y = df.iloc[:, -1]
        X = df.iloc[:, :-1]
        if X.isnull().any().any():
            imputer = SimpleImputer(strategy="median")
            X = pd.DataFrame(imputer.fit_transform(X), columns=X.columns)
        y = (y > 0).astype(int).values
        return X.values, y
    else:
        return load_csv_dataset(path)


def preprocess_data(X, y, n_qubits=4, test_size=0.2):
    """
    Preprocess data for quantum ML

    Args:
        X: Feature matrix
        y: Labels
        n_qubits: Number of qubits (features will be reduced/padded to match)
        test_size: Validation split ratio

    Returns:
        X_train, X_val, y_train, y_val: Preprocessed data
        scaler: Fitted StandardScaler (save this for inference!)
        pca: Fitted PCA (if used, else None)
    """
    print("\n🔧 Preprocessing data...")
    print(f"   Original shape: {X.shape}")
    # Ensure labels are int (for CrossEntropyLoss)
    if not np.issubdtype(y.dtype, np.integer):
        # Factorize as safety net
        vals, y = np.unique(y, return_inverse=True)
    print(f"   Classes: {np.unique(y)}")
    try:
        print(f"   Class distribution: {np.bincount(y)}")
    except Exception:
        pass

    # Split data
    X_train, X_val, y_train, y_val = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=42,
        stratify=y,  # Maintains class balance
    )

    # Standardize (CRITICAL for quantum circuits!)
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_val = scaler.transform(X_val)

    print("   ✅ Standardized (mean≈0, std≈1)")

    # Handle feature dimension
    n_features = X_train.shape[1]
    pca = None

    if n_features < n_qubits:
        # Pad with zeros
        padding_train = np.zeros((X_train.shape[0], n_qubits - n_features))
        X_train = np.hstack([X_train, padding_train])

        padding_val = np.zeros((X_val.shape[0], n_qubits - n_features))
        X_val = np.hstack([X_val, padding_val])

        print(f"   ✅ Padded from {n_features} to {n_qubits} features")

    elif n_features > n_qubits:
        # Use PCA to reduce dimensions
        pca = PCA(n_components=n_qubits)
        X_train = pca.fit_transform(X_train)
        X_val = pca.transform(X_val)

        explained_var = pca.explained_variance_ratio_.sum()
        print(f"   ✅ Reduced from {n_features} to {n_qubits} features using PCA")
        print(f"   ✅ Explained variance: {explained_var:.2%}")
    else:
        print(f"   ✅ Features already match qubits ({n_qubits})")

    print(f"   Final training shape: {X_train.shape}")
    print(f"   Final validation shape: {X_val.shape}")

    return X_train, X_val, y_train, y_val, scaler, pca


def plot_training_results(history, save_path="results/custom_training.png"):
    """Plot training curves"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

    # Loss curves
    ax1.plot(history["train_loss"], label="Training Loss", linewidth=2)
    ax1.plot(history["val_loss"], label="Validation Loss", linewidth=2)
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Loss")
    ax1.set_title("Training Progress")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Accuracy curve
    ax2.plot(
        history["val_acc"], label="Validation Accuracy", linewidth=2, color="green"
    )
    ax2.axhline(
        y=max(history["val_acc"]),
        color="red",
        linestyle="--",
        label=f'Best: {max(history["val_acc"]):.4f}',
    )
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("Accuracy")
    ax2.set_title("Validation Accuracy")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    print(f"\n📊 Training plot saved to: {save_path}")
    plt.close()


def save_model_and_preprocessors(
    model,
    scaler,
    pca=None,
    model_path="results/custom_model.pt",
    scaler_path="results/custom_scaler.pkl",
    pca_path="results/custom_pca.pkl",
):
    """Save model and preprocessing objects"""
    import joblib

    # Save model weights
    torch.save(model.state_dict(), model_path)
    print(f"💾 Model saved to: {model_path}")

    # Save scaler
    joblib.dump(scaler, scaler_path)
    print(f"💾 Scaler saved to: {scaler_path}")

    # Save PCA if used
    if pca is not None:
        joblib.dump(pca, pca_path)
        print(f"💾 PCA saved to: {pca_path}")


def train_quantum_model(
    model,
    X_train,
    y_train,
    X_val,
    y_val,
    num_epochs=20,
    batch_size=32,
    learning_rate=0.001,
):
    """
    Train the quantum model

    Args:
        model: HybridQNN model
        X_train, y_train: Training data
        X_val, y_val: Validation data
        num_epochs: Number of training epochs
        batch_size: Batch size
        learning_rate: Learning rate

    Returns:
        history: Dictionary with training metrics
    """
    # Convert to PyTorch tensors
    X_train_tensor = torch.FloatTensor(X_train)
    y_train_tensor = torch.LongTensor(y_train)
    X_val_tensor = torch.FloatTensor(X_val)
    y_val_tensor = torch.LongTensor(y_val)

    # Create data loaders
    train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
    val_dataset = TensorDataset(X_val_tensor, y_val_tensor)

    # Use drop_last=True to avoid batchnorm errors on final batch of size 1
    train_loader = DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True, drop_last=True
    )
    val_loader = DataLoader(
        val_dataset, batch_size=batch_size, shuffle=False, drop_last=False
    )

    # Create trainer
    trainer = QuantumClassicalTrainer(model, learning_rate=learning_rate)

    # Train
    trainer.train(train_loader, val_loader, num_epochs)

    # Return history (now includes real val_loss from trainer)
    history = {
        "train_loss": trainer.train_losses,
        "val_acc": trainer.val_accuracies,
        "val_loss": trainer.val_losses,
    }

    return history


def _default_n_qubits(
    config_path: str = "config/quantum_config.yaml", fallback: int = 4
) -> int:
    """Read default n_qubits from YAML config if available."""
    try:
        with open(config_path, "r") as f:
            cfg = yaml.safe_load(f)
        return int(cfg.get("ml", {}).get("model", {}).get("n_qubits", fallback))
    except Exception:
        return fallback


def main(argv: list[str] | None = None):
    """Main training pipeline"""
    parser = argparse.ArgumentParser(
        description="Train Hybrid Quantum-Classical model on CSV or preset dataset"
    )
    src_root = Path(__file__).parent
    default_results = src_root / "results"
    parser.add_argument("--csv", type=str, help="Path to CSV file containing dataset")
    parser.add_argument(
        "--preset",
        type=str,
        choices=["heart", "ionosphere", "sonar", "banknote"],
        help="Use a built-in preset dataset",
    )
    parser.add_argument(
        "--label-col", type=str, help="Label/target column name (auto if omitted)"
    )
    parser.add_argument(
        "--drop-cols",
        type=str,
        help="Comma-separated column names to drop before training",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Validation split ratio (default 0.2)",
    )
    parser.add_argument(
        "--n-qubits",
        type=int,
        help="Number of qubits (defaults from config ml.model.n_qubits or 4)",
    )
    parser.add_argument(
        "--epochs", type=int, default=20, help="Training epochs (default 20)"
    )
    parser.add_argument(
        "--batch-size", type=int, default=32, help="Batch size (default 32)"
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=0.001,
        help="Learning rate (default 1e-3)",
    )
    args = parser.parse_args(argv)

    drop_cols = (
        [c.strip() for c in args.drop_cols.split(",")] if args.drop_cols else None
    )
    n_qubits = args.n_qubits or _default_n_qubits()

    print("=" * 70)
    print("  QUANTUM AI - CUSTOM DATASET TRAINING")
    print("=" * 70)
    print(
        f"Using n_qubits={n_qubits}, epochs={args.epochs}, batch={args.batch_size}, lr={args.learning_rate}"
    )

    # ============================================
    # 1. LOAD DATA
    # ============================================
    print("\n📁 Step 1: Loading your data...")
    if args.preset:
        X, y = load_preset_dataset(args.preset)
        print(f"   ✅ Loaded preset dataset: {args.preset}")
        dataset_desc = f"preset:{args.preset}"
    elif args.csv:
        X, y = load_csv_dataset(args.csv, label_col=args.label_col, drop_cols=drop_cols)
        print(f"   ✅ Loaded CSV: {args.csv}")
        dataset_desc = f"csv:{args.csv}"
    else:
        # Fallback demo: scikit-learn wine dataset (binary)
        from sklearn.datasets import load_wine

        data = load_wine()
        X = data.data
        # Binary: Class 0 vs others
        y = (data.target == 0).astype(int)
        print("   ℹ️  No dataset specified. Using demo Wine dataset (binary)")
        dataset_desc = "demo:wine"

    # ============================================
    # 2. PREPROCESS
    # ============================================
    print("\n🔧 Step 2: Preprocessing...")
    X_train, X_val, y_train, y_val, scaler, pca = preprocess_data(
        X, y, n_qubits=n_qubits, test_size=args.test_size
    )

    # ============================================
    # 3. CREATE MODEL
    # ============================================
    print("\n🧠 Step 3: Creating quantum model...")
    n_qubits = X_train.shape[1]  # After preprocessing

    # Determine number of classes
    n_classes = len(np.unique(y_train))

    # Create hybrid quantum-classical model
    model = HybridQNN(
        input_dim=n_qubits,
        hidden_dim=16,
        n_qubits=n_qubits,
        n_quantum_layers=2,
        output_dim=n_classes,
        dropout=0.2,
    )
    print("   ✅ Created HybridQNN")
    print(f"   ✅ Quantum circuit: {n_qubits} qubits, 2 layers")
    print(f"   ✅ Output classes: {n_classes}")

    # ============================================
    # 4. TRAIN MODEL
    # ============================================
    print("\n🚀 Step 4: Training quantum model...")
    print("   This may take a few minutes...")

    history = train_quantum_model(
        model=model,
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
    )

    # ============================================
    # 5. EVALUATE RESULTS
    # ============================================
    print("\n" + "=" * 70)
    print("  TRAINING COMPLETE!")
    print("=" * 70)

    final_train_loss = history["train_loss"][-1]
    final_val_loss = history["val_loss"][-1]
    final_val_acc = history["val_acc"][-1]
    best_val_acc = max(history["val_acc"])

    print("\n📊 Final Results:")
    print(f"   Training Loss:        {final_train_loss:.4f}")
    print(f"   Validation Loss:      {final_val_loss:.4f}")
    print(f"   Validation Accuracy:  {final_val_acc:.4f} ({final_val_acc*100:.2f}%)")
    print(f"   Best Val Accuracy:    {best_val_acc:.4f} ({best_val_acc*100:.2f}%)")

    # Determine performance level
    if best_val_acc >= 0.90:
        grade = "🏆 EXCELLENT!"
        emoji = "🎉"
    elif best_val_acc >= 0.80:
        grade = "⭐ VERY GOOD!"
        emoji = "🚀"
    elif best_val_acc >= 0.70:
        grade = "✅ GOOD"
        emoji = "👍"
    elif best_val_acc >= 0.60:
        grade = "⚠️  FAIR"
        emoji = "📈"
    else:
        grade = "❌ NEEDS IMPROVEMENT"
        emoji = "🔧"

    print(f"\n{emoji} Performance Grade: {grade}")

    # ============================================
    # 6. SAVE MODEL
    # ============================================
    print("\n💾 Step 5: Saving model and preprocessors...")
    # Ensure results directory exists
    results_dir = Path(Path(__file__).parent / "results")
    results_dir.mkdir(parents=True, exist_ok=True)

    model_path = str(results_dir / "custom_model.pt")
    scaler_path = str(results_dir / "custom_scaler.pkl")
    pca_path = str(results_dir / "custom_pca.pkl")
    plot_path = str(results_dir / "custom_training.png")
    summary_path = str(results_dir / "custom_training_summary.json")

    save_model_and_preprocessors(
        model,
        scaler,
        pca,
        model_path=model_path,
        scaler_path=scaler_path,
        pca_path=pca_path,
    )

    # ============================================
    # 7. PLOT RESULTS
    # ============================================
    print("\n📊 Step 6: Generating training plots...")
    plot_training_results(history, save_path=plot_path)

    # ============================================
    # 7. SAVE SUMMARY
    # ============================================
    try:
        y_train_counts = np.bincount(y_train).tolist()
        y_val_counts = np.bincount(y_val).tolist()
    except Exception:
        y_train_counts, y_val_counts = None, None

    pca_explained_variance = None
    if pca is not None and hasattr(pca, "explained_variance_ratio_"):
        try:
            pca_explained_variance = float(np.sum(pca.explained_variance_ratio_))
        except Exception:
            pca_explained_variance = None

    summary = {
        "dataset": dataset_desc,
        "params": {
            "n_qubits": n_qubits,
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "learning_rate": args.learning_rate,
            "test_size": args.test_size,
        },
        "metrics": {
            "train_loss_last": float(final_train_loss),
            "val_loss_last": float(final_val_loss),
            "val_acc_last": float(final_val_acc),
            "val_acc_best": float(best_val_acc),
            "history": {
                "train_loss": [float(x) for x in history["train_loss"]],
                "val_loss": [float(x) for x in history["val_loss"]],
                "val_acc": [float(x) for x in history["val_acc"]],
            },
        },
        "data": {
            "n_train": int(len(X_train)),
            "n_val": int(len(X_val)),
            "n_classes": int(len(np.unique(y_train))),
            "class_distribution_train": y_train_counts,
            "class_distribution_val": y_val_counts,
            "pca_explained_variance": pca_explained_variance,
        },
        "artifacts": {
            "model": model_path,
            "scaler": scaler_path,
            "pca": pca_path if pca is not None else None,
            "plot": plot_path,
        },
    }

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\n📝 Summary saved to: {summary_path}")

    # ============================================
    # 8. RECOMMENDATIONS
    # ============================================
    print("\n💡 Recommendations:")

    if best_val_acc < 0.70:
        print("   ⚠️  Accuracy is low. Try:")
        print(f"      - More training data (currently {len(X_train)} samples)")
        print("      - Better feature engineering")
        print("      - Hyperparameter tuning (run experiments/parameter_tuning.py)")
        print("      - Check if data is properly standardized")

    elif best_val_acc >= 0.90:
        print("   🎉 Excellent performance! Consider:")
        print("      - Deploy to production")
        print("      - Test on Azure Quantum hardware")
        print("      - Try ensemble methods for even better results")

    else:
        print("   ✅ Good performance! To improve further:")
        print("      - Run hyperparameter optimization")
        print("      - Try different quantum circuit architectures")
        print("      - Collect more training data")

    print("\n📚 Next Steps:")
    print("   1. Review training plot: results/custom_training.png")
    print("   2. Load model for inference:")
    print("      model.load_state_dict(torch.load('results/custom_model.pt'))")
    print("   3. Run hyperparameter tuning:")
    print("      python experiments/parameter_tuning.py")
    print("   4. Deploy to Azure Quantum:")
    print("      See experiments/AZURE_QUICKSTART.md")

    print("\n" + "=" * 70)
    print("  🎉 QUANTUM AI TRAINING COMPLETE!")
    print("=" * 70 + "\n")
    return model, history


if __name__ == "__main__":
    model, history = main()
