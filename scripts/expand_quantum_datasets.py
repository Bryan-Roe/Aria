"""
Expand Quantum AI Dataset Collection
Searches UCI ML Repository and other sources for high-quality classification datasets
suitable for quantum machine learning (100-5000 samples, 4-60 features).

Usage:
    python scripts/expand_quantum_datasets.py --search      # Search and list candidates
    python scripts/expand_quantum_datasets.py --download    # Download all candidates
    python scripts/expand_quantum_datasets.py --validate    # Validate downloaded data
"""

import argparse
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import urllib.request
import urllib.error
import ssl
import time

# Base paths
SCRIPT_DIR = Path(__file__).parent
WORKSPACE_ROOT = SCRIPT_DIR.parent
QUANTUM_DIR = WORKSPACE_ROOT / "datasets" / "quantum"
INDEX_FILE = WORKSPACE_ROOT / "datasets" / "dataset_index.json"

# Create SSL context that doesn't verify certificates (for UCI downloads)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Candidate datasets from UCI ML Repository (manually curated)
CANDIDATE_DATASETS = [
    {
        "name": "ecoli",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/ecoli/ecoli.data",
        "description": "E. coli Protein Localization Sites",
        "samples": 336,
        "features": 7,
        "classes": 8,
        "task": "Multi-class: Protein cellular localization prediction",
        "category": "biology",
        "difficulty": "hard",
        "delimiter": ",",
        "header": None,
        "skip_columns": [0],  # Sequence name
        "target_column": -1
    },
    {
        "name": "parkinsons",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/parkinsons/parkinsons.data",
        "description": "Parkinsons Disease Detection",
        "samples": 195,
        "features": 22,
        "classes": 2,
        "task": "Binary: Parkinsons disease detection from voice measurements",
        "category": "medical",
        "difficulty": "medium",
        "delimiter": ",",
        "header": 0,
        "skip_columns": [0],  # Name column
        "target_column": "status"
    },
    {
        "name": "vehicle",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/statlog/vehicle/vehicle.dat",
        "description": "Vehicle Silhouette Classification",
        "samples": 846,
        "features": 18,
        "classes": 4,
        "task": "Multi-class: Vehicle type from silhouette features",
        "category": "image_features",
        "difficulty": "medium",
        "delimiter": " ",
        "header": None,
        "skip_columns": [],
        "target_column": -1
    },
    {
        "name": "dermatology",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/dermatology/dermatology.data",
        "description": "Dermatology Disease Classification",
        "samples": 366,
        "features": 34,
        "classes": 6,
        "task": "Multi-class: Skin disease classification",
        "category": "medical",
        "difficulty": "hard",
        "delimiter": ",",
        "header": None,
        "skip_columns": [],
        "target_column": -1
    },
    {
        "name": "liver_disorders",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/liver-disorders/bupa.data",
        "description": "Liver Disorders (BUPA)",
        "samples": 345,
        "features": 6,
        "classes": 2,
        "task": "Binary: Liver disorder detection from blood tests",
        "category": "medical",
        "difficulty": "medium",
        "delimiter": ",",
        "header": None,
        "skip_columns": [],
        "target_column": -1
    },
    {
        "name": "contraceptive",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/cmc/cmc.data",
        "description": "Contraceptive Method Choice",
        "samples": 1473,
        "features": 9,
        "classes": 3,
        "task": "Multi-class: Contraceptive method prediction",
        "category": "social_science",
        "difficulty": "hard",
        "delimiter": ",",
        "header": None,
        "skip_columns": [],
        "target_column": -1
    },
    {
        "name": "balance_scale",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/balance-scale/balance-scale.data",
        "description": "Balance Scale Weight & Distance",
        "samples": 625,
        "features": 4,
        "classes": 3,
        "task": "Multi-class: Balance scale tip direction",
        "category": "physics",
        "difficulty": "easy",
        "delimiter": ",",
        "header": None,
        "skip_columns": [],
        "target_column": 0  # First column is target
    },
    {
        "name": "thyroid",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/thyroid-disease/new-thyroid.data",
        "description": "Thyroid Disease",
        "samples": 215,
        "features": 5,
        "classes": 3,
        "task": "Multi-class: Thyroid condition classification",
        "category": "medical",
        "difficulty": "medium",
        "delimiter": ",",
        "header": None,
        "skip_columns": [],
        "target_column": 0  # First column is target
    },
    {
        "name": "yeast",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/yeast/yeast.data",
        "description": "Yeast Protein Localization",
        "samples": 1484,
        "features": 8,
        "classes": 10,
        "task": "Multi-class: Protein cellular localization",
        "category": "biology",
        "difficulty": "hard",
        "delimiter": r"\s+",
        "header": None,
        "skip_columns": [0],  # Sequence name
        "target_column": -1
    },
    {
        "name": "seeds",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/00236/seeds_dataset.txt",
        "description": "Seeds (Wheat Varieties)",
        "samples": 210,
        "features": 7,
        "classes": 3,
        "task": "Multi-class: Wheat variety classification",
        "category": "agriculture",
        "difficulty": "easy",
        "delimiter": r"\s+",
        "header": None,
        "skip_columns": [],
        "target_column": -1
    },
    {
        "name": "statlog_heart",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/statlog/heart/heart.dat",
        "description": "StatLog Heart Disease",
        "samples": 270,
        "features": 13,
        "classes": 2,
        "task": "Binary: Heart disease presence",
        "category": "medical",
        "difficulty": "medium",
        "delimiter": " ",
        "header": None,
        "skip_columns": [],
        "target_column": -1
    },
    {
        "name": "statlog_australian",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/statlog/australian/australian.dat",
        "description": "StatLog Australian Credit Approval",
        "samples": 690,
        "features": 14,
        "classes": 2,
        "task": "Binary: Credit approval prediction",
        "category": "finance",
        "difficulty": "medium",
        "delimiter": " ",
        "header": None,
        "skip_columns": [],
        "target_column": -1
    },
    {
        "name": "wine_quality_combined",
        "url": None,  # Will combine existing wine_red and wine_white
        "description": "Wine Quality (Combined Red & White)",
        "samples": 6497,
        "features": 12,  # 11 + wine type
        "classes": 7,
        "task": "Multi-class: Wine quality with type feature",
        "category": "chemistry",
        "difficulty": "hard",
        "special": "combine_existing"
    },
    {
        "name": "page_blocks",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/page-blocks/page-blocks.data",
        "description": "Page Blocks Classification",
        "samples": 5473,
        "features": 10,
        "classes": 5,
        "task": "Multi-class: Document page block type",
        "category": "image_features",
        "difficulty": "medium",
        "delimiter": r"\s+",
        "header": None,
        "skip_columns": [],
        "target_column": -1
    },
    {
        "name": "optical_recognition",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/optdigits/optdigits.tra",
        "description": "Optical Recognition of Handwritten Digits",
        "samples": 3823,
        "features": 64,
        "classes": 10,
        "task": "Multi-class: Digit recognition (0-9)",
        "category": "image_features",
        "difficulty": "medium",
        "delimiter": ",",
        "header": None,
        "skip_columns": [],
        "target_column": -1,
        "note": "Training set only; 8x8 pixel images flattened"
    },
    {
        "name": "pendigits",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/pendigits/pendigits.tra",
        "description": "Pen-Based Recognition of Handwritten Digits",
        "samples": 7494,
        "features": 16,
        "classes": 10,
        "task": "Multi-class: Handwritten digit recognition",
        "category": "image_features",
        "difficulty": "easy",
        "delimiter": ",",
        "header": None,
        "skip_columns": [],
        "target_column": -1,
        "note": "Training set only"
    }
]


def search_datasets():
    """Display candidate datasets with statistics."""
    print("\n" + "="*80)
    print("CANDIDATE QUANTUM ML DATASETS")
    print("="*80)
    print(f"Total Candidates: {len(CANDIDATE_DATASETS)}")
    print()
    
    # Group by category
    categories = {}
    for ds in CANDIDATE_DATASETS:
        cat = ds['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(ds)
    
    # Display by category
    for cat, datasets in sorted(categories.items()):
        print(f"\n📁 {cat.upper()} ({len(datasets)} datasets)")
        print("-" * 80)
        for ds in datasets:
            print(f"  • {ds['name']:<25} {ds['samples']:>5} samples, {ds['features']:>2} features, {ds['classes']:>2} classes")
            print(f"    {ds['description']}")
            print(f"    Task: {ds['task']}")
            print(f"    Difficulty: {ds['difficulty']}")
            if 'note' in ds:
                print(f"    Note: {ds['note']}")
            print()
    
    # Summary statistics
    total_samples = sum(ds['samples'] for ds in CANDIDATE_DATASETS)
    total_features_avg = sum(ds['features'] for ds in CANDIDATE_DATASETS) / len(CANDIDATE_DATASETS)
    
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    print(f"Total Datasets: {len(CANDIDATE_DATASETS)}")
    print(f"Total Samples: {total_samples:,}")
    print(f"Average Features: {total_features_avg:.1f}")
    print(f"Categories: {len(categories)}")
    print(f"Size Range: {min(ds['samples'] for ds in CANDIDATE_DATASETS)}-{max(ds['samples'] for ds in CANDIDATE_DATASETS)} samples")
    print(f"Feature Range: {min(ds['features'] for ds in CANDIDATE_DATASETS)}-{max(ds['features'] for ds in CANDIDATE_DATASETS)} features")
    print()


def download_dataset(dataset_info: Dict) -> Tuple[bool, str]:
    """
    Download a single dataset.
    
    Returns:
        (success, message)
    """
    name = dataset_info['name']
    url = dataset_info.get('url')
    
    # Special case: combine existing datasets
    if dataset_info.get('special') == 'combine_existing':
        try:
            red_path = QUANTUM_DIR / "wine_red.csv"
            white_path = QUANTUM_DIR / "wine_white.csv"
            
            if not red_path.exists() or not white_path.exists():
                return False, "Missing wine_red or wine_white datasets"
            
            red_df = pd.read_csv(red_path, sep=';')
            white_df = pd.read_csv(white_path, sep=';')
            
            red_df['wine_type'] = 0  # Red
            white_df['wine_type'] = 1  # White
            
            combined = pd.concat([red_df, white_df], ignore_index=True)
            output_path = QUANTUM_DIR / f"{name}.csv"
            combined.to_csv(output_path, index=False)
            
            return True, f"Combined {len(red_df)} red + {len(white_df)} white samples"
        except Exception as e:
            return False, f"Failed to combine: {str(e)}"
    
    if not url:
        return False, "No URL provided"
    
    output_path = QUANTUM_DIR / f"{name}.csv"
    
    # Skip if already exists
    if output_path.exists():
        return True, f"Already exists ({output_path.stat().st_size:,} bytes)"
    
    try:
        print(f"  Downloading from {url}...")
        
        # Download with custom opener for SSL
        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl_context))
        urllib.request.install_opener(opener)
        
        response = urllib.request.urlopen(url, timeout=30)
        data = response.read()
        
        # Parse based on delimiter
        delimiter = dataset_info.get('delimiter', ',')
        header = dataset_info.get('header')
        
        # Write raw data first
        temp_path = output_path.with_suffix('.tmp')
        temp_path.write_bytes(data)
        
        # Load and validate
        if delimiter == r'\s+':
            df = pd.read_csv(temp_path, sep=r'\s+', header=header)
        else:
            df = pd.read_csv(temp_path, sep=delimiter, header=header)
        
        # Remove skip columns if specified
        skip_cols = dataset_info.get('skip_columns', [])
        if skip_cols:
            if isinstance(skip_cols[0], int):
                df = df.drop(df.columns[skip_cols], axis=1)
            else:
                df = df.drop(columns=skip_cols, errors='ignore')
        
        # Move target to last column if needed
        target_col = dataset_info.get('target_column')
        if target_col is not None:
            if isinstance(target_col, int) and target_col != -1:
                cols = list(df.columns)
                target = cols.pop(target_col)
                cols.append(target)
                df = df[cols]
            elif isinstance(target_col, str):
                cols = [c for c in df.columns if c != target_col] + [target_col]
                df = df[cols]
        
        # Save cleaned CSV
        df.to_csv(output_path, index=False, header=False)
        temp_path.unlink()
        
        # Validate
        actual_samples = len(df)
        actual_features = len(df.columns) - 1
        expected_samples = dataset_info['samples']
        
        if abs(actual_samples - expected_samples) > expected_samples * 0.1:  # 10% tolerance
            return False, f"Sample count mismatch: expected {expected_samples}, got {actual_samples}"
        
        return True, f"Downloaded {actual_samples} samples, {actual_features} features"
    
    except Exception as e:
        if output_path.exists():
            output_path.unlink()
        return False, f"Error: {str(e)}"


def download_all():
    """Download all candidate datasets."""
    print("\n" + "="*80)
    print("DOWNLOADING QUANTUM ML DATASETS")
    print("="*80)
    
    QUANTUM_DIR.mkdir(parents=True, exist_ok=True)
    
    results = []
    for i, ds_info in enumerate(CANDIDATE_DATASETS, 1):
        name = ds_info['name']
        print(f"\n[{i}/{len(CANDIDATE_DATASETS)}] {name}")
        print(f"  Description: {ds_info['description']}")
        
        success, message = download_dataset(ds_info)
        results.append((name, success, message))
        
        if success:
            print(f"  ✅ {message}")
        else:
            print(f"  ❌ {message}")
        
        time.sleep(0.5)  # Be nice to UCI servers
    
    # Summary
    print("\n" + "="*80)
    print("DOWNLOAD SUMMARY")
    print("="*80)
    
    successful = [r for r in results if r[1]]
    failed = [r for r in results if not r[1]]
    
    print(f"✅ Successful: {len(successful)}/{len(CANDIDATE_DATASETS)}")
    print(f"❌ Failed: {len(failed)}/{len(CANDIDATE_DATASETS)}")
    
    if failed:
        print("\nFailed downloads:")
        for name, _, msg in failed:
            print(f"  • {name}: {msg}")
    
    print()


def validate_datasets():
    """Validate downloaded datasets."""
    print("\n" + "="*80)
    print("VALIDATING DOWNLOADED DATASETS")
    print("="*80)
    
    csv_files = list(QUANTUM_DIR.glob("*.csv"))
    print(f"Found {len(csv_files)} CSV files in {QUANTUM_DIR}")
    print()
    
    results = []
    for csv_path in sorted(csv_files):
        name = csv_path.stem
        print(f"Validating {name}...")
        
        try:
            # Try standard loading
            df = pd.read_csv(csv_path, header=None)
            samples = len(df)
            features = len(df.columns) - 1  # Assume last column is target
            
            # Check for missing values
            missing = df.isnull().sum().sum()
            missing_pct = (missing / (samples * df.shape[1])) * 100
            
            # Check target distribution
            target = df.iloc[:, -1]
            unique_classes = target.nunique()
            class_dist = target.value_counts().to_dict()
            
            results.append({
                'name': name,
                'status': 'OK',
                'samples': samples,
                'features': features,
                'classes': unique_classes,
                'missing_pct': missing_pct,
                'class_distribution': class_dist
            })
            
            print(f"  ✅ {samples} samples, {features} features, {unique_classes} classes")
            print(f"     Missing: {missing_pct:.1f}%")
            print(f"     Classes: {class_dist}")
        
        except Exception as e:
            results.append({
                'name': name,
                'status': 'ERROR',
                'error': str(e)
            })
            print(f"  ❌ {str(e)}")
        
        print()
    
    # Summary
    print("="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    
    ok_count = sum(1 for r in results if r['status'] == 'OK')
    error_count = sum(1 for r in results if r['status'] == 'ERROR')
    
    print(f"✅ Valid: {ok_count}/{len(results)}")
    print(f"❌ Errors: {error_count}/{len(results)}")
    
    if ok_count > 0:
        total_samples = sum(r['samples'] for r in results if r['status'] == 'OK')
        avg_features = sum(r['features'] for r in results if r['status'] == 'OK') / ok_count
        print(f"\nTotal Samples: {total_samples:,}")
        print(f"Average Features: {avg_features:.1f}")
    
    print()
    
    return results


def update_index(validation_results: List[Dict]):
    """Update dataset_index.json with new datasets."""
    print("\n" + "="*80)
    print("UPDATING DATASET INDEX")
    print("="*80)
    
    # Load existing index
    if INDEX_FILE.exists():
        with open(INDEX_FILE, 'r') as f:
            index = json.load(f)
    else:
        index = {"datasets": {}, "metadata": {}, "storage": {}}
    
    # Add new datasets
    added_count = 0
    for result in validation_results:
        if result['status'] != 'OK':
            continue
        
        name = result['name']
        if name in index['datasets']:
            print(f"  Skipping {name} (already in index)")
            continue
        
        # Find dataset info
        ds_info = next((ds for ds in CANDIDATE_DATASETS if ds['name'] == name), None)
        if not ds_info:
            print(f"  Warning: No metadata for {name}")
            continue
        
        # Add to index
        csv_path = QUANTUM_DIR / f"{name}.csv"
        index['datasets'][name] = {
            "category": "quantum",
            "filename": f"{name}.csv",
            "path": str(csv_path),
            "description": ds_info['description'],
            "size": csv_path.stat().st_size,
            "features": result['features'],
            "samples": result['samples'],
            "classes": result['classes'],
            "task": ds_info['task'],
            "difficulty": ds_info['difficulty'],
            "dataset_category": ds_info['category']
        }
        
        added_count += 1
        print(f"  ✅ Added {name} to index")
    
    # Update metadata
    index['last_updated'] = pd.Timestamp.now().isoformat()
    
    # Save index
    with open(INDEX_FILE, 'w') as f:
        json.dump(index, f, indent=2)
    
    print(f"\n✅ Updated index with {added_count} new datasets")
    print(f"   Total datasets in index: {len(index['datasets'])}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Expand quantum ML dataset collection")
    parser.add_argument('--search', action='store_true', help='Search and list candidate datasets')
    parser.add_argument('--download', action='store_true', help='Download all candidate datasets')
    parser.add_argument('--validate', action='store_true', help='Validate downloaded datasets')
    parser.add_argument('--update-index', action='store_true', help='Update dataset_index.json')
    parser.add_argument('--all', action='store_true', help='Run all steps (search, download, validate, update)')
    
    args = parser.parse_args()
    
    if args.all:
        args.search = True
        args.download = True
        args.validate = True
        args.update_index = True
    
    if not any([args.search, args.download, args.validate, args.update_index]):
        parser.print_help()
        return
    
    if args.search:
        search_datasets()
    
    if args.download:
        download_all()
    
    validation_results = None
    if args.validate:
        validation_results = validate_datasets()
    
    if args.update_index:
        if validation_results is None:
            validation_results = validate_datasets()
        update_index(validation_results)
    
    print("\n✅ Dataset expansion complete!")
    print(f"   Datasets location: {QUANTUM_DIR}")
    print(f"   Index file: {INDEX_FILE}")
    print()


if __name__ == "__main__":
    main()
