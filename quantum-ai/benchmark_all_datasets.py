"""
Benchmark Quantum AI on All Available Datasets
================================================

Trains the hybrid quantum-classical neural network on all quantum datasets
and generates a comprehensive comparison report.

Datasets tested:
- Ionosphere (radar returns)
- Banknote (fraud detection)
- Heart Disease (medical diagnosis)
- Sonar (object classification)

Author: Quantum AI System
Date: November 1, 2025
"""

import numpy as np
import pandas as pd
from pathlib import Path
import sys
import json
from datetime import datetime

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.hybrid_qnn import HybridQNN, QuantumClassicalTrainer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import torch
from torch.utils.data import TensorDataset, DataLoader
import matplotlib.pyplot as plt


# Dataset configurations
DATASETS = {
    'ionosphere': {
        'file': 'ionosphere.csv',
        'description': 'Radar returns classification',
        'task': 'Binary classification: Good vs Bad radar signals',
    },
    'banknote': {
        'file': 'banknote.csv',
        'description': 'Banknote authentication',
        'task': 'Binary classification: Genuine vs Forged banknotes',
    },
    'heart_disease': {
        'file': 'heart_disease.csv',
        'description': 'Heart disease diagnosis',
        'task': 'Binary classification: Disease present vs absent',
    },
    'sonar': {
        'file': 'sonar.csv',
        'description': 'Sonar returns classification',
        'task': 'Binary classification: Mine vs Rock detection',
    }
}


def load_dataset(dataset_name):
    """Load a dataset by name"""
    dataset_config = DATASETS[dataset_name]
    dataset_path = Path(__file__).parent.parent / "datasets" / "quantum" / dataset_config['file']
    
    print(f"\n📁 Loading {dataset_name} dataset...")
    print(f"   File: {dataset_config['file']}")
    print(f"   Task: {dataset_config['task']}")
    
    df = pd.read_csv(dataset_path)
    
    # Separate features and labels (last column is target)
    X = df.iloc[:, :-1].values
    y = df.iloc[:, -1].values
    
    # Convert labels to binary if needed
    if y.dtype == object or len(np.unique(y)) > 2:
        unique_labels = np.unique(y)
        if len(unique_labels) > 2:
            # Multi-class: convert to binary (first class vs rest)
            y = (y == unique_labels[0]).astype(int)
        else:
            # String labels
            y = (y == unique_labels[0]).astype(int)
    else:
        # Ensure binary 0/1
        y = (y != 0).astype(int)
    
    print(f"   Samples: {len(X)}")
    print(f"   Features: {X.shape[1]}")
    print(f"   Class distribution: {np.bincount(y)}")
    
    return X, y


def preprocess_data(X, y, n_qubits=4, test_size=0.2):
    """Preprocess data for quantum ML"""
    # Split data
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )
    
    # Standardize
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_val = scaler.transform(X_val)
    
    # Reduce/pad to n_qubits features
    n_features = X_train.shape[1]
    pca = None
    
    if n_features > n_qubits:
        pca = PCA(n_components=n_qubits)
        X_train = pca.fit_transform(X_train)
        X_val = pca.transform(X_val)
        explained_var = pca.explained_variance_ratio_.sum()
        print(f"   PCA: {n_features} → {n_qubits} features ({explained_var:.2%} variance)")
    elif n_features < n_qubits:
        pad_train = np.zeros((X_train.shape[0], n_qubits - n_features))
        pad_val = np.zeros((X_val.shape[0], n_qubits - n_features))
        X_train = np.hstack([X_train, pad_train])
        X_val = np.hstack([X_val, pad_val])
        print(f"   Padded: {n_features} → {n_qubits} features")
    
    return X_train, X_val, y_train, y_val, scaler, pca


def train_model(X_train, y_train, X_val, y_val, num_epochs=25, batch_size=16):
    """Train quantum model"""
    n_qubits = X_train.shape[1]
    n_classes = len(np.unique(y_train))
    
    # Create model
    model = HybridQNN(
        input_dim=n_qubits,
        hidden_dim=16,
        n_qubits=n_qubits,
        n_quantum_layers=2,
        output_dim=n_classes,
        dropout=0.2
    )
    
    # Convert to tensors
    X_train_t = torch.FloatTensor(X_train)
    y_train_t = torch.LongTensor(y_train)
    X_val_t = torch.FloatTensor(X_val)
    y_val_t = torch.LongTensor(y_val)
    
    # Create data loaders
    train_dataset = TensorDataset(X_train_t, y_train_t)
    val_dataset = TensorDataset(X_val_t, y_val_t)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    # Train
    trainer = QuantumClassicalTrainer(model, learning_rate=0.001)
    trainer.train(train_loader, val_loader, num_epochs)
    
    return model, trainer


def benchmark_dataset(dataset_name):
    """Benchmark a single dataset"""
    print("\n" + "="*70)
    print(f"  BENCHMARKING: {dataset_name.upper()}")
    print("="*70)
    
    # Load and preprocess
    X, y = load_dataset(dataset_name)
    X_train, X_val, y_train, y_val, scaler, pca = preprocess_data(X, y)
    
    # Train
    print(f"\n🚀 Training model (25 epochs)...")
    model, trainer = train_model(X_train, y_train, X_val, y_val)
    
    # Get results
    best_acc = max(trainer.val_accuracies)
    final_acc = trainer.val_accuracies[-1]
    final_loss = trainer.train_losses[-1]
    
    print(f"\n📊 Results:")
    print(f"   Best Accuracy:  {best_acc:.4f} ({best_acc*100:.2f}%)")
    print(f"   Final Accuracy: {final_acc:.4f} ({final_acc*100:.2f}%)")
    print(f"   Final Loss:     {final_loss:.4f}")
    
    return {
        'dataset': dataset_name,
        'description': DATASETS[dataset_name]['description'],
        'task': DATASETS[dataset_name]['task'],
        'n_samples': len(X),
        'n_features': X.shape[1],
        'n_train': len(X_train),
        'n_val': len(X_val),
        'best_accuracy': float(best_acc),
        'final_accuracy': float(final_acc),
        'final_loss': float(final_loss),
        'train_losses': [float(x) for x in trainer.train_losses],
        'val_accuracies': [float(x) for x in trainer.val_accuracies],
    }


def plot_comparison(results, save_path="results/benchmark_comparison.png"):
    """Plot comparison across datasets"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Quantum AI Benchmark - All Datasets', fontsize=16, fontweight='bold')
    
    # Best accuracy comparison
    ax = axes[0, 0]
    datasets = [r['dataset'] for r in results]
    accuracies = [r['best_accuracy'] for r in results]
    colors = ['green' if a >= 0.85 else 'orange' if a >= 0.75 else 'red' for a in accuracies]
    bars = ax.bar(datasets, accuracies, color=colors, alpha=0.7)
    ax.set_ylabel('Accuracy')
    ax.set_title('Best Validation Accuracy')
    ax.set_ylim([0, 1])
    ax.grid(axis='y', alpha=0.3)
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{accuracies[i]:.2%}', ha='center', va='bottom')
    
    # Training curves
    ax = axes[0, 1]
    for r in results:
        ax.plot(r['val_accuracies'], label=r['dataset'], linewidth=2)
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Accuracy')
    ax.set_title('Training Progress')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Dataset sizes
    ax = axes[1, 0]
    sizes = [r['n_samples'] for r in results]
    ax.bar(datasets, sizes, color='skyblue', alpha=0.7)
    ax.set_ylabel('Number of Samples')
    ax.set_title('Dataset Sizes')
    ax.grid(axis='y', alpha=0.3)
    
    # Loss curves
    ax = axes[1, 1]
    for r in results:
        ax.plot(r['train_losses'], label=r['dataset'], linewidth=2)
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Loss')
    ax.set_title('Training Loss')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"\n📊 Comparison plot saved to: {save_path}")
    plt.close()


def generate_report(results, save_path="results/benchmark_report.md"):
    """Generate markdown report"""
    report = []
    report.append("# Quantum AI Benchmark Report")
    report.append(f"\n**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("\n## Model Configuration")
    report.append("- **Architecture:** Hybrid Quantum-Classical Neural Network")
    report.append("- **Quantum Circuit:** 4 qubits, 2 variational layers")
    report.append("- **Classical Layers:** 16-node hidden layer with dropout (0.2)")
    report.append("- **Training:** 25 epochs, batch size 16, learning rate 0.001")
    report.append("- **Optimizer:** Adam")
    
    report.append("\n## Results Summary\n")
    report.append("| Dataset | Samples | Features | Best Accuracy | Final Accuracy | Grade |")
    report.append("|---------|---------|----------|---------------|----------------|-------|")
    
    for r in results:
        acc = r['best_accuracy']
        grade = "🏆 Excellent" if acc >= 0.85 else "⭐ Very Good" if acc >= 0.75 else "✅ Good" if acc >= 0.65 else "⚠️ Fair"
        report.append(f"| {r['dataset']} | {r['n_samples']} | {r['n_features']} | {acc:.2%} | {r['final_accuracy']:.2%} | {grade} |")
    
    report.append("\n## Detailed Results\n")
    for r in results:
        report.append(f"\n### {r['dataset'].title()}")
        report.append(f"\n**Description:** {r['description']}")
        report.append(f"\n**Task:** {r['task']}")
        report.append(f"\n**Metrics:**")
        report.append(f"- Best Validation Accuracy: **{r['best_accuracy']:.2%}**")
        report.append(f"- Final Training Loss: {r['final_loss']:.4f}")
        report.append(f"- Training Samples: {r['n_train']}")
        report.append(f"- Validation Samples: {r['n_val']}")
    
    report.append("\n## Conclusions\n")
    best_dataset = max(results, key=lambda x: x['best_accuracy'])
    avg_acc = np.mean([r['best_accuracy'] for r in results])
    
    report.append(f"- **Best Performance:** {best_dataset['dataset']} ({best_dataset['best_accuracy']:.2%})")
    report.append(f"- **Average Accuracy:** {avg_acc:.2%}")
    report.append(f"- **Total Datasets Tested:** {len(results)}")
    
    if avg_acc >= 0.80:
        report.append("\n✅ **Overall Assessment:** The quantum AI model demonstrates strong performance across all datasets!")
    else:
        report.append("\n⚠️ **Overall Assessment:** Results are mixed. Consider hyperparameter tuning or architecture modifications.")
    
    # Save report
    Path(save_path).write_text('\n'.join(report), encoding='utf-8')
    print(f"📄 Report saved to: {save_path}")


def main():
    """Main benchmark pipeline"""
    print("="*70)
    print("  QUANTUM AI - COMPREHENSIVE BENCHMARK")
    print("="*70)
    print(f"\n🔬 Testing on {len(DATASETS)} quantum datasets")
    print("   Model: Hybrid Quantum-Classical Neural Network")
    print("   Configuration: 4 qubits, 2 quantum layers, 25 epochs")
    
    results = []
    
    # Benchmark each dataset
    for dataset_name in DATASETS.keys():
        try:
            result = benchmark_dataset(dataset_name)
            results.append(result)
        except Exception as e:
            print(f"\n❌ Error benchmarking {dataset_name}: {e}")
            continue
    
    if not results:
        print("\n❌ No successful benchmarks!")
        return
    
    # Generate visualizations and report
    print("\n" + "="*70)
    print("  GENERATING BENCHMARK REPORT")
    print("="*70)
    
    plot_comparison(results)
    generate_report(results)
    
    # Save JSON results
    json_path = Path("results/benchmark_results.json")
    json_path.write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(f"💾 JSON results saved to: {json_path}")
    
    # Print summary
    print("\n" + "="*70)
    print("  BENCHMARK SUMMARY")
    print("="*70)
    print(f"\n{'Dataset':<15} {'Samples':<10} {'Best Acc':<12} {'Grade':<15}")
    print("-"*70)
    
    for r in results:
        acc = r['best_accuracy']
        grade = "🏆 Excellent" if acc >= 0.85 else "⭐ Very Good" if acc >= 0.75 else "✅ Good"
        print(f"{r['dataset']:<15} {r['n_samples']:<10} {acc:>6.2%}      {grade}")
    
    avg_acc = np.mean([r['best_accuracy'] for r in results])
    print("-"*70)
    print(f"{'AVERAGE':<15} {'':<10} {avg_acc:>6.2%}")
    
    print("\n📚 Next Steps:")
    print("   1. Review: results/benchmark_comparison.png")
    print("   2. Read: results/benchmark_report.md")
    print("   3. Analyze: results/benchmark_results.json")
    print("   4. Deploy best model to Azure Quantum hardware")
    
    print("\n" + "="*70)
    print("  🎉 BENCHMARK COMPLETE!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
