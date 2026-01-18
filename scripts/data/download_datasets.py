"""
Automated Dataset Downloader
=============================

Downloads curated datasets for AI training across all workspace projects.
Supports quantum ML, chat fine-tuning, and general ML datasets.

Usage:
    python download_datasets.py --category all
    python download_datasets.py --category quantum
    python download_datasets.py --category chat --dataset dolly
    python download_datasets.py --category chat --dataset all --max-size 5GB

Author: AI Workspace
Date: October 31, 2025
"""

import argparse
import json
import urllib.request
import zipfile
import gzip
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import sys

# Add progress bar if available
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    print("⚠️  Install tqdm for progress bars: pip install tqdm")


class DatasetDownloader:
    """Automated dataset downloader with validation and caching."""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.datasets_dir = base_dir / "datasets"
        self.raw_dir = self.datasets_dir / "raw"
        self.quantum_dir = self.datasets_dir / "quantum"
        self.chat_dir = self.datasets_dir / "chat"
        self.index_file = self.datasets_dir / "dataset_index.json"
        
        # Create directories
        for dir_path in [self.raw_dir, self.quantum_dir, self.chat_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Load or create index
        self.index = self._load_index()
    
    def _load_index(self) -> Dict:
        """Load dataset index from JSON."""
        if self.index_file.exists():
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"datasets": {}, "last_updated": None}
    
    def _save_index(self):
        """Save dataset index to JSON."""
        from datetime import datetime
        self.index["last_updated"] = datetime.now().isoformat()
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, indent=2)
    
    def _download_file(self, url: str, dest: Path, desc: str = "Downloading"):
        """Download file with progress bar."""
        if dest.exists():
            print(f"✓ Already exists: {dest.name}")
            return True
        
        print(f"📥 Downloading {desc}...")
        try:
            if HAS_TQDM:
                # Download with progress bar
                response = urllib.request.urlopen(url)
                total_size = int(response.headers.get('content-length', 0))
                
                with open(dest, 'wb') as f:
                    with tqdm(total=total_size, unit='B', unit_scale=True) as pbar:
                        while True:
                            chunk = response.read(8192)
                            if not chunk:
                                break
                            f.write(chunk)
                            pbar.update(len(chunk))
            else:
                # Simple download
                urllib.request.urlretrieve(url, dest)
            
            print(f"✓ Downloaded: {dest.name}")
            return True
        
        except Exception as e:
            print(f"❌ Failed to download {url}: {e}")
            if dest.exists():
                dest.unlink()
            return False
    
    def download_quantum_datasets(self):
        """Download quantum ML datasets from UCI and other sources."""
        print("\n" + "="*60)
        print("🔬 DOWNLOADING QUANTUM AI DATASETS")
        print("="*60)
        
        datasets = {
            "heart_disease": {
                "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.cleveland.data",
                "filename": "heart_disease.csv",
                "description": "Cleveland Heart Disease Dataset"
            },
            "ionosphere": {
                "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/ionosphere/ionosphere.data",
                "filename": "ionosphere.csv",
                "description": "Ionosphere Radar Dataset"
            },
            "sonar": {
                "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/undocumented/connectionist-bench/sonar/sonar.all-data",
                "filename": "sonar.csv",
                "description": "Sonar Mines vs Rocks Dataset"
            },
            "banknote": {
                "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/00267/data_banknote_authentication.txt",
                "filename": "banknote.csv",
                "description": "Banknote Authentication Dataset"
            }
        }
        
        for name, info in datasets.items():
            dest = self.quantum_dir / info["filename"]
            success = self._download_file(info["url"], dest, info["description"])
            
            if success:
                # Add to index
                self.index["datasets"][name] = {
                    "category": "quantum",
                    "filename": info["filename"],
                    "path": str(dest),
                    "description": info["description"],
                    "size": dest.stat().st_size if dest.exists() else 0
                }
        
        print(f"\n✅ Quantum datasets saved to: {self.quantum_dir}")
        self._save_index()
    
    def download_chat_datasets(self, dataset_name: str = "all", max_size_gb: float = 10.0):
        """Download chat/LLM fine-tuning datasets from Hugging Face."""
        print("\n" + "="*60)
        print("💬 DOWNLOADING CHAT/LLM DATASETS")
        print("="*60)
        
        # Check if datasets library is available
        try:
            from datasets import load_dataset
        except ImportError:
            print("❌ Error: 'datasets' library not installed")
            print("   Install with: pip install datasets")
            return
        
        # Dataset configurations
        available_datasets = {
            "dolly": {
                "hf_name": "databricks/databricks-dolly-15k",
                "description": "Dolly 15k - High-quality instruction pairs",
                "size_gb": 0.05,
                "license": "CC BY-SA 3.0 (Commercial OK)"
            },
            "openassistant": {
                "hf_name": "OpenAssistant/oasst1",
                "description": "OpenAssistant Conversations - Multi-turn dialogue",
                "size_gb": 0.5,
                "license": "Apache 2.0"
            },
            "alpaca": {
                "hf_name": "tatsu-lab/alpaca",
                "description": "Stanford Alpaca - Instruction tuning",
                "size_gb": 0.1,
                "license": "CC BY-NC 4.0 (Non-commercial)"
            }
        }
        
        # Filter by name and size
        datasets_to_download = {}
        if dataset_name == "all":
            datasets_to_download = {
                k: v for k, v in available_datasets.items() 
                if v["size_gb"] <= max_size_gb
            }
        elif dataset_name in available_datasets:
            datasets_to_download = {dataset_name: available_datasets[dataset_name]}
        else:
            print(f"❌ Unknown dataset: {dataset_name}")
            print(f"   Available: {', '.join(available_datasets.keys())}")
            return
        
        # Download each dataset
        for name, info in datasets_to_download.items():
            print(f"\n📚 Downloading: {info['description']}")
            print(f"   Size: ~{info['size_gb']} GB")
            print(f"   License: {info['license']}")
            
            try:
                # Load dataset
                dataset = load_dataset(info["hf_name"])
                
                # Save to JSONL (Phi-3 format)
                output_dir = self.chat_dir / name
                output_dir.mkdir(exist_ok=True)
                
                for split in dataset.keys():
                    output_file = output_dir / f"{split}.jsonl"
                    
                    print(f"   Converting {split} split to JSONL...")
                    # Use buffered I/O with batch writes for better performance
                    buffer = []
                    buffer_size = 1000  # Write in batches of 1000 lines
                    
                    with open(output_file, 'w', encoding='utf-8', buffering=65536) as f:
                        for example in dataset[split]:
                            # Convert to chat format if needed
                            if "messages" in example:
                                line = json.dumps({"messages": example["messages"]})
                            elif "instruction" in example and "response" in example:
                                # Alpaca/Dolly format - build user content
                                input_text = example.get("input", "").strip()
                                instruction = example["instruction"]
                                user_content = f"{input_text}\n\n{instruction}".strip() if input_text else instruction
                                messages = [
                                    {"role": "user", "content": user_content},
                                    {"role": "assistant", "content": example["response"]}
                                ]
                                line = json.dumps({"messages": messages})
                            else:
                                # Try to preserve original format
                                line = json.dumps(example)
                            
                            buffer.append(line)
                            
                            # Flush buffer when it reaches threshold
                            if len(buffer) >= buffer_size:
                                f.write('\n'.join(buffer) + '\n')
                                buffer.clear()
                        
                        # Write remaining items
                        if buffer:
                            f.write('\n'.join(buffer) + '\n')
                    
                    print(f"   ✓ Saved: {output_file}")
                
                # Update index
                self.index["datasets"][name] = {
                    "category": "chat",
                    "hf_name": info["hf_name"],
                    "path": str(output_dir),
                    "description": info["description"],
                    "license": info["license"],
                    "size_gb": info["size_gb"]
                }
                
                print(f"✅ {name} downloaded successfully")
            
            except Exception as e:
                print(f"❌ Failed to download {name}: {e}")
        
        print(f"\n✅ Chat datasets saved to: {self.chat_dir}")
        self._save_index()
    
    def list_downloaded(self):
        """List all downloaded datasets."""
        print("\n" + "="*60)
        print("📊 DOWNLOADED DATASETS")
        print("="*60)
        
        if not self.index["datasets"]:
            print("No datasets downloaded yet.")
            return
        
        for name, info in self.index["datasets"].items():
            print(f"\n{name}:")
            print(f"  Category: {info.get('category', 'unknown')}")
            print(f"  Description: {info.get('description', 'N/A')}")
            print(f"  Path: {info.get('path', 'N/A')}")
            if 'size' in info:
                size_mb = info['size'] / (1024 * 1024)
                print(f"  Size: {size_mb:.2f} MB")
            if 'license' in info:
                print(f"  License: {info['license']}")


def main():
    parser = argparse.ArgumentParser(
        description="Download AI training datasets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download all quantum datasets
  python download_datasets.py --category quantum
  
  # Download specific chat dataset
  python download_datasets.py --category chat --dataset dolly
  
  # Download all chat datasets under 5GB
  python download_datasets.py --category chat --dataset all --max-size 5
  
  # List downloaded datasets
  python download_datasets.py --list
        """
    )
    
    parser.add_argument(
        '--category',
        choices=['quantum', 'chat', 'all'],
        help='Dataset category to download'
    )
    
    parser.add_argument(
        '--dataset',
        default='all',
        help='Specific dataset name (for chat category)'
    )
    
    parser.add_argument(
        '--max-size',
        type=float,
        default=10.0,
        help='Maximum dataset size in GB (default: 10)'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all downloaded datasets'
    )
    
    args = parser.parse_args()
    
    # Get base directory (workspace root)
    base_dir = Path(__file__).parent.parent
    downloader = DatasetDownloader(base_dir)
    
    if args.list:
        downloader.list_downloaded()
        return
    
    if not args.category:
        parser.print_help()
        return
    
    # Download datasets
    if args.category in ['quantum', 'all']:
        downloader.download_quantum_datasets()
    
    if args.category in ['chat', 'all']:
        downloader.download_chat_datasets(args.dataset, args.max_size)
    
    # Show summary
    downloader.list_downloaded()


if __name__ == "__main__":
    main()
