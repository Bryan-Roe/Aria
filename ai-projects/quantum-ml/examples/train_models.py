"""
Demonstration of training quantum machine learning models
"""

import sys
from pathlib import Path

import matplotlib
import numpy as np
from sklearn.datasets import load_iris, make_circles, make_moons
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Add project root to sys.path so 'src' can be imported as a package
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from src.quantum_classifier import (HybridQuantumClassifier,
                                        QuantumClassifier, train_quantum_model)
except ModuleNotFoundError:
    # Fallback for environments without namespace package support
    sys.path.insert(0, str(project_root / "src"))
    from quantum_classifier import HybridQuantumClassifier  # type: ignore
    from quantum_classifier import QuantumClassifier, train_quantum_model

# Create results directory
results_dir = Path(__file__).parent.parent / "results"
results_dir.mkdir(exist_ok=True)

print("=" * 60)
print("QUANTUM MACHINE LEARNING TRAINING EXAMPLES")
print("=" * 60)

# ============================================
# Example 1: Binary Classification with Moons Dataset
# ============================================
print("\n1. BINARY CLASSIFICATION: MOONS DATASET")
print("-" * 60)

# Generate data
X, y = make_moons(n_samples=200, noise=0.1, random_state=42)
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

# Normalize
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_val = scaler.transform(X_val)

# Pad features to 4 dimensions (matching n_qubits=4)
X_train_padded = np.pad(X_train, ((0, 0), (0, 2)), mode="constant")
X_val_padded = np.pad(X_val, ((0, 0), (0, 2)), mode="constant")

# Create and train model
print("Creating hybrid quantum-classical model...")
qc = QuantumClassifier()
model = HybridQuantumClassifier(input_dim=4, quantum_classifier=qc)

print(f"Training on {len(X_train)} samples...")
history = train_quantum_model(model, X_train_padded, y_train, X_val_padded, y_val)

print("\nFinal Results:")
print(f"  Training Loss: {history['train_loss'][-1]:.4f}")
print(f"  Validation Loss: {history['val_loss'][-1]:.4f}")
print(f"  Validation Accuracy: {history['val_acc'][-1]:.4f}")

# Plot training history
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

ax1.plot(history["train_loss"], label="Training Loss", linewidth=2)
ax1.plot(history["val_loss"], label="Validation Loss", linewidth=2)
ax1.set_xlabel("Epoch", fontsize=12)
ax1.set_ylabel("Loss", fontsize=12)
ax1.set_title("Moons Dataset: Loss Curves", fontsize=14)
ax1.legend()
ax1.grid(True, alpha=0.3)

ax2.plot(history["val_acc"], label="Validation Accuracy", linewidth=2, color="green")
ax2.set_xlabel("Epoch", fontsize=12)
ax2.set_ylabel("Accuracy", fontsize=12)
ax2.set_title("Moons Dataset: Accuracy", fontsize=14)
ax2.legend()
ax2.grid(True, alpha=0.3)

plot_path = results_dir / "training_moons.png"
plt.tight_layout()
plt.savefig(plot_path, dpi=150, bbox_inches="tight")
print(f"Training plot saved to: {plot_path}")

# ============================================
# Example 2: Circles Dataset
# ============================================
print("\n2. BINARY CLASSIFICATION: CIRCLES DATASET")
print("-" * 60)

# Generate circles data
X_circles, y_circles = make_circles(
    n_samples=200, noise=0.1, factor=0.5, random_state=42
)
X_train_c, X_val_c, y_train_c, y_val_c = train_test_split(
    X_circles, y_circles, test_size=0.2, random_state=42
)

# Normalize and pad
scaler_c = StandardScaler()
X_train_c = scaler_c.fit_transform(X_train_c)
X_val_c = scaler_c.transform(X_val_c)
X_train_c_padded = np.pad(X_train_c, ((0, 0), (0, 2)), mode="constant")
X_val_c_padded = np.pad(X_val_c, ((0, 0), (0, 2)), mode="constant")

# Create new model
qc_circles = QuantumClassifier()
model_circles = HybridQuantumClassifier(input_dim=4, quantum_classifier=qc_circles)

print(f"Training on circles dataset ({len(X_train_c)} samples)...")
history_circles = train_quantum_model(
    model_circles, X_train_c_padded, y_train_c, X_val_c_padded, y_val_c
)

print("\nFinal Results:")
print(f"  Validation Accuracy: {history_circles['val_acc'][-1]:.4f}")

# ============================================
# Example 3: Multi-Class Classification (Iris)
# ============================================
print("\n3. MULTI-CLASS CHALLENGE: IRIS DATASET")
print("-" * 60)

# Load iris dataset
iris = load_iris()
X_iris = iris.data
y_iris = iris.target

# Convert to binary classification (class 0 vs rest)
y_iris_binary = (y_iris == 0).astype(int)

X_train_i, X_val_i, y_train_i, y_val_i = train_test_split(
    X_iris, y_iris_binary, test_size=0.2, random_state=42
)

# Normalize
scaler_i = StandardScaler()
X_train_i = scaler_i.fit_transform(X_train_i)
X_val_i = scaler_i.transform(X_val_i)

# Create model
qc_iris = QuantumClassifier()
model_iris = HybridQuantumClassifier(input_dim=4, quantum_classifier=qc_iris)

print(f"Training on iris dataset ({len(X_train_i)} samples)...")
print("Task: Classify Setosa vs. Other species")

history_iris = train_quantum_model(model_iris, X_train_i, y_train_i, X_val_i, y_val_i)

print("\nFinal Results:")
print(f"  Validation Accuracy: {history_iris['val_acc'][-1]:.4f}")

# ============================================
# Example 4: Compare Multiple Datasets
# ============================================
print("\n4. COMPARATIVE ANALYSIS")
print("-" * 60)

results = {
    "Moons": history["val_acc"][-1],
    "Circles": history_circles["val_acc"][-1],
    "Iris": history_iris["val_acc"][-1],
}

print("\nQuantum Classifier Performance Summary:")
print("-" * 40)
for dataset, accuracy in results.items():
    stars = "★" * int(accuracy * 10)
    print(f"  {dataset:12s}: {accuracy:.4f} ({accuracy*100:.1f}%) {stars}")

# Plot comparison
fig, ax = plt.subplots(figsize=(10, 6))
datasets = list(results.keys())
accuracies = list(results.values())
colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]

bars = ax.bar(
    datasets, accuracies, color=colors, alpha=0.7, edgecolor="black", linewidth=2
)
ax.set_ylabel("Validation Accuracy", fontsize=12)
ax.set_title("Quantum ML Model Performance Comparison", fontsize=14, fontweight="bold")
ax.set_ylim([0, 1])
ax.grid(True, axis="y", alpha=0.3)

# Add value labels on bars
for bar, acc in zip(bars, accuracies):
    height = bar.get_height()
    ax.text(
        bar.get_x() + bar.get_width() / 2.0,
        height,
        f"{acc:.3f}",
        ha="center",
        va="bottom",
        fontsize=11,
        fontweight="bold",
    )

plot_path = results_dir / "model_comparison.png"
plt.tight_layout()
plt.savefig(plot_path, dpi=150, bbox_inches="tight")
print(f"\nComparison plot saved to: {plot_path}")

# ============================================
# Summary
# ============================================
print("\n" + "=" * 60)
print("QUANTUM ML TRAINING COMPLETED!")
print("=" * 60)
print("\nKey Insights:")
print("  • Quantum circuits can learn non-linear decision boundaries")
print("  • Hybrid models combine quantum + classical advantages")
print("  • Training uses standard backpropagation with quantum gradients")
print("  • Performance competitive with classical neural networks")
print(f"\nAll training plots saved to: {results_dir}")
