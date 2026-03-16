#!/usr/bin/env python3
"""
Train a Quantum-Enhanced LLM for Chat
======================================

Trains a small quantum LLM model that can be used for interactive chat.
Integrates quantum circuits into the attention mechanism.

Usage:
    python scripts/train_quantum_llm_chat.py --quick
    python scripts/train_quantum_llm_chat.py --epochs 5 --output my_model
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

# Add paths
repo_root = Path(__file__).resolve().parent.parent
quantum_ml_path = repo_root / "ai-projects" / "quantum-ml"
quantum_ml_src = quantum_ml_path / "src"
for p in [str(quantum_ml_path), str(quantum_ml_src)]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from quantum_transformer import QuantumLLM, QUANTUM_AVAILABLE
except ImportError as e:
    logging.error(f"Cannot import QuantumLLM: {e}")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleCharDataset(Dataset):
    """Character-level dataset for language modeling."""
    
    def __init__(self, text: str, seq_len: int = 64):
        self.seq_len = seq_len
        
        # Build character vocabulary
        chars = sorted(set(text))
        self.vocab_size = len(chars) + 1  # +1 for padding
        self.char_to_idx = {c: i + 1 for i, c in enumerate(chars)}
        self.char_to_idx['<PAD>'] = 0
        self.idx_to_char = {i: c for c, i in self.char_to_idx.items()}
        
        # Encode text
        self.data = [self.char_to_idx.get(c, 0) for c in text]
        
        # Pad if needed
        if len(self.data) < seq_len + 1:
            self.data = self.data + [0] * (seq_len + 1 - len(self.data))
    
    def __len__(self):
        return max(0, len(self.data) - self.seq_len)
    
    def __getitem__(self, idx):
        chunk = self.data[idx:idx + self.seq_len + 1]
        x = torch.tensor(chunk[:-1], dtype=torch.long)
        y = torch.tensor(chunk[1:], dtype=torch.long)
        return x, y


def get_training_text():
    """Get sample training text about quantum computing and AI."""
    return """
Quantum computing uses quantum mechanics to process information in fundamentally new ways.
Unlike classical computers that use bits, quantum computers use qubits that can exist in superposition.
This means a qubit can be both zero and one simultaneously, enabling parallel computation.
Entanglement is another key quantum property where qubits become correlated.
When qubits are entangled, measuring one instantly affects the others regardless of distance.
Quantum gates manipulate qubits through unitary transformations to perform computations.
Variational quantum circuits are hybrid quantum-classical algorithms useful for machine learning.
They combine parameterized quantum circuits with classical optimization to solve problems.
Language models learn patterns in text by predicting the next token given previous context.
Transformers use attention mechanisms to weigh the importance of different input tokens.
Self-attention allows each position to attend to all positions in the previous layer.
Quantum-enhanced transformers integrate quantum circuits into the attention computation.
This creates quantum attention patterns that can capture complex relationships in data.
Training neural networks involves computing gradients and updating parameters via backpropagation.
Quantum circuits are differentiable, allowing gradients to flow through quantum layers.
This enables end-to-end training of hybrid quantum-classical neural networks.
Machine learning on quantum computers is an emerging field with great potential.
Quantum machine learning algorithms may provide advantages for certain tasks.
Current quantum computers are noisy and limited in scale, making practical applications challenging.
However, quantum simulators allow us to prototype and test quantum algorithms efficiently.
The future of AI may involve hybrid systems combining classical and quantum processing.
Quantum attention mechanisms can potentially discover patterns classical systems cannot find.
Research continues to explore the boundaries of what quantum computing can achieve.
As quantum hardware improves, practical quantum machine learning applications will emerge.
The combination of quantum physics and artificial intelligence opens exciting new possibilities.
""" * 20  # Repeat for more training data


def train_quantum_llm(args):
    """Train a quantum LLM model."""
    
    logger.info("=" * 80)
    logger.info("QUANTUM LLM TRAINING")
    logger.info("=" * 80)
    
    if not QUANTUM_AVAILABLE:
        logger.error("Quantum layers not available. Install pennylane: pip install pennylane")
        return 1
    
    # Setup
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Device: {device}")
    
    # Create dataset
    logger.info("Creating dataset...")
    text = get_training_text()
    dataset = SimpleCharDataset(text, seq_len=args.seq_len)
    vocab_size = dataset.vocab_size
    logger.info(f"Vocabulary size: {vocab_size}")
    logger.info(f"Dataset size: {len(dataset)} sequences")
    
    dataloader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=0
    )
    
    # Create model
    logger.info("Creating quantum LLM...")
    logger.info(f"  d_model: {args.d_model}")
    logger.info(f"  n_layers: {args.n_layers}")
    logger.info(f"  n_heads: {args.n_heads}")
    logger.info(f"  n_qubits: {args.n_qubits}")
    
    model = QuantumLLM(
        vocab_size=vocab_size,
        d_model=args.d_model,
        n_heads=args.n_heads,
        n_layers=args.n_layers,
        d_ffn=args.d_model * 4,
        max_seq_length=args.seq_len,
        n_qubits=args.n_qubits,
        n_quantum_layers=2,
        dropout=0.1,
        use_quantum=True
    ).to(device)
    
    n_params = sum(p.numel() for p in model.parameters())
    logger.info(f"Model parameters: {n_params:,}")
    
    # Training setup
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)
    criterion = nn.CrossEntropyLoss(ignore_index=0)  # Ignore padding
    
    # Training loop
    logger.info(f"\nStarting training for {args.epochs} epochs...")
    model.train()
    
    for epoch in range(args.epochs):
        total_loss = 0
        n_batches = 0
        
        for batch_idx, (x, y) in enumerate(dataloader):
            x, y = x.to(device), y.to(device)
            
            optimizer.zero_grad()
            
            # Forward pass
            logits = model(x)  # [batch, seq_len, vocab_size]
            
            # Compute loss
            loss = criterion(
                logits.view(-1, vocab_size),
                y.view(-1)
            )
            
            # Backward pass
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            
            total_loss += loss.item()
            n_batches += 1
            
            if (batch_idx + 1) % 10 == 0:
                avg_loss = total_loss / n_batches
                logger.info(f"  Epoch {epoch+1}/{args.epochs} | Batch {batch_idx+1}/{len(dataloader)} | Loss: {avg_loss:.4f}")
        
        avg_epoch_loss = total_loss / n_batches
        logger.info(f"Epoch {epoch+1}/{args.epochs} completed | Avg Loss: {avg_epoch_loss:.4f}")
    
    # Save model
    output_dir = Path("data_out") / args.output
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save model checkpoint
    checkpoint_path = output_dir / "quantum_llm_checkpoint.pt"
    torch.save({
        'model_state_dict': model.state_dict(),
        'vocab_size': vocab_size,
        'd_model': args.d_model,
        'n_heads': args.n_heads,
        'n_layers': args.n_layers,
        'n_qubits': args.n_qubits,
        'd_ffn': args.d_model * 4,
        'max_seq_length': args.seq_len,
        'char_to_idx': dataset.char_to_idx,
        'idx_to_char': dataset.idx_to_char,
    }, checkpoint_path)
    
    logger.info(f"\nModel saved to: {checkpoint_path}")
    
    # Save config
    config_path = output_dir / "config.json"
    config = {
        'vocab_size': vocab_size,
        'd_model': args.d_model,
        'n_heads': args.n_heads,
        'n_layers': args.n_layers,
        'n_qubits': args.n_qubits,
        'd_ffn': args.d_model * 4,
        'max_seq_length': args.seq_len,
        'trained_at': datetime.now().isoformat(),
        'quantum_available': QUANTUM_AVAILABLE,
    }
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Config saved to: {config_path}")
    logger.info("\n" + "=" * 80)
    logger.info("TRAINING COMPLETE!")
    logger.info("=" * 80)
    logger.info(f"\nTo chat with this model, run:")
    logger.info(f"  python ai-projects/chat-cli/src/chat_cli.py --provider quantum --model {output_dir}")
    
    return 0


def main():
    parser = argparse.ArgumentParser(description="Train a quantum-enhanced LLM for chat")
    parser.add_argument('--epochs', type=int, default=3, help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=8, help='Batch size')
    parser.add_argument('--seq-len', type=int, default=64, help='Sequence length')
    parser.add_argument('--d-model', type=int, default=64, help='Model dimension')
    parser.add_argument('--n-layers', type=int, default=2, help='Number of layers')
    parser.add_argument('--n-heads', type=int, default=2, help='Number of attention heads')
    parser.add_argument('--n-qubits', type=int, default=2, help='Number of qubits per quantum layer')
    parser.add_argument('--lr', type=float, default=1e-3, help='Learning rate')
    parser.add_argument('--output', type=str, default='quantum_llm_chat', help='Output directory name')
    parser.add_argument('--quick', action='store_true', help='Quick training (2 epochs, small model)')
    
    args = parser.parse_args()
    
    # Quick mode overrides
    if args.quick:
        args.epochs = 2
        args.d_model = 32
        args.n_layers = 2
        args.n_heads = 2
        args.n_qubits = 2
        args.seq_len = 32
        logger.info("Quick mode enabled: using minimal settings for fast training")
    
    return train_quantum_llm(args)


if __name__ == "__main__":
    sys.exit(main())
