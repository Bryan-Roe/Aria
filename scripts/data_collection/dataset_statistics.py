#!/usr/bin/env python3
"""
Dataset Statistics and Reporting
Generates comprehensive statistics about available datasets
"""

import json
from pathlib import Path
from datetime import datetime
import pandas as pd


def analyze_datasets():
    """Analyze all datasets and generate statistics"""
    datasets_dir = Path("datasets")
    stats = {
        "generated_at": datetime.now().isoformat(),
        "categories": {},
        "totals": {
            "total_files": 0,
            "total_samples": 0,
            "total_size_mb": 0
        }
    }
    
    categories = ["quantum", "chat", "vision", "massive_quantum"]
    
    for category in categories:
        cat_dir = datasets_dir / category
        if not cat_dir.exists():
            continue
        
        cat_stats = {
            "csv_files": 0,
            "jsonl_files": 0,
            "total_files": 0,
            "total_samples": 0,
            "total_size_mb": 0,
            "files": []
        }
        
        # Process CSV files
        for csv_file in cat_dir.glob("*.csv"):
            try:
                df = pd.read_csv(csv_file, encoding='utf-8', on_bad_lines='skip')
                file_info = {
                    "name": csv_file.name,
                    "type": "csv",
                    "samples": len(df),
                    "features": len(df.columns),
                    "size_kb": csv_file.stat().st_size / 1024
                }
                cat_stats["files"].append(file_info)
                cat_stats["csv_files"] += 1
                cat_stats["total_samples"] += len(df)
                cat_stats["total_size_mb"] += csv_file.stat().st_size / 1024 / 1024
            except Exception as e:
                # Silently skip problematic files
                continue
        
        # Process JSONL files
        for jsonl_file in cat_dir.rglob("*.jsonl"):
            try:
                with open(jsonl_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = sum(1 for line in f if line.strip())
                
                file_info = {
                    "name": jsonl_file.name,
                    "type": "jsonl",
                    "samples": lines,
                    "size_kb": jsonl_file.stat().st_size / 1024
                }
                cat_stats["files"].append(file_info)
                cat_stats["jsonl_files"] += 1
                cat_stats["total_samples"] += lines
                cat_stats["total_size_mb"] += jsonl_file.stat().st_size / 1024 / 1024
            except Exception as e:
                # Silently skip problematic files
                continue
        
        cat_stats["total_files"] = cat_stats["csv_files"] + cat_stats["jsonl_files"]
        stats["categories"][category] = cat_stats
        
        # Update totals
        stats["totals"]["total_files"] += cat_stats["total_files"]
        stats["totals"]["total_samples"] += cat_stats["total_samples"]
        stats["totals"]["total_size_mb"] += cat_stats["total_size_mb"]
    
    return stats


def print_statistics(stats):
    """Print formatted statistics"""
    print("=" * 80)
    print("📊 DATASET STATISTICS")
    print("=" * 80)
    print(f"Generated: {stats['generated_at']}\n")
    
    for category, cat_stats in stats["categories"].items():
        print(f"\n📁 {category.upper()}")
        print(f"   Files: {cat_stats['total_files']} ({cat_stats['csv_files']} CSV, {cat_stats['jsonl_files']} JSONL)")
        print(f"   Samples: {cat_stats['total_samples']:,}")
        print(f"   Size: {cat_stats['total_size_mb']:.1f} MB")
        
        if cat_stats['total_files'] > 0:
            # Show top 5 largest files
            sorted_files = sorted(cat_stats['files'], key=lambda x: x.get('samples', 0), reverse=True)[:5]
            if sorted_files:
                print(f"   Top files by sample count:")
                for f in sorted_files:
                    print(f"      - {f['name']}: {f.get('samples', 0):,} samples")
    
    print(f"\n" + "=" * 80)
    print("📈 TOTALS")
    print("=" * 80)
    print(f"Total Files: {stats['totals']['total_files']}")
    print(f"Total Samples: {stats['totals']['total_samples']:,}")
    print(f"Total Size: {stats['totals']['total_size_mb']:.1f} MB")
    print("=" * 80)


def main():
    """Main entry point"""
    print("Analyzing datasets...")
    stats = analyze_datasets()
    
    # Print to console
    print_statistics(stats)
    
    # Save to file
    output_dir = Path("data_out/reports")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "dataset_statistics.json"
    with open(output_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    print(f"\n📄 Full report saved to: {output_file}")


if __name__ == "__main__":
    main()
