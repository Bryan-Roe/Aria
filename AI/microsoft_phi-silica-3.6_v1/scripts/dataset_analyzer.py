"""
Dataset Analyzer & Health Check
Provides comprehensive analysis of training datasets
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from collections import Counter, defaultdict
import numpy as np
from dataclasses import dataclass, asdict
import matplotlib.pyplot as plt
import seaborn as sns


@dataclass
class DatasetStatistics:
    """Container for dataset statistics"""
    total_samples: int
    total_tokens: int
    avg_tokens_per_sample: float
    median_tokens_per_sample: float
    std_tokens_per_sample: float
    min_tokens: int
    max_tokens: int
    
    # Content analysis
    unique_samples: int
    duplicate_rate: float
    avg_unique_tokens_per_sample: float
    vocabulary_size: int
    
    # Quality metrics
    avg_quality_score: float
    low_quality_count: int
    low_quality_rate: float
    
    # Distribution
    token_distribution: Dict[str, int]
    length_percentiles: Dict[str, int]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def print_summary(self):
        """Print human-readable summary"""
        print("\n" + "="*60)
        print("DATASET ANALYSIS SUMMARY")
        print("="*60)
        
        print(f"\n📊 Basic Statistics:")
        print(f"  Total samples: {self.total_samples:,}")
        print(f"  Total tokens: {self.total_tokens:,}")
        print(f"  Avg tokens/sample: {self.avg_tokens_per_sample:.1f}")
        print(f"  Median tokens/sample: {self.median_tokens_per_sample:.1f}")
        print(f"  Std dev: {self.std_tokens_per_sample:.1f}")
        print(f"  Min tokens: {self.min_tokens}")
        print(f"  Max tokens: {self.max_tokens}")
        
        print(f"\n🔍 Content Analysis:")
        print(f"  Unique samples: {self.unique_samples:,}")
        print(f"  Duplicate rate: {self.duplicate_rate:.2%}")
        print(f"  Vocabulary size: {self.vocabulary_size:,}")
        print(f"  Avg unique tokens/sample: {self.avg_unique_tokens_per_sample:.1f}")
        
        print(f"\n✨ Quality Metrics:")
        print(f"  Avg quality score: {self.avg_quality_score:.3f}")
        print(f"  Low quality samples: {self.low_quality_count:,} ({self.low_quality_rate:.2%})")
        
        print(f"\n📈 Length Distribution (percentiles):")
        for pct, value in sorted(self.length_percentiles.items()):
            print(f"  {pct}: {value} tokens")


class DatasetAnalyzer:
    """Comprehensive dataset analysis tool"""
    
    def __init__(self):
        self.results_dir = Path("data_out/dataset_analysis")
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def analyze(
        self,
        dataset_path: str,
        create_visualizations: bool = True,
        quality_threshold: float = 0.3
    ) -> DatasetStatistics:
        """
        Perform comprehensive dataset analysis
        
        Args:
            dataset_path: Path to JSONL dataset
            create_visualizations: Whether to create plots
            quality_threshold: Threshold for low quality samples
            
        Returns:
            DatasetStatistics object
        """
        print(f"Analyzing dataset: {dataset_path}")
        
        # Load dataset
        samples = self._load_dataset(dataset_path)
        
        # Extract texts and compute token counts
        texts = [self._extract_text(s) for s in samples]
        token_counts = [len(text.split()) for text in texts]
        
        # Basic statistics
        total_samples = len(samples)
        total_tokens = sum(token_counts)
        avg_tokens = np.mean(token_counts)
        median_tokens = np.median(token_counts)
        std_tokens = np.std(token_counts)
        min_tokens = min(token_counts)
        max_tokens = max(token_counts)
        
        # Content analysis
        unique_samples = len(set(texts))
        duplicate_rate = (total_samples - unique_samples) / total_samples
        
        # Vocabulary analysis
        all_tokens = []
        unique_tokens_per_sample = []
        for text in texts:
            tokens = text.lower().split()
            all_tokens.extend(tokens)
            unique_tokens_per_sample.append(len(set(tokens)))
        
        vocabulary = set(all_tokens)
        vocabulary_size = len(vocabulary)
        avg_unique_tokens = np.mean(unique_tokens_per_sample)
        
        # Quality analysis
        quality_scores = [self._compute_quality_score(text) for text in texts]
        avg_quality = np.mean(quality_scores)
        low_quality_count = sum(1 for q in quality_scores if q < quality_threshold)
        low_quality_rate = low_quality_count / total_samples
        
        # Distribution analysis
        token_distribution = self._compute_distribution(token_counts)
        length_percentiles = {
            "10th": int(np.percentile(token_counts, 10)),
            "25th": int(np.percentile(token_counts, 25)),
            "50th": int(np.percentile(token_counts, 50)),
            "75th": int(np.percentile(token_counts, 75)),
            "90th": int(np.percentile(token_counts, 90)),
            "95th": int(np.percentile(token_counts, 95)),
            "99th": int(np.percentile(token_counts, 99))
        }
        
        # Create statistics object
        stats = DatasetStatistics(
            total_samples=total_samples,
            total_tokens=total_tokens,
            avg_tokens_per_sample=avg_tokens,
            median_tokens_per_sample=median_tokens,
            std_tokens_per_sample=std_tokens,
            min_tokens=min_tokens,
            max_tokens=max_tokens,
            unique_samples=unique_samples,
            duplicate_rate=duplicate_rate,
            avg_unique_tokens_per_sample=avg_unique_tokens,
            vocabulary_size=vocabulary_size,
            avg_quality_score=avg_quality,
            low_quality_count=low_quality_count,
            low_quality_rate=low_quality_rate,
            token_distribution=token_distribution,
            length_percentiles=length_percentiles
        )
        
        # Create visualizations
        if create_visualizations:
            self._create_visualizations(
                token_counts,
                quality_scores,
                Path(dataset_path).stem
            )
        
        # Save results
        self._save_results(stats, Path(dataset_path).stem)
        
        return stats
    
    def _load_dataset(self, path: str) -> List[Dict[str, Any]]:
        """Load dataset from JSONL"""
        samples = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    samples.append(json.loads(line))
        return samples
    
    def _extract_text(self, sample: Dict[str, Any]) -> str:
        """Extract text from sample"""
        if "messages" in sample:
            return " ".join([m.get("content", "") for m in sample["messages"]])
        elif "text" in sample:
            return sample["text"]
        elif "instruction" in sample:
            return f"{sample['instruction']} {sample.get('response', '')}"
        else:
            return json.dumps(sample)
    
    def _compute_quality_score(self, text: str) -> float:
        """Compute quality score for text"""
        scores = []
        
        # Length score
        word_count = len(text.split())
        length_score = min(word_count / 100, 1.0)
        scores.append(length_score)
        
        # Character diversity
        unique_chars = len(set(text.lower()))
        char_diversity = min(unique_chars / 26, 1.0)
        scores.append(char_diversity)
        
        # Word diversity
        words = text.lower().split()
        if words:
            unique_words = len(set(words))
            word_diversity = unique_words / len(words)
            scores.append(word_diversity)
        
        # Punctuation
        punct_count = sum(1 for c in text if c in '.,!?;:')
        punct_score = min(punct_count / 10, 1.0)
        scores.append(punct_score)
        
        return np.mean(scores) if scores else 0.0
    
    def _compute_distribution(self, token_counts: List[int]) -> Dict[str, int]:
        """Compute token count distribution"""
        bins = [0, 50, 100, 200, 500, 1000, 2000, float('inf')]
        labels = ["0-50", "51-100", "101-200", "201-500", "501-1000", "1001-2000", "2000+"]
        
        distribution = defaultdict(int)
        for count in token_counts:
            for i, (low, high) in enumerate(zip(bins[:-1], bins[1:])):
                if low < count <= high:
                    distribution[labels[i]] += 1
                    break
        
        return dict(distribution)
    
    def _create_visualizations(
        self,
        token_counts: List[int],
        quality_scores: List[float],
        dataset_name: str
    ):
        """Create visualization plots"""
        try:
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            
            # Token length distribution (histogram)
            axes[0, 0].hist(token_counts, bins=50, edgecolor='black', alpha=0.7)
            axes[0, 0].set_xlabel('Token Count')
            axes[0, 0].set_ylabel('Frequency')
            axes[0, 0].set_title('Token Length Distribution')
            axes[0, 0].axvline(np.median(token_counts), color='r', linestyle='--', label='Median')
            axes[0, 0].legend()
            
            # Token length box plot
            axes[0, 1].boxplot(token_counts, vert=True)
            axes[0, 1].set_ylabel('Token Count')
            axes[0, 1].set_title('Token Length Box Plot')
            axes[0, 1].grid(True, alpha=0.3)
            
            # Quality score distribution
            axes[1, 0].hist(quality_scores, bins=30, edgecolor='black', alpha=0.7, color='green')
            axes[1, 0].set_xlabel('Quality Score')
            axes[1, 0].set_ylabel('Frequency')
            axes[1, 0].set_title('Quality Score Distribution')
            axes[1, 0].axvline(np.mean(quality_scores), color='r', linestyle='--', label='Mean')
            axes[1, 0].legend()
            
            # Length vs Quality scatter
            sample_indices = np.random.choice(len(token_counts), min(1000, len(token_counts)), replace=False)
            sampled_counts = [token_counts[i] for i in sample_indices]
            sampled_quality = [quality_scores[i] for i in sample_indices]
            axes[1, 1].scatter(sampled_counts, sampled_quality, alpha=0.5)
            axes[1, 1].set_xlabel('Token Count')
            axes[1, 1].set_ylabel('Quality Score')
            axes[1, 1].set_title('Length vs Quality')
            axes[1, 1].grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save plot
            plot_path = self.results_dir / f"{dataset_name}_analysis.png"
            plt.savefig(plot_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"✓ Visualizations saved to {plot_path}")
            
        except ImportError:
            print("⚠ matplotlib not available, skipping visualizations")
        except Exception as e:
            print(f"⚠ Error creating visualizations: {e}")
    
    def _save_results(self, stats: DatasetStatistics, dataset_name: str):
        """Save analysis results"""
        output_file = self.results_dir / f"{dataset_name}_stats.json"
        
        with open(output_file, 'w') as f:
            json.dump(stats.to_dict(), f, indent=2)
        
        print(f"✓ Statistics saved to {output_file}")
    
    def compare_datasets(
        self,
        dataset_paths: List[str]
    ) -> Dict[str, DatasetStatistics]:
        """Compare multiple datasets"""
        results = {}
        
        for path in dataset_paths:
            dataset_name = Path(path).stem
            print(f"\n{'='*60}")
            print(f"Analyzing: {dataset_name}")
            print(f"{'='*60}")
            
            stats = self.analyze(path, create_visualizations=False)
            results[dataset_name] = stats
            stats.print_summary()
        
        # Create comparison visualization
        self._create_comparison_plot(results)
        
        return results
    
    def _create_comparison_plot(self, results: Dict[str, DatasetStatistics]):
        """Create comparison visualization"""
        try:
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            
            datasets = list(results.keys())
            
            # Compare avg tokens
            avg_tokens = [results[d].avg_tokens_per_sample for d in datasets]
            axes[0, 0].bar(datasets, avg_tokens)
            axes[0, 0].set_ylabel('Avg Tokens/Sample')
            axes[0, 0].set_title('Average Token Count Comparison')
            axes[0, 0].tick_params(axis='x', rotation=45)
            
            # Compare quality scores
            avg_quality = [results[d].avg_quality_score for d in datasets]
            axes[0, 1].bar(datasets, avg_quality, color='green')
            axes[0, 1].set_ylabel('Avg Quality Score')
            axes[0, 1].set_title('Average Quality Comparison')
            axes[0, 1].tick_params(axis='x', rotation=45)
            
            # Compare duplicate rates
            dup_rates = [results[d].duplicate_rate * 100 for d in datasets]
            axes[1, 0].bar(datasets, dup_rates, color='orange')
            axes[1, 0].set_ylabel('Duplicate Rate (%)')
            axes[1, 0].set_title('Duplicate Rate Comparison')
            axes[1, 0].tick_params(axis='x', rotation=45)
            
            # Compare vocabulary sizes
            vocab_sizes = [results[d].vocabulary_size for d in datasets]
            axes[1, 1].bar(datasets, vocab_sizes, color='purple')
            axes[1, 1].set_ylabel('Vocabulary Size')
            axes[1, 1].set_title('Vocabulary Size Comparison')
            axes[1, 1].tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            
            plot_path = self.results_dir / "dataset_comparison.png"
            plt.savefig(plot_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"\n✓ Comparison plot saved to {plot_path}")
            
        except Exception as e:
            print(f"⚠ Error creating comparison plot: {e}")


def main():
    """CLI for dataset analysis"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Dataset Analysis & Health Check")
    parser.add_argument("--dataset", type=str, help="Path to dataset (JSONL)")
    parser.add_argument("--compare", nargs="+", help="Compare multiple datasets")
    parser.add_argument("--no-visualizations", action="store_true",
                        help="Skip creating visualizations")
    parser.add_argument("--quality-threshold", type=float, default=0.3,
                        help="Quality threshold for flagging samples")
    
    args = parser.parse_args()
    
    analyzer = DatasetAnalyzer()
    
    if args.compare:
        results = analyzer.compare_datasets(args.compare)
    elif args.dataset:
        stats = analyzer.analyze(
            args.dataset,
            create_visualizations=not args.no_visualizations,
            quality_threshold=args.quality_threshold
        )
        stats.print_summary()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
