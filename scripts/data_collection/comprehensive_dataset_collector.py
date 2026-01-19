"""
Comprehensive Dataset Collection and Enhancement
Automatically discovers, downloads, validates, and augments datasets from multiple sources
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import hashlib
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatasetCollector:
    """Comprehensive dataset collection and management"""
    
    def __init__(self):
        self.datasets_dir = Path("datasets")
        self.data_out_dir = Path("data_out/data_collection")
        self.data_out_dir.mkdir(parents=True, exist_ok=True)
        
        self.categories = ["quantum", "chat", "vision"]
        self.sources = {
            "openml": self.collect_from_openml,
            "huggingface": self.collect_from_huggingface,
            "kaggle": self.collect_from_kaggle,
            "sklearn": self.collect_from_sklearn,
            "uci": self.collect_from_uci
        }
        
        self.stats = {
            "started_at": datetime.now().isoformat(),
            "downloaded": 0,
            "augmented": 0,
            "validated": 0,
            "failed": 0,
            "datasets_by_category": {},
            "datasets_by_source": {}
        }
    
    async def collect_from_openml(self, category: str, limit: int = 50) -> List[Dict]:
        """Collect datasets from OpenML"""
        logger.info(f"📦 Collecting from OpenML ({category})...")
        datasets = []
        
        try:
            # Try importing openml
            import openml
            
            # Get datasets based on category
            if category == "quantum":
                # Small classification datasets suitable for quantum ML
                dataset_list = openml.datasets.list_datasets(
                    size=1000,
                    number_instances=1000,
                    number_features=50,
                    output_format="dataframe"
                )
                
                # Take first 'limit' datasets
                for idx, (dataset_id, row) in enumerate(dataset_list.head(limit).iterrows()):
                    try:
                        dataset = openml.datasets.get_dataset(dataset_id)
                        X, y, _, _ = dataset.get_data(dataset_format="array")
                        
                        # Save to CSV
                        import pandas as pd
                        df = pd.DataFrame(X)
                        if y is not None:
                            df['target'] = y
                        
                        filename = f"openml_{dataset_id}_{dataset.name.replace(' ', '_')}.csv"
                        filepath = self.datasets_dir / category / filename
                        df.to_csv(filepath, index=False)
                        
                        datasets.append({
                            "source": "openml",
                            "category": category,
                            "name": dataset.name,
                            "id": dataset_id,
                            "path": str(filepath),
                            "samples": len(df),
                            "features": len(df.columns)
                        })
                        
                        logger.info(f"  ✅ Downloaded: {dataset.name}")
                        
                    except Exception as e:
                        logger.warning(f"  ⚠️  Failed to download dataset {dataset_id}: {e}")
                        continue
            
        except ImportError:
            logger.warning("⚠️  OpenML not installed. Install with: pip install openml")
        except Exception as e:
            logger.error(f"❌ Error collecting from OpenML: {e}")
        
        return datasets
    
    async def collect_from_huggingface(self, category: str, limit: int = 20) -> List[Dict]:
        """Collect datasets from HuggingFace"""
        logger.info(f"🤗 Collecting from HuggingFace ({category})...")
        datasets = []
        
        try:
            from datasets import load_dataset
            
            if category == "chat":
                # High-quality instruction/chat datasets
                dataset_names = [
                    "databricks/databricks-dolly-15k",
                    "OpenAssistant/oasst1",
                    "HuggingFaceH4/ultrachat_200k",
                    "HuggingFaceH4/no_robots",
                    "teknium/OpenHermes-2.5",
                    "Intel/orca_dpo_pairs",
                    "GAIR/lima",
                    "tatsu-lab/alpaca"
                ]
                
                for dataset_name in dataset_names[:limit]:
                    try:
                        logger.info(f"  Downloading: {dataset_name}")
                        ds = load_dataset(dataset_name, split="train[:1000]")
                        
                        # Convert to chat format
                        output_dir = self.datasets_dir / category / dataset_name.split("/")[-1]
                        output_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Save as JSONL
                        output_file = output_dir / "train.jsonl"
                        
                        with open(output_file, 'w') as f:
                            for item in ds:
                                # Convert to standard chat format
                                if 'messages' in item:
                                    f.write(json.dumps({"messages": item['messages']}) + '\n')
                                elif 'conversations' in item:
                                    f.write(json.dumps({"messages": item['conversations']}) + '\n')
                                elif 'instruction' in item and 'response' in item:
                                    messages = [
                                        {"role": "user", "content": item['instruction']},
                                        {"role": "assistant", "content": item['response']}
                                    ]
                                    f.write(json.dumps({"messages": messages}) + '\n')
                        
                        datasets.append({
                            "source": "huggingface",
                            "category": category,
                            "name": dataset_name,
                            "path": str(output_dir),
                            "samples": len(ds)
                        })
                        
                        logger.info(f"  ✅ Downloaded: {dataset_name}")
                        
                    except Exception as e:
                        logger.warning(f"  ⚠️  Failed to download {dataset_name}: {e}")
                        continue
                        
        except ImportError:
            logger.warning("⚠️  HuggingFace datasets not installed. Install with: pip install datasets")
        except Exception as e:
            logger.error(f"❌ Error collecting from HuggingFace: {e}")
        
        return datasets
    
    async def collect_from_sklearn(self, category: str, limit: int = 20) -> List[Dict]:
        """Collect datasets from scikit-learn"""
        logger.info(f"🔬 Collecting from scikit-learn ({category})...")
        datasets = []
        
        try:
            from sklearn import datasets as sklearn_datasets
            import pandas as pd
            
            if category == "quantum":
                # Built-in sklearn datasets
                dataset_loaders = [
                    ("iris", sklearn_datasets.load_iris),
                    ("wine", sklearn_datasets.load_wine),
                    ("breast_cancer", sklearn_datasets.load_breast_cancer),
                    ("digits", sklearn_datasets.load_digits)
                ]
                
                for name, loader in dataset_loaders:
                    try:
                        data = loader()
                        df = pd.DataFrame(data.data, columns=data.feature_names)
                        df['target'] = data.target
                        
                        filepath = self.datasets_dir / category / f"sklearn_{name}.csv"
                        df.to_csv(filepath, index=False)
                        
                        datasets.append({
                            "source": "sklearn",
                            "category": category,
                            "name": name,
                            "path": str(filepath),
                            "samples": len(df),
                            "features": len(data.feature_names)
                        })
                        
                        logger.info(f"  ✅ Created: sklearn_{name}")
                        
                    except Exception as e:
                        logger.warning(f"  ⚠️  Failed to load {name}: {e}")
                        
        except ImportError:
            logger.warning("⚠️  scikit-learn not installed")
        except Exception as e:
            logger.error(f"❌ Error collecting from sklearn: {e}")
        
        return datasets
    
    async def collect_from_kaggle(self, category: str, limit: int = 10) -> List[Dict]:
        """Collect datasets from Kaggle (requires API key)"""
        logger.info(f"🏆 Collecting from Kaggle ({category})...")
        datasets = []
        
        try:
            import kaggle
            
            # Search for datasets
            search_terms = {
                "quantum": ["classification", "small", "ml"],
                "chat": ["conversation", "chatbot", "qa"],
                "vision": ["image", "computer-vision", "cv"]
            }
            
            terms = search_terms.get(category, [])
            for term in terms[:limit]:
                try:
                    # Search datasets
                    results = kaggle.api.dataset_list(search=term, max_size=100000)[:5]
                    
                    for dataset_ref in results:
                        try:
                            dataset_name = f"{dataset_ref.ref}"
                            download_dir = self.datasets_dir / category / "kaggle" / dataset_name.replace("/", "_")
                            download_dir.mkdir(parents=True, exist_ok=True)
                            
                            kaggle.api.dataset_download_files(
                                dataset_name,
                                path=str(download_dir),
                                unzip=True
                            )
                            
                            datasets.append({
                                "source": "kaggle",
                                "category": category,
                                "name": dataset_name,
                                "path": str(download_dir)
                            })
                            
                            logger.info(f"  ✅ Downloaded: {dataset_name}")
                            
                        except Exception as e:
                            logger.warning(f"  ⚠️  Failed to download {dataset_ref.ref}: {e}")
                            continue
                            
                except Exception as e:
                    logger.warning(f"  ⚠️  Error searching for '{term}': {e}")
                    continue
                    
        except ImportError:
            logger.warning("⚠️  Kaggle not installed. Install with: pip install kaggle")
        except Exception as e:
            logger.error(f"❌ Error collecting from Kaggle: {e}")
        
        return datasets
    
    async def collect_from_uci(self, category: str, limit: int = 20) -> List[Dict]:
        """Collect datasets from UCI ML Repository"""
        logger.info(f"🎓 Collecting from UCI ML Repository ({category})...")
        datasets = []
        
        # Popular UCI datasets
        uci_datasets = {
            "quantum": [
                ("adult", "https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data"),
                ("car", "https://archive.ics.uci.edu/ml/machine-learning-databases/car/car.data"),
                ("mushroom", "https://archive.ics.uci.edu/ml/machine-learning-databases/mushroom/agaricus-lepiota.data"),
                ("abalone", "https://archive.ics.uci.edu/ml/machine-learning-databases/abalone/abalone.data"),
                ("letter", "https://archive.ics.uci.edu/ml/machine-learning-databases/letter-recognition/letter-recognition.data")
            ]
        }
        
        try:
            import requests
            import pandas as pd
            
            for name, url in uci_datasets.get(category, [])[:limit]:
                try:
                    response = requests.get(url, timeout=30)
                    if response.status_code == 200:
                        filepath = self.datasets_dir / category / f"uci_{name}.csv"
                        
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                        
                        # Validate it's readable
                        df = pd.read_csv(filepath, header=None)
                        
                        datasets.append({
                            "source": "uci",
                            "category": category,
                            "name": name,
                            "path": str(filepath),
                            "samples": len(df)
                        })
                        
                        logger.info(f"  ✅ Downloaded: {name}")
                        
                except Exception as e:
                    logger.warning(f"  ⚠️  Failed to download {name}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Error collecting from UCI: {e}")
        
        return datasets
    
    async def augment_datasets(self, datasets: List[Dict]) -> int:
        """Augment datasets with synthetic variations"""
        logger.info("🔄 Augmenting datasets...")
        augmented_count = 0
        
        try:
            import pandas as pd
            import numpy as np
            
            for dataset_info in datasets:
                if dataset_info["category"] != "quantum":
                    continue
                
                filepath = Path(dataset_info["path"])
                if not filepath.exists() or not filepath.is_file():
                    continue
                
                try:
                    df = pd.read_csv(filepath)
                    
                    # Simple augmentation: add Gaussian noise
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    
                    if len(numeric_cols) > 0:
                        aug_df = df.copy()
                        for col in numeric_cols:
                            noise = np.random.normal(0, 0.01 * df[col].std(), len(df))
                            aug_df[col] = df[col] + noise
                        
                        # Save augmented version
                        aug_filepath = filepath.parent / f"{filepath.stem}_aug.csv"
                        aug_df.to_csv(aug_filepath, index=False)
                        augmented_count += 1
                        
                except Exception as e:
                    logger.warning(f"  ⚠️  Failed to augment {filepath.name}: {e}")
                    continue
            
            logger.info(f"✅ Augmented {augmented_count} datasets")
            
        except Exception as e:
            logger.error(f"❌ Error augmenting datasets: {e}")
        
        return augmented_count
    
    async def validate_datasets(self, datasets: List[Dict]) -> Tuple[int, int]:
        """Validate dataset quality and integrity"""
        logger.info("🔍 Validating datasets...")
        valid_count = 0
        invalid_count = 0
        
        for dataset_info in datasets:
            filepath = Path(dataset_info["path"])
            
            if not filepath.exists():
                invalid_count += 1
                continue
            
            try:
                if filepath.is_file() and filepath.suffix == ".csv":
                    import pandas as pd
                    df = pd.read_csv(filepath)
                    
                    # Basic validation
                    if len(df) > 10 and len(df.columns) > 0:
                        # Check for too many missing values
                        missing_ratio = df.isnull().sum().sum() / (len(df) * len(df.columns))
                        if missing_ratio < 0.5:  # Less than 50% missing
                            valid_count += 1
                        else:
                            invalid_count += 1
                    else:
                        invalid_count += 1
                        
                elif filepath.is_dir():
                    # Check for files in directory
                    files = list(filepath.glob("*"))
                    if len(files) > 0:
                        valid_count += 1
                    else:
                        invalid_count += 1
                else:
                    valid_count += 1
                    
            except Exception as e:
                logger.warning(f"  ⚠️  Validation failed for {filepath.name}: {e}")
                invalid_count += 1
                continue
        
        logger.info(f"✅ Valid: {valid_count}, Invalid: {invalid_count}")
        return valid_count, invalid_count
    
    async def collect_all(self, sources: List[str] = None, limit_per_source: int = 20):
        """Collect datasets from all sources"""
        if sources is None:
            sources = list(self.sources.keys())
        
        logger.info("="*80)
        logger.info("🚀 Starting Comprehensive Dataset Collection")
        logger.info("="*80)
        
        all_datasets = []
        
        for source_name in sources:
            if source_name not in self.sources:
                logger.warning(f"⚠️  Unknown source: {source_name}")
                continue
            
            collector_func = self.sources[source_name]
            
            for category in self.categories:
                try:
                    datasets = await collector_func(category, limit=limit_per_source)
                    all_datasets.extend(datasets)
                    
                    self.stats["datasets_by_source"].setdefault(source_name, 0)
                    self.stats["datasets_by_source"][source_name] += len(datasets)
                    
                    self.stats["datasets_by_category"].setdefault(category, 0)
                    self.stats["datasets_by_category"][category] += len(datasets)
                    
                except Exception as e:
                    logger.error(f"❌ Error collecting from {source_name}/{category}: {e}")
                    continue
        
        self.stats["downloaded"] = len(all_datasets)
        
        # Augment datasets
        if all_datasets:
            self.stats["augmented"] = await self.augment_datasets(all_datasets)
        
        # Validate datasets
        if all_datasets:
            valid, invalid = await self.validate_datasets(all_datasets)
            self.stats["validated"] = valid
            self.stats["failed"] = invalid
        
        # Save report
        self.save_report(all_datasets)
        
        logger.info("="*80)
        logger.info("✅ Dataset Collection Complete!")
        logger.info(f"   Downloaded: {self.stats['downloaded']}")
        logger.info(f"   Augmented: {self.stats['augmented']}")
        logger.info(f"   Validated: {self.stats['validated']}")
        logger.info(f"   Failed: {self.stats['failed']}")
        logger.info("="*80)
        
        return all_datasets
    
    def save_report(self, datasets: List[Dict]):
        """Save collection report"""
        report = {
            "stats": self.stats,
            "datasets": datasets,
            "completed_at": datetime.now().isoformat()
        }
        
        report_file = self.data_out_dir / "collection_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📄 Report saved to: {report_file}")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive Dataset Collection")
    parser.add_argument("--sources", nargs="+", default=None,
                       help="Sources to collect from (openml, huggingface, kaggle, sklearn, uci)")
    parser.add_argument("--limit", type=int, default=20,
                       help="Limit per source")
    parser.add_argument("--quick", action="store_true",
                       help="Quick mode (sklearn only)")
    
    args = parser.parse_args()
    
    collector = DatasetCollector()
    
    if args.quick:
        sources = ["sklearn"]
        limit = 10
    else:
        sources = args.sources
        limit = args.limit
    
    await collector.collect_all(sources=sources, limit_per_source=limit)


if __name__ == "__main__":
    asyncio.run(main())
