"""
Bulk Dataset Generator - Create Synthetic Training Data
========================================================

Generates diverse synthetic classification datasets for ML training.
Much faster than downloading, ensures data quality, and creates datasets
tailored for testing different algorithm characteristics.

Usage:
    python generate_synthetic_datasets.py --count 200
    python generate_synthetic_datasets.py --count 100 --min-samples 500 --max-samples 5000
"""

from sklearn.datasets import (
    make_classification,
    make_moons,
    make_circles,
    make_blobs,
    make_gaussian_quantiles
)
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
import argparse
import json


def generate_dataset(
    n_samples,
    n_features,
    n_classes,
    n_informative_ratio=0.7,
    n_redundant_ratio=0.15,
    dataset_type="classification"
):
    """
    Generate a single synthetic classification dataset.
    
    Args:
        n_samples: Number of samples
        n_features: Number of features
        n_classes: Number of classes
        n_informative_ratio: Ratio of informative features
        n_redundant_ratio: Ratio of redundant features
        dataset_type: Type of dataset pattern
    
    Returns:
        DataFrame with features and target
    """
    n_informative = max(n_classes, int(n_features * n_informative_ratio))
    n_redundant = int(n_features * n_redundant_ratio)
    n_repeated = 0
    n_clusters_per_class = max(1, min(3, n_samples // (n_classes * 50)))
    
    if dataset_type == "classification":
        X, y = make_classification(
            n_samples=n_samples,
            n_features=n_features,
            n_informative=n_informative,
            n_redundant=n_redundant,
            n_repeated=n_repeated,
            n_classes=n_classes,
            n_clusters_per_class=n_clusters_per_class,
            flip_y=0.01,  # 1% label noise
            class_sep=1.0,
            random_state=None
        )
    elif dataset_type == "moons":
        X, y = make_moons(n_samples=n_samples, noise=0.1, random_state=None)
        # Add extra features if needed
        if n_features > 2:
            extra_features = np.random.randn(n_samples, n_features - 2)
            X = np.hstack([X, extra_features])
    elif dataset_type == "circles":
        X, y = make_circles(n_samples=n_samples, noise=0.1, factor=0.5, random_state=None)
        if n_features > 2:
            extra_features = np.random.randn(n_samples, n_features - 2)
            X = np.hstack([X, extra_features])
    elif dataset_type == "blobs":
        X, y = make_blobs(
            n_samples=n_samples,
            n_features=n_features,
            centers=n_classes,
            cluster_std=1.0,
            random_state=None
        )
    elif dataset_type == "gaussian":
        X, y = make_gaussian_quantiles(
            n_samples=n_samples,
            n_features=n_features,
            n_classes=n_classes,
            random_state=None
        )
    
    # Create DataFrame
    feature_names = [f"feature_{i}" for i in range(X.shape[1])]
    df = pd.DataFrame(X, columns=feature_names)
    df['target'] = y
    
    return df


def generate_bulk_datasets(
    count=200,
    min_samples=200,
    max_samples=20000,
    min_features=2,
    max_features=100,
    min_classes=2,
    max_classes=10,
    output_dir="datasets/massive_quantum"
):
    """
    Generate many synthetic datasets with varying characteristics.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*70}")
    print("🧬 SYNTHETIC DATASET GENERATOR")
    print(f"{'='*70}")
    print(f"Target: {count} classification datasets")
    print(f"Samples: {min_samples} to {max_samples}")
    print(f"Features: {min_features} to {max_features}")
    print(f"Classes: {min_classes} to {max_classes}")
    print(f"Output: {output_path}")
    print(f"{'='*70}\n")
    
    np.random.seed()  # Random seed for variety
    
    dataset_types = ["classification", "moons", "circles", "blobs", "gaussian"]
    metadata = {}
    generated = 0
    
    for i in tqdm(range(count), desc="Generating datasets"):
        try:
            # Random dataset characteristics
            n_samples = np.random.randint(min_samples, max_samples + 1)
            n_features = np.random.randint(min_features, max_features + 1)
            n_classes = np.random.randint(min_classes, max_classes + 1)
            dataset_type = np.random.choice(dataset_types)
            
            # Generate dataset
            df = generate_dataset(
                n_samples=n_samples,
                n_features=n_features,
                n_classes=n_classes,
                dataset_type=dataset_type
            )
            
            # Create filename
            filename = f"synthetic_{dataset_type}_{n_samples}s_{n_features}f_{n_classes}c_{i:04d}.csv"
            output_file = output_path / filename
            
            # Skip if exists
            if output_file.exists():
                continue
            
            # Save dataset
            df.to_csv(output_file, index=False)
            
            # Store metadata
            metadata[filename] = {
                "type": dataset_type,
                "samples": n_samples,
                "features": n_features,
                "classes": n_classes,
                "file": str(output_file)
            }
            
            generated += 1
            
        except Exception as e:
            print(f"\n❌ Failed to generate dataset {i}: {e}")
            continue
    
    # Save metadata
    metadata_file = output_path / "synthetic_metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n{'='*70}")
    print("📈 GENERATION SUMMARY")
    print(f"{'='*70}")
    print(f"✓ Successfully generated: {generated}")
    print(f"\n💾 Datasets saved to: {output_path}")
    print(f"📋 Metadata saved to: {metadata_file}")
    print(f"{'='*70}\n")
    
    return generated


def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic classification datasets"
    )
    
    parser.add_argument(
        '--count',
        type=int,
        default=200,
        help='Number of datasets to generate (default: 200)'
    )
    
    parser.add_argument(
        '--min-samples',
        type=int,
        default=200,
        help='Minimum number of samples per dataset (default: 200)'
    )
    
    parser.add_argument(
        '--max-samples',
        type=int,
        default=20000,
        help='Maximum number of samples per dataset (default: 20000)'
    )
    
    parser.add_argument(
        '--min-features',
        type=int,
        default=2,
        help='Minimum number of features (default: 2)'
    )
    
    parser.add_argument(
        '--max-features',
        type=int,
        default=100,
        help='Maximum number of features (default: 100)'
    )
    
    parser.add_argument(
        '--min-classes',
        type=int,
        default=2,
        help='Minimum number of classes (default: 2)'
    )
    
    parser.add_argument(
        '--max-classes',
        type=int,
        default=10,
        help='Maximum number of classes (default: 10)'
    )
    
    parser.add_argument(
        '--output-dir',
        default='datasets/massive_quantum',
        help='Output directory for datasets'
    )
    
    args = parser.parse_args()
    
    generate_bulk_datasets(
        count=args.count,
        min_samples=args.min_samples,
        max_samples=args.max_samples,
        min_features=args.min_features,
        max_features=args.max_features,
        min_classes=args.min_classes,
        max_classes=args.max_classes,
        output_dir=args.output_dir
    )


if __name__ == "__main__":
    main()
