"""
OpenML Dataset Downloader - Get More Training Data
===================================================

Downloads high-quality classification datasets from OpenML for ML training.
Targets datasets with 100-50000 samples for optimal training performance.

Usage:
    python download_openml_datasets.py --count 100
    python download_openml_datasets.py --count 50 --min-samples 500 --max-samples 10000
"""

import openml
import pandas as pd
from pathlib import Path
import json
from tqdm import tqdm
import argparse

def download_openml_datasets(
    count=100,
    min_samples=100,
    max_samples=50000,
    min_features=2,
    max_features=1000,
    output_dir="datasets/massive_quantum"
):
    """
    Download classification datasets from OpenML.
    
    Args:
        count: Number of datasets to download
        min_samples: Minimum number of samples
        max_samples: Maximum number of samples
        min_features: Minimum number of features
        max_features: Maximum number of features
        output_dir: Directory to save datasets
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*70}")
    print("📊 OPENML DATASET DOWNLOADER")
    print(f"{'='*70}")
    print(f"Target: {count} classification datasets")
    print(f"Samples: {min_samples} to {max_samples}")
    print(f"Features: {min_features} to {max_features}")
    print(f"Output: {output_path}")
    print(f"{'='*70}\n")
    
    # Get list of classification datasets
    print("🔍 Searching OpenML for datasets...")
    datasets_list = openml.datasets.list_datasets(output_format='dataframe')
    
    # Filter for classification tasks
    classification_datasets = datasets_list[
        (datasets_list['NumberOfInstances'] >= min_samples) &
        (datasets_list['NumberOfInstances'] <= max_samples) &
        (datasets_list['NumberOfFeatures'] >= min_features) &
        (datasets_list['NumberOfFeatures'] <= max_features) &
        (datasets_list['NumberOfClasses'] >= 2)  # Classification tasks
    ].copy()
    
    # Sort by number of instances (prefer medium-sized datasets)
    classification_datasets = classification_datasets.sort_values('NumberOfInstances')
    
    print(f"✓ Found {len(classification_datasets)} suitable datasets\n")
    
    # Download datasets
    downloaded = 0
    skipped = 0
    failed = 0
    metadata = {}
    
    for idx, (dataset_id, row) in enumerate(tqdm(classification_datasets.head(count * 3).iterrows(), 
                                                   desc="Downloading", 
                                                   total=min(count * 3, len(classification_datasets)))):
        if downloaded >= count:
            break
            
        try:
            # Get dataset info
            dataset_name = row['name']
            n_samples = int(row['NumberOfInstances'])
            n_features = int(row['NumberOfFeatures'])
            n_classes = int(row['NumberOfClasses'])
            
            # Create safe filename
            safe_name = f"{dataset_name}_{dataset_id}".replace('/', '_').replace('\\', '_')[:100]
            output_file = output_path / f"{safe_name}.csv"
            
            # Skip if already exists
            if output_file.exists():
                skipped += 1
                continue
            
            # Download dataset
            dataset = openml.datasets.get_dataset(
                dataset_id,
                download_data=True,
                download_qualities=True,
                download_features_meta_data=True
            )
            
            # Get data as pandas DataFrame
            X, y, categorical_indicator, attribute_names = dataset.get_data(
                dataset_format="dataframe",
                target=dataset.default_target_attribute
            )
            
            # Combine features and target
            if y is not None:
                df = pd.concat([X, y], axis=1)
            else:
                df = X
            
            # Remove rows with all NaN
            df = df.dropna(how='all')
            
            # Save to CSV
            df.to_csv(output_file, index=False)
            
            # Store metadata
            metadata[safe_name] = {
                "openml_id": int(dataset_id),
                "name": dataset_name,
                "samples": n_samples,
                "features": n_features,
                "classes": n_classes,
                "file": str(output_file),
                "description": row.get('description', 'N/A')[:200]
            }
            
            downloaded += 1
            
        except Exception as e:
            failed += 1
            print(f"\n❌ Failed to download {dataset_name} (ID: {dataset_id}): {str(e)[:100]}")
            continue
    
    # Save metadata
    metadata_file = output_path / "openml_metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n{'='*70}")
    print("📈 DOWNLOAD SUMMARY")
    print(f"{'='*70}")
    print(f"✓ Successfully downloaded: {downloaded}")
    print(f"⊘ Skipped (already exists): {skipped}")
    print(f"❌ Failed: {failed}")
    print(f"\n💾 Datasets saved to: {output_path}")
    print(f"📋 Metadata saved to: {metadata_file}")
    print(f"{'='*70}\n")
    
    return downloaded


def main():
    parser = argparse.ArgumentParser(
        description="Download classification datasets from OpenML"
    )
    
    parser.add_argument(
        '--count',
        type=int,
        default=100,
        help='Number of datasets to download (default: 100)'
    )
    
    parser.add_argument(
        '--min-samples',
        type=int,
        default=100,
        help='Minimum number of samples per dataset (default: 100)'
    )
    
    parser.add_argument(
        '--max-samples',
        type=int,
        default=50000,
        help='Maximum number of samples per dataset (default: 50000)'
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
        default=1000,
        help='Maximum number of features (default: 1000)'
    )
    
    parser.add_argument(
        '--output-dir',
        default='datasets/massive_quantum',
        help='Output directory for datasets'
    )
    
    args = parser.parse_args()
    
    download_openml_datasets(
        count=args.count,
        min_samples=args.min_samples,
        max_samples=args.max_samples,
        min_features=args.min_features,
        max_features=args.max_features,
        output_dir=args.output_dir
    )


if __name__ == "__main__":
    main()
