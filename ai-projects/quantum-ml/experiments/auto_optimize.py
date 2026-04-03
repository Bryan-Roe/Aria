"""
Automated Parameter Optimization - Run All Experiments
======================================================

This script runs comprehensive hyperparameter tuning automatically:
1. Layer depth (already completed: 2 layers optimal)
2. Learning rate optimization (0.001 to 0.1)
3. Entanglement pattern comparison (linear, circular, full)

Results saved to: results/experiments/
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# Add parent directory to path to access src modules
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

import torch.nn as nn
import torch.optim as optim
# Import from src package
from src.quantum_classifier import QuantumClassifier


# Simple Hybrid Model Class
class HybridQuantumClassifier(nn.Module):
    def __init__(self, input_dim, quantum_classifier):
        super().__init__()
        self.quantum_classifier = quantum_classifier
        self.classical_layer = nn.Linear(input_dim, quantum_classifier.n_qubits)
        self.output_layer = nn.Linear(1, 2)  # Binary classification

    def forward(self, x):
        x = torch.relu(self.classical_layer(x))
        # Quantum layer expects data in [0, 2π] range
        x = torch.abs(x) % (2 * np.pi)
        quantum_out = self.quantum_classifier.forward(x.detach().numpy())
        quantum_tensor = torch.FloatTensor(quantum_out).unsqueeze(1)
        return self.output_layer(quantum_tensor)


# Simple Trainer Class
class QuantumClassicalTrainer:
    def __init__(self, model, learning_rate=0.001):
        self.model = model
        self.optimizer = optim.Adam(model.parameters(), lr=learning_rate)
        self.criterion = nn.CrossEntropyLoss()
        self.train_losses = []
        self.val_accuracies = []

    def train(self, train_loader, val_loader, num_epochs):
        for epoch in range(num_epochs):
            # Training
            self.model.train()
            epoch_loss = 0
            for X_batch, y_batch in train_loader:
                self.optimizer.zero_grad()
                outputs = self.model(X_batch)
                loss = self.criterion(outputs, y_batch)
                loss.backward()
                self.optimizer.step()
                epoch_loss += loss.item()

            self.train_losses.append(epoch_loss / len(train_loader))

            # Validation
            self.model.eval()
            correct = 0
            total = 0
            with torch.no_grad():
                for X_batch, y_batch in val_loader:
                    outputs = self.model(X_batch)
                    _, predicted = torch.max(outputs, 1)
                    total += y_batch.size(0)
                    correct += (predicted == y_batch).sum().item()

            acc = correct / total
            self.val_accuracies.append(acc)

            if (epoch + 1) % 5 == 0:
                print(
                    f"    Epoch {epoch+1}/{num_epochs} - Loss: {self.train_losses[-1]:.4f}, Val Acc: {acc:.4f}"
                )


import torch
import yaml
from sklearn.datasets import make_moons
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, TensorDataset


# Helper function to train model (add this after imports)
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
    """Train the quantum model"""

    # Convert to PyTorch tensors
    X_train_tensor = torch.FloatTensor(X_train)
    y_train_tensor = torch.LongTensor(y_train)
    X_val_tensor = torch.FloatTensor(X_val)
    y_val_tensor = torch.LongTensor(y_val)

    # Create data loaders
    train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
    val_dataset = TensorDataset(X_val_tensor, y_val_tensor)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    # Create trainer (assuming QuantumClassicalTrainer exists in hybrid_model or create simple trainer)
    trainer = QuantumClassicalTrainer(model, learning_rate=learning_rate)

    # Train
    trainer.train(train_loader, val_loader, num_epochs)

    # Return history
    history = {
        "train_loss": trainer.train_losses,
        "val_acc": trainer.val_accuracies,
        "val_loss": [0] * len(trainer.val_accuracies),
    }

    return history


print("=" * 70)
print("  AUTOMATED PARAMETER OPTIMIZATION")
print("=" * 70)
print("\nRunning all hyperparameter experiments automatically...")
print("This will take approximately 10-15 minutes.\n")

# Create results directory
results_dir = Path(__file__).parent.parent / "results" / "experiments"
results_dir.mkdir(parents=True, exist_ok=True)

# ============================================
# PREPARE DATASET
# ============================================
print("📊 Preparing Moons dataset...")
X, y = make_moons(n_samples=200, noise=0.1, random_state=42)
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_val = scaler.transform(X_val)

# Pad to 4 features
X_train_padded = np.hstack([X_train, np.zeros((X_train.shape[0], 2))])
X_val_padded = np.hstack([X_val, np.zeros((X_val.shape[0], 2))])

print(f"   Training samples: {X_train_padded.shape[0]}")
print(f"   Validation samples: {X_val_padded.shape[0]}\n")

# ============================================
# EXPERIMENT 2: LEARNING RATE OPTIMIZATION
# ============================================
print("=" * 70)
print("EXPERIMENT 2: Learning Rate Optimization")
print("=" * 70)

learning_rates = [0.001, 0.005, 0.01, 0.05, 0.1]
lr_results = []

for lr in learning_rates:
    print(f"\n>>> Testing learning rate: {lr}")

    # Create fresh model
    quantum_clf = QuantumClassifier()

    # Manually set learning rate in config
    config_path = Path(__file__).parent.parent / "config" / "quantum_config.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    original_lr = config["ml"]["training"]["learning_rate"]
    config["ml"]["training"]["learning_rate"] = lr

    # Save temporarily
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    # Train
    model = HybridQuantumClassifier(input_dim=4, quantum_classifier=quantum_clf)

    try:
        history = train_quantum_model(
            model, X_train_padded, y_train, X_val_padded, y_val
        )

        final_acc = history["val_acc"][-1]
        best_acc = max(history["val_acc"])
        lr_results.append({"lr": lr, "final_acc": final_acc, "best_acc": best_acc})

        print(f"    Final Accuracy: {final_acc:.4f}")
        print(f"    Best Accuracy:  {best_acc:.4f}")

    except Exception as e:
        print(f"    ✗ Error: {e}")
        lr_results.append({"lr": lr, "final_acc": 0.0, "best_acc": 0.0})

    # Restore original learning rate
    config["ml"]["training"]["learning_rate"] = original_lr
    with open(config_path, "w") as f:
        yaml.dump(config, f)

# Plot learning rate results
plt.figure(figsize=(10, 6))
lrs = [r["lr"] for r in lr_results]
final_accs = [r["final_acc"] for r in lr_results]
best_accs = [r["best_acc"] for r in lr_results]

plt.plot(lrs, final_accs, "o-", label="Final Accuracy", linewidth=2, markersize=8)
plt.plot(lrs, best_accs, "s-", label="Best Accuracy", linewidth=2, markersize=8)
plt.xlabel("Learning Rate", fontsize=12)
plt.ylabel("Validation Accuracy", fontsize=12)
plt.title("Learning Rate Optimization", fontsize=14, fontweight="bold")
plt.xscale("log")
plt.grid(True, alpha=0.3)
plt.legend(fontsize=11)
plt.tight_layout()

lr_plot_path = results_dir / "experiment2_learning_rate.png"
plt.savefig(lr_plot_path, dpi=150, bbox_inches="tight")
print(f"\n✓ Plot saved: {lr_plot_path}")
plt.close()

# ============================================
# EXPERIMENT 3: ENTANGLEMENT PATTERN
# ============================================
print("\n" + "=" * 70)
print("EXPERIMENT 3: Entanglement Pattern Comparison")
print("=" * 70)

entanglement_patterns = ["linear", "circular", "full"]
ent_results = []

for pattern in entanglement_patterns:
    print(f"\n>>> Testing entanglement: {pattern}")

    # Update config
    config_path = Path(__file__).parent.parent / "config" / "quantum_config.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    original_ent = config["ml"]["model"]["entanglement"]
    config["ml"]["model"]["entanglement"] = pattern

    with open(config_path, "w") as f:
        yaml.dump(config, f)

    # Create and train model
    quantum_clf = QuantumClassifier()
    model = HybridQuantumClassifier(input_dim=4, quantum_classifier=quantum_clf)

    try:
        history = train_quantum_model(
            model, X_train_padded, y_train, X_val_padded, y_val
        )

        final_acc = history["val_acc"][-1]
        best_acc = max(history["val_acc"])
        ent_results.append(
            {"pattern": pattern, "final_acc": final_acc, "best_acc": best_acc}
        )

        print(f"    Final Accuracy: {final_acc:.4f}")
        print(f"    Best Accuracy:  {best_acc:.4f}")

    except Exception as e:
        print(f"    ✗ Error: {e}")
        ent_results.append({"pattern": pattern, "final_acc": 0.0, "best_acc": 0.0})

    # Restore original entanglement
    config["ml"]["model"]["entanglement"] = original_ent
    with open(config_path, "w") as f:
        yaml.dump(config, f)

# Plot entanglement results
plt.figure(figsize=(10, 6))
patterns = [r["pattern"] for r in ent_results]
final_accs_ent = [r["final_acc"] for r in ent_results]
best_accs_ent = [r["best_acc"] for r in ent_results]

x = np.arange(len(patterns))
width = 0.35

plt.bar(x - width / 2, final_accs_ent, width, label="Final Accuracy", alpha=0.8)
plt.bar(x + width / 2, best_accs_ent, width, label="Best Accuracy", alpha=0.8)
plt.xlabel("Entanglement Pattern", fontsize=12)
plt.ylabel("Validation Accuracy", fontsize=12)
plt.title("Entanglement Pattern Comparison", fontsize=14, fontweight="bold")
plt.xticks(x, patterns)
plt.legend(fontsize=11)
plt.grid(True, alpha=0.3, axis="y")
plt.tight_layout()

ent_plot_path = results_dir / "experiment3_entanglement.png"
plt.savefig(ent_plot_path, dpi=150, bbox_inches="tight")
print(f"\n✓ Plot saved: {ent_plot_path}")
plt.close()

# ============================================
# FINAL SUMMARY
# ============================================
print("\n" + "=" * 70)
print("  OPTIMIZATION COMPLETE!")
print("=" * 70)

print("\n📊 LEARNING RATE RESULTS:")
print("-" * 50)
for r in lr_results:
    print(f"  LR {r['lr']:.4f}: Final={r['final_acc']:.4f}, Best={r['best_acc']:.4f}")

best_lr = max(lr_results, key=lambda x: x["best_acc"])
print(
    f"\n🏆 Best Learning Rate: {best_lr['lr']:.4f} (Accuracy: {best_lr['best_acc']:.4f})"
)

print("\n📊 ENTANGLEMENT RESULTS:")
print("-" * 50)
for r in ent_results:
    print(f"  {r['pattern']:8s}: Final={r['final_acc']:.4f}, Best={r['best_acc']:.4f}")

best_ent = max(ent_results, key=lambda x: x["best_acc"])
print(
    f"\n🏆 Best Entanglement: {best_ent['pattern']} (Accuracy: {best_ent['best_acc']:.4f})"
)

print("\n💡 OPTIMAL CONFIGURATION:")
print("-" * 50)
print("  Layers:       2 (from previous experiment)")
print(f"  Learning Rate: {best_lr['lr']:.4f}")
print(f"  Entanglement:  {best_ent['pattern']}")
print(f"  Expected Accuracy: ~{best_ent['best_acc']:.1%}")

print("\n📁 Generated Files:")
print(f"  {lr_plot_path}")
print(f"  {ent_plot_path}")

print("\n🚀 Next Steps:")
print("  1. Update config/quantum_config.yaml with optimal parameters")
print("  2. Re-train all models with optimized settings")
print("  3. Deploy to Azure Quantum for hardware testing")

print("\n" + "=" * 70)
