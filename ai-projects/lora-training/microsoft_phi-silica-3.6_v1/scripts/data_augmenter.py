"""
Data Augmentation for Text
Techniques to augment training data for improved model generalization
"""

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class AugmentationConfig:
    """Data augmentation configuration"""

    synonym_replacement_prob: float = 0.1
    random_insertion_prob: float = 0.1
    random_swap_prob: float = 0.1
    random_deletion_prob: float = 0.1
    back_translation: bool = False
    paraphrase: bool = False
    num_augmentations_per_sample: int = 1


class TextAugmenter:
    """Text data augmentation toolkit"""

    def __init__(self, config: AugmentationConfig = None):
        self.config = config or AugmentationConfig()
        self.results_dir = Path("data_out/augmented_data")
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def augment_dataset(
        self, input_path: str, output_path: str, techniques: List[str] = None
    ) -> Dict[str, Any]:
        """
        Augment entire dataset

        Args:
            input_path: Input JSONL file
            output_path: Output JSONL file
            techniques: List of augmentation techniques to use

        Returns:
            Statistics dictionary
        """
        techniques = techniques or ["synonym", "insertion", "swap", "deletion"]

        print(f"Augmenting dataset: {input_path}")
        print(f"Techniques: {', '.join(techniques)}")

        # Load dataset
        samples = self._load_dataset(input_path)
        original_count = len(samples)

        augmented_samples = []

        for sample in samples:
            # Keep original
            augmented_samples.append(sample)

            # Generate augmentations
            text = self._extract_text(sample)

            for _ in range(self.config.num_augmentations_per_sample):
                augmented_text = self._augment_text(text, techniques)

                # Create augmented sample
                aug_sample = sample.copy()
                self._update_text(aug_sample, augmented_text)
                augmented_samples.append(aug_sample)

        # Save augmented dataset
        self._save_dataset(augmented_samples, output_path)

        stats = {
            "original_samples": original_count,
            "augmented_samples": len(augmented_samples),
            "augmentation_factor": len(augmented_samples) / original_count,
            "techniques_used": techniques,
        }

        print("\n✓ Augmentation complete")
        print(f"  Original: {original_count:,}")
        print(f"  Augmented: {len(augmented_samples):,}")
        print(f"  Factor: {stats['augmentation_factor']:.1f}x")

        return stats

    def _augment_text(self, text: str, techniques: List[str]) -> str:
        """Apply augmentation techniques to text"""
        words = text.split()

        if (
            "synonym" in techniques
            and random.random() < self.config.synonym_replacement_prob
        ):
            words = self._synonym_replacement(words)

        if (
            "insertion" in techniques
            and random.random() < self.config.random_insertion_prob
        ):
            words = self._random_insertion(words)

        if "swap" in techniques and random.random() < self.config.random_swap_prob:
            words = self._random_swap(words)

        if (
            "deletion" in techniques
            and random.random() < self.config.random_deletion_prob
        ):
            words = self._random_deletion(words)

        return " ".join(words)

    def _synonym_replacement(self, words: List[str], n: int = None) -> List[str]:
        """Replace n random words with synonyms"""
        if n is None:
            n = max(1, int(len(words) * 0.1))

        new_words = words.copy()
        random_word_indices = list(range(len(words)))
        random.shuffle(random_word_indices)

        replaced = 0
        for idx in random_word_indices:
            if replaced >= n:
                break

            # Simple synonym replacement (in practice, use WordNet or transformer-based)
            word = words[idx]
            synonym = self._get_simple_synonym(word)

            if synonym != word:
                new_words[idx] = synonym
                replaced += 1

        return new_words

    def _random_insertion(self, words: List[str], n: int = None) -> List[str]:
        """Randomly insert n words"""
        if n is None:
            n = max(1, int(len(words) * 0.1))

        new_words = words.copy()

        for _ in range(n):
            if not new_words:
                break

            # Insert a random word from the text
            random_word = random.choice(words)
            random_idx = random.randint(0, len(new_words))
            new_words.insert(random_idx, random_word)

        return new_words

    def _random_swap(self, words: List[str], n: int = None) -> List[str]:
        """Randomly swap n pairs of words"""
        if n is None:
            n = max(1, int(len(words) * 0.1))

        new_words = words.copy()

        for _ in range(n):
            if len(new_words) < 2:
                break

            idx1, idx2 = random.sample(range(len(new_words)), 2)
            new_words[idx1], new_words[idx2] = new_words[idx2], new_words[idx1]

        return new_words

    def _random_deletion(self, words: List[str], p: float = None) -> List[str]:
        """Randomly delete words with probability p"""
        if p is None:
            p = self.config.random_deletion_prob

        # Don't delete all words
        if len(words) == 1:
            return words

        new_words = []
        for word in words:
            if random.random() > p:
                new_words.append(word)

        # Return original if all deleted
        return new_words if new_words else words

    def _get_simple_synonym(self, word: str) -> str:
        """Get simple synonym (basic implementation)"""
        # Simple synonym dictionary (in production, use WordNet or BERT)
        synonyms = {
            "good": ["great", "excellent", "fine", "nice"],
            "bad": ["poor", "terrible", "awful", "horrible"],
            "big": ["large", "huge", "enormous", "massive"],
            "small": ["tiny", "little", "mini", "compact"],
            "fast": ["quick", "rapid", "swift", "speedy"],
            "slow": ["sluggish", "gradual", "leisurely"],
            "happy": ["joyful", "cheerful", "pleased", "content"],
            "sad": ["unhappy", "sorrowful", "depressed", "melancholy"],
        }

        lower_word = word.lower()
        if lower_word in synonyms:
            synonym = random.choice(synonyms[lower_word])
            # Preserve capitalization
            if word[0].isupper():
                synonym = synonym.capitalize()
            return synonym

        return word

    def _load_dataset(self, path: str) -> List[Dict[str, Any]]:
        """Load dataset from JSONL"""
        samples = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    samples.append(json.loads(line))
        return samples

    def _save_dataset(self, samples: List[Dict[str, Any]], path: str):
        """Save dataset to JSONL"""
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            for sample in samples:
                f.write(json.dumps(sample, ensure_ascii=False) + "\n")

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

    def _update_text(self, sample: Dict[str, Any], new_text: str):
        """Update text in sample"""
        if "text" in sample:
            sample["text"] = new_text
        elif "instruction" in sample:
            # Split back into instruction and response (approximate)
            parts = new_text.split("\n instruction", 1)
            if len(parts) == 2:
                sample["instruction"] = parts[0].strip()
                sample["response"] = parts[1].strip()
            else:
                sample["instruction"] = new_text
        # Messages format is more complex, skip for now


def main():
    """CLI for data augmentation"""
    import argparse

    parser = argparse.ArgumentParser(description="Text Data Augmentation")
    parser.add_argument(
        "--input", type=str, required=True, help="Input dataset (JSONL)"
    )
    parser.add_argument(
        "--output", type=str, required=True, help="Output dataset (JSONL)"
    )
    parser.add_argument(
        "--techniques",
        nargs="+",
        default=["synonym", "insertion", "swap", "deletion"],
        help="Augmentation techniques",
    )
    parser.add_argument(
        "--num-aug", type=int, default=1, help="Number of augmentations per sample"
    )
    parser.add_argument(
        "--prob", type=float, default=0.1, help="Probability for each technique"
    )

    args = parser.parse_args()

    config = AugmentationConfig(
        synonym_replacement_prob=args.prob,
        random_insertion_prob=args.prob,
        random_swap_prob=args.prob,
        random_deletion_prob=args.prob,
        num_augmentations_per_sample=args.num_aug,
    )

    augmenter = TextAugmenter(config)
    stats = augmenter.augment_dataset(
        args.input, args.output, techniques=args.techniques
    )

    print(f"\n✓ Augmented dataset saved to {args.output}")


if __name__ == "__main__":
    main()
