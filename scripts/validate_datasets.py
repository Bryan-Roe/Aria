"""
Dataset Validator
=================

Validates downloaded datasets for integrity, format, and quality.
Checks JSONL format, counts samples, reports statistics.

Usage:
    python validate_datasets.py
    python validate_datasets.py --category quantum
    python validate_datasets.py --dataset dolly --verbose

Author: AI Workspace
Date: October 31, 2025
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple
import sys


class DatasetValidator:
    """Validates AI training datasets."""
    
    def __init__(self, datasets_dir: Path):
        self.datasets_dir = datasets_dir
        self.quantum_dir = datasets_dir / "quantum"
        self.chat_dir = datasets_dir / "chat"
        self.index_file = datasets_dir / "dataset_index.json"
        self.errors = []
        self.warnings = []
    
    def validate_csv(self, filepath: Path, verbose: bool = False) -> Dict:
        """Validate CSV dataset.
        
        Uses efficient line counting and iterator-based reading for
        memory efficiency and better performance on large files.
        """
        stats = {
            "valid": False,
            "samples": 0,
            "features": 0,
            "errors": [],
            "warnings": []
        }
        
        try:
            # Check if file is empty first
            if filepath.stat().st_size == 0:
                stats["errors"].append("File is empty")
                return stats
            
            # Efficient line count using binary mode (fastest method)
            with open(filepath, 'rb') as f:
                line_count = sum(1 for _ in f)
            stats["samples"] = line_count
            
            # Read first line for feature count, validate first 100 lines
            with open(filepath, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if not first_line:
                    stats["errors"].append("First line is empty")
                    return stats
                    
                stats["features"] = len(first_line.split(','))
                
                # Check consistency of first 100 lines (including the one we read)
                num_cols = len(first_line.split(','))
                if num_cols != stats["features"]:
                    stats["warnings"].append(
                        f"Line 1: Expected {stats['features']} columns, got {num_cols}"
                    )
                
                # Continue checking lines 2-100
                for i, line in enumerate(f, 2):
                    if i > 100:
                        break
                    num_cols = len(line.strip().split(','))
                    if num_cols != stats["features"]:
                        stats["warnings"].append(
                            f"Line {i}: Expected {stats['features']} columns, got {num_cols}"
                        )
            
            stats["valid"] = len(stats["errors"]) == 0
            
            if verbose:
                print(f"  Samples: {stats['samples']}")
                print(f"  Features: {stats['features']}")
        
        except Exception as e:
            stats["errors"].append(f"Failed to read file: {e}")
        
        return stats
    
    def validate_jsonl(self, filepath: Path, verbose: bool = False) -> Dict:
        """Validate JSONL dataset (chat format).
        
        Uses iterator-based file reading instead of readlines() to avoid
        loading entire file into memory at once.
        """
        stats = {
            "valid": False,
            "samples": 0,
            "total_messages": 0,
            "avg_messages_per_sample": 0,
            "format_errors": [],
            "warnings": []
        }
        
        try:
            # Check if file is empty first
            if filepath.stat().st_size == 0:
                stats["format_errors"].append("File is empty")
                return stats
            
            # Use iterator-based reading (memory efficient for large files)
            with open(filepath, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        stats["warnings"].append(f"Line {i}: Empty line (should be removed)")
                        continue
                    
                    try:
                        data = json.loads(line)
                        
                        # Check for messages field (Phi-3 format)
                        if "messages" in data:
                            messages = data["messages"]
                            if not isinstance(messages, list):
                                stats["format_errors"].append(
                                    f"Line {i}: 'messages' should be a list"
                                )
                            else:
                                stats["total_messages"] += len(messages)
                                
                                # Validate message structure
                                for msg_idx, msg in enumerate(messages):
                                    if not isinstance(msg, dict):
                                        stats["format_errors"].append(
                                            f"Line {i}, message {msg_idx}: Should be a dict"
                                        )
                                    elif "role" not in msg or "content" not in msg:
                                        stats["format_errors"].append(
                                            f"Line {i}, message {msg_idx}: Missing 'role' or 'content'"
                                        )
                        
                        stats["samples"] += 1
                    
                    except json.JSONDecodeError as e:
            
            # Check if file was empty or contained only blank lines
            if stats["samples"] == 0 and not stats["format_errors"]:
                stats["format_errors"].append("File is empty or contains no valid data")
            
            # Calculate statistics
            if stats["samples"] > 0:
                stats["avg_messages_per_sample"] = stats["total_messages"] / stats["samples"]
            
            stats["valid"] = len(stats["format_errors"]) == 0
            
            if verbose:
                print(f"  Samples: {stats['samples']}")
                print(f"  Total messages: {stats['total_messages']}")
                print(f"  Avg messages/sample: {stats['avg_messages_per_sample']:.2f}")
        
        except Exception as e:
            stats["format_errors"].append(f"Failed to read file: {e}")
        
        return stats
    
    def validate_quantum_datasets(self, verbose: bool = False):
        """Validate all quantum datasets."""
        print("\n" + "="*60)
        print("🔬 VALIDATING QUANTUM DATASETS")
        print("="*60)
        
        if not self.quantum_dir.exists():
            print("❌ Quantum datasets directory not found")
            return
        
        csv_files = list(self.quantum_dir.glob("*.csv"))
        if not csv_files:
            print("⚠️  No quantum datasets found")
            return
        
        for csv_file in csv_files:
            print(f"\n📄 {csv_file.name}")
            stats = self.validate_csv(csv_file, verbose)
            
            if stats["valid"]:
                print("  ✅ Valid")
            else:
                print("  ❌ Invalid")
                for error in stats["errors"]:
                    print(f"     Error: {error}")
            
            if stats["warnings"] and verbose:
                for warning in stats["warnings"][:5]:  # Show first 5
                    print(f"     Warning: {warning}")
    
    def validate_chat_datasets(self, dataset_name: str = None, verbose: bool = False):
        """Validate chat/LLM datasets."""
        print("\n" + "="*60)
        print("💬 VALIDATING CHAT DATASETS")
        print("="*60)
        
        if not self.chat_dir.exists():
            print("❌ Chat datasets directory not found")
            return
        
        # Get dataset directories
        dataset_dirs = [d for d in self.chat_dir.iterdir() if d.is_dir()]
        if dataset_name:
            dataset_dirs = [d for d in dataset_dirs if d.name == dataset_name]
        
        if not dataset_dirs:
            print("⚠️  No chat datasets found")
            return
        
        for dataset_dir in dataset_dirs:
            print(f"\n📚 {dataset_dir.name}")
            
            jsonl_files = list(dataset_dir.glob("*.jsonl"))
            if not jsonl_files:
                print("  ⚠️  No JSONL files found")
                continue
            
            for jsonl_file in jsonl_files:
                print(f"\n  📄 {jsonl_file.name}")
                stats = self.validate_jsonl(jsonl_file, verbose)
                
                if stats["valid"]:
                    print("    ✅ Valid JSONL format")
                else:
                    print("    ❌ Format errors detected")
                    for error in stats["format_errors"][:5]:  # Show first 5
                        print(f"       Error: {error}")
                
                if stats["warnings"] and verbose:
                    for warning in stats["warnings"][:5]:
                        print(f"       Warning: {warning}")
    
    def generate_report(self):
        """Generate validation report."""
        print("\n" + "="*60)
        print("📊 VALIDATION REPORT")
        print("="*60)
        
        # Load index
        if not self.index_file.exists():
            print("⚠️  No dataset index found. Run download_datasets.py first.")
            return
        
        with open(self.index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        total_datasets = len(index.get("datasets", {}))
        print(f"\nTotal registered datasets: {total_datasets}")
        
        # Calculate total size
        total_size = 0
        for name, info in index.get("datasets", {}).items():
            if "size" in info:
                total_size += info["size"]
            elif "size_gb" in info:
                total_size += info["size_gb"] * 1024 * 1024 * 1024
        
        size_gb = total_size / (1024 * 1024 * 1024)
        print(f"Total storage used: {size_gb:.2f} GB")
        
        if index.get("last_updated"):
            print(f"Last updated: {index['last_updated']}")


def main():
    parser = argparse.ArgumentParser(
        description="Validate AI training datasets",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--category',
        choices=['quantum', 'chat', 'all'],
        default='all',
        help='Dataset category to validate (default: all)'
    )
    
    parser.add_argument(
        '--dataset',
        help='Specific dataset name to validate'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed statistics'
    )
    
    args = parser.parse_args()
    
    # Get datasets directory
    base_dir = Path(__file__).parent.parent
    datasets_dir = base_dir / "datasets"
    
    validator = DatasetValidator(datasets_dir)
    
    # Validate datasets
    if args.category in ['quantum', 'all']:
        validator.validate_quantum_datasets(args.verbose)
    
    if args.category in ['chat', 'all']:
        validator.validate_chat_datasets(args.dataset, args.verbose)
    
    # Generate report
    validator.generate_report()


if __name__ == "__main__":
    main()
