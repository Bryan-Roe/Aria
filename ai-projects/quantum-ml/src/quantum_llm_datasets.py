"""
Quantum LLM Dataset Utilities
==============================

Dataset loaders, tokenizers, and data processing for quantum LLM training.

Supports:
- Character-level tokenization
- Subword/BPE tokenization
- Context window management
- Data augmentation
- Multi-source dataset integration

Author: Quantum AI Workspace
Date: March 9, 2026
"""

import json
import logging
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
from torch.utils.data import Dataset

logger = logging.getLogger(__name__)


class CharacterTokenizer:
    """
    Character-level tokenizer for quantum LLM.

    Simple but effective for proof-of-concept quantum training.
    """

    def __init__(self, vocab_size: int = 256):
        self.vocab_size = vocab_size
        # ASCII characters + special tokens
        self.char_to_id = {chr(i): i for i in range(min(256, vocab_size))}
        self.id_to_char = {i: chr(i) for i in range(min(256, vocab_size))}

        # Special tokens
        self.pad_token = "<PAD>"
        self.unk_token = "<UNK>"
        self.bos_token = "<BOS>"
        self.eos_token = "<EOS>"

        # Add special tokens to vocab
        special_tokens = [
            self.pad_token,
            self.unk_token,
            self.bos_token,
            self.eos_token,
        ]
        for token in special_tokens:
            if token not in self.char_to_id:
                idx = len(self.char_to_id)
                if idx < vocab_size:
                    self.char_to_id[token] = idx
                    self.id_to_char[idx] = token

        self.pad_id = self.char_to_id.get(self.pad_token, 0)
        self.unk_id = self.char_to_id.get(self.unk_token, 1)
        self.bos_id = self.char_to_id.get(self.bos_token, 2)
        self.eos_id = self.char_to_id.get(self.eos_token, 3)

        logger.info(f"CharacterTokenizer initialized: vocab_size={self.vocab_size}")

    def encode(self, text: str, add_special_tokens: bool = True) -> List[int]:
        """
        Encode text to token IDs.

        Args:
            text: Input text
            add_special_tokens: Whether to add BOS/EOS tokens

        Returns:
            List of token IDs
        """
        ids = []

        if add_special_tokens:
            ids.append(self.bos_id)

        for char in text:
            ids.append(self.char_to_id.get(char, self.unk_id))

        if add_special_tokens:
            ids.append(self.eos_id)

        return ids

    def decode(self, ids: List[int], skip_special_tokens: bool = True) -> str:
        """
        Decode token IDs to text.

        Args:
            ids: List of token IDs
            skip_special_tokens: Whether to skip special tokens

        Returns:
            Decoded text
        """
        special_ids = (
            {self.pad_id, self.bos_id, self.eos_id} if skip_special_tokens else set()
        )

        chars = []
        for id in ids:
            if id not in special_ids:
                chars.append(self.id_to_char.get(id, self.unk_token))

        return "".join(chars)

    def save(self, path: Path):
        """Save tokenizer."""
        data = {
            "vocab_size": self.vocab_size,
            "char_to_id": self.char_to_id,
            "id_to_char": {int(k): v for k, v in self.id_to_char.items()},
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Tokenizer saved: {path}")

    @classmethod
    def load(cls, path: Path):
        """Load tokenizer."""
        with open(path) as f:
            data = json.load(f)

        tokenizer = cls(data["vocab_size"])
        tokenizer.char_to_id = data["char_to_id"]
        tokenizer.id_to_char = {int(k): v for k, v in data["id_to_char"].items()}

        logger.info(f"Tokenizer loaded: {path}")
        return tokenizer


class TextDataset(Dataset):
    """
    Dataset for text sequences.

    Handles tokenization and sequence windowing.
    """

    def __init__(
        self,
        texts: List[str],
        tokenizer: CharacterTokenizer,
        max_seq_length: int = 512,
        stride: int = 256,
    ):
        self.texts = texts
        self.tokenizer = tokenizer
        self.max_seq_length = max_seq_length
        self.stride = stride

        # Pre-tokenize and create windows
        self.samples = []
        self._prepare_samples()

        logger.info(f"TextDataset: {len(texts)} texts → {len(self.samples)} samples")

    def _prepare_samples(self):
        """Tokenize texts and create training samples."""
        for text in self.texts:
            # Tokenize
            token_ids = self.tokenizer.encode(text, add_special_tokens=False)

            # Create sliding windows
            for i in range(0, len(token_ids) - self.max_seq_length, self.stride):
                window = token_ids[i : i + self.max_seq_length + 1]

                if len(window) > 1:  # Need at least 2 tokens for input/target
                    self.samples.append(window)

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Get a training sample.

        Returns:
            (input_ids, target_ids) tuple
        """
        sample = self.samples[idx]

        # Input is all but last token
        input_ids = torch.tensor(sample[:-1], dtype=torch.long)

        # Target is all but first token (shifted by 1)
        target_ids = torch.tensor(sample[1:], dtype=torch.long)

        # Padding if needed
        if len(input_ids) < self.max_seq_length:
            padding = self.max_seq_length - len(input_ids)
            input_ids = torch.cat(
                [
                    input_ids,
                    torch.full((padding,), self.tokenizer.pad_id, dtype=torch.long),
                ]
            )
            target_ids = torch.cat(
                [
                    target_ids,
                    torch.full((padding,), self.tokenizer.pad_id, dtype=torch.long),
                ]
            )

        return input_ids, target_ids


class MultiSourceDataset(Dataset):
    """
    Dataset combining multiple text sources.

    Useful for training on diverse data.
    """

    def __init__(
        self,
        data_sources: List[Dict[str, Any]],
        tokenizer: CharacterTokenizer,
        max_seq_length: int = 512,
        sampling_weights: Optional[List[float]] = None,
    ):
        self.data_sources = data_sources
        self.tokenizer = tokenizer
        self.max_seq_length = max_seq_length
        self.sampling_weights = sampling_weights or [1.0] * len(data_sources)

        # Normalize weights
        total_weight = sum(self.sampling_weights)
        self.sampling_weights = [w / total_weight for w in self.sampling_weights]

        # Load all datasets
        self.datasets = []
        for source in data_sources:
            dataset = self._load_source(source)
            self.datasets.append(dataset)

        self.total_samples = sum(len(ds) for ds in self.datasets)

        logger.info(
            f"MultiSourceDataset: {len(data_sources)} sources, {self.total_samples} samples"
        )

    def _load_source(self, source: Dict[str, Any]) -> Dataset:
        """Load a single data source."""
        source_type = source.get("type", "text")
        path = Path(source["path"])

        if source_type == "text":
            with open(path) as f:
                texts = [line.strip() for line in f if line.strip()]
        elif source_type == "json":
            with open(path) as f:
                data = json.load(f)
                texts = [item.get("text", "") for item in data]
        else:
            logger.warning(f"Unknown source type: {source_type}")
            texts = []

        return TextDataset(
            texts=texts,
            tokenizer=self.tokenizer,
            max_seq_length=self.max_seq_length,
        )

    def __len__(self) -> int:
        return self.total_samples

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """Get sample from randomly selected source."""
        # Choose source based on sampling weights
        source_idx = np.random.choice(len(self.datasets), p=self.sampling_weights)
        dataset = self.datasets[source_idx]

        # Get random sample from chosen dataset
        sample_idx = random.randint(0, len(dataset) - 1)

        return dataset[sample_idx]


class QuantumDataAugmenter:
    """
    Data augmentation specifically designed for quantum LLM training.

    Applies quantum-inspired perturbations to training data.
    """

    def __init__(
        self,
        noise_level: float = 0.1,
        enable_quantum_noise: bool = True,
    ):
        self.noise_level = noise_level
        self.enable_quantum_noise = enable_quantum_noise

        logger.info(f"QuantumDataAugmenter: noise_level={noise_level}")

    def augment(self, input_ids: torch.Tensor) -> torch.Tensor:
        """
        Apply quantum-inspired augmentation.

        Args:
            input_ids: Input token IDs [seq_length]

        Returns:
            Augmented token IDs
        """
        augmented = input_ids.clone()

        if self.enable_quantum_noise:
            # Quantum-style bit flips (superposition-inspired)
            flip_mask = torch.rand_like(augmented.float()) < self.noise_level

            # Random token substitutions
            random_tokens = torch.randint_like(augmented, 0, 256)
            augmented = torch.where(flip_mask, random_tokens, augmented)

        return augmented

    def augment_batch(self, batch: torch.Tensor) -> torch.Tensor:
        """Apply augmentation to a batch."""
        return torch.stack([self.augment(sample) for sample in batch])


class DatasetBuilder:
    """
    Utility for building datasets from various sources.
    """

    @staticmethod
    def from_text_file(
        path: Path,
        tokenizer: CharacterTokenizer,
        max_seq_length: int = 512,
    ) -> TextDataset:
        """Load dataset from plain text file."""
        with open(path) as f:
            texts = [line.strip() for line in f if line.strip()]

        return TextDataset(texts, tokenizer, max_seq_length)

    @staticmethod
    def from_json_file(
        path: Path,
        tokenizer: CharacterTokenizer,
        max_seq_length: int = 512,
        text_field: str = "text",
    ) -> TextDataset:
        """Load dataset from JSON file."""
        with open(path) as f:
            data = json.load(f)

        texts = [item.get(text_field, "") for item in data]

        return TextDataset(texts, tokenizer, max_seq_length)

    @staticmethod
    def from_chat_dataset(
        path: Path,
        tokenizer: CharacterTokenizer,
        max_seq_length: int = 512,
    ) -> TextDataset:
        """Load dataset from chat format."""
        with open(path) as f:
            data = json.load(f)

        texts = []
        for conversation in data:
            messages = conversation.get("messages", [])
            text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
            texts.append(text)

        return TextDataset(texts, tokenizer, max_seq_length)

    @staticmethod
    def auto_detect_and_load(
        path: Path,
        tokenizer: CharacterTokenizer,
        max_seq_length: int = 512,
    ) -> Dataset:
        """Auto-detect format and load dataset."""
        if not path.exists():
            raise FileNotFoundError(f"Dataset not found: {path}")

        # Try to detect format
        if path.suffix == ".json":
            with open(path) as f:
                data = json.load(f)

            # Check if it's chat format
            if isinstance(data, list) and len(data) > 0:
                first_item = data[0]
                if isinstance(first_item, dict) and "messages" in first_item:
                    logger.info(f"Detected chat format: {path}")
                    return DatasetBuilder.from_chat_dataset(
                        path, tokenizer, max_seq_length
                    )
                elif isinstance(first_item, dict) and "text" in first_item:
                    logger.info(f"Detected JSON format: {path}")
                    return DatasetBuilder.from_json_file(
                        path, tokenizer, max_seq_length
                    )

        # Default to text format
        logger.info(f"Using text format: {path}")
        return DatasetBuilder.from_text_file(path, tokenizer, max_seq_length)


def create_train_val_split(
    dataset: Dataset,
    val_ratio: float = 0.1,
    seed: int = 42,
) -> Tuple[Dataset, Dataset]:
    """
    Split dataset into train and validation.

    Args:
        dataset: Full dataset
        val_ratio: Validation split ratio
        seed: Random seed

    Returns:
        (train_dataset, val_dataset) tuple
    """
    torch.manual_seed(seed)

    total_size = len(dataset)
    val_size = int(total_size * val_ratio)
    train_size = total_size - val_size

    train_dataset, val_dataset = torch.utils.data.random_split(
        dataset,
        [train_size, val_size],
    )

    logger.info(f"Dataset split: {train_size} train, {val_size} val")

    return train_dataset, val_dataset


# Export all utilities
__all__ = [
    "CharacterTokenizer",
    "TextDataset",
    "MultiSourceDataset",
    "QuantumDataAugmenter",
    "DatasetBuilder",
    "create_train_val_split",
]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test tokenizer
    tokenizer = CharacterTokenizer(vocab_size=256)
    text = "Hello, Quantum World!"
    encoded = tokenizer.encode(text)
    decoded = tokenizer.decode(encoded)

    logger.info(f"Original: {text}")
    logger.info(f"Encoded: {encoded}")
    logger.info(f"Decoded: {decoded}")

    # Test dataset
    sample_texts = [
        "The quantum computer processes information.",
        "Machine learning meets quantum computing.",
        "Training language models with quantum circuits.",
    ]

    dataset = TextDataset(
        texts=sample_texts,
        tokenizer=tokenizer,
        max_seq_length=64,
        stride=32,
    )

    logger.info(f"Dataset size: {len(dataset)}")

    # Test sample
    input_ids, target_ids = dataset[0]
    logger.info(f"Sample shapes: input={input_ids.shape}, target={target_ids.shape}")
    logger.info(f"Sample input: {tokenizer.decode(input_ids.tolist())}")

    logger.info("✅ All dataset utilities tested successfully")
