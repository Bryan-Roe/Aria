"""
Extend Quantum AI with New Datasets and Architectures
Demonstrates advanced quantum ML techniques
"""

import sys
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.datasets import load_wine, make_classification
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Add project root to sys.path so 'src' can be imported as a package
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from src.quantum_classifier import HybridQuantumClassifier, QuantumClassifier, train_quantum_model
except ModuleNotFoundError:
    # Fallback for environments without namespace package support
    sys.path.insert(0, str(project_root / "src"))
    from quantum_classifier import (
        HybridQuantumClassifier,  # type: ignore
        QuantumClassifier,
        train_quantum_model,
    )

results_dir = Path(__file__).parent.parent / "results" / "extended_datasets"
results_dir.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("  EXTENDED DATASETS FOR QUANTUM ML")
print("=" * 70)

# ============================================================================
# DATASET 1: XOR Problem (Classic Quantum Advantage)
# ============================================================================
print("\n📊 DATASET 1: XOR PROBLEM")
print("=" * 70)
print("The XOR problem is linearly inseparable - perfect for quantum!")

# Create XOR dataset
np.random.seed(42)
n_samples = 200

X_xor = np.random.randn(n_samples, 2)
y_xor = np.logical_xor(X_xor[:, 0] > 0, X_xor[:, 1] > 0).astype(int)

# Add noise
X_xor += np.random.randn(n_samples, 2) * 0.3

X_train, X_val, y_train, y_val = train_test_split(X_xor, y_xor, test_size=0.2, random_state=42)

scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_val = scaler.transform(X_val)

# Pad to 4D
X_train_padded = np.pad(X_train, ((0, 0), (0, 2)), mode="constant")
X_val_padded = np.pad(X_val, ((0, 0), (0, 2)), mode="constant")

print(f"Training samples: {len(X_train)}")
print("Training quantum classifier on XOR...")

qc_xor = QuantumClassifier()
model_xor = HybridQuantumClassifier(input_dim=4, quantum_classifier=qc_xor)
history_xor = train_quantum_model(model_xor, X_train_padded, y_train, X_val_padded, y_val)

print(f"\n✓ XOR Accuracy: {history_xor['val_acc'][-1]:.4f}")

# Visualize XOR
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Original XOR pattern
scatter = ax1.scatter(
    X_xor[:, 0],
    X_xor[:, 1],
    c=y_xor,
    cmap="coolwarm",
    s=50,
    alpha=0.6,
    edgecolors="black",
)
ax1.set_xlabel("Feature 1", fontsize=12)
ax1.set_ylabel("Feature 2", fontsize=12)
ax1.set_title("XOR Pattern (Linearly Inseparable)", fontsize=14, fontweight="bold")
ax1.axhline(y=0, color="k", linestyle="--", alpha=0.3)
ax1.axvline(x=0, color="k", linestyle="--", alpha=0.3)
ax1.grid(True, alpha=0.3)

# Training curve
ax2.plot(history_xor["val_acc"], linewidth=2, color="#e74c3c")
ax2.set_xlabel("Epoch", fontsize=12)
ax2.set_ylabel("Validation Accuracy", fontsize=12)
ax2.set_title(
    f"XOR Training (Final: {history_xor['val_acc'][-1]:.1%})",
    fontsize=14,
    fontweight="bold",
)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(results_dir / "xor_problem.png", dpi=150, bbox_inches="tight")
print(f"✓ Plot saved: {results_dir / 'xor_problem.png'}")

# ============================================================================
# DATASET 2: Spiral Dataset (High Complexity)
# ============================================================================
print("\n\n📊 DATASET 2: SPIRAL DATASET")
print("=" * 70)
print("Intertwined spirals - tests quantum entanglement benefits")


def make_spirals(n_points=100, noise=0.2):
    """Create spiral dataset"""
    n = np.sqrt(np.random.rand(n_points, 1)) * 780 * (2 * np.pi) / 360
    d1x = -np.cos(n) * n + np.random.rand(n_points, 1) * noise
    d1y = np.sin(n) * n + np.random.rand(n_points, 1) * noise
    X1 = np.hstack((d1x, d1y)) / 3

    d2x = np.cos(n) * n + np.random.rand(n_points, 1) * noise
    d2y = -np.sin(n) * n + np.random.rand(n_points, 1) * noise
    X2 = np.hstack((d2x, d2y)) / 3

    X = np.vstack((X1, X2))
    y = np.hstack((np.zeros(n_points), np.ones(n_points)))

    return X, y


X_spiral, y_spiral = make_spirals(n_points=100, noise=0.5)

X_train, X_val, y_train, y_val = train_test_split(X_spiral, y_spiral, test_size=0.2, random_state=42)

scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_val = scaler.transform(X_val)
X_train_padded = np.pad(X_train, ((0, 0), (0, 2)), mode="constant")
X_val_padded = np.pad(X_val, ((0, 0), (0, 2)), mode="constant")

print("Training quantum classifier on Spirals...")
qc_spiral = QuantumClassifier()
model_spiral = HybridQuantumClassifier(input_dim=4, quantum_classifier=qc_spiral)
history_spiral = train_quantum_model(model_spiral, X_train_padded, y_train, X_val_padded, y_val)

print(f"\n✓ Spiral Accuracy: {history_spiral['val_acc'][-1]:.4f}")

# Visualize spirals
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

scatter = ax1.scatter(
    X_spiral[:, 0],
    X_spiral[:, 1],
    c=y_spiral,
    cmap="viridis",
    s=50,
    alpha=0.6,
    edgecolors="black",
)
ax1.set_xlabel("Feature 1", fontsize=12)
ax1.set_ylabel("Feature 2", fontsize=12)
ax1.set_title("Spiral Pattern (Highly Non-linear)", fontsize=14, fontweight="bold")
ax1.grid(True, alpha=0.3)

ax2.plot(history_spiral["val_acc"], linewidth=2, color="#9b59b6")
ax2.set_xlabel("Epoch", fontsize=12)
ax2.set_ylabel("Validation Accuracy", fontsize=12)
ax2.set_title(
    f"Spiral Training (Final: {history_spiral['val_acc'][-1]:.1%})",
    fontsize=14,
    fontweight="bold",
)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(results_dir / "spiral_dataset.png", dpi=150, bbox_inches="tight")
print(f"✓ Plot saved: {results_dir / 'spiral_dataset.png'}")

# ============================================================================
# DATASET 3: Imbalanced Dataset
# ============================================================================
print("\n\n📊 DATASET 3: IMBALANCED DATASET")
print("=" * 70)
print("Tests robustness with class imbalance (90% vs 10%)")

X_imb, y_imb = make_classification(
    n_samples=200,
    n_features=4,
    n_informative=3,
    n_redundant=1,
    n_clusters_per_class=1,
    weights=[0.9, 0.1],  # 90-10 split
    flip_y=0.01,
    random_state=42,
)

X_train, X_val, y_train, y_val = train_test_split(X_imb, y_imb, test_size=0.2, stratify=y_imb, random_state=42)

scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_val = scaler.transform(X_val)

print(f"Class distribution: {np.bincount(y_train)}")
print("Training quantum classifier on Imbalanced data...")

qc_imb = QuantumClassifier()
model_imb = HybridQuantumClassifier(input_dim=4, quantum_classifier=qc_imb)
history_imb = train_quantum_model(model_imb, X_train, y_train, X_val, y_val)

print(f"\n✓ Imbalanced Accuracy: {history_imb['val_acc'][-1]:.4f}")

# ============================================================================
# DATASET 4: Wine Quality (Real-world)
# ============================================================================
print("\n\n📊 DATASET 4: WINE QUALITY")
print("=" * 70)
print("Real-world dataset: Wine chemical analysis")

wine = load_wine()
X_wine = wine.data
y_wine = (wine.target == 0).astype(int)  # Class 0 vs rest

X_train, X_val, y_train, y_val = train_test_split(X_wine, y_wine, test_size=0.2, random_state=42)

scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_val = scaler.transform(X_val)

# Reduce to 4 features using PCA approximation (take first 4)
from sklearn.decomposition import PCA

pca = PCA(n_components=4)
X_train = pca.fit_transform(X_train)
X_val = pca.transform(X_val)

print(f"Training samples: {len(X_train)}")
print(f"PCA explained variance: {pca.explained_variance_ratio_.sum():.2%}")
print("Training quantum classifier on Wine...")

qc_wine = QuantumClassifier()
model_wine = HybridQuantumClassifier(input_dim=4, quantum_classifier=qc_wine)
history_wine = train_quantum_model(model_wine, X_train, y_train, X_val, y_val)

print(f"\n✓ Wine Accuracy: {history_wine['val_acc'][-1]:.4f}")

# ============================================================================
# COMPARATIVE SUMMARY
# ============================================================================
print("\n\n" + "=" * 70)
print("EXTENDED DATASETS - COMPARATIVE RESULTS")
print("=" * 70)

results_summary = {
    "XOR": history_xor["val_acc"][-1],
    "Spiral": history_spiral["val_acc"][-1],
    "Imbalanced": history_imb["val_acc"][-1],
    "Wine": history_wine["val_acc"][-1],
}

print("\nFinal Accuracies:")
print("-" * 70)
for dataset, acc in results_summary.items():
    stars = "★" * int(acc * 10)
    print(f"  {dataset:12s}: {acc:.4f} ({acc * 100:.1f}%) {stars}")

# Create summary plot
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes = axes.ravel()

datasets = ["XOR", "Spiral", "Imbalanced", "Wine"]
histories = [history_xor, history_spiral, history_imb, history_wine]
colors = ["#e74c3c", "#9b59b6", "#3498db", "#2ecc71"]

for i, (dataset, history, _color) in enumerate(zip(datasets, histories, colors, strict=False)):
    axes[i].plot(history["train_loss"], label="Train Loss", alpha=0.7, linewidth=2)
    axes[i].plot(history["val_loss"], label="Val Loss", linewidth=2)
    axes[i].set_title(f"{dataset}: Acc={history['val_acc'][-1]:.3f}", fontsize=12, fontweight="bold")
    axes[i].set_xlabel("Epoch")
    axes[i].set_ylabel("Loss")
    axes[i].legend()
    axes[i].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(results_dir / "all_datasets_comparison.png", dpi=150, bbox_inches="tight")
print(f"\n✓ Summary plot saved: {results_dir / 'all_datasets_comparison.png'}")

print("\n" + "=" * 70)
print("INSIGHTS AND RECOMMENDATIONS")
print("=" * 70)

print("\n✅ Successful on:")
print("  • XOR: Quantum entanglement handles non-linearity")
print("  • Wine: Real-world data works with proper preprocessing")

print("\n⚠️  Challenging:")
print("  • Spirals: May need more qubits or specialized encoding")
print("  • Imbalanced: Consider weighted loss functions")

print("\n🎯 Next Steps:")
print("  1. Try different quantum feature maps")
print("  2. Implement quantum data re-uploading")
print("  3. Test with 6-8 qubits for complex patterns")
print("  4. Add quantum pooling layers")

print(f"\n✓ All plots saved to: {results_dir}")
print("=" * 70)
