#!/usr/bin/env python
"""
Data Augmentation Script
Expands training datasets by generating synthetic samples using various techniques.

Usage:
    python scripts/augment_training_data.py --all       # Augment all datasets
    python scripts/augment_training_data.py --quantum   # Augment quantum datasets
    python scripts/augment_training_data.py --status    # Show augmentation status
"""

import argparse
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List
import warnings
warnings.filterwarnings('ignore')

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent
QUANTUM_DIR = REPO_ROOT / "datasets" / "quantum"
MASSIVE_DIR = REPO_ROOT / "datasets" / "massive_quantum"
CHAT_DIR = REPO_ROOT / "datasets" / "chat"
OUTPUT_DIR = REPO_ROOT / "data_out" / "augmentation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

class DataAugmentor:
    """Augments training data using multiple techniques"""
    
    @staticmethod
    def load_csv(path: Path) -> Optional[pd.DataFrame]:
        """Load CSV safely"""
        try:
            return pd.read_csv(path)
        except:
            return None
    
    @staticmethod
    def gaussian_noise_augmentation(df: pd.DataFrame, n_samples: int) -> pd.DataFrame:
        """Add Gaussian noise to numeric features"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            return df
        
        augmented_data = []
        for _ in range(n_samples):
            row = df.sample(1).copy()
            for col in numeric_cols:
                std = row[col].std() if hasattr(row[col], 'std') else df[col].std()
                noise = np.random.normal(0, std * 0.05)
                row[col] = row[col] + noise
            augmented_data.append(row)
        
        return pd.concat(augmented_data, ignore_index=True)
    
    @staticmethod
    def mixup_augmentation(df: pd.DataFrame, n_samples: int) -> pd.DataFrame:
        """Mixup: blend two random samples"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            return df
        
        augmented_data = []
        for _ in range(n_samples):
            idx1, idx2 = np.random.choice(len(df), 2, replace=False)
            row1 = df.iloc[idx1].copy()
            row2 = df.iloc[idx2].copy()
            
            alpha = np.random.random()
            for col in numeric_cols:
                row1[col] = alpha * row1[col] + (1 - alpha) * row2[col]
            
            augmented_data.append(row1)
        
        return pd.concat([pd.DataFrame(augmented_data)], ignore_index=True)
    
    @staticmethod
    def smote_like_augmentation(df: pd.DataFrame, n_samples: int) -> pd.DataFrame:
        """SMOTE-like: interpolate between samples"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            return df
        
        augmented_data = []
        for _ in range(n_samples):
            idx = np.random.randint(0, len(df))
            # Find k nearest neighbors
            k = min(5, len(df) - 1)
            dists = ((df[numeric_cols].values - df.iloc[idx][numeric_cols].values) ** 2).sum(axis=1)
            neighbors = np.argsort(dists)[1:k+1]
            
            neighbor_idx = np.random.choice(neighbors)
            row = df.iloc[idx].copy()
            row_neighbor = df.iloc[neighbor_idx].copy()
            
            alpha = np.random.random()
            for col in numeric_cols:
                row[col] = row[col] + alpha * (row_neighbor[col] - row[col])
            
            augmented_data.append(row)
        
        return pd.concat([pd.DataFrame(augmented_data)], ignore_index=True)
    
    @staticmethod
    def augment_dataset(df: pd.DataFrame, multiplier: float = 0.5) -> pd.DataFrame:
        """Augment dataset with multiple techniques"""
        n_original = len(df)
        n_augment = int(n_original * multiplier)
        
        # Split augmentation across techniques
        n_per_technique = n_augment // 3
        
        augmented_parts = [df.copy()]
        
        # Apply techniques
        augmented_parts.append(DataAugmentor.gaussian_noise_augmentation(df, n_per_technique))
        augmented_parts.append(DataAugmentor.mixup_augmentation(df, n_per_technique))
        augmented_parts.append(DataAugmentor.smote_like_augmentation(df, n_augment - 2*n_per_technique))
        
        return pd.concat(augmented_parts, ignore_index=True)


def augment_directory(source_dir: Path, multiplier: float = 0.5) -> Dict[str, any]:
    """Augment all CSV files in a directory"""
    stats = {
        "total_files": 0,
        "processed": 0,
        "failed": 0,
        "original_rows": 0,
        "augmented_rows": 0,
        "size_before_mb": 0.0,
        "size_after_mb": 0.0,
        "files": {}
    }
    
    augmentor = DataAugmentor()
    
    for csv_file in source_dir.glob("*.csv"):
        stats["total_files"] += 1
        df = augmentor.load_csv(csv_file)
        
        if df is None:
            stats["failed"] += 1
            continue
        
        original_len = len(df)
        original_size = csv_file.stat().st_size / (1024**2)
        stats["original_rows"] += original_len
        stats["size_before_mb"] += original_size
        
        # Augment
        augmented_df = augmentor.augment_dataset(df, multiplier)
        augmented_len = len(augmented_df)
        
        # Save with _aug suffix
        output_path = source_dir / f"{csv_file.stem}_aug.csv"
        augmented_df.to_csv(output_path, index=False)
        output_size = output_path.stat().st_size / (1024**2)
        
        stats["processed"] += 1
        stats["augmented_rows"] += augmented_len
        stats["size_after_mb"] += output_size
        stats["files"][csv_file.name] = {
            "original_rows": original_len,
            "augmented_rows": augmented_len,
            "growth_factor": augmented_len / original_len,
            "output_file": output_path.name
        }
    
    return stats


def print_status():
    """Print augmentation status"""
    print("\n" + "="*70)
    print("DATA AUGMENTATION STATUS")
    print("="*70)
    
    for name, path in [("Quantum", QUANTUM_DIR), ("Massive Quantum", MASSIVE_DIR), ("Chat", CHAT_DIR)]:
        if path.exists():
            csv_files = list(path.glob("*.csv"))
            aug_files = list(path.glob("*_aug.csv"))
            total_size = sum(f.stat().st_size for f in csv_files) / (1024**2)
            print(f"\n{name}:")
            print(f"  Original CSVs: {len(csv_files)}")
            print(f"  Augmented CSVs: {len(aug_files)}")
            print(f"  Total size: {total_size:.1f} MB")


def main():
    parser = argparse.ArgumentParser(description="Augment training data")
    parser.add_argument("--all", action="store_true", help="Augment all datasets")
    parser.add_argument("--quantum", action="store_true", help="Augment quantum datasets")
    parser.add_argument("--massive", action="store_true", help="Augment massive quantum datasets")
    parser.add_argument("--chat", action="store_true", help="Augment chat datasets")
    parser.add_argument("--status", action="store_true", help="Show augmentation status")
    parser.add_argument("--multiplier", type=float, default=0.5, help="Augmentation multiplier (default: 0.5)")
    
    args = parser.parse_args()
    
    if args.status:
        print_status()
        return
    
    if not any([args.all, args.quantum, args.massive, args.chat]):
        args.all = True
    
    print("\n" + "="*70)
    print("DATA AUGMENTATION")
    print("="*70)
    
    results = {}
    
    if args.all or args.quantum:
        print(f"\n🔄 Augmenting Quantum datasets (multiplier: {args.multiplier})...")
        results["quantum"] = augment_directory(QUANTUM_DIR, args.multiplier)
        print(f"   ✓ Processed {results['quantum']['processed']}/{results['quantum']['total_files']} files")
        print(f"   ✓ Rows: {results['quantum']['original_rows']:,} → {results['quantum']['augmented_rows']:,}")
        print(f"   ✓ Size: {results['quantum']['size_before_mb']:.1f}MB → {results['quantum']['size_after_mb']:.1f}MB")
    
    if args.all or args.massive:
        print(f"\n🔄 Augmenting Massive Quantum datasets (multiplier: {args.multiplier})...")
        results["massive"] = augment_directory(MASSIVE_DIR, args.multiplier)
        print(f"   ✓ Processed {results['massive']['processed']}/{results['massive']['total_files']} files")
        print(f"   ✓ Rows: {results['massive']['original_rows']:,} → {results['massive']['augmented_rows']:,}")
        print(f"   ✓ Size: {results['massive']['size_before_mb']:.1f}MB → {results['massive']['size_after_mb']:.1f}MB")
    
    if args.all or args.chat:
        print(f"\n🔄 Augmenting Chat datasets (multiplier: {args.multiplier})...")
        if CHAT_DIR.exists():
            results["chat"] = augment_directory(CHAT_DIR, args.multiplier)
            print(f"   ✓ Processed {results['chat']['processed']}/{results['chat']['total_files']} files")
            print(f"   ✓ Rows: {results['chat']['original_rows']:,} → {results['chat']['augmented_rows']:,}")
            print(f"   ✓ Size: {results['chat']['size_before_mb']:.1f}MB → {results['chat']['size_after_mb']:.1f}MB")
        else:
            print("   ⚠ Chat dataset directory not found")
    
    # Save results
    results_file = OUTPUT_DIR / "augmentation_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print("\n" + "="*70)
    print("✅ AUGMENTATION COMPLETE")
    print(f"   Results saved to: {results_file}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
