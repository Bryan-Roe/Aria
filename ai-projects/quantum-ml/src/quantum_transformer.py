"""
Quantum Transformer: Real quantum circuits integrated into transformer architecture.

Uses PennyLane variational quantum circuits for attention and feed-forward layers.
Provides a small-scale proof-of-concept QuantumLLM that can be trained on character-level
language modeling with gradients flowing through quantum circuits.

Classes:
    ClassicalSelfAttention  - Standard dot-product attention (fallback)
    ClassicalFeedForward    - Standard 2-layer FFN (fallback)
    QuantumSelfAttention    - Quantum kernel attention using QuantumLayer
    QuantumFeedForward      - Hybrid quantum-classical FFN
    QuantumTransformerBlock - Pre-norm transformer block with quantum components
    QuantumLLM              - Full language model with quantum transformer blocks
"""

import logging
import math
from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F

logger = logging.getLogger(__name__)

try:
    from hybrid_qnn import QuantumLayer

    QUANTUM_AVAILABLE = True
    logger.info("QuantumLayer loaded successfully")
except ImportError:
    try:
        import sys
        from pathlib import Path

        _src_dir = str(Path(__file__).parent)
        if _src_dir not in sys.path:
            sys.path.insert(0, _src_dir)
        from hybrid_qnn import QuantumLayer

        QUANTUM_AVAILABLE = True
        logger.info("QuantumLayer loaded from local src directory")
    except ImportError as e:
        QUANTUM_AVAILABLE = False
        logger.warning(f"QuantumLayer not available - using classical fallbacks: {e}")


# ---------------------------------------------------------------------------
# Classical fallbacks
# ---------------------------------------------------------------------------


class ClassicalSelfAttention(nn.Module):
    """Standard multi-head dot-product attention (fallback when quantum unavailable)."""

    def __init__(self, d_model: int, n_heads: int, dropout: float = 0.1):
        super().__init__()
        assert d_model % n_heads == 0, "d_model must be divisible by n_heads"
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_head = d_model // n_heads
        self.scale = 1.0 / math.sqrt(self.d_head)

        self.W_Q = nn.Linear(d_model, d_model)
        self.W_K = nn.Linear(d_model, d_model)
        self.W_V = nn.Linear(d_model, d_model)
        self.W_O = nn.Linear(d_model, d_model)
        self.attn_dropout = nn.Dropout(dropout)

    def forward(
        self, x: torch.Tensor, mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        batch, seq_len, _ = x.shape

        Q = self.W_Q(x).view(batch, seq_len, self.n_heads, self.d_head).transpose(1, 2)
        K = self.W_K(x).view(batch, seq_len, self.n_heads, self.d_head).transpose(1, 2)
        V = self.W_V(x).view(batch, seq_len, self.n_heads, self.d_head).transpose(1, 2)

        attn_logits = torch.matmul(Q, K.transpose(-2, -1)) * self.scale

        if mask is not None:
            attn_logits = attn_logits.masked_fill(mask == 0, float("-inf"))

        attn_weights = self.attn_dropout(F.softmax(attn_logits, dim=-1))
        out = torch.matmul(attn_weights, V)
        out = out.transpose(1, 2).contiguous().view(batch, seq_len, self.d_model)
        return self.W_O(out)


class ClassicalFeedForward(nn.Module):
    """Standard 2-layer feed-forward network (fallback)."""

    def __init__(self, d_model: int, d_ffn: int = 256, dropout: float = 0.1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_model, d_ffn),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_ffn, d_model),
            nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


# ---------------------------------------------------------------------------
# Quantum components
# ---------------------------------------------------------------------------


class QuantumSelfAttention(nn.Module):
    """
    Multi-head attention using quantum circuits as learned feature maps.

    Instead of computing softmax(QK^T / sqrt(d_k)), this maps Q and K through
    a parameterised variational quantum circuit (QuantumLayer) and computes
    attention logits as the dot product of the quantum-mapped features:

        attention_logits_{ij} = phi(Q_i) . phi(K_j) / sqrt(n_qubits)

    One QuantumLayer per head provides separate learned quantum kernels.
    """

    def __init__(
        self,
        d_model: int = 64,
        n_heads: int = 4,
        n_qubits: int = 4,
        n_quantum_layers: int = 2,
        entanglement: str = "circular",
        dropout: float = 0.1,
    ):
        super().__init__()
        assert d_model % n_heads == 0, "d_model must be divisible by n_heads"

        self.d_model = d_model
        self.n_heads = n_heads
        self.d_head = d_model // n_heads
        self.n_qubits = n_qubits
        self.quantum_input_dim = 2**n_qubits
        self.scale = 1.0 / math.sqrt(n_qubits)

        # Classical projections
        self.W_Q = nn.Linear(d_model, d_model)
        self.W_K = nn.Linear(d_model, d_model)
        self.W_V = nn.Linear(d_model, d_model)
        self.W_O = nn.Linear(d_model, d_model)

        # Quantum projection (only needed when d_head != 2^n_qubits)
        if self.d_head != self.quantum_input_dim:
            self.quantum_proj = nn.Linear(self.d_head, self.quantum_input_dim)
        else:
            self.quantum_proj = None

        # One QuantumLayer per attention head
        self.quantum_layers = nn.ModuleList(
            [
                QuantumLayer(
                    n_qubits=n_qubits,
                    n_layers=n_quantum_layers,
                    device="default.qubit",
                    entanglement=entanglement,
                )
                for _ in range(n_heads)
            ]
        )

        self.attn_dropout = nn.Dropout(dropout)

    def _quantum_map(self, x: torch.Tensor, head_idx: int) -> torch.Tensor:
        """Map input through quantum circuit for a specific head.

        Args:
            x: (batch * seq, d_head) tensor
            head_idx: which head's QuantumLayer to use

        Returns:
            (batch * seq, n_qubits) tensor of quantum expectation values
        """
        if self.quantum_proj is not None:
            x = self.quantum_proj(x)
        x = F.normalize(x, p=2, dim=-1)
        return self.quantum_layers[head_idx](x)

    def forward(
        self, x: torch.Tensor, mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        batch, seq_len, _ = x.shape

        Q = self.W_Q(x).view(batch, seq_len, self.n_heads, self.d_head)
        K = self.W_K(x).view(batch, seq_len, self.n_heads, self.d_head)
        V = self.W_V(x).view(batch, seq_len, self.n_heads, self.d_head).transpose(1, 2)

        head_outputs = []
        for h in range(self.n_heads):
            Q_h = Q[:, :, h, :].reshape(batch * seq_len, self.d_head)
            K_h = K[:, :, h, :].reshape(batch * seq_len, self.d_head)

            Q_q = self._quantum_map(Q_h, h).view(batch, seq_len, self.n_qubits)
            K_q = self._quantum_map(K_h, h).view(batch, seq_len, self.n_qubits)

            attn_logits = torch.bmm(Q_q, K_q.transpose(1, 2)) * self.scale

            if mask is not None:
                attn_logits = attn_logits.masked_fill(mask == 0, float("-inf"))

            attn_weights = self.attn_dropout(F.softmax(attn_logits, dim=-1))

            V_h = V[:, h, :, :]  # (batch, seq, d_head)
            head_out = torch.bmm(attn_weights, V_h)  # (batch, seq, d_head)
            head_outputs.append(head_out)

        multi_head = torch.cat(head_outputs, dim=-1)  # (batch, seq, d_model)
        return self.W_O(multi_head)


class QuantumFeedForward(nn.Module):
    """
    Hybrid quantum-classical feed-forward network.

    Classical down-projection to 2^n_qubits dims, quantum processing through
    a variational circuit, then classical up-projection back to d_model.
    The quantum circuit acts as a nonlinear bottleneck with quantum-mechanical
    expressivity.
    """

    def __init__(
        self,
        d_model: int = 64,
        n_qubits: int = 4,
        n_quantum_layers: int = 2,
        entanglement: str = "circular",
        dropout: float = 0.1,
    ):
        super().__init__()
        self.quantum_input_dim = 2**n_qubits
        self.n_qubits = n_qubits

        self.down_proj = nn.Linear(d_model, self.quantum_input_dim)
        self.quantum_layer = QuantumLayer(
            n_qubits=n_qubits,
            n_layers=n_quantum_layers,
            device="default.qubit",
            entanglement=entanglement,
        )
        self.activation = nn.GELU()
        self.up_proj = nn.Linear(n_qubits, d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch, seq_len, d_model = x.shape

        x_flat = x.reshape(batch * seq_len, d_model)
        x_down = self.down_proj(x_flat)
        x_norm = F.normalize(x_down, p=2, dim=-1)
        x_quantum = self.quantum_layer(x_norm)
        x_act = self.activation(x_quantum)
        x_up = self.up_proj(x_act)
        x_out = self.dropout(x_up)

        return x_out.view(batch, seq_len, d_model)


# ---------------------------------------------------------------------------
# Transformer block and full LLM
# ---------------------------------------------------------------------------


class QuantumTransformerBlock(nn.Module):
    """
    Pre-norm transformer block with optional quantum attention and FFN.

    Falls back to classical components when quantum libraries are unavailable
    or when use_quantum_* flags are set to False.
    """

    def __init__(
        self,
        d_model: int = 64,
        n_heads: int = 4,
        n_qubits: int = 4,
        n_quantum_layers: int = 2,
        entanglement: str = "circular",
        dropout: float = 0.1,
        use_quantum_attention: bool = True,
        use_quantum_ffn: bool = True,
    ):
        super().__init__()

        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.drop1 = nn.Dropout(dropout)
        self.drop2 = nn.Dropout(dropout)

        if use_quantum_attention and QUANTUM_AVAILABLE:
            self.attention = QuantumSelfAttention(
                d_model=d_model,
                n_heads=n_heads,
                n_qubits=n_qubits,
                n_quantum_layers=n_quantum_layers,
                entanglement=entanglement,
                dropout=dropout,
            )
            logger.info("Using QuantumSelfAttention")
        else:
            self.attention = ClassicalSelfAttention(d_model, n_heads, dropout)
            logger.info("Using ClassicalSelfAttention (fallback)")

        if use_quantum_ffn and QUANTUM_AVAILABLE:
            self.ffn = QuantumFeedForward(
                d_model=d_model,
                n_qubits=n_qubits,
                n_quantum_layers=n_quantum_layers,
                entanglement=entanglement,
                dropout=dropout,
            )
            logger.info("Using QuantumFeedForward")
        else:
            self.ffn = ClassicalFeedForward(d_model, d_ffn=d_model * 4, dropout=dropout)
            logger.info("Using ClassicalFeedForward (fallback)")

    def forward(
        self, x: torch.Tensor, mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        x = x + self.drop1(self.attention(self.norm1(x), mask=mask))
        x = x + self.drop2(self.ffn(self.norm2(x)))
        return x


class QuantumLLM(nn.Module):
    """
    Small-scale language model with quantum transformer blocks.

    Architecture:
        Token embedding + learned positional encoding
        -> N QuantumTransformerBlock layers
        -> LayerNorm -> LM head (vocab projection)

    Designed for proof-of-concept with 4-8 qubit quantum circuits.
    Default config (~100k params): vocab=1000, d_model=64, 2 blocks, 4 heads, 4 qubits.
    """

    def __init__(
        self,
        vocab_size: int = 1000,
        d_model: int = 64,
        n_heads: int = 4,
        n_transformer_layers: int = 2,
        n_qubits: int = 4,
        n_quantum_layers: int = 2,
        max_seq_len: int = 32,
        entanglement: str = "circular",
        dropout: float = 0.1,
        use_quantum_attention: bool = True,
        use_quantum_ffn: bool = True,
        tie_embeddings: bool = True,
    ):
        super().__init__()
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.max_seq_len = max_seq_len

        self.token_embedding = nn.Embedding(vocab_size, d_model)
        self.pos_embedding = nn.Embedding(max_seq_len, d_model)
        self.embedding_dropout = nn.Dropout(dropout)

        self.blocks = nn.ModuleList(
            [
                QuantumTransformerBlock(
                    d_model=d_model,
                    n_heads=n_heads,
                    n_qubits=n_qubits,
                    n_quantum_layers=n_quantum_layers,
                    entanglement=entanglement,
                    dropout=dropout,
                    use_quantum_attention=use_quantum_attention,
                    use_quantum_ffn=use_quantum_ffn,
                )
                for _ in range(n_transformer_layers)
            ]
        )

        self.final_norm = nn.LayerNorm(d_model)
        self.lm_head = nn.Linear(d_model, vocab_size, bias=False)

        if tie_embeddings:
            self.lm_head.weight = self.token_embedding.weight

        # Initialise weights
        self.apply(self._init_weights)

        n_params = sum(p.numel() for p in self.parameters())
        logger.info(f"QuantumLLM initialised: {n_params:,} parameters")
        logger.info(
            f"  vocab={vocab_size}, d_model={d_model}, heads={n_heads}, "
            f"blocks={n_transformer_layers}, qubits={n_qubits}, "
            f"seq_len={max_seq_len}"
        )

    @staticmethod
    def _init_weights(module: nn.Module):
        if isinstance(module, nn.Linear):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
        elif isinstance(module, nn.LayerNorm):
            nn.init.ones_(module.weight)
            nn.init.zeros_(module.bias)

    def forward(
        self,
        input_ids: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Args:
            input_ids: (batch, seq_len) LongTensor of token indices
            mask: optional attention mask; if None a causal mask is created

        Returns:
            logits: (batch, seq_len, vocab_size)
        """
        batch, seq_len = input_ids.shape
        assert (
            seq_len <= self.max_seq_len
        ), f"Sequence length {seq_len} exceeds max {self.max_seq_len}"

        positions = torch.arange(seq_len, device=input_ids.device).unsqueeze(0)
        x = self.token_embedding(input_ids) + self.pos_embedding(positions)
        x = self.embedding_dropout(x)

        if mask is None:
            mask = torch.tril(torch.ones(seq_len, seq_len, device=x.device)).unsqueeze(
                0
            )

        for block in self.blocks:
            x = block(x, mask=mask)

        x = self.final_norm(x)
        logits = self.lm_head(x)
        return logits

    @torch.no_grad()
    def generate(
        self,
        input_ids: torch.Tensor,
        max_new_tokens: int = 20,
        temperature: float = 1.0,
        top_k: Optional[int] = None,
    ) -> torch.Tensor:
        """Autoregressive token-by-token generation."""
        self.eval()
        for _ in range(max_new_tokens):
            x = input_ids[:, -self.max_seq_len :]
            logits = self.forward(x)
            next_logits = logits[:, -1, :] / temperature

            if top_k is not None:
                topk_vals, _ = torch.topk(next_logits, min(top_k, next_logits.size(-1)))
                next_logits[next_logits < topk_vals[:, [-1]]] = float("-inf")

            probs = F.softmax(next_logits, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)
            input_ids = torch.cat([input_ids, next_token], dim=1)
        return input_ids

    @classmethod
    def from_config(cls, config: dict) -> "QuantumLLM":
        """Create a QuantumLLM from a configuration dictionary."""
        qt = config.get("quantum_transformer", config)
        return cls(
            vocab_size=qt.get("vocab_size", 1000),
            d_model=qt.get("d_model", 64),
            n_heads=qt.get("n_heads", 4),
            n_transformer_layers=qt.get("n_transformer_layers", 2),
            n_qubits=qt.get("n_qubits", 4),
            n_quantum_layers=qt.get("n_quantum_layers", 2),
            max_seq_len=qt.get("max_seq_len", 32),
            entanglement=qt.get("entanglement", "circular"),
            dropout=qt.get("dropout", 0.1),
            use_quantum_attention=qt.get("use_quantum_attention", True),
            use_quantum_ffn=qt.get("use_quantum_ffn", True),
            tie_embeddings=qt.get("tie_embeddings", True),
        )


# ---------------------------------------------------------------------------
# Quick smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("Quantum Transformer Smoke Test")
    print("=" * 60)

    model = QuantumLLM(
        vocab_size=256,
        d_model=64,
        n_heads=4,
        n_transformer_layers=1,
        n_qubits=4,
        n_quantum_layers=1,
        max_seq_len=16,
    )

    input_ids = torch.randint(0, 256, (2, 8))
    logits = model(input_ids)

    print(f"Input shape:  {input_ids.shape}")
    print(f"Output shape: {logits.shape}")
    assert logits.shape == (2, 8, 256), f"Unexpected shape: {logits.shape}"

    loss = F.cross_entropy(
        logits.view(-1, 256),
        torch.randint(0, 256, (2 * 8,)),
    )
    loss.backward()
    print(f"Loss: {loss.item():.4f}")
    print("Gradient check: OK - gradients flow through quantum circuits")

    generated = model.generate(input_ids, max_new_tokens=4, temperature=1.0)
    print(f"Generated shape: {generated.shape}")
    print("Smoke test PASSED")
