"""
Hyperparameter Optimization for Quantum Hybrid QNN
================================================

Automated grid search over key hyperparameters to improve performance
on datasets where quantum underperformed vs classical baselines.

Focus: ionosphere and sonar (gaps of ~9-11 pp vs classical)

Hyperparameters swept:
- n_qubits: 3, 4, 5, 6
- n_quantum_layers: 2, 3, 4
- hidden_dim: 16, 32, 64
- learning_rate: 5e-4, 1e-3, 2e-3
- batch_size: 8, 16, 32
- epochs: up to 50 with early stopping (patience=10)

Results saved to: results/hpo_optimization_report.json

Author: Quantum AI System
Date: November 1, 2025
"""

import numpy as np
import pandas as pd
from pathlib import Path
import sys
import json
import itertools
from datetime import datetime
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.hybrid_qnn import HybridQNN, QuantumClassicalTrainer
from src.dataset_loader import load_dataset, preprocess_for_qubits
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import torch
from torch.utils.data import TensorDataset, DataLoader
import matplotlib.pyplot as plt


class EarlyStoppingTrainer(QuantumClassicalTrainer):
    """Extended trainer with early stopping on validation loss."""
    
    def __init__(self, model, learning_rate=0.001, device='cpu', patience=10):
        super().__init__(model, learning_rate, device)
        self.patience = patience
        self.best_val_loss = float('inf')
        self.patience_counter = 0
        self.best_model_state = None
    
    def train(self, train_loader, val_loader, num_epochs=50):
        """Train with early stopping."""
        for epoch in range(num_epochs):
            train_loss = self.train_epoch(train_loader)
            val_acc, val_loss = self.evaluate(val_loader)
            
            # Early stopping check
            if val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                self.patience_counter = 0
                self.best_model_state = {k: v.cpu().clone() for k, v in self.model.state_dict().items()}
            else:
                self.patience_counter += 1
            
            if self.patience_counter >= self.patience:
                print(f"   Early stopping at epoch {epoch + 1}")
                # Restore best model
                if self.best_model_state:
                    self.model.load_state_dict(self.best_model_state)
                break
            
            if (epoch + 1) % 10 == 0 or epoch == 0:
                print(f"   Epoch {epoch + 1}/{num_epochs} - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}")


def train_config(dataset_name: str, config: Dict) -> Dict:
    """Train a single config and return metrics."""
    X, y, _ = load_dataset(dataset_name)
    
    # Split
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Preprocess
    X_train, X_val, scaler, pca = preprocess_for_qubits(
        X_train, X_val, config['n_qubits']
    )
    
    n_classes = len(np.unique(y_train))
    
    # Create model
    model = HybridQNN(
        input_dim=config['n_qubits'],
        hidden_dim=config['hidden_dim'],
        n_qubits=config['n_qubits'],
        n_quantum_layers=config['n_quantum_layers'],
        output_dim=n_classes,
        dropout=0.2
    )
    
    # Create data loaders
    X_train_tensor = torch.FloatTensor(X_train)
    y_train_tensor = torch.LongTensor(y_train)
    X_val_tensor = torch.FloatTensor(X_val)
    y_val_tensor = torch.LongTensor(y_val)
    
    train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
    val_dataset = TensorDataset(X_val_tensor, y_val_tensor)
    
    train_loader = DataLoader(train_dataset, batch_size=config['batch_size'], shuffle=True, drop_last=True)
    val_loader = DataLoader(val_dataset, batch_size=config['batch_size'], shuffle=False, drop_last=False)
    
    # Train
    trainer = EarlyStoppingTrainer(
        model, 
        learning_rate=config['learning_rate'],
        patience=10
    )
    
    trainer.train(train_loader, val_loader, num_epochs=50)
    
    # Get best metrics
    best_val_acc = max(trainer.val_accuracies) if trainer.val_accuracies else 0.0
    best_val_loss = min(trainer.val_losses) if trainer.val_losses else float('inf')
    
    return {
        'val_acc': best_val_acc,
        'val_loss': best_val_loss,
        'epochs_trained': len(trainer.val_accuracies)
    }


def run_hpo_sweep(dataset_name: str, param_grid: Dict) -> List[Dict]:
    """Run grid search over parameter space."""
    results = []
    
    # Generate all combinations
    keys = list(param_grid.keys())
    values = list(param_grid.values())
    
    total_configs = np.prod([len(v) for v in values])
    print(f"\n{'='*70}")
    print(f"  HPO SWEEP: {dataset_name.upper()}")
    print(f"{'='*70}")
    print(f"Total configurations: {total_configs}")
    print(f"Parameter grid: {param_grid}\n")
    
    for i, combo in enumerate(itertools.product(*values), 1):
        config = dict(zip(keys, combo))
        
        print(f"\n[{i}/{total_configs}] Testing config: {config}")
        
        try:
            metrics = train_config(dataset_name, config)
            
            result = {
                'config': config,
                'metrics': metrics,
                'dataset': dataset_name
            }
            
            results.append(result)
            
            print(f"   ✅ Val Acc: {metrics['val_acc']:.4f}, Val Loss: {metrics['val_loss']:.4f}, Epochs: {metrics['epochs_trained']}")
            
        except Exception as e:
            print(f"   ❌ Config failed: {str(e)}")
            continue
    
    return results


def find_best_config(results: List[Dict]) -> Dict:
    """Find the best config based on validation accuracy."""
    if not results:
        return None
    
    best = max(results, key=lambda x: x['metrics']['val_acc'])
    return best


def save_hpo_report(all_results: Dict, output_path: str = "results/hpo_optimization_report.json"):
    """Save comprehensive HPO report."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'datasets': list(all_results.keys()),
        'results_by_dataset': {}
    }
    
    for dataset, results in all_results.items():
        best = find_best_config(results)
        
        # Baseline from classical comparison
        baselines = {
            'ionosphere': 0.8571,
            'sonar': 0.7619,
            'heart': 0.9464,
            'banknote': 1.0
        }
        
        baseline_acc = baselines.get(dataset, 0.0)
        improvement = (best['metrics']['val_acc'] - baseline_acc) * 100 if best else 0.0
        
        report['results_by_dataset'][dataset] = {
            'baseline_accuracy': baseline_acc,
            'best_config': best['config'] if best else None,
            'best_metrics': best['metrics'] if best else None,
            'improvement_pp': improvement,
            'total_configs_tested': len(results),
            'all_results': results
        }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ HPO report saved to: {output_path}")
    return report


def plot_hpo_results(all_results: Dict, output_path: str = "results/hpo_comparison.png"):
    """Plot HPO results comparison."""
    fig, axes = plt.subplots(1, len(all_results), figsize=(6 * len(all_results), 5))
    
    if len(all_results) == 1:
        axes = [axes]
    
    for idx, (dataset, results) in enumerate(all_results.items()):
        ax = axes[idx]
        
        # Extract configs and accuracies
        accs = [r['metrics']['val_acc'] for r in results]
        configs = [f"C{i+1}" for i in range(len(results))]
        
        # Sort by accuracy
        sorted_pairs = sorted(zip(accs, configs), reverse=True)
        accs_sorted, configs_sorted = zip(*sorted_pairs)
        
        # Plot top 10
        top_n = min(10, len(accs_sorted))
        colors = ['green' if i == 0 else 'steelblue' for i in range(top_n)]
        
        ax.barh(range(top_n), accs_sorted[:top_n], color=colors)
        ax.set_yticks(range(top_n))
        ax.set_yticklabels(configs_sorted[:top_n])
        ax.set_xlabel('Validation Accuracy')
        ax.set_title(f'{dataset.capitalize()}\nTop {top_n} Configs')
        ax.grid(axis='x', alpha=0.3)
        
        # Add baseline line
        baselines = {'ionosphere': 0.8571, 'sonar': 0.7619, 'heart': 0.9464, 'banknote': 1.0}
        if dataset in baselines:
            ax.axvline(baselines[dataset], color='red', linestyle='--', label='Baseline', linewidth=2)
            ax.legend()
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✅ HPO plot saved to: {output_path}")
    plt.close()


def main():
    """Run HPO sweep."""
    print("="*70)
    print("  QUANTUM HYBRID QNN - HYPERPARAMETER OPTIMIZATION")
    print("="*70)
    print("\nTarget: Improve performance on ionosphere and sonar datasets")
    print("Method: Grid search with early stopping")
    print("Baseline accuracies:")
    print("  - Ionosphere: 85.71% (gap: -11.47 pp vs SVM RBF)")
    print("  - Sonar: 76.19% (gap: -9.52 pp vs SVM RBF)")
    
    # Define parameter grid (focused on ionosphere and sonar)
    param_grid = {
        'n_qubits': [4, 5, 6],
        'n_quantum_layers': [2, 3, 4],
        'hidden_dim': [16, 32],
        'learning_rate': [5e-4, 1e-3],
        'batch_size': [8, 16]
    }
    
    # Datasets to optimize
    datasets = ['ionosphere', 'sonar']
    
    all_results = {}
    
    for dataset in datasets:
        results = run_hpo_sweep(dataset, param_grid)
        all_results[dataset] = results
    
    # Save report
    report = save_hpo_report(all_results)
    
    # Plot results
    plot_hpo_results(all_results)
    
    # Print summary
    print("\n" + "="*70)
    print("  HPO SUMMARY")
    print("="*70)
    
    for dataset in datasets:
        best = find_best_config(all_results[dataset])
        if best:
            baseline = {'ionosphere': 0.8571, 'sonar': 0.7619}[dataset]
            improvement = (best['metrics']['val_acc'] - baseline) * 100
            
            print(f"\n{dataset.upper()}:")
            print(f"  Baseline:    {baseline:.4f} ({baseline*100:.2f}%)")
            print(f"  Best HPO:    {best['metrics']['val_acc']:.4f} ({best['metrics']['val_acc']*100:.2f}%)")
            print(f"  Improvement: {improvement:+.2f} pp")
            print(f"  Best config: {best['config']}")
    
    print("\n" + "="*70)
    print("  ✅ HPO COMPLETE!")
    print("="*70)
    print("\n📊 Output files:")
    print("   - results/hpo_optimization_report.json")
    print("   - results/hpo_comparison.png")
    print("\n💡 Next steps:")
    print("   1. Review best configs in the report")
    print("   2. Retrain with best configs on full datasets")
    print("   3. Test on Azure Quantum hardware")
    print("   4. Compare vs classical baselines again\n")


if __name__ == "__main__":
    main()
