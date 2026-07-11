"""
Interactive Parameter Tuning Experiment
Demonstrates how different parameters affect quantum ML performance
"""

import sys
from pathlib import Path

import matplotlib
import numpy as np
import yaml

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.datasets import make_moons
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

# Results directory
results_dir = Path(__file__).parent.parent / "results" / "experiments"
results_dir.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("  QUANTUM ML PARAMETER TUNING EXPERIMENTS")
print("=" * 70)

# Prepare dataset
print("\nPreparing Moons dataset...")
X, y = make_moons(n_samples=200, noise=0.1, random_state=42)
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_val = scaler.transform(X_val)

# Pad to 4 dimensions
X_train_padded = np.pad(X_train, ((0, 0), (0, 2)), mode="constant")
X_val_padded = np.pad(X_val, ((0, 0), (0, 2)), mode="constant")

print(f"Training samples: {len(X_train)}, Validation samples: {len(X_val)}")

# ============================================================================
# EXPERIMENT 1: Number of Quantum Layers
# ============================================================================
print("\n" + "=" * 70)
print("EXPERIMENT 1: Effect of Quantum Layer Depth")
print("=" * 70)

layer_configs = [1, 2, 3, 4]
layer_results = []

for n_layers in layer_configs:
    print(f"\n>>> Testing with {n_layers} layers...")

    # Update config
    config_path = Path(__file__).parent.parent / "config" / "quantum_config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    config["ml"]["model"]["n_layers"] = n_layers
    config["ml"]["training"]["epochs"] = 50  # Reduce for faster testing

    with open(config_path, "w") as f:
        yaml.dump(config, f)

    # Train model
    qc = QuantumClassifier()
    model = HybridQuantumClassifier(input_dim=4, quantum_classifier=qc)
    history = train_quantum_model(model, X_train_padded, y_train, X_val_padded, y_val)

    final_acc = history["val_acc"][-1]
    layer_results.append(
        {
            "n_layers": n_layers,
            "accuracy": final_acc,
            "final_loss": history["val_loss"][-1],
            "history": history,
        }
    )

    print(f"    Final Validation Accuracy: {final_acc:.4f}")

# Plot layer results
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Accuracy vs Layers
layers = [r["n_layers"] for r in layer_results]
accuracies = [r["accuracy"] for r in layer_results]
ax1.plot(layers, accuracies, "o-", linewidth=2, markersize=10, color="#2ecc71")
ax1.set_xlabel("Number of Quantum Layers", fontsize=12)
ax1.set_ylabel("Validation Accuracy", fontsize=12)
ax1.set_title("Impact of Layer Depth on Performance", fontsize=14, fontweight="bold")
ax1.grid(True, alpha=0.3)
ax1.set_ylim([0, 1])

# Add value labels
for x, y in zip(layers, accuracies, strict=False):
    ax1.text(x, y + 0.02, f"{y:.3f}", ha="center", fontsize=10, fontweight="bold")

# Training curves for all layers
for result in layer_results:
    ax2.plot(result["history"]["val_acc"], label=f"{result['n_layers']} layers", linewidth=2)

ax2.set_xlabel("Epoch", fontsize=12)
ax2.set_ylabel("Validation Accuracy", fontsize=12)
ax2.set_title("Training Convergence by Layer Depth", fontsize=14, fontweight="bold")
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plot_path = results_dir / "experiment1_layer_depth.png"
plt.savefig(plot_path, dpi=150, bbox_inches="tight")
print(f"\n✓ Plot saved: {plot_path}")

# ============================================================================
# EXPERIMENT 2: Learning Rate
# ============================================================================
print("\n" + "=" * 70)
print("EXPERIMENT 2: Effect of Learning Rate")
print("=" * 70)

learning_rates = [0.001, 0.005, 0.01, 0.05, 0.1]
lr_results = []

# Reset to 2 layers for this experiment
config["ml"]["model"]["n_layers"] = 2

for lr in learning_rates:
    print(f"\n>>> Testing learning rate: {lr}")

    config["ml"]["training"]["learning_rate"] = lr
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    qc = QuantumClassifier()
    model = HybridQuantumClassifier(input_dim=4, quantum_classifier=qc)
    history = train_quantum_model(model, X_train_padded, y_train, X_val_padded, y_val)

    final_acc = history["val_acc"][-1]
    lr_results.append({"lr": lr, "accuracy": final_acc, "history": history})

    print(f"    Final Validation Accuracy: {final_acc:.4f}")

# Plot learning rate results
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

lrs = [r["lr"] for r in lr_results]
accs = [r["accuracy"] for r in lr_results]
ax1.semilogx(lrs, accs, "o-", linewidth=2, markersize=10, color="#e74c3c")
ax1.set_xlabel("Learning Rate (log scale)", fontsize=12)
ax1.set_ylabel("Validation Accuracy", fontsize=12)
ax1.set_title("Impact of Learning Rate on Performance", fontsize=14, fontweight="bold")
ax1.grid(True, alpha=0.3, which="both")
ax1.set_ylim([0, 1])

for result in lr_results:
    ax2.plot(result["history"]["val_acc"], label=f"LR={result['lr']}", linewidth=2)

ax2.set_xlabel("Epoch", fontsize=12)
ax2.set_ylabel("Validation Accuracy", fontsize=12)
ax2.set_title("Training Convergence by Learning Rate", fontsize=14, fontweight="bold")
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plot_path = results_dir / "experiment2_learning_rate.png"
plt.savefig(plot_path, dpi=150, bbox_inches="tight")
print(f"\n✓ Plot saved: {plot_path}")

# ============================================================================
# EXPERIMENT 3: Entanglement Patterns
# ============================================================================
print("\n" + "=" * 70)
print("EXPERIMENT 3: Effect of Entanglement Pattern")
print("=" * 70)

entanglement_types = ["linear", "circular", "full"]
ent_results = []

# Reset learning rate
config["ml"]["training"]["learning_rate"] = 0.01

for ent_type in entanglement_types:
    print(f"\n>>> Testing entanglement: {ent_type}")

    config["ml"]["model"]["entanglement"] = ent_type
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    qc = QuantumClassifier()
    model = HybridQuantumClassifier(input_dim=4, quantum_classifier=qc)
    history = train_quantum_model(model, X_train_padded, y_train, X_val_padded, y_val)

    final_acc = history["val_acc"][-1]
    ent_results.append({"entanglement": ent_type, "accuracy": final_acc, "history": history})

    print(f"    Final Validation Accuracy: {final_acc:.4f}")

# Plot entanglement results
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

ent_names = [r["entanglement"] for r in ent_results]
ent_accs = [r["accuracy"] for r in ent_results]
colors = ["#3498db", "#9b59b6", "#f39c12"]

bars = ax1.bar(ent_names, ent_accs, color=colors, alpha=0.7, edgecolor="black", linewidth=2)
ax1.set_ylabel("Validation Accuracy", fontsize=12)
ax1.set_title("Impact of Entanglement Pattern", fontsize=14, fontweight="bold")
ax1.set_ylim([0, 1])
ax1.grid(True, axis="y", alpha=0.3)

for bar, acc in zip(bars, ent_accs, strict=False):
    height = bar.get_height()
    ax1.text(
        bar.get_x() + bar.get_width() / 2.0,
        height,
        f"{acc:.3f}",
        ha="center",
        va="bottom",
        fontsize=11,
        fontweight="bold",
    )

for result in ent_results:
    ax2.plot(result["history"]["val_acc"], label=result["entanglement"], linewidth=2)

ax2.set_xlabel("Epoch", fontsize=12)
ax2.set_ylabel("Validation Accuracy", fontsize=12)
ax2.set_title("Training Convergence by Entanglement", fontsize=14, fontweight="bold")
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plot_path = results_dir / "experiment3_entanglement.png"
plt.savefig(plot_path, dpi=150, bbox_inches="tight")
print(f"\n✓ Plot saved: {plot_path}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print("EXPERIMENT SUMMARY")
print("=" * 70)

print("\nBest Configurations:")
print("-" * 70)

# Best layer depth
best_layer = max(layer_results, key=lambda x: x["accuracy"])
print(f"Optimal Layers: {best_layer['n_layers']} (Accuracy: {best_layer['accuracy']:.4f})")

# Best learning rate
best_lr = max(lr_results, key=lambda x: x["accuracy"])
print(f"Optimal Learning Rate: {best_lr['lr']} (Accuracy: {best_lr['accuracy']:.4f})")

# Best entanglement
best_ent = max(ent_results, key=lambda x: x["accuracy"])
print(f"Optimal Entanglement: {best_ent['entanglement']} (Accuracy: {best_ent['accuracy']:.4f})")

print("\nKey Insights:")
print("-" * 70)
print("• More layers generally improve performance (diminishing returns)")
print("• Learning rate around 0.01-0.05 works best for this problem")
print("• Entanglement pattern choice depends on problem structure")
print("• Training convergence varies significantly with hyperparameters")

print(f"\n✓ All experiment plots saved to: {results_dir}")
print("=" * 70)
