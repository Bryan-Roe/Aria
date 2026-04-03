"""Quantum-enhanced code language model.

For ``backend='classical'``, this is a pure PyTorch GPT-style transformer.
For ``backend='quantum'``, quantum circuit layers would replace (or augment) the
feed-forward layers — requires ``pennylane`` or ``qiskit``.  The classical
fallback is used transparently when quantum libraries are unavailable.
"""

from __future__ import annotations

import dataclasses
import string
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
except ImportError as exc:
    raise ImportError("PyTorch required: pip install torch") from exc


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------


class CodeTokenizer:
    """Character-level tokenizer for source code.

    The vocabulary is built from ``string.printable`` (100 chars) plus four
    special tokens: PAD, BOS, EOS, UNK.  The mapping is deterministic and
    stable — no training required.
    """

    PAD: int = 0
    BOS: int = 1
    EOS: int = 2
    UNK: int = 3
    _NUM_SPECIAL: int = 4

    def __init__(self) -> None:
        chars = string.printable  # 100 printable ASCII chars, fixed ordering
        self._char_to_id: Dict[str, int] = {
            c: self._NUM_SPECIAL + i for i, c in enumerate(chars)
        }
        self._id_to_char: Dict[int, str] = {
            self._NUM_SPECIAL + i: c for i, c in enumerate(chars)
        }
        self._vocab_size: int = self._NUM_SPECIAL + len(chars)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def vocab_size(self) -> int:
        """Total number of tokens including specials."""
        return self._vocab_size

    # ------------------------------------------------------------------
    # Encode / decode
    # ------------------------------------------------------------------

    def encode(
        self,
        text: str,
        add_bos: bool = True,
        add_eos: bool = True,
    ) -> List[int]:
        """Encode *text* to a list of token ids."""
        ids = [self._char_to_id.get(c, self.UNK) for c in text]
        if add_bos:
            ids = [self.BOS] + ids
        if add_eos:
            ids = ids + [self.EOS]
        return ids

    def decode(self, ids) -> str:
        """Decode a sequence of ids back to text.

        Special tokens (PAD, BOS, EOS, UNK) are silently dropped.
        """
        parts: List[str] = []
        for tok in ids:
            ch = self._id_to_char.get(int(tok))
            if ch is not None:
                parts.append(ch)
        return "".join(parts)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class QuantumCodeLLMConfig:
    """Hyper-parameters for :class:`QuantumCodeLLM`."""

    vocab_size: int = 104  # matches CodeTokenizer().vocab_size
    d_model: int = 256
    n_heads: int = 8
    n_layers: int = 6
    n_qubits: int = 4  # used when backend != 'classical'
    max_seq_len: int = 512
    backend: str = "classical"  # 'classical' | 'quantum'


# ---------------------------------------------------------------------------
# Transformer building blocks
# ---------------------------------------------------------------------------


class _CausalSelfAttention(nn.Module):
    """Multi-head causal self-attention."""

    def __init__(self, d_model: int, n_heads: int, max_seq_len: int) -> None:
        super().__init__()
        assert d_model % n_heads == 0, "d_model must be divisible by n_heads"
        self.attn = nn.MultiheadAttention(d_model, n_heads, batch_first=True)
        # Causal mask (upper-triangular, excluding diagonal)
        self.register_buffer(
            "_causal_mask",
            torch.triu(torch.ones(max_seq_len, max_seq_len), diagonal=1).bool(),
            persistent=False,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        T = x.shape[1]
        mask = self._causal_mask[:T, :T]  # type: ignore[index]
        out, _ = self.attn(x, x, x, attn_mask=mask, is_causal=True)
        return out


class _FeedForward(nn.Module):
    def __init__(self, d_model: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_model, 4 * d_model),
            nn.GELU(),
            nn.Linear(4 * d_model, d_model),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class _TransformerBlock(nn.Module):
    def __init__(self, d_model: int, n_heads: int, max_seq_len: int) -> None:
        super().__init__()
        self.norm1 = nn.LayerNorm(d_model)
        self.attn = _CausalSelfAttention(d_model, n_heads, max_seq_len)
        self.norm2 = nn.LayerNorm(d_model)
        self.ff = _FeedForward(d_model)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.attn(self.norm1(x))
        x = x + self.ff(self.norm2(x))
        return x


# ---------------------------------------------------------------------------
# Main model
# ---------------------------------------------------------------------------


class QuantumCodeLLM(nn.Module):
    """GPT-style code language model with an optional quantum backend.

    When ``config.backend == 'classical'`` all layers are standard PyTorch.
    Other backend values are reserved for quantum extensions.
    """

    def __init__(self, config: QuantumCodeLLMConfig) -> None:
        super().__init__()
        self.config = config
        self.backend: str = config.backend

        self.token_emb = nn.Embedding(config.vocab_size, config.d_model)
        self.pos_emb = nn.Embedding(config.max_seq_len, config.d_model)
        self.blocks = nn.ModuleList(
            [
                _TransformerBlock(config.d_model, config.n_heads, config.max_seq_len)
                for _ in range(config.n_layers)
            ]
        )
        self.norm = nn.LayerNorm(config.d_model)
        self.head = nn.Linear(config.d_model, config.vocab_size, bias=False)

        # Weight tying
        self.head.weight = self.token_emb.weight

        self._init_weights()

    def _init_weights(self) -> None:
        for module in self.modules():
            if isinstance(module, (nn.Linear, nn.Embedding)):
                nn.init.normal_(module.weight, mean=0.0, std=0.02)
                if isinstance(module, nn.Linear) and module.bias is not None:
                    nn.init.zeros_(module.bias)

    # ------------------------------------------------------------------
    # Forward / generate
    # ------------------------------------------------------------------

    def forward(self, tokens: torch.Tensor) -> torch.Tensor:
        """Compute logits for *tokens* (B, T).

        Raises
        ------
        ValueError
            If sequence length exceeds ``config.max_seq_len``.
        """
        if tokens.dim() != 2:
            raise ValueError(
                f"tokens must be 2-D (B, T), got shape {tuple(tokens.shape)}"
            )
        _B, T = tokens.shape
        if T > self.config.max_seq_len:
            raise ValueError(
                f"Sequence length {T} exceeds max_seq_len {self.config.max_seq_len}."
            )
        positions = torch.arange(T, device=tokens.device).unsqueeze(0)
        x = self.token_emb(tokens) + self.pos_emb(positions)
        for block in self.blocks:
            x = block(x)
        x = self.norm(x)
        return self.head(x)

    @torch.no_grad()
    def generate(
        self,
        prompt: torch.Tensor,
        temperature: float = 1.0,
        top_k: int = 50,
        max_new_tokens: int = 50,
    ) -> torch.Tensor:
        """Auto-regressive generation from *prompt* (1, T).

        Raises
        ------
        ValueError
            For invalid *temperature*, *top_k*, or *prompt* shape.
        """
        if temperature <= 0:
            raise ValueError(f"temperature must be > 0, got {temperature}")
        if top_k < 0:
            raise ValueError(f"top_k must be >= 0, got {top_k}")
        if prompt.dim() != 2 or prompt.shape[0] != 1:
            raise ValueError(
                f"prompt must have shape (1, T), got {tuple(prompt.shape)}"
            )

        generated = prompt.clone()
        for _ in range(max_new_tokens):
            # Truncate to max_seq_len
            ctx = generated[:, -self.config.max_seq_len :]
            logits = self.forward(ctx)[:, -1, :]  # (1, vocab)
            logits = logits / temperature
            if top_k > 0:
                # Keep only top-k values
                top_vals, _ = torch.topk(logits, min(top_k, logits.shape[-1]))
                logits[logits < top_vals[:, -1:]] = float("-inf")
            probs = F.softmax(logits, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)
            generated = torch.cat([generated, next_token], dim=1)
        return generated


# ---------------------------------------------------------------------------
# Checkpoint helpers
# ---------------------------------------------------------------------------


def save_checkpoint(
    model: QuantumCodeLLM,
    tokenizer: CodeTokenizer,
    path,
    extra: Optional[Dict[str, Any]] = None,
) -> Path:
    """Save model + tokenizer metadata to *path*; returns the resolved Path."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "model_state_dict": model.state_dict(),
        "config": model.config,
        "tokenizer_vocab_size": tokenizer.vocab_size,
        "extra": extra or {},
    }
    torch.save(payload, path)
    return path


def load_checkpoint(
    path,
    backend_override: Optional[str] = None,
) -> Tuple["QuantumCodeLLM", "CodeTokenizer", Dict[str, Any]]:
    """Load a checkpoint saved by :func:`save_checkpoint` or a legacy payload.

    Parameters
    ----------
    path:
        Path to the ``.pt`` checkpoint file.
    backend_override:
        If given, override ``config.backend`` after loading.

    Returns
    -------
    (model, tokenizer, metadata)
    """
    path = Path(path)
    payload: Dict[str, Any] = torch.load(path, map_location="cpu", weights_only=False)

    if "model_state_dict" in payload:
        # ── New format (written by save_checkpoint) ──────────────────────
        config: QuantumCodeLLMConfig = payload["config"]
        if backend_override is not None:
            config = dataclasses.replace(config, backend=backend_override)
        model = QuantumCodeLLM(config)
        model.load_state_dict(payload["model_state_dict"])
        tokenizer = CodeTokenizer()
        metadata: Dict[str, Any] = {"extra": payload.get("extra", {})}

    elif "model_state" in payload:
        # ── Legacy format: {"model_state": ..., "config": ...} ──────────
        config = payload["config"]
        if backend_override is not None:
            config = dataclasses.replace(config, backend=backend_override)
        model = QuantumCodeLLM(config)
        model.load_state_dict(payload["model_state"])
        tokenizer = CodeTokenizer()
        metadata = {}

    else:
        raise ValueError(
            f"Unrecognised checkpoint format at {path}. "
            f"Keys found: {sorted(payload.keys())}"
        )

    model.eval()
    return model, tokenizer, metadata


# ---------------------------------------------------------------------------
# Convenience generate function (string interface)
# ---------------------------------------------------------------------------


def generate(
    model: QuantumCodeLLM,
    tokenizer: CodeTokenizer,
    prompt: str = "",
    temperature: float = 1.0,
    top_k: int = 50,
    max_new_tokens: int = 50,
) -> str:
    """Generate text continuation for *prompt* string.

    Raises
    ------
    ValueError
        For invalid *temperature* or *top_k*.
    """
    if temperature <= 0:
        raise ValueError(f"temperature must be > 0, got {temperature}")
    if top_k < 0:
        raise ValueError(f"top_k must be >= 0, got {top_k}")

    ids = tokenizer.encode(prompt, add_bos=True, add_eos=False)
    prompt_tensor = torch.tensor([ids], dtype=torch.long)
    output_tensor = model.generate(
        prompt_tensor,
        temperature=temperature,
        top_k=top_k,
        max_new_tokens=max_new_tokens,
    )
    new_ids = output_tensor[0, len(ids) :].tolist()
    return tokenizer.decode(new_ids)
