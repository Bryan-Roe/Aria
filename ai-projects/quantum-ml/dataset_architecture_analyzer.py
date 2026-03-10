"""
Dataset-Architecture Analyzer
==============================

Analyzes all quantum datasets and recommends optimal architectures:
- Qubit count (4-6 based on feature complexity)
- Layer count (2-4 based on dataset difficulty)
- Training parameters (batch size, learning rate)

Uses heuristics based on:
- Number of features (high → more qubits)
- Number of samples (small → fewer layers to avoid overfitting)
- Class distribution (imbalanced → lower learning rate)
- Task complexity (multi-class → more layers)

Author: Quantum AI System
Date: November 16, 2025
"""

import numpy as np
import pandas as pd
from pathlib import Path
import json
from datetime import datetime
from sklearn.preprocessing import LabelEncoder


# Dataset metadata (27 working datasets)
DATASET_INFO = {
    # Original 4
    'ionosphere': {'category': 'physics', 'task_type': 'binary', 'difficulty': 'medium'},
    'banknote': {'category': 'forensics', 'task_type': 'binary', 'difficulty': 'easy'},
    'heart_disease': {'category': 'medical', 'task_type': 'binary', 'difficulty': 'medium'},
    'sonar': {'category': 'geophysics', 'task_type': 'binary', 'difficulty': 'hard'},
    # Medical (13 total including statlog_heart)
    'breast_cancer': {'category': 'medical', 'task_type': 'binary', 'difficulty': 'medium'},
    'diabetes': {'category': 'medical', 'task_type': 'binary', 'difficulty': 'medium'},
    'blood_transfusion': {'category': 'medical', 'task_type': 'binary', 'difficulty': 'hard'},
    'haberman': {'category': 'medical', 'task_type': 'binary', 'difficulty': 'hard'},
    'parkinsons': {'category': 'medical', 'task_type': 'binary', 'difficulty': 'medium'},
    'dermatology': {'category': 'medical', 'task_type': 'multiclass', 'difficulty': 'medium'},
    'liver_disorders': {'category': 'medical', 'task_type': 'binary', 'difficulty': 'medium'},
    'thyroid': {'category': 'medical', 'task_type': 'multiclass', 'difficulty': 'medium'},
    'statlog_heart': {'category': 'medical', 'task_type': 'binary', 'difficulty': 'medium'},
    # Biology (1 - ecoli corrupted)
    'yeast': {'category': 'biology', 'task_type': 'multiclass', 'difficulty': 'hard'},
    # Chemistry (3)
    'wine_red': {'category': 'chemistry', 'task_type': 'multiclass', 'difficulty': 'hard'},
    'wine_white': {'category': 'chemistry', 'task_type': 'multiclass', 'difficulty': 'hard'},
    'wine_quality_combined': {'category': 'chemistry', 'task_type': 'multiclass', 'difficulty': 'hard'},
    # Image Features (4)
    'iris': {'category': 'biology', 'task_type': 'multiclass', 'difficulty': 'easy'},
    'optical_recognition': {'category': 'image', 'task_type': 'multiclass', 'difficulty': 'hard'},
    'pendigits': {'category': 'image', 'task_type': 'multiclass', 'difficulty': 'medium'},
    # Agriculture (2)
    'wheat_seeds': {'category': 'agriculture', 'task_type': 'multiclass', 'difficulty': 'medium'},
    'seeds': {'category': 'agriculture', 'task_type': 'multiclass', 'difficulty': 'medium'},
    # Finance (1)
    'statlog_australian': {'category': 'finance', 'task_type': 'binary', 'difficulty': 'medium'},
    # Physics (2 - including balance_scale)
    'magic_gamma': {'category': 'physics', 'task_type': 'binary', 'difficulty': 'medium'},
    'balance_scale': {'category': 'physics', 'task_type': 'multiclass', 'difficulty': 'easy'},
    # Social Science (1)
    'contraceptive': {'category': 'social', 'task_type': 'multiclass', 'difficulty': 'medium'},
    # Forensics (1)
    'glass': {'category': 'forensics', 'task_type': 'multiclass', 'difficulty': 'hard'},
}


def analyze_dataset(dataset_name):
    """Analyze a dataset and recommend architecture"""
    dataset_path = Path(__file__).parent.parent / "datasets" / "quantum" / f"{dataset_name}.csv"
    
    # Load dataset with specific strategies
    try:
        if dataset_name in {'wine_red', 'wine_white'}:
            df = pd.read_csv(dataset_path, sep=';', na_values=['?', 'NA', '', 'NaN'])
        elif dataset_name == 'wine_quality_combined':
            df = pd.read_csv(dataset_path, na_values=['?', 'NA', '', 'NaN'])
        elif dataset_name in {'wheat_seeds', 'seeds'}:
            df = pd.read_csv(dataset_path, sep=r'\s+', header=None, na_values=['?', 'NA', '', 'NaN'])
        elif dataset_name == 'yeast':
            df = pd.read_csv(dataset_path, sep=r'\s+', header=None, na_values=['?', 'NA', '', 'NaN'])
            df = df.iloc[:, 1:]  # Skip sequence name
        elif dataset_name == 'parkinsons':
            df = pd.read_csv(dataset_path, na_values=['?', 'NA', '', 'NaN'])
            df = df.drop(columns=df.columns[0])  # Skip name column
        elif dataset_name in {'statlog_australian', 'statlog_heart'}:
            df = pd.read_csv(dataset_path, sep=' ', header=None, na_values=['?', 'NA', '', 'NaN'])
        elif dataset_name == 'blood_transfusion':
            df = pd.read_csv(dataset_path, skiprows=1, na_values=['?', 'NA', '', 'NaN'])
        elif dataset_name == 'breast_cancer':
            df = pd.read_csv(dataset_path, header=None, na_values=['?', 'NA', '', 'NaN'])
        elif dataset_name == 'balance_scale':
            df = pd.read_csv(dataset_path, na_values=['?', 'NA', '', 'NaN'])
        elif dataset_name in {'optical_recognition', 'pendigits', 'contraceptive', 'dermatology', 
                               'liver_disorders', 'thyroid'}:
            df = pd.read_csv(dataset_path, header=None, na_values=['?', 'NA', '', 'NaN'])
        else:
            df = pd.read_csv(dataset_path, na_values=['?', 'NA', '', 'NaN'])
    except Exception as e:
        raise ValueError(f"Failed to load {dataset_name}: {str(e)}")
    
    # Basic statistics
    n_samples = len(df)
    n_features = df.shape[1] - 1  # Exclude target
    
    # Target analysis
    y = df.iloc[:, -1]
    if y.dtype == object:
        le = LabelEncoder()
        y_encoded = le.fit_transform(y)
        n_classes = len(le.classes_)
        class_counts = np.bincount(y_encoded)
    else:
        n_classes = len(y.unique())
        class_counts = y.value_counts().values
    
    # Class imbalance ratio
    imbalance_ratio = class_counts.max() / class_counts.min() if len(class_counts) > 1 else 1.0
    
    # Missing values
    missing_ratio = df.isnull().sum().sum() / (df.shape[0] * df.shape[1])
    
    # Get metadata
    meta = DATASET_INFO.get(dataset_name, {})
    task_type = meta.get('task_type', 'binary' if n_classes == 2 else 'multiclass')
    difficulty = meta.get('difficulty', 'medium')
    
    # === ARCHITECTURE RECOMMENDATIONS ===
    
    # 1. Qubit Count (4-6)
    if n_features <= 4:
        n_qubits = 4
        qubit_reasoning = "Low feature count (≤4) - use 4 qubits minimum"
    elif n_features <= 10:
        n_qubits = 4
        qubit_reasoning = "Medium feature count (5-10) - standard 4 qubits"
    elif n_features <= 20:
        n_qubits = 5
        qubit_reasoning = "High feature count (11-20) - use 5 qubits for better representation"
    else:
        n_qubits = 6
        qubit_reasoning = "Very high feature count (>20) - use 6 qubits for dimensionality"
    
    # 2. Layer Count (2-4)
    if n_samples < 300:
        n_layers = 2
        layer_reasoning = "Small dataset (<300 samples) - use 2 layers to avoid overfitting"
    elif task_type == 'multiclass' and n_classes > 3:
        n_layers = 4
        layer_reasoning = f"Multi-class ({n_classes} classes) - use 4 layers for complexity"
    elif difficulty == 'hard':
        n_layers = 3
        layer_reasoning = "Hard task - use 3 layers for learning capacity"
    else:
        n_layers = 2
        layer_reasoning = "Standard task - use 2 layers (efficient baseline)"
    
    # 3. Hidden Dimension (16 or 32)
    if n_samples < 500:
        hidden_dim = 16
        hidden_reasoning = "Small dataset - use hidden_dim=16 to reduce parameters"
    elif n_features > 15:
        hidden_dim = 32
        hidden_reasoning = "High-dimensional input - use hidden_dim=32 for capacity"
    else:
        hidden_dim = 16
        hidden_reasoning = "Standard configuration - use hidden_dim=16"
    
    # 4. Learning Rate (0.0005 or 0.001)
    if imbalance_ratio > 3.0:
        learning_rate = 0.0005
        lr_reasoning = f"Imbalanced classes (ratio: {imbalance_ratio:.1f}) - lower LR for stability"
    elif n_samples < 300:
        learning_rate = 0.0005
        lr_reasoning = "Small dataset - lower LR to avoid overfitting"
    else:
        learning_rate = 0.001
        lr_reasoning = "Balanced dataset - standard LR for faster convergence"
    
    # 5. Batch Size (8 or 16)
    if n_samples < 300:
        batch_size = 8
        batch_reasoning = "Small dataset - use batch_size=8 for more gradient updates"
    elif n_samples > 5000:
        batch_size = 32
        batch_reasoning = "Large dataset - use batch_size=32 for efficiency"
    else:
        batch_size = 16
        batch_reasoning = "Medium dataset - standard batch_size=16"
    
    # 6. Epoch Count
    if difficulty == 'hard' or task_type == 'multiclass':
        epochs = 50
        epoch_reasoning = "Complex task - train for 50 epochs"
    elif n_samples < 300:
        epochs = 30
        epoch_reasoning = "Small dataset - 30 epochs to avoid overfitting"
    else:
        epochs = 40
        epoch_reasoning = "Standard task - 40 epochs for convergence"
    
    # Calculate expected PCA variance retained
    if n_features > n_qubits:
        # Estimate based on typical variance distributions
        if n_features <= 10:
            pca_variance = 0.90
        elif n_features <= 20:
            pca_variance = 0.85
        else:
            pca_variance = 0.80
    else:
        pca_variance = 1.0
    
    return {
        'dataset': dataset_name,
        'statistics': {
            'samples': int(n_samples),
            'features': int(n_features),
            'classes': int(n_classes),
            'task_type': task_type,
            'difficulty': difficulty,
            'imbalance_ratio': float(imbalance_ratio),
            'missing_ratio': float(missing_ratio),
            'class_distribution': [int(c) for c in class_counts],
        },
        'recommended_architecture': {
            'n_qubits': n_qubits,
            'n_quantum_layers': n_layers,
            'hidden_dim': hidden_dim,
            'learning_rate': learning_rate,
            'batch_size': batch_size,
            'epochs': epochs,
            'expected_pca_variance': float(pca_variance),
        },
        'reasoning': {
            'qubits': qubit_reasoning,
            'layers': layer_reasoning,
            'hidden_dim': hidden_reasoning,
            'learning_rate': lr_reasoning,
            'batch_size': batch_reasoning,
            'epochs': epoch_reasoning,
        }
    }


def main():
    print("=" * 70)
    print("  DATASET-ARCHITECTURE ANALYZER")
    print("=" * 70)
    print("\nAnalyzing all 15 quantum datasets...\n")
    
    all_results = []
    
    # Analyze each dataset
    for dataset_name in sorted(DATASET_INFO.keys()):
        print(f"📊 {dataset_name}")
        print("-" * 70)
        
        try:
            result = analyze_dataset(dataset_name)
            all_results.append(result)
            
            stats = result['statistics']
            arch = result['recommended_architecture']
            reason = result['reasoning']
            
            # Print statistics
            print(f"  Samples: {stats['samples']:,} | Features: {stats['features']} | "
                  f"Classes: {stats['classes']} | Type: {stats['task_type']}")
            print(f"  Difficulty: {stats['difficulty']} | Imbalance: {stats['imbalance_ratio']:.2f}x")
            
            # Print recommendations
            print(f"\n  🎯 RECOMMENDED ARCHITECTURE:")
            print(f"     Qubits: {arch['n_qubits']} → {reason['qubits']}")
            print(f"     Layers: {arch['n_quantum_layers']} → {reason['layers']}")
            print(f"     Hidden: {arch['hidden_dim']} → {reason['hidden_dim']}")
            print(f"     Learn Rate: {arch['learning_rate']} → {reason['learning_rate']}")
            print(f"     Batch: {arch['batch_size']} → {reason['batch_size']}")
            print(f"     Epochs: {arch['epochs']} → {reason['epochs']}")
            
            if stats['features'] > arch['n_qubits']:
                print(f"     PCA: {stats['features']}→{arch['n_qubits']} features "
                      f"({arch['expected_pca_variance']:.0%} variance)")
            
            print()
            
        except Exception as e:
            print(f"  ❌ ERROR: {e}\n")
    
    # Summary by category
    print("=" * 70)
    print("  SUMMARY BY CATEGORY")
    print("=" * 70)
    
    categories = {}
    for result in all_results:
        cat = DATASET_INFO[result['dataset']]['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(result)
    
    for category, datasets in sorted(categories.items()):
        print(f"\n📁 {category.upper()} ({len(datasets)} datasets)")
        print("-" * 70)
        for ds in datasets:
            arch = ds['recommended_architecture']
            stats = ds['statistics']
            print(f"  {ds['dataset']:20s} | {stats['samples']:5d} samples | "
                  f"{stats['features']:2d}→{arch['n_qubits']} features | "
                  f"{arch['n_quantum_layers']} layers | "
                  f"dim={arch['hidden_dim']} | "
                  f"lr={arch['learning_rate']}")
    
    # Architecture distribution
    print("\n" + "=" * 70)
    print("  ARCHITECTURE DISTRIBUTION")
    print("=" * 70)
    
    qubit_dist = {}
    layer_dist = {}
    for result in all_results:
        arch = result['recommended_architecture']
        qubit_dist[arch['n_qubits']] = qubit_dist.get(arch['n_qubits'], 0) + 1
        layer_dist[arch['n_quantum_layers']] = layer_dist.get(arch['n_quantum_layers'], 0) + 1
    
    print(f"\n🔢 Qubit Distribution:")
    for qubits, count in sorted(qubit_dist.items()):
        pct = 100 * count / len(all_results)
        print(f"   {qubits} qubits: {count} datasets ({pct:.0f}%)")
    
    print(f"\n🔢 Layer Distribution:")
    for layers, count in sorted(layer_dist.items()):
        pct = 100 * count / len(all_results)
        print(f"   {layers} layers: {count} datasets ({pct:.0f}%)")
    
    # Save results
    output_file = Path(__file__).parent / "results" / "architecture_analysis.json"
    output_file.parent.mkdir(exist_ok=True)
    
    output_data = {
        'timestamp': datetime.now().isoformat(),
        'total_datasets': len(all_results),
        'analyses': all_results,
        'distributions': {
            'qubits': qubit_dist,
            'layers': layer_dist,
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n📄 Analysis saved: {output_file}")
    
    print("\n" + "=" * 70)
    print("  ✅ ANALYSIS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
