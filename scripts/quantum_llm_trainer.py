"""
Quantum-Enhanced LLM Training Module
=====================================

Trains a QuantumLLM (transformer with real quantum circuits in attention and
feed-forward layers) on character-level language modeling tasks.

Features:
- Real quantum circuits via PennyLane in attention and FFN layers
- Character-level dataset for proof-of-concept training
- Gradient backpropagation through quantum circuits
- Passive background training mode
- Classical fallback when quantum libraries unavailable

Usage:
    # Train on a text file
    python quantum_llm_trainer.py --dataset path/to/text_or_json

    # Train with custom architecture
    python quantum_llm_trainer.py --dataset path/to/data --n-qubits 4 --d-model 64

    # Passive mode (background training)
    python quantum_llm_trainer.py --passive --interval 3600

Author: Quantum AI Workspace
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import yaml
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> f7862a0 (refactor: Consolidate AI projects under ai-projects/ directory)
# Add ai-projects/quantum-ml to path
quantum_ml_path = Path(__file__).parent.parent / "ai-projects" / "quantum-ml"
quantum_ml_src = quantum_ml_path / "src"
for p in [str(quantum_ml_path), str(quantum_ml_src)]:
<<<<<<< HEAD
=======
# Add quantum-ai to path
quantum_ai_path = Path(__file__).parent.parent / "quantum-ai"
quantum_ai_src = quantum_ai_path / "src"
for p in [str(quantum_ai_path), str(quantum_ai_src)]:
>>>>>>> 6f22fc0 (refactor: Organize repository structure)
=======
>>>>>>> f7862a0 (refactor: Consolidate AI projects under ai-projects/ directory)
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from quantum_transformer import QuantumLLM, QUANTUM_AVAILABLE
except ImportError as e:
    logging.warning(f"QuantumLLM not available: {e}")
    QUANTUM_AVAILABLE = False

try:
    from hybrid_qnn import QuantumLayer
    QUANTUM_LAYER_AVAILABLE = True
except ImportError:
    QUANTUM_LAYER_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Character-level dataset
# ---------------------------------------------------------------------------

class CharacterDataset(Dataset):
    """Character-level dataset for quantum LLM training.

    Reads text, builds a character vocabulary, and produces overlapping
    windows of (input_ids, target_ids) where target is shifted by one
    position (standard next-token prediction).
    """

    def __init__(self, text: str, seq_len: int = 32, vocab_size: int = 1000):
        self.seq_len = seq_len

        # Build vocabulary from the text (up to vocab_size unique chars)
        unique_chars = sorted(set(text))
        if len(unique_chars) > vocab_size - 1:
            unique_chars = unique_chars[:vocab_size - 1]

        self.char_to_id = {c: i + 1 for i, c in enumerate(unique_chars)}
        self.char_to_id["\x00"] = 0  # padding / unknown
        self.id_to_char = {v: k for k, v in self.char_to_id.items()}
        self.actual_vocab_size = len(self.char_to_id)

        # Encode entire text
        self.encoded = [self.char_to_id.get(c, 0) for c in text]

        # We need at least seq_len + 1 characters for one sample
        if len(self.encoded) < seq_len + 1:
            # Pad with zeros if text is too short
            self.encoded = self.encoded + [0] * (seq_len + 1 - len(self.encoded))

        logger.info(
            f"CharacterDataset: {len(text)} chars, "
            f"{self.actual_vocab_size} unique tokens, "
            f"{len(self)} samples (seq_len={seq_len})"
        )

    def __len__(self) -> int:
        return max(1, len(self.encoded) - self.seq_len)

    def __getitem__(self, idx: int):
        chunk = self.encoded[idx: idx + self.seq_len + 1]
        input_ids = torch.tensor(chunk[:-1], dtype=torch.long)
        target_ids = torch.tensor(chunk[1:], dtype=torch.long)
        return input_ids, target_ids

    def decode(self, ids) -> str:
        """Convert token ids back to text."""
        if isinstance(ids, torch.Tensor):
            ids = ids.tolist()
        return "".join(self.id_to_char.get(i, "?") for i in ids)


# ---------------------------------------------------------------------------
# Feature encoder (kept for auxiliary use, uses real QuantumLayer)
# ---------------------------------------------------------------------------

class QuantumFeatureEncoder:
    """Encodes classical features into quantum-enhanced representations."""

    def __init__(self, n_qubits: int = 4, n_layers: int = 2):
        self.n_qubits = n_qubits
        self.quantum_layer = None

        if QUANTUM_LAYER_AVAILABLE:
            try:
                self.quantum_layer = QuantumLayer(
                    n_qubits=n_qubits,
                    n_layers=n_layers,
                    device="default.qubit",
                    entanglement="circular",
                )
                logger.info("Initialized quantum feature encoder")
            except Exception as e:
                logger.warning(f"Failed to initialize quantum layer: {e}")

    def encode(self, features: torch.Tensor) -> torch.Tensor:
        if self.quantum_layer is None:
            return torch.tanh(features)

        try:
            batch_size, feature_dim = features.shape
            quantum_dim = 2 ** self.n_qubits
            if feature_dim < quantum_dim:
                padded = torch.zeros(batch_size, quantum_dim, device=features.device)
                padded[:, :feature_dim] = features
                features = padded
            elif feature_dim > quantum_dim:
                features = features[:, :quantum_dim]

            features_norm = features / (torch.norm(features, dim=1, keepdim=True) + 1e-8)
            return self.quantum_layer(features_norm)
        except Exception as e:
            logger.warning(f"Quantum encoding failed: {e}, using classical fallback")
            return torch.tanh(features)


# ---------------------------------------------------------------------------
# Main trainer
# ---------------------------------------------------------------------------

class QuantumEnhancedLLMTrainer:
    """
    Trains a QuantumLLM on character-level language modeling.

    The QuantumLLM uses real PennyLane quantum circuits inside its
    transformer blocks (QuantumSelfAttention and QuantumFeedForward).
    Gradients flow through the quantum circuits via PennyLane's
    torch interface.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.passive_mode = config.get("passive", False)
        self.interval = config.get("interval", 3600)

        # Device
        use_gpu = config.get("use_gpu", True)
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() and use_gpu else "cpu"
        )

        # Build quantum transformer config
        qt_config = config.get("quantum_transformer", {})
        self.model_config = {
            "vocab_size": qt_config.get("vocab_size", config.get("vocab_size", 256)),
            "d_model": qt_config.get("d_model", config.get("d_model", 64)),
            "n_heads": qt_config.get("n_heads", config.get("n_heads", 4)),
            "n_transformer_layers": qt_config.get(
                "n_transformer_layers", config.get("n_transformer_layers", 2)
            ),
            "n_qubits": qt_config.get("n_qubits", config.get("n_qubits", 4)),
            "n_quantum_layers": qt_config.get(
                "n_quantum_layers", config.get("n_quantum_layers", 2)
            ),
            "max_seq_len": qt_config.get("max_seq_len", config.get("max_seq_len", 32)),
            "entanglement": qt_config.get(
                "entanglement", config.get("entanglement", "circular")
            ),
            "dropout": qt_config.get("dropout", config.get("dropout", 0.1)),
            "use_quantum_attention": qt_config.get("use_quantum_attention", True),
            "use_quantum_ffn": qt_config.get("use_quantum_ffn", True),
            "tie_embeddings": qt_config.get("tie_embeddings", True),
        }

        # Create model
        self.model = QuantumLLM.from_config({"quantum_transformer": self.model_config})
        self.model = self.model.to(self.device)

        # Optimizer
        lr = qt_config.get("learning_rate", config.get("learning_rate", 0.001))
        wd = qt_config.get("weight_decay", config.get("weight_decay", 0.01))
        self.optimizer = torch.optim.AdamW(self.model.parameters(), lr=lr, weight_decay=wd)

        # Loss and gradient clipping
        self.criterion = nn.CrossEntropyLoss()
        self.grad_clip = qt_config.get("gradient_clip", config.get("gradient_clip", 1.0))
        self.batch_size = qt_config.get("batch_size", config.get("batch_size", 4))

        # Learning rate scheduler
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode="min", factor=0.5, patience=3
        )

        # Feature encoder (auxiliary)
        self.feature_encoder = QuantumFeatureEncoder(
            n_qubits=self.model_config["n_qubits"],
            n_layers=self.model_config["n_quantum_layers"],
        )

        # Metrics
        self.training_history: List[Dict] = []
        self.quantum_metrics = {
            "circuit_executions": 0,
            "optimization_steps": 0,
            "quantum_available": QUANTUM_AVAILABLE,
        }

        n_params = sum(p.numel() for p in self.model.parameters())
        logger.info("Initialized QuantumEnhancedLLMTrainer")
        logger.info(f"  Device: {self.device}")
        logger.info(f"  Parameters: {n_params:,}")
        logger.info(f"  Quantum available: {QUANTUM_AVAILABLE}")
        logger.info(f"  Model config: {self.model_config}")

    # ------------------------------------------------------------------
    # Dataset loading
    # ------------------------------------------------------------------

    def _extract_text(self, dataset_path: Path) -> str:
        """Extract raw text from various file formats."""
        text_parts = []

        if dataset_path.is_file():
            if dataset_path.suffix == ".txt":
                text_parts.append(dataset_path.read_text(errors="replace"))

            elif dataset_path.suffix == ".jsonl":
                with open(dataset_path) as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        record = json.loads(line)
                        for key in ("text", "content", "message", "input", "output"):
                            if key in record:
                                text_parts.append(str(record[key]))

            elif dataset_path.suffix == ".json":
                with open(dataset_path) as f:
                    data = json.load(f)
                if isinstance(data, list):
                    for record in data:
                        if isinstance(record, dict):
                            for key in ("text", "content", "message", "input", "output"):
                                if key in record:
                                    text_parts.append(str(record[key]))
                        elif isinstance(record, str):
                            text_parts.append(record)
                elif isinstance(data, dict):
                    for key in ("text", "content", "message", "input", "output"):
                        if key in data:
                            text_parts.append(str(data[key]))

        elif dataset_path.is_dir():
            for pattern in ["*.txt", "*.json", "*.jsonl"]:
                for fp in sorted(dataset_path.glob(pattern)):
                    text_parts.append(self._extract_text(fp))
            for subdir_name in ["train.json", "train.jsonl"]:
                sub = dataset_path / subdir_name
                if sub.exists():
                    text_parts.append(self._extract_text(sub))

        combined = "\n".join(text_parts)
        if not combined.strip():
            # Generate a small synthetic corpus so training can still run
            logger.warning(
                "No text extracted from dataset -- using synthetic placeholder text"
            )
            combined = (
                "The quick brown fox jumps over the lazy dog. "
                "Pack my box with five dozen liquor jugs. "
                "How vexingly quick daft zebras jump. "
            ) * 50

        return combined

    def _make_dataloader(self, dataset_path: Path) -> DataLoader:
        """Build a DataLoader from a dataset path."""
        text = self._extract_text(dataset_path)
        dataset = CharacterDataset(
            text=text,
            seq_len=self.model_config["max_seq_len"],
            vocab_size=self.model_config["vocab_size"],
        )
        return DataLoader(
            dataset,
            batch_size=self.batch_size,
            shuffle=True,
            drop_last=True,
        )

    # ------------------------------------------------------------------
    # Training loop
    # ------------------------------------------------------------------

    def _estimate_circuit_evals(self, batch_size: int, seq_len: int) -> int:
        """Estimate the number of quantum circuit evaluations per batch."""
        if not QUANTUM_AVAILABLE:
            return 0
        n_heads = self.model_config["n_heads"]
        n_blocks = self.model_config["n_transformer_layers"]
        # Attention: 2 maps (Q, K) * batch*seq per head per block
        attn_evals = 2 * batch_size * seq_len * n_heads * n_blocks
        # FFN: 1 map * batch*seq per block
        ffn_evals = batch_size * seq_len * n_blocks
        return attn_evals + ffn_evals

    def _train_epoch(self, dataloader: DataLoader, epoch: int) -> float:
        """Train one epoch with real forward/backward through quantum circuits."""
        self.model.train()
        total_loss = 0.0
        num_batches = 0

        for batch_idx, (input_ids, targets) in enumerate(dataloader):
            input_ids = input_ids.to(self.device)
            targets = targets.to(self.device)

            # Forward pass (gradients flow through quantum circuits)
            logits = self.model(input_ids)

            # Cross-entropy loss
            loss = self.criterion(
                logits.view(-1, self.model.vocab_size),
                targets.view(-1),
            )

            # Backward pass
            self.optimizer.zero_grad()
            loss.backward()

            # Gradient clipping
            if self.grad_clip > 0:
                torch.nn.utils.clip_grad_norm_(
                    self.model.parameters(), self.grad_clip
                )

            self.optimizer.step()

            batch_loss = loss.item()
            total_loss += batch_loss
            num_batches += 1

            # Track quantum circuit evaluations
            evals = self._estimate_circuit_evals(
                input_ids.shape[0], input_ids.shape[1]
            )
            self.quantum_metrics["circuit_executions"] += evals
            self.quantum_metrics["optimization_steps"] += 1

            if batch_idx % 5 == 0:
                logger.info(
                    f"  Epoch {epoch+1} | Batch {batch_idx}/{len(dataloader)} | "
                    f"Loss: {batch_loss:.4f} | "
                    f"Circuit evals: {evals}"
                )

        avg_loss = total_loss / max(num_batches, 1)
        self.training_history.append({
            "epoch": epoch,
            "loss": avg_loss,
            "circuit_executions": self.quantum_metrics["circuit_executions"],
            "lr": self.optimizer.param_groups[0]["lr"],
        })

        # Update scheduler
        self.scheduler.step(avg_loss)

        return avg_loss

    def train_with_quantum_enhancement(
        self,
        dataset_path: Path,
        output_dir: Path,
        epochs: int = 3,
    ) -> Dict[str, Any]:
        """
        Train the QuantumLLM on a dataset.

        Args:
            dataset_path: Path to training data (text, json, or jsonl)
            output_dir: Directory for results and checkpoints
            epochs: Number of training epochs

        Returns:
            Training results and quantum metrics
        """
        logger.info("Starting quantum-enhanced LLM training")
        logger.info(f"  Dataset: {dataset_path}")
        logger.info(f"  Output: {output_dir}")
        logger.info(f"  Epochs: {epochs}")

        output_dir.mkdir(parents=True, exist_ok=True)

        # Build dataloader
        dataloader = self._make_dataloader(dataset_path)
        logger.info(f"  Batches per epoch: {len(dataloader)}")

        results = {
            "status": "success",
            "epochs_completed": 0,
            "final_loss": 0.0,
            "quantum_metrics": self.quantum_metrics,
            "model_config": self.model_config,
            "started_at": datetime.now().isoformat(),
        }

        best_loss = float("inf")

        for epoch in range(epochs):
            logger.info(f"\n--- Epoch {epoch + 1}/{epochs} ---")

            epoch_loss = self._train_epoch(dataloader, epoch)

            results["epochs_completed"] = epoch + 1
            results["final_loss"] = epoch_loss

            logger.info(
                f"  Epoch {epoch+1} complete | Avg Loss: {epoch_loss:.4f} | "
                f"LR: {self.optimizer.param_groups[0]['lr']:.6f}"
            )

            # Save best checkpoint
            if epoch_loss < best_loss:
                best_loss = epoch_loss
                ckpt_path = output_dir / "best_quantum_llm.pt"
                torch.save({
                    "model_state_dict": self.model.state_dict(),
                    "optimizer_state_dict": self.optimizer.state_dict(),
                    "epoch": epoch,
                    "loss": epoch_loss,
                    "model_config": self.model_config,
                }, ckpt_path)
                logger.info(f"  Saved best checkpoint: {ckpt_path}")

        results["completed_at"] = datetime.now().isoformat()
        results["best_loss"] = best_loss

        # Save results JSON
        results_file = output_dir / "quantum_training_results.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"\nTraining complete! Results saved to: {results_file}")

        # Generate sample text
        self._generate_sample(output_dir, dataloader.dataset)

        return results
    
    def _load_dataset(self, dataset_path: Path) -> List[Dict[str, Any]]:
        """Load training dataset from JSONL or JSON format."""
        dataset = []
        
        if dataset_path.is_file():
            if dataset_path.suffix == '.jsonl':
                with open(dataset_path) as f:
                    for line in f:
                        if line.strip():
                            dataset.append(json.loads(line))
            elif dataset_path.suffix == '.json':
                with open(dataset_path) as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        dataset = data
                    else:
                        dataset = [data]
        elif dataset_path.is_dir():
            # Look for train files using glob for efficiency
            train_files = list(dataset_path.glob("train.json")) + list(dataset_path.glob("train.jsonl"))
            if train_files:
                return self._load_dataset(train_files[0])
        
        return dataset
    
    def _train_epoch_with_quantum(
        self,
        model: Optional[Any],
        dataset: List[Dict[str, Any]],
        epoch: int
    ) -> float:
        """
        Train one epoch with quantum enhancement.
        
        Returns:
            Average loss for the epoch
        """
        total_loss = 0.0
        num_batches = max(1, len(dataset) // 32)
        
        for batch_idx in range(num_batches):
            # Simulate forward pass
            batch_loss = np.random.uniform(0.5, 2.0)  # Mock random loss (low, high)
            
            # Apply quantum optimization every N steps
            if batch_idx % 10 == 0:
                # Quantum-enhanced optimization step
                mock_attention = torch.randn(1, 8, 8)
                optimized = self.attention_optimizer.optimize_attention_weights(mock_attention)
                self.quantum_metrics["circuit_executions"] += 1
                self.quantum_metrics["optimization_steps"] += 1
                
                # Simulate quantum advantage (small improvement)
                batch_loss *= 0.98
            
            total_loss += batch_loss
        
        avg_loss = total_loss / num_batches
        self.training_history.append({
            "epoch": epoch,
            "loss": avg_loss,
            "quantum_executions": self.quantum_metrics["circuit_executions"]
        })
        
        return avg_loss
    

    def _generate_sample(self, output_dir: Path, dataset: CharacterDataset):
        """Generate a sample from the trained model."""
        try:
            prompt_ids = torch.tensor([[1, 2, 3, 4]], dtype=torch.long, device=self.device)
            generated = self.model.generate(
                prompt_ids, max_new_tokens=50, temperature=0.8, top_k=20
            )
            text = dataset.decode(generated[0])
            logger.info(f"  Sample generation: {text[:100]}...")

            sample_path = output_dir / "generated_sample.txt"
            sample_path.write_text(text)
        except Exception as e:
            logger.warning(f"Sample generation failed: {e}")

    # ------------------------------------------------------------------
    # Passive training
    # ------------------------------------------------------------------

    def run_passive_training(self):
        """Run in passive mode -- continuous background training cycles."""
        logger.info("Starting passive quantum-enhanced LLM training")
        logger.info(f"  Interval: {self.interval} seconds")

        import time
        import signal

        self.running = True

        def signal_handler(sig, frame):
            logger.info("Received shutdown signal")
            self.running = False

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        cycle_count = 0

        while self.running:
            cycle_count += 1
            logger.info(f"\n=== Passive Training Cycle {cycle_count} ===")

            try:
                # Look for available datasets using combined glob pattern
                datasets_dir = Path("datasets/chat")
                if datasets_dir.exists():
                    # Use explicit patterns to match only train.json and train.jsonl
                    dataset_files = list(datasets_dir.glob("*/train.json")) + list(datasets_dir.glob("*/train.jsonl"))
                    
                    dataset_files = (
                        list(datasets_dir.glob("*/train.json"))
                        + list(datasets_dir.glob("*/train.jsonl"))
                        + list(datasets_dir.glob("*.txt"))
                    )

                    if dataset_files:
                        import random
                        dataset_path = random.choice(dataset_files)
                        logger.info(f"Selected dataset: {dataset_path}")

                        output_dir = (
                            Path("data_out/quantum_llm_training") / f"cycle_{cycle_count}"
                        )

                        results = self.train_with_quantum_enhancement(
                            dataset_path=dataset_path,
                            output_dir=output_dir,
                            epochs=1,
                        )
                        logger.info(
                            f"Cycle {cycle_count} complete: "
                            f"Loss={results['final_loss']:.4f}"
                        )
                    else:
                        logger.warning("No datasets found for passive training")
                else:
                    logger.warning(f"Datasets directory not found: {datasets_dir}")

            except Exception as e:
                logger.error(f"Error in passive training cycle: {e}", exc_info=True)

            if self.running:
                if self.interval == 0:
                    logger.info(
                        "Interval is 0; completed single passive training cycle, exiting."
                    )
                    break
                logger.info(f"Waiting {self.interval} seconds until next cycle...")
                time.sleep(self.interval)

        logger.info("Passive training stopped")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Quantum-Enhanced LLM Training with Real Quantum Circuits",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Dataset / output
    parser.add_argument("--dataset", type=str, help="Path to training data")
    parser.add_argument(
        "--output-dir", type=str, default="data_out/quantum_llm_training",
        help="Output directory for results",
    )

    # Model architecture
    parser.add_argument("--vocab-size", type=int, default=256)
    parser.add_argument("--d-model", type=int, default=64)
    parser.add_argument("--n-heads", type=int, default=4)
    parser.add_argument("--n-transformer-layers", type=int, default=2)
    parser.add_argument("--max-seq-len", type=int, default=32)

    # Quantum circuit settings
    parser.add_argument("--n-qubits", type=int, default=4)
    parser.add_argument("--n-quantum-layers", type=int, default=2)
    parser.add_argument(
        "--entanglement", type=str, default="circular",
        choices=["linear", "circular", "full"],
    )

    # Training
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=0.001)
    parser.add_argument("--gradient-clip", type=float, default=1.0)

    # Passive mode
    parser.add_argument("--passive", action="store_true")
    parser.add_argument("--interval", type=int, default=3600)

    # Config file
    parser.add_argument("--config", type=str, help="Path to YAML config file")

    args = parser.parse_args()

    # Build config from CLI args
    config = {
        "quantum_transformer": {
            "vocab_size": args.vocab_size,
            "d_model": args.d_model,
            "n_heads": args.n_heads,
            "n_transformer_layers": args.n_transformer_layers,
            "max_seq_len": args.max_seq_len,
            "n_qubits": args.n_qubits,
            "n_quantum_layers": args.n_quantum_layers,
            "entanglement": args.entanglement,
            "learning_rate": args.learning_rate,
            "batch_size": args.batch_size,
            "gradient_clip": args.gradient_clip,
        },
        "passive": args.passive,
        "interval": args.interval,
    }

    # Merge config file if provided
    if args.config:
        config_path = Path(args.config)
        if config_path.exists():
            with open(config_path) as f:
                file_config = yaml.safe_load(f)
                config.update(file_config)

    # Create trainer
    trainer = QuantumEnhancedLLMTrainer(config)

    if args.passive:
        trainer.run_passive_training()
    else:
        if not args.dataset:
            logger.error("--dataset is required for active training mode")
            return 1

        results = trainer.train_with_quantum_enhancement(
            dataset_path=Path(args.dataset),
            output_dir=Path(args.output_dir),
            epochs=args.epochs,
        )

        logger.info("\nTraining Summary:")
        logger.info(f"  Status: {results['status']}")
        logger.info(f"  Epochs: {results['epochs_completed']}")
        logger.info(f"  Final Loss: {results['final_loss']:.4f}")
        logger.info(f"  Best Loss: {results.get('best_loss', 'N/A')}")
        logger.info(
            f"  Circuit Executions: "
            f"{results['quantum_metrics']['circuit_executions']}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
