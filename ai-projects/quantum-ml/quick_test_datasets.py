"""
Quick Test: Validate All Quantum Datasets
==========================================

Rapidly validates that all 29 datasets can be:
1. Successfully loaded
2. Preprocessed for quantum circuits
3. Trained for 1 epoch (smoke test)

This script provides fast feedback on dataset compatibility before
running full benchmarks or hyperparameter optimization.

Author: Quantum AI System
Date: November 16, 2025 (Updated)
"""

import numpy as np
import pandas as pd
from pathlib import Path
import sys
import json
from datetime import datetime
import time

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.hybrid_qnn import HybridQNN, QuantumClassicalTrainer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
import torch
from torch.utils.data import TensorDataset, DataLoader


# All 29 datasets (26 working, 3 excluded: vertebral_column, ecoli corrupted)
DATASETS = [
    # Original 4
    'ionosphere', 'banknote', 'heart_disease', 'sonar',
    # Medical (8 total)
    'breast_cancer', 'diabetes', 'blood_transfusion', 'haberman',
    'parkinsons', 'dermatology', 'liver_disorders', 'thyroid', 'statlog_heart',
    # Biology (3 working - ecoli corrupted)
    'yeast',
    # Chemistry (3 total)
    'wine_red', 'wine_white', 'wine_quality_combined',
    # Image Features (4 total)
    'iris', 'optical_recognition', 'pendigits',
    # Agriculture (2 total)
    'wheat_seeds', 'seeds',
    # Finance (1)
    'statlog_australian',
    # Physics (1)
    'balance_scale',
    # Social Science (1)
    'contraceptive',
    # Other
    'magic_gamma', 'glass',
    # Note: vertebral_column and ecoli excluded (corrupted)
]


def load_and_preprocess(dataset_name, n_qubits=4):
    """Load and preprocess a dataset"""
    dataset_path = Path(__file__).parent.parent / "datasets" / "quantum" / f"{dataset_name}.csv"
    
    print(f"  Loading {dataset_name}...", end=" ")
    
    try:
        # Dataset-specific loading strategies
        if dataset_name in {'wine_red', 'wine_white'}:
            # These use semicolon delimiter with header
            df = pd.read_csv(dataset_path, sep=';', na_values=['?', 'NA', '', 'NaN'])
        elif dataset_name == 'wine_quality_combined':
            # Combined wine dataset with comma delimiter (not semicolon!)
            df = pd.read_csv(dataset_path, na_values=['?', 'NA', '', 'NaN'])
        elif dataset_name in {'wheat_seeds', 'seeds'}:
            # Whitespace-delimited datasets with no header
            df = pd.read_csv(dataset_path, sep=r'\s+', header=None, na_values=['?', 'NA', '', 'NaN'])
        elif dataset_name == 'ecoli':
            # Known corrupted dataset - skip
            raise ValueError("Dataset file appears to be corrupted or empty")
        elif dataset_name == 'yeast':
            # Whitespace-delimited, no header, skip first column (sequence name)
            df = pd.read_csv(dataset_path, sep=r'\s+', header=None, na_values=['?', 'NA', '', 'NaN'])
            df = df.iloc[:, 1:]  # Skip sequence name column
        elif dataset_name == 'parkinsons':
            # Comma-delimited with header, skip first column (name)
            df = pd.read_csv(dataset_path, na_values=['?', 'NA', '', 'NaN'])
            df = df.drop(columns=df.columns[0])  # Skip name column
        elif dataset_name in {'statlog_australian', 'statlog_heart'}:
            # Space-delimited, no header
            df = pd.read_csv(dataset_path, sep=' ', header=None, na_values=['?', 'NA', '', 'NaN'])
        elif dataset_name == 'vertebral_column':
            # Binary file or severely corrupted - skip for now
            raise ValueError("Dataset file appears to be corrupted or binary format")
        elif dataset_name == 'blood_transfusion':
            # Has header with description in first row, skip it
            df = pd.read_csv(dataset_path, skiprows=1, na_values=['?', 'NA', '', 'NaN'])
        elif dataset_name == 'breast_cancer':
            # No header, need to skip ID column
            df = pd.read_csv(dataset_path, header=None, na_values=['?', 'NA', '', 'NaN'])
        elif dataset_name == 'balance_scale':
            # Comma-delimited with header
            df = pd.read_csv(dataset_path, na_values=['?', 'NA', '', 'NaN'])
        elif dataset_name in {'optical_recognition', 'pendigits', 'contraceptive', 'dermatology', 
                               'liver_disorders', 'thyroid'}:
            # Comma-delimited, no header
            df = pd.read_csv(dataset_path, header=None, na_values=['?', 'NA', '', 'NaN'])
        else:
            # Standard loading with fallback
            try:
                df = pd.read_csv(dataset_path, na_values=['?', 'NA', '', 'NaN'])
                # Check if it looks like semicolon-delimited
                if df.shape[1] == 1 and ';' in str(df.iloc[0, 0]):
                    df = pd.read_csv(dataset_path, sep=';', na_values=['?', 'NA', '', 'NaN'])
            except UnicodeDecodeError:
                # Try different encoding
                try:
                    df = pd.read_csv(dataset_path, na_values=['?', 'NA', '', 'NaN'], encoding='latin-1')
                except:
                    df = pd.read_csv(dataset_path, sep=';', na_values=['?', 'NA', '', 'NaN'], encoding='latin-1')
        
        # Check if first row looks like data (all numeric except possibly last column) - only for unhandled cases
        if dataset_name not in {'breast_cancer', 'vertebral_column', 'blood_transfusion', 'wine_red', 'wine_white', 'wine_quality_combined', 'wheat_seeds'}:
            first_row_numeric = all(str(df.iloc[0, i]).replace('.', '').replace('-', '').replace('e', '').isdigit() or str(df.iloc[0, i]).replace('.', '').replace('-', '').replace('e', '').replace('+', '').isdigit() 
                                     for i in range(min(3, df.shape[1] - 1)))
            
            if first_row_numeric or df.columns[0].replace('.', '').replace('-', '').isdigit():
                # No header - reload without header
                try:
                    df = pd.read_csv(dataset_path, header=None, na_values=['?', 'NA', '', 'NaN'])
                except UnicodeDecodeError:
                    df = pd.read_csv(dataset_path, header=None, na_values=['?', 'NA', '', 'NaN'], encoding='latin-1')
        
        # Separate features and labels (last column is target)
        X = df.iloc[:, :-1]
        y = df.iloc[:, -1].values
        
        # Dataset-specific feature handling
        if dataset_name == 'breast_cancer':
            # Column 0 is ID, Column 1 is diagnosis (M/B), rest are features
            # We need to use column 1 as label and skip column 0
            if X.shape[1] > 20:  # Has ID column
                y = X.iloc[:, 0].values  # Second column (index 1 in original) is now at index 0 after removing last
                X = X.iloc[:, 1:]  # Skip both ID and diagnosis, keep only features
                # Now y is from what was the label column, and X has only numeric features
                # Actually, let's reload this correctly
                X = df.iloc[:, 2:-1]  # Skip ID (col 0) and diagnosis (col 1), take features
                y = df.iloc[:, 1].values  # Diagnosis column
        
        # Impute missing values in features if any
        if X.isnull().any().any():
            imputer = SimpleImputer(strategy='median')
            X = pd.DataFrame(imputer.fit_transform(X), columns=X.columns)
        
        X = X.values
        
        # Convert labels to binary (first class vs rest for multi-class)
        unique_labels = np.unique(y)
        if len(unique_labels) > 2 or y.dtype == object:
            if y.dtype == object:
                y = (y == unique_labels[0]).astype(int)
            else:
                # For multi-class numeric, convert to binary
                y = (y == unique_labels[0]).astype(int)
        else:
            y = (y != 0).astype(int)
        
        # Check class distribution for stratified split
        unique, counts = np.unique(y, return_counts=True)
        min_class_count = counts.min()
        
        # Use stratified split only if each class has at least 2 samples
        if min_class_count >= 2:
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
        else:
            # Non-stratified split for very imbalanced data
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
        
        # Standardize
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_val = scaler.transform(X_val)
        
        # Reduce/pad to n_qubits features
        n_features = X_train.shape[1]
        
        if n_features > n_qubits:
            pca = PCA(n_components=n_qubits)
            X_train = pca.fit_transform(X_train)
            X_val = pca.transform(X_val)
        elif n_features < n_qubits:
            pad_train = np.zeros((X_train.shape[0], n_qubits - n_features))
            pad_val = np.zeros((X_val.shape[0], n_qubits - n_features))
            X_train = np.hstack([X_train, pad_train])
            X_val = np.hstack([X_val, pad_val])
        
        print(f"✓ {len(X)} samples, {X.shape[1]}→{n_qubits} features")
        return X_train, X_val, y_train, y_val, True, ""
        
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        return None, None, None, None, False, str(e)


def quick_train(X_train, y_train, X_val, y_val, dataset_name):
    """Train for 1 epoch to validate model works"""
    n_qubits = X_train.shape[1]
    
    try:
        # Create model
        model = HybridQNN(
            input_dim=n_qubits,
            hidden_dim=16,
            n_qubits=n_qubits,
            n_quantum_layers=2,
            output_dim=2,
            dropout=0.2
        )
        
        # Create data loaders
        train_dataset = TensorDataset(
            torch.FloatTensor(X_train),
            torch.LongTensor(y_train)
        )
        val_dataset = TensorDataset(
            torch.FloatTensor(X_val),
            torch.LongTensor(y_val)
        )
        
        train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True, drop_last=True)
        val_loader = DataLoader(val_dataset, batch_size=16, drop_last=True)
        
        # Create trainer
        trainer = QuantumClassicalTrainer(model, learning_rate=0.001)
        
        # Train 1 epoch
        print(f"  Training {dataset_name}...", end=" ")
        start_time = time.time()
        
        trainer.train(train_loader, val_loader, num_epochs=1)
        
        # Evaluate
        val_acc, val_loss = trainer.evaluate(val_loader)
        train_time = time.time() - start_time
        
        print(f"✓ Acc: {val_acc:.2%}, Loss: {val_loss:.4f}, Time: {train_time:.1f}s")
        
        return True, val_acc, val_loss, train_time, ""
        
    except Exception as e:
        print(f"✗ TRAINING ERROR: {str(e)}")
        return False, 0.0, 0.0, 0.0, str(e)


def main():
    print("=" * 70)
    print("  QUICK TEST: ALL QUANTUM DATASETS")
    print("=" * 70)
    print(f"\nTesting {len(DATASETS)} datasets with 1-epoch smoke tests\n")
    
    results = {}
    success_count = 0
    load_failures = []
    train_failures = []
    
    total_start = time.time()
    
    for dataset_name in DATASETS:
        print(f"\n📊 {dataset_name.upper()}")
        print("-" * 70)
        
        # Load and preprocess
        X_train, X_val, y_train, y_val, load_success, load_error = load_and_preprocess(dataset_name)
        
        if not load_success:
            load_failures.append((dataset_name, load_error))
            results[dataset_name] = {
                'status': 'load_failed',
                'error': load_error
            }
            continue
        
        # Quick train
        train_success, val_acc, val_loss, train_time, train_error = quick_train(
            X_train, y_train, X_val, y_val, dataset_name
        )
        
        if not train_success:
            train_failures.append((dataset_name, train_error))
            results[dataset_name] = {
                'status': 'train_failed',
                'error': train_error,
                'samples': len(X_train) + len(X_val)
            }
        else:
            success_count += 1
            results[dataset_name] = {
                'status': 'success',
                'val_accuracy': float(val_acc),
                'val_loss': float(val_loss),
                'train_time_seconds': float(train_time),
                'samples': len(X_train) + len(X_val),
                'train_samples': len(X_train),
                'val_samples': len(X_val)
            }
    
    total_time = time.time() - total_start
    
    # Summary
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print(f"\n✅ Successful: {success_count}/{len(DATASETS)}")
    print(f"⏱️  Total time: {total_time:.1f}s")
    
    if load_failures:
        print(f"\n❌ Load failures ({len(load_failures)}):")
        for name, error in load_failures:
            print(f"   - {name}: {error}")
    
    if train_failures:
        print(f"\n❌ Training failures ({len(train_failures)}):")
        for name, error in train_failures:
            print(f"   - {name}: {error}")
    
    # Save results
    output_file = Path(__file__).parent / "results" / "quick_test_results.json"
    output_file.parent.mkdir(exist_ok=True)
    
    output_data = {
        'timestamp': datetime.now().isoformat(),
        'total_datasets': len(DATASETS),
        'successful': success_count,
        'total_time_seconds': total_time,
        'results': results
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n📄 Results saved: {output_file}")
    
    print("\n" + "=" * 70)
    print("  ✅ QUICK TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
