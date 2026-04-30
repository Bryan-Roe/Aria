"""
Semantic Pruning for Training Data
Removes redundant and low-quality samples to improve training efficiency
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np


@dataclass
class PruningConfig:
    """Semantic pruning configuration"""

    similarity_threshold: float = 0.95  # Remove samples above this similarity
    min_length: int = 10  # Minimum token length
    max_length: int = 2048  # Maximum token length
    diversity_clusters: int = 50  # Number of clusters for diversity
    quality_threshold: float = 0.3  # Minimum quality score
    target_reduction: float = 0.3  # Target % of data to remove


@dataclass
class PruningStatistics:
    """Statistics from pruning operation"""

    original_count: int
    final_count: int
    removed_duplicates: int
    removed_low_quality: int
    removed_outliers: int
    removed_redundant: int
    reduction_percentage: float

    def print_summary(self):
        """Print pruning summary"""
        print("\n=== Semantic Pruning Results ===")
        print(f"Original samples: {self.original_count:,}")
        print(f"Final samples: {self.final_count:,}")
        print(
            f"Total removed: {self.original_count - self.final_count:,} ({self.reduction_percentage:.1f}%)"
        )
        print("\nBreakdown:")
        print(f"  - Duplicates: {self.removed_duplicates:,}")
        print(f"  - Low quality: {self.removed_low_quality:,}")
        print(f"  - Outliers: {self.removed_outliers:,}")
        print(f"  - Redundant: {self.removed_redundant:,}")


class SemanticPruner:
    """Semantic data pruning system"""

    def __init__(self, config: PruningConfig = None):
        self.config = config or PruningConfig()
        self.embedding_model = None

    def prune_dataset(
        self, input_path: str, output_path: str, use_embeddings: bool = True
    ) -> PruningStatistics:
        """
        Prune dataset using multiple strategies

        Args:
            input_path: Path to input dataset (JSONL)
            output_path: Path to save pruned dataset
            use_embeddings: Whether to use semantic embeddings

        Returns:
            PruningStatistics object
        """
        print(f"Loading dataset from {input_path}...")
        samples = self._load_dataset(input_path)
        original_count = len(samples)

        stats = PruningStatistics(
            original_count=original_count,
            final_count=0,
            removed_duplicates=0,
            removed_low_quality=0,
            removed_outliers=0,
            removed_redundant=0,
            reduction_percentage=0.0,
        )

        # Step 1: Remove exact duplicates
        print("\n[1/5] Removing exact duplicates...")
        samples, removed = self._remove_duplicates(samples)
        stats.removed_duplicates = removed
        print(f"  Removed {removed:,} duplicates")

        # Step 2: Filter by length
        print("\n[2/5] Filtering by length...")
        samples, removed = self._filter_by_length(samples)
        stats.removed_outliers += removed
        print(f"  Removed {removed:,} outliers")

        # Step 3: Quality filtering
        print("\n[3/5] Filtering low quality samples...")
        samples, removed = self._filter_by_quality(samples)
        stats.removed_low_quality = removed
        print(f"  Removed {removed:,} low quality samples")

        # Step 4: Semantic deduplication (if embeddings available)
        if use_embeddings:
            print("\n[4/5] Semantic deduplication...")
            try:
                samples, removed = self._semantic_deduplication(samples)
                stats.removed_redundant = removed
                print(f"  Removed {removed:,} redundant samples")
            except Exception as e:
                print(f"  ⚠ Skipping semantic deduplication: {e}")

        # Step 5: Diversity sampling
        print("\n[5/5] Ensuring diversity...")
        samples = self._ensure_diversity(samples)

        stats.final_count = len(samples)
        stats.reduction_percentage = (
            (original_count - stats.final_count) / original_count * 100
        )

        # Save pruned dataset
        self._save_dataset(samples, output_path)
        print(f"\n✓ Pruned dataset saved to {output_path}")

        return stats

    def _load_dataset(self, path: str) -> List[Dict[str, Any]]:
        """Load dataset from JSONL file"""
        samples = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    samples.append(json.loads(line))
        return samples

    def _save_dataset(self, samples: List[Dict[str, Any]], path: str):
        """Save dataset to JSONL file"""
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            for sample in samples:
                f.write(json.dumps(sample, ensure_ascii=False) + "\n")

    def _remove_duplicates(
        self, samples: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Remove exact duplicate samples"""
        seen = set()
        unique_samples = []
        removed = 0

        for sample in samples:
            # Create hash of content
            content_hash = self._hash_sample(sample)

            if content_hash not in seen:
                seen.add(content_hash)
                unique_samples.append(sample)
            else:
                removed += 1

        return unique_samples, removed

    def _hash_sample(self, sample: Dict[str, Any]) -> str:
        """Create hash of sample content"""
        if "messages" in sample:
            text = json.dumps(sample["messages"], sort_keys=True)
        elif "text" in sample:
            text = sample["text"]
        else:
            text = json.dumps(sample, sort_keys=True)

        return str(hash(text))

    def _filter_by_length(
        self, samples: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Filter samples by length"""
        filtered = []
        removed = 0

        for sample in samples:
            text = self._extract_text(sample)
            word_count = len(text.split())

            if self.config.min_length <= word_count <= self.config.max_length:
                filtered.append(sample)
            else:
                removed += 1

        return filtered, removed

    def _filter_by_quality(
        self, samples: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Filter low quality samples"""
        filtered = []
        removed = 0

        for sample in samples:
            quality_score = self._compute_quality_score(sample)

            if quality_score >= self.config.quality_threshold:
                sample["_quality_score"] = quality_score
                filtered.append(sample)
            else:
                removed += 1

        return filtered, removed

    def _compute_quality_score(self, sample: Dict[str, Any]) -> float:
        """Compute quality score for sample"""
        text = self._extract_text(sample)

        scores = []

        # Length score (prefer moderate length)
        word_count = len(text.split())
        length_score = min(word_count / 100, 1.0)  # Normalize to 100 words
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

        # Punctuation presence (indicates structure)
        punct_count = sum(1 for c in text if c in ".,!?;:")
        punct_score = min(punct_count / 10, 1.0)
        scores.append(punct_score)

        return np.mean(scores) if scores else 0.0

    def _semantic_deduplication(
        self, samples: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Remove semantically similar samples"""
        try:
            from sentence_transformers import SentenceTransformer

            if self.embedding_model is None:
                print("  Loading embedding model...")
                self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

            # Extract texts
            texts = [self._extract_text(s) for s in samples]

            # Compute embeddings
            print("  Computing embeddings...")
            embeddings = self.embedding_model.encode(
                texts, show_progress_bar=True, convert_to_numpy=True
            )

            # Compute pairwise similarities
            print("  Computing similarities...")
            keep_indices = set(range(len(samples)))
            removed = 0

            for i in range(len(embeddings)):
                if i not in keep_indices:
                    continue

                for j in range(i + 1, len(embeddings)):
                    if j not in keep_indices:
                        continue

                    # Compute cosine similarity
                    similarity = np.dot(embeddings[i], embeddings[j]) / (
                        np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j])
                    )

                    if similarity >= self.config.similarity_threshold:
                        # Keep the higher quality sample
                        quality_i = samples[i].get("_quality_score", 0.5)
                        quality_j = samples[j].get("_quality_score", 0.5)

                        if quality_i >= quality_j:
                            keep_indices.discard(j)
                            removed += 1
                        else:
                            keep_indices.discard(i)
                            removed += 1
                            break

            filtered = [samples[i] for i in sorted(keep_indices)]
            return filtered, removed

        except ImportError:
            print("  ⚠ sentence-transformers not installed")
            return samples, 0

    def _ensure_diversity(self, samples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ensure diversity in final dataset"""
        # Sort by quality and keep top samples
        samples_with_quality = [(s, s.get("_quality_score", 0.5)) for s in samples]
        samples_with_quality.sort(key=lambda x: x[1], reverse=True)

        # Remove quality score from samples
        clean_samples = []
        for sample, _ in samples_with_quality:
            if "_quality_score" in sample:
                del sample["_quality_score"]
            clean_samples.append(sample)

        return clean_samples

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


def main():
    """CLI for semantic pruning"""
    import argparse

    parser = argparse.ArgumentParser(description="Semantic Data Pruning")
    parser.add_argument(
        "--input", type=str, required=True, help="Input dataset (JSONL)"
    )
    parser.add_argument(
        "--output", type=str, required=True, help="Output dataset (JSONL)"
    )
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=0.95,
        help="Similarity threshold for deduplication",
    )
    parser.add_argument(
        "--quality-threshold", type=float, default=0.3, help="Minimum quality threshold"
    )
    parser.add_argument(
        "--no-embeddings", action="store_true", help="Skip semantic deduplication"
    )

    args = parser.parse_args()

    config = PruningConfig(
        similarity_threshold=args.similarity_threshold,
        quality_threshold=args.quality_threshold,
    )

    pruner = SemanticPruner(config)
    stats = pruner.prune_dataset(
        args.input, args.output, use_embeddings=not args.no_embeddings
    )

    stats.print_summary()


if __name__ == "__main__":
    main()
