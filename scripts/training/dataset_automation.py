#!/usr/bin/env python3
"""
Unified Dataset Collection and Validation Automation
Orchestrates comprehensive dataset gathering, validation, and preparation for training
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_collection(sources=None, limit=20, quick=False):
    """Run dataset collection"""
    from data_collection.comprehensive_dataset_collector import DatasetCollector
    
    logger.info("="*80)
    logger.info("PHASE 1: Dataset Collection")
    logger.info("="*80)
    
    collector = DatasetCollector()
    
    if quick:
        sources = ["sklearn"]
        limit = 10
    
    datasets = await collector.collect_all(sources=sources, limit_per_source=limit)
    
    return len(datasets)


async def run_validation():
    """Run dataset validation"""
    from data_collection.dataset_validator import DatasetValidator
    
    logger.info("\n" + "="*80)
    logger.info("PHASE 2: Dataset Validation")
    logger.info("="*80 + "\n")
    
    validator = DatasetValidator()
    results = validator.validate_all()
    
    return results


async def run_training_preparation():
    """Prepare datasets for training"""
    logger.info("\n" + "="*80)
    logger.info("PHASE 3: Training Preparation")
    logger.info("="*80 + "\n")
    
    # Update dataset index
    from pathlib import Path
    import json
    
    datasets_dir = Path("datasets")
    index = {"datasets": {}, "updated_at": datetime.now().isoformat()}
    
    # Scan all categories
    for category in ["quantum", "chat", "vision", "massive_quantum"]:
        cat_dir = datasets_dir / category
        if not cat_dir.exists():
            continue
        
        # Count files
        csv_files = list(cat_dir.glob("*.csv"))
        jsonl_files = list(cat_dir.glob("*.jsonl"))
        
        # Add subdirectories for chat
        if category == "chat":
            for subdir in cat_dir.iterdir():
                if subdir.is_dir():
                    jsonl_files.extend(subdir.glob("*.jsonl"))
        
        total = len(csv_files) + len(jsonl_files)
        
        index["datasets"][category] = {
            "count": total,
            "csv_files": len(csv_files),
            "jsonl_files": len(jsonl_files),
            "path": str(cat_dir)
        }
        
        logger.info(f"{category}: {total} datasets ({len(csv_files)} CSV, {len(jsonl_files)} JSONL)")
    
    # Save updated index
    index_file = datasets_dir / "dataset_index_updated.json"
    with open(index_file, 'w') as f:
        json.dump(index, f, indent=2)
    
    logger.info(f"\n✅ Dataset index updated: {index_file}")
    
    return index


def print_summary(collection_count, validation_results, preparation_index):
    """Print final summary"""
    logger.info("\n" + "="*80)
    logger.info("📊 FINAL SUMMARY")
    logger.info("="*80)
    
    logger.info(f"\n📦 Collection:")
    logger.info(f"   New datasets collected: {collection_count}")
    
    logger.info(f"\n🔍 Validation:")
    if validation_results:
        total = validation_results.get("summary", {}).get("total_datasets", 0)
        valid = validation_results.get("summary", {}).get("valid_datasets", 0)
        invalid = validation_results.get("summary", {}).get("failed_datasets", 0)
        logger.info(f"   Total validated: {total}")
        logger.info(f"   Valid: {valid}")
        logger.info(f"   Invalid: {invalid}")
        if total > 0:
            logger.info(f"   Success rate: {valid/total*100:.1f}%")
    
    logger.info(f"\n📚 Dataset Inventory:")
    for category, info in preparation_index.get("datasets", {}).items():
        logger.info(f"   {category}: {info['count']} datasets")
    
    total_datasets = sum(info['count'] for info in preparation_index.get("datasets", {}).values())
    logger.info(f"\n🎯 Total Available Datasets: {total_datasets}")
    
    logger.info("\n📄 Reports Generated:")
    logger.info("   - data_out/data_collection/collection_report.json")
    logger.info("   - data_out/validation/validation_report.json")
    logger.info("   - datasets/dataset_index_updated.json")
    
    logger.info("\n✅ All operations completed successfully!")
    logger.info("="*80)


async def main():
    """Main orchestrator"""
    parser = argparse.ArgumentParser(
        description="Unified Dataset Collection and Validation Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick mode (sklearn only, fast)
  python scripts/dataset_automation.py --quick
  
  # Full collection from all sources
  python scripts/dataset_automation.py --sources sklearn openml huggingface
  
  # Validation only (skip collection)
  python scripts/dataset_automation.py --validate-only
  
  # Collection with custom limit
  python scripts/dataset_automation.py --sources sklearn openml --limit 50
        """
    )
    
    parser.add_argument("--sources", nargs="+",
                       choices=["sklearn", "openml", "huggingface", "kaggle", "uci"],
                       help="Sources to collect from")
    parser.add_argument("--limit", type=int, default=20,
                       help="Limit per source (default: 20)")
    parser.add_argument("--quick", action="store_true",
                       help="Quick mode: sklearn only, limit 10")
    parser.add_argument("--validate-only", action="store_true",
                       help="Only run validation, skip collection")
    parser.add_argument("--collect-only", action="store_true",
                       help="Only run collection, skip validation")
    
    args = parser.parse_args()
    
    start_time = datetime.now()
    
    logger.info("="*80)
    logger.info("🚀 Dataset Automation Pipeline Started")
    logger.info(f"   Time: {start_time.isoformat()}")
    logger.info("="*80)
    
    collection_count = 0
    validation_results = None
    preparation_index = None
    
    try:
        # Phase 1: Collection
        if not args.validate_only:
            collection_count = await run_collection(
                sources=args.sources,
                limit=args.limit,
                quick=args.quick
            )
        
        # Phase 2: Validation
        if not args.collect_only:
            validation_results = await run_validation()
        
        # Phase 3: Preparation
        preparation_index = await run_training_preparation()
        
        # Summary
        print_summary(collection_count, validation_results, preparation_index)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"\n⏱️  Total Duration: {duration:.1f} seconds")
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("\n\n⚠️  Operation cancelled by user")
        return 130
    except Exception as e:
        logger.error(f"\n\n❌ Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
