"""
Train Hybrid Quantum-Classical model from a CSV dataset in datasets/.

Usage (PowerShell):
    python .\\scripts\\train_from_dataset.py --dataset banknote --epochs 2
    python .\\scripts\\train_from_dataset.py --dataset ionosphere --epochs 2
    python .\\scripts\\train_from_dataset.py --dataset sonar --epochs 2
    python .\\scripts\\train_from_dataset.py --dataset heart_disease --epochs 2

This script reads the workspace dataset index at ../../datasets/dataset_index.json,
loads the selected dataset, preprocesses to match n_qubits from config,
and trains the HybridQuantumClassifier with a small number of epochs by default.

Results are saved under results/datasets/<dataset>/
"""

import argparse
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import yaml

# Resolve paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
WORKSPACE_ROOT = PROJECT_ROOT.parent
DATASETS_INDEX = WORKSPACE_ROOT / "datasets" / "dataset_index.json"
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "quantum_config.yaml"
RESULTS_DIR = PROJECT_ROOT / "results" / "datasets"

# Add src to path
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from quantum_classifier import QuantumClassifier, HybridQuantumClassifier, train_quantum_model  # type: ignore


def load_dataset_from_csv(name: str, path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Load known UCI datasets with simple rules per dataset."""
    name = name.lower()

    if name == "banknote":
        # 4 features + 1 label (0/1), no header
        df = pd.read_csv(path, header=None)
        X = df.iloc[:, :-1].values.astype(float)
        y = df.iloc[:, -1].values.astype(int)
        return X, y

    if name == "ionosphere":
        # 34 features + 1 label ('g'/'b'), no header
        df = pd.read_csv(path, header=None)
        # Last column: 'g' (good, 1) or 'b' (bad, 0)
        y = (df.iloc[:, -1] == 'g').astype(int).values
        X = df.iloc[:, :-1].values.astype(float)
        return X, y

    if name == "sonar":
        # 60 features + 1 label ('M'/'R'), no header
        df = pd.read_csv(path, header=None)
        y = (df.iloc[:, -1] == 'M').astype(int).values
        X = df.iloc[:, :-1].values.astype(float)
        return X, y

    if name == "heart_disease":
        # 13 features + 1 label (0..4); convert to binary (>=1 -> 1)
        # Data contains '?' values -> treat as NaN and drop
        df = pd.read_csv(path, header=None, na_values=['?'])
        df = df.dropna()
        # In processed.cleveland.data last column is num (0..4)
        y = (df.iloc[:, -1].astype(int) >= 1).astype(int).values
        X = df.iloc[:, :-1].values.astype(float)
        return X, y

    # Fallback: try generic CSV (last column = label)
    df = pd.read_csv(path)
    X = df.iloc[:, :-1].values
    y = df.iloc[:, -1].values
    # Try to make y binary if not numeric
    if y.dtype == object:
        classes = sorted(pd.Series(y).unique())
        y = (pd.Series(y) == classes[0]).astype(int).values
    return X.astype(float), y.astype(int)


def preprocess(X: np.ndarray, y: np.ndarray, n_qubits: int, test_size: float = 0.2):
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_val = scaler.transform(X_val)

    pca = None
    if X_train.shape[1] > n_qubits:
        pca = PCA(n_components=n_qubits, random_state=42)
        X_train = pca.fit_transform(X_train)
        X_val = pca.transform(X_val)
    elif X_train.shape[1] < n_qubits:
        # pad with zeros
        pad = n_qubits - X_train.shape[1]
        X_train = np.hstack([X_train, np.zeros((X_train.shape[0], pad))])
        X_val = np.hstack([X_val, np.zeros((X_val.shape[0], pad))])

    return X_train, X_val, y_train, y_val, scaler, pca


def make_quick_config(base_cfg_path: Path, epochs: int, batch_size: int | None = None, lr: float | None = None) -> Path:
    with open(base_cfg_path, 'r') as f:
        cfg = yaml.safe_load(f)
    cfg['ml']['training']['epochs'] = int(epochs)
    if batch_size is not None:
        cfg['ml']['training']['batch_size'] = int(batch_size)
    if lr is not None:
        cfg['ml']['training']['learning_rate'] = float(lr)
    quick_path = PROJECT_ROOT / "config" / "quantum_config.quick.yaml"
    with open(quick_path, 'w') as f:
        yaml.safe_dump(cfg, f)
    return quick_path


def main():
    parser = argparse.ArgumentParser(description="Train hybrid quantum model from CSV dataset")
    parser.add_argument('--dataset', default='banknote', help='Dataset key from dataset_index.json (e.g., banknote)')
    parser.add_argument('--epochs', type=int, default=2)
    parser.add_argument('--batch-size', type=int, default=None)
    parser.add_argument('--lr', type=float, default=None)
    args = parser.parse_args()

    # Load dataset index
    if not DATASETS_INDEX.exists():
        raise FileNotFoundError(f"Dataset index not found: {DATASETS_INDEX}")

    with open(DATASETS_INDEX, 'r') as f:
        index = json.load(f)

    if args.dataset not in index['datasets']:
        available = ', '.join(index['datasets'].keys())
        raise ValueError(f"Unknown dataset '{args.dataset}'. Available: {available}")

    ds_info = index['datasets'][args.dataset]
    data_path = Path(ds_info['path'])
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {data_path}")

    # Load config for model params
    with open(DEFAULT_CONFIG, 'r') as f:
        base_cfg = yaml.safe_load(f)
    n_qubits = int(base_cfg['ml']['model']['n_qubits'])

    print("\n=== Loading dataset ===")
    print(f"Name: {args.dataset}")
    print(f"Path: {data_path}")

    X, y = load_dataset_from_csv(args.dataset, data_path)
    print(f"Shape: {X.shape}, Positive rate: {y.mean():.3f}")

    # Preprocess to match qubits
    X_train, X_val, y_train, y_val, scaler, pca = preprocess(X, y, n_qubits)

    # Build model
    qc = QuantumClassifier(config_path=str(DEFAULT_CONFIG))
    model = HybridQuantumClassifier(input_dim=X_train.shape[1], quantum_classifier=qc)

    # Make quick config override for fast training
    quick_cfg = make_quick_config(DEFAULT_CONFIG, epochs=args.epochs, batch_size=args.batch_size, lr=args.lr)

    # Train
    history = train_quantum_model(
        model,
        X_train,
        y_train,
        X_val,
        y_val,
        config_path=str(quick_cfg)
    )

    # Save results
    out_dir = RESULTS_DIR / args.dataset
    out_dir.mkdir(parents=True, exist_ok=True)

    # Save a simple summary
    summary = {
        "dataset": args.dataset,
        "samples_train": int(X_train.shape[0]),
        "samples_val": int(X_val.shape[0]),
        "features": int(X_train.shape[1]),
        "epochs": int(args.epochs),
        "final_val_acc": float(history['val_acc'][-1]) if history.get('val_acc') else None,
    }
    with open(out_dir / 'training_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"\n✅ Saved summary to {out_dir / 'training_summary.json'}")


if __name__ == "__main__":
    main()
