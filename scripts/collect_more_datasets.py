"""
Enhanced Dataset Collection for Quantum ML
===========================================

Downloads additional high-quality datasets suitable for quantum machine learning.
Focuses on binary and multi-class classification problems with 2-20 features.

New Datasets Added:
- Wisconsin Breast Cancer (diagnostic)
- Diabetes (Pima Indians)
- Wine Quality (red & white)
- Glass Identification
- Iris (multi-class)
- Wheat Seeds
- Vertebral Column
- Blood Transfusion
- Haberman Survival
- MAGIC Gamma Telescope

Usage:
    python collect_more_datasets.py --all
    python collect_more_datasets.py --dataset breast_cancer
    python collect_more_datasets.py --category medical

Author: Quantum AI System
Date: November 16, 2025
"""

import urllib.request
import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime
import argparse
import sys

# Add progress bar if available
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False


class QuantumDatasetCollector:
    """Collect datasets optimized for quantum ML (2-20 features, clear labels)."""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.quantum_dir = base_dir / "datasets" / "quantum"
        self.raw_dir = base_dir / "datasets" / "raw"
        self.index_file = base_dir / "datasets" / "dataset_index.json"
        
        # Create directories
        self.quantum_dir.mkdir(parents=True, exist_ok=True)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        
        # Dataset catalog
        self.datasets = {
            "breast_cancer": {
                "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/breast-cancer-wisconsin/wdbc.data",
                "filename": "breast_cancer.csv",
                "description": "Wisconsin Breast Cancer Diagnostic",
                "features": 30,
                "samples": 569,
                "classes": 2,
                "category": "medical",
                "difficulty": "medium",
                "task": "Binary classification: Malignant vs Benign"
            },
            "diabetes": {
                "url": "https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv",
                "filename": "diabetes.csv",
                "description": "Pima Indians Diabetes",
                "features": 8,
                "samples": 768,
                "classes": 2,
                "category": "medical",
                "difficulty": "medium",
                "task": "Binary classification: Diabetes onset prediction"
            },
            "wine_red": {
                "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-red.csv",
                "filename": "wine_red.csv",
                "description": "Red Wine Quality",
                "features": 11,
                "samples": 1599,
                "classes": 6,
                "category": "chemistry",
                "difficulty": "hard",
                "task": "Multi-class: Wine quality rating (3-8)"
            },
            "wine_white": {
                "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-white.csv",
                "filename": "wine_white.csv",
                "description": "White Wine Quality",
                "features": 11,
                "samples": 4898,
                "classes": 7,
                "category": "chemistry",
                "difficulty": "hard",
                "task": "Multi-class: Wine quality rating (3-9)"
            },
            "glass": {
                "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/glass/glass.data",
                "filename": "glass.csv",
                "description": "Glass Identification",
                "features": 9,
                "samples": 214,
                "classes": 6,
                "category": "forensics",
                "difficulty": "hard",
                "task": "Multi-class: Glass type classification"
            },
            "iris": {
                "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data",
                "filename": "iris.csv",
                "description": "Iris Flower Species",
                "features": 4,
                "samples": 150,
                "classes": 3,
                "category": "biology",
                "difficulty": "easy",
                "task": "Multi-class: Iris species (setosa, versicolor, virginica)"
            },
            "wheat_seeds": {
                "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/00236/seeds_dataset.txt",
                "filename": "wheat_seeds.csv",
                "description": "Wheat Seeds Classification",
                "features": 7,
                "samples": 210,
                "classes": 3,
                "category": "agriculture",
                "difficulty": "medium",
                "task": "Multi-class: Wheat variety classification"
            },
            "vertebral_column": {
                "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/00212/vertebral_column_data.zip",
                "filename": "vertebral_column.csv",
                "description": "Vertebral Column Classification",
                "features": 6,
                "samples": 310,
                "classes": 3,
                "category": "medical",
                "difficulty": "medium",
                "task": "Multi-class: Normal, Disk Hernia, Spondylolisthesis",
                "requires_extraction": True
            },
            "blood_transfusion": {
                "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/blood-transfusion/transfusion.data",
                "filename": "blood_transfusion.csv",
                "description": "Blood Transfusion Service Center",
                "features": 4,
                "samples": 748,
                "classes": 2,
                "category": "medical",
                "difficulty": "medium",
                "task": "Binary: Blood donation prediction"
            },
            "haberman": {
                "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/haberman/haberman.data",
                "filename": "haberman.csv",
                "description": "Haberman Survival",
                "features": 3,
                "samples": 306,
                "classes": 2,
                "category": "medical",
                "difficulty": "hard",
                "task": "Binary: Patient survival (5+ years)"
            },
            "magic_gamma": {
                "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/magic/magic04.data",
                "filename": "magic_gamma.csv",
                "description": "MAGIC Gamma Telescope",
                "features": 10,
                "samples": 19020,
                "classes": 2,
                "category": "physics",
                "difficulty": "medium",
                "task": "Binary: Gamma signal vs Hadron background"
            }
        }
    
    def _download_file(self, url: str, dest: Path, desc: str = "Downloading") -> bool:
        """Download file with progress tracking."""
        if dest.exists():
            print(f"   ✓ Already exists: {dest.name}")
            return True
        
        print(f"   📥 Downloading {desc}...")
        try:
            if HAS_TQDM:
                response = urllib.request.urlopen(url)
                total_size = int(response.headers.get('content-length', 0))
                
                with open(dest, 'wb') as f:
                    with tqdm(total=total_size, unit='B', unit_scale=True, desc="   ") as pbar:
                        while True:
                            chunk = response.read(8192)
                            if not chunk:
                                break
                            f.write(chunk)
                            pbar.update(len(chunk))
            else:
                urllib.request.urlretrieve(url, dest)
            
            print(f"   ✓ Downloaded: {dest.name} ({dest.stat().st_size / 1024:.1f} KB)")
            return True
        
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            if dest.exists():
                dest.unlink()
            return False
    
    def download_dataset(self, name: str) -> bool:
        """Download and prepare a single dataset."""
        if name not in self.datasets:
            print(f"❌ Unknown dataset: {name}")
            return False
        
        info = self.datasets[name]
        print(f"\n{'='*70}")
        print(f"📊 {info['description']}")
        print(f"{'='*70}")
        print(f"   Task: {info['task']}")
        print(f"   Features: {info['features']}, Samples: {info['samples']}, Classes: {info['classes']}")
        print(f"   Category: {info['category']}, Difficulty: {info['difficulty']}")
        
        dest = self.quantum_dir / info["filename"]
        
        # Download
        success = self._download_file(info["url"], dest, info["description"])
        
        if success:
            # Validate the file
            try:
                df = pd.read_csv(dest, header=None if 'header' not in info else 0)
                print(f"   ✓ Validated: {len(df)} rows, {len(df.columns)} columns")
                
                # Update index
                self._update_index(name, info, dest)
                return True
            except Exception as e:
                print(f"   ⚠️  Warning: Could not validate CSV: {e}")
                return True  # Still count as success if download worked
        
        return False
    
    def download_by_category(self, category: str) -> int:
        """Download all datasets in a category."""
        matching = {k: v for k, v in self.datasets.items() if v.get('category') == category}
        
        if not matching:
            print(f"❌ No datasets found for category: {category}")
            print(f"   Available categories: {set(d['category'] for d in self.datasets.values())}")
            return 0
        
        print(f"\n🎯 Downloading {len(matching)} datasets in category: {category}")
        
        success_count = 0
        for name in matching:
            if self.download_dataset(name):
                success_count += 1
        
        return success_count
    
    def download_all(self) -> int:
        """Download all datasets."""
        print(f"\n🚀 Downloading ALL datasets ({len(self.datasets)} total)")
        
        success_count = 0
        for name in self.datasets:
            if self.download_dataset(name):
                success_count += 1
        
        return success_count
    
    def _update_index(self, name: str, info: dict, path: Path):
        """Update dataset index."""
        # Load existing index
        if self.index_file.exists():
            with open(self.index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
        else:
            index = {"datasets": {}, "metadata": {}, "storage": {}}
        
        # Add dataset
        index["datasets"][name] = {
            "category": "quantum",
            "filename": info["filename"],
            "path": str(path),
            "description": info["description"],
            "size": path.stat().st_size if path.exists() else 0,
            "features": info["features"],
            "samples": info["samples"],
            "classes": info["classes"],
            "task": info["task"],
            "difficulty": info["difficulty"],
            "dataset_category": info["category"]
        }
        
        # Update timestamp
        index["last_updated"] = datetime.now().isoformat()
        
        # Save
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2)
    
    def show_catalog(self):
        """Display all available datasets."""
        print("\n" + "="*70)
        print("📚 QUANTUM ML DATASET CATALOG")
        print("="*70)
        
        # Group by category
        by_category = {}
        for name, info in self.datasets.items():
            cat = info['category']
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append((name, info))
        
        for cat, items in sorted(by_category.items()):
            print(f"\n🏷️  {cat.upper()}")
            print("-" * 70)
            for name, info in items:
                status = "✅" if (self.quantum_dir / info["filename"]).exists() else "⬜"
                print(f"{status} {name:20s} - {info['description']}")
                print(f"   {info['samples']:5d} samples | {info['features']:2d} features | {info['classes']} classes | {info['difficulty']}")
        
        print("\n" + "="*70)
        total = len(self.datasets)
        downloaded = sum(1 for d in self.datasets.values() if (self.quantum_dir / d["filename"]).exists())
        print(f"Total: {total} datasets | Downloaded: {downloaded} | Remaining: {total - downloaded}")
        print("="*70)


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(description="Collect additional quantum ML datasets")
    parser.add_argument("--all", action="store_true", help="Download all datasets")
    parser.add_argument("--dataset", type=str, help="Download specific dataset by name")
    parser.add_argument("--category", type=str, help="Download all datasets in category (medical, physics, etc)")
    parser.add_argument("--catalog", action="store_true", help="Show dataset catalog")
    parser.add_argument("--base-dir", type=str, help="Base directory (default: current dir)")
    
    args = parser.parse_args()
    
    # Determine base directory
    if args.base_dir:
        base_dir = Path(args.base_dir)
    else:
        # Try to find workspace root
        current = Path.cwd()
        if (current / "datasets").exists():
            base_dir = current
        elif (current.parent / "datasets").exists():
            base_dir = current.parent
        else:
            base_dir = current
    
    print("="*70)
    print("  QUANTUM ML DATASET COLLECTOR")
    print("="*70)
    print(f"\n📂 Base Directory: {base_dir}")
    print(f"📂 Quantum Datasets: {base_dir / 'datasets' / 'quantum'}")
    
    collector = QuantumDatasetCollector(base_dir)
    
    # Execute requested action
    if args.catalog:
        collector.show_catalog()
    elif args.all:
        success = collector.download_all()
        print(f"\n✅ Successfully downloaded {success}/{len(collector.datasets)} datasets")
    elif args.category:
        success = collector.download_by_category(args.category)
        print(f"\n✅ Successfully downloaded {success} datasets in category: {args.category}")
    elif args.dataset:
        if collector.download_dataset(args.dataset):
            print(f"\n✅ Successfully downloaded: {args.dataset}")
        else:
            print(f"\n❌ Failed to download: {args.dataset}")
            sys.exit(1)
    else:
        # Default: show catalog
        collector.show_catalog()
        print("\n💡 Usage:")
        print("   python collect_more_datasets.py --all")
        print("   python collect_more_datasets.py --dataset breast_cancer")
        print("   python collect_more_datasets.py --category medical")
        print("   python collect_more_datasets.py --catalog")
    
    print("\n" + "="*70)
    print("  ✅ COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()
