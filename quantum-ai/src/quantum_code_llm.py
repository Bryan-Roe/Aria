"""quantum_code_llm.py — Self-contained Quantum LLM for Code Generation
========================================================================
Architecture: Hybrid quantum-classical transformer
  - Quantum kernel attention  : angle encoding + variational circuit as feature map
  - Quantum FFN middle layer  : variational quantum circuit between linear projections
  - Code-aware tokenizer      : character-level + keyword special tokens
  - Auto-detect backend       : Qiskit Aer (via pennylane-qiskit) → PennyLane
                                default.qubit → classical MLP fallback

Quick start
-----------
    from quantum_code_llm import train, generate

    model, tokenizer = train()          # train on built-in Python snippets
    print(generate(model, tokenizer, "def factorial(n):"))
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset

# ─────────────────────────────────────────────────────────────────────────────
# 1. QUANTUM BACKEND DETECTION
# ─────────────────────────────────────────────────────────────────────────────

QUANTUM_BACKEND: str = "classical"  # resolved at module load

try:
    import pennylane as qml  # type: ignore

    _PENNYLANE_AVAILABLE = True
except ImportError:
    _PENNYLANE_AVAILABLE = False

_QISKIT_AER_AVAILABLE = False
if _PENNYLANE_AVAILABLE:
    try:
        import pennylane_qiskit  # type: ignore  # noqa: F401
        from qiskit_aer import AerSimulator  # type: ignore  # noqa: F401

        _QISKIT_AER_AVAILABLE = True
    except ImportError:
        pass


def _make_device(n_qubits: int):
    """Return (backend_label, qml.device) using the best available backend."""
    if _QISKIT_AER_AVAILABLE:
        try:
            dev = qml.device(
                "qiskit.aer", wires=n_qubits, backend="statevector_simulator"
            )
            return "qiskit.aer", dev
        except Exception:
            pass
    if _PENNYLANE_AVAILABLE:
        dev = qml.device("default.qubit", wires=n_qubits)
        return "default.qubit", dev
    return "classical", None


# ─────────────────────────────────────────────────────────────────────────────
# 2. CODE TOKENIZER
# ─────────────────────────────────────────────────────────────────────────────

_CODE_KEYWORDS = [
    "def ",
    "class ",
    "return ",
    "import ",
    "from ",
    "with ",
    "    ",  # 4-space indent block
    "if ",
    "else:",
    "elif ",
    "for ",
    "while ",
    "try:",
    "except ",
    "pass",
    "None",
    "True",
    "False",
    "self.",
    "print(",
]


class CodeTokenizer:
    """Character-level tokenizer with code-aware multi-char special tokens.

    Token priority: special tokens → individual printable ASCII characters.
    """

    PAD, BOS, EOS, UNK = 0, 1, 2, 3

    def __init__(self, keywords: List[str] = _CODE_KEYWORDS) -> None:
        # Special single-char controls
        self._special = ["<PAD>", "<BOS>", "<EOS>", "<UNK>"]
        # Multi-char keyword tokens
        self._keywords: List[str] = sorted(keywords, key=len, reverse=True)
        # All printable ASCII characters
        self._chars: List[str] = [chr(c) for c in range(32, 127)]

        self._tok2id: dict[str, int] = {}
        idx = len(self._special)
        for kw in self._keywords:
            self._tok2id[kw] = idx
            idx += 1
        for ch in self._chars:
            if ch not in self._tok2id:
                self._tok2id[ch] = idx
                idx += 1

        self._id2tok: dict[int, str] = {v: k for k, v in self._tok2id.items()}
        self._id2tok[self.PAD] = ""
        self._id2tok[self.BOS] = ""
        self._id2tok[self.EOS] = ""
        self._id2tok[self.UNK] = "?"

        self.vocab_size: int = idx

    def encode(
        self, text: str, add_bos: bool = True, add_eos: bool = True
    ) -> List[int]:
        ids: List[int] = []
        if add_bos:
            ids.append(self.BOS)
        i = 0
        while i < len(text):
            matched = False
            for kw in self._keywords:
                if text[i : i + len(kw)] == kw:
                    ids.append(self._tok2id[kw])
                    i += len(kw)
                    matched = True
                    break
            if not matched:
                ch = text[i]
                ids.append(self._tok2id.get(ch, self.UNK))
                i += 1
        if add_eos:
            ids.append(self.EOS)
        return ids

    def decode(self, ids: List[int], skip_special: bool = True) -> str:
        parts: List[str] = []
        for i in ids:
            tok = self._id2tok.get(i, "")
            if skip_special and i in (self.PAD, self.BOS, self.EOS, self.UNK):
                continue
            parts.append(tok)
        return "".join(parts)

    @property
    def keywords(self) -> List[str]:
        return list(self._keywords)

    def to_dict(self) -> Dict[str, Any]:
        return {"keywords": self.keywords}

    @classmethod
    def from_dict(cls, payload: Optional[Dict[str, Any]]) -> "CodeTokenizer":
        if not payload:
            return cls()
        keywords = payload.get("keywords", _CODE_KEYWORDS)
        if not isinstance(keywords, list):
            keywords = list(_CODE_KEYWORDS)
        return cls(keywords=keywords)


# ─────────────────────────────────────────────────────────────────────────────
# 3. QUANTUM FEATURE MAP LAYER
# ─────────────────────────────────────────────────────────────────────────────


class QuantumFeatureMapLayer(nn.Module):
    """Variational quantum circuit used as a learnable feature map.

    Input  : (batch, n_qubits) — values normalised to [-π, π]
    Output : (batch, n_qubits) — Pauli-Z expectation values ∈ [-1, 1]

    When quantum is unavailable, a classical Tanh-bounded MLP is used.
    """

    def __init__(self, n_qubits: int, n_var_layers: int, device) -> None:
        super().__init__()
        self.n_qubits = n_qubits
        self.quantum = device is not None

        if self.quantum:

            @qml.qnode(device, interface="torch", diff_method="best")
            def _circuit(inputs, weights):
                qml.AngleEmbedding(inputs, wires=range(n_qubits), rotation="Y")
                qml.StronglyEntanglingLayers(weights, wires=range(n_qubits))
                return [qml.expval(qml.PauliZ(i)) for i in range(n_qubits)]

            weight_shapes = {"weights": (n_var_layers, n_qubits, 3)}
            self.qlayer = qml.qnn.TorchLayer(_circuit, weight_shapes)
        else:
            # Classical fallback: MLP that mimics bounded quantum outputs
            self.qlayer = nn.Sequential(
                nn.Linear(n_qubits, n_qubits * 4),
                nn.Tanh(),
                nn.Linear(n_qubits * 4, n_qubits),
                nn.Tanh(),
            )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (..., n_qubits)
        shape = x.shape
        x_flat = x.reshape(-1, self.n_qubits)
        out = self.qlayer(x_flat)
        if isinstance(out, list):
            out = torch.stack(out, dim=-1)
        return out.reshape(*shape[:-1], self.n_qubits)


# ─────────────────────────────────────────────────────────────────────────────
# 4. QUANTUM KERNEL ATTENTION
# ─────────────────────────────────────────────────────────────────────────────


class QuantumKernelAttention(nn.Module):
    """Multi-head attention where Q and K are projected through a quantum
    feature map before computing scaled dot-product attention.

         Q_quantum = φ(W_q · x)
         K_quantum = φ(W_k · x)
         scores    = Q_quantum · K_quantum^T / sqrt(n_qubits)

    φ is the QuantumFeatureMapLayer — a variational quantum circuit.
    V is projected classically as in standard attention.
    """

    def __init__(
        self,
        d_model: int,
        n_heads: int,
        n_qubits: int,
        n_var_layers: int,
        device,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        assert d_model % n_heads == 0
        self.n_heads = n_heads
        self.n_qubits = n_qubits
        self.head_dim = d_model // n_heads

        # Classical projections
        self.w_q = nn.Linear(d_model, n_heads * n_qubits, bias=False)
        self.w_k = nn.Linear(d_model, n_heads * n_qubits, bias=False)
        self.w_v = nn.Linear(d_model, d_model, bias=False)
        self.w_o = nn.Linear(d_model, d_model, bias=False)

        # Shared quantum feature map for Q and K
        self.q_map = QuantumFeatureMapLayer(n_qubits, n_var_layers, device)
        self.k_map = QuantumFeatureMapLayer(n_qubits, n_var_layers, device)

        self.drop = nn.Dropout(dropout)
        self.scale = math.sqrt(n_qubits)

    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        B, T, _ = x.shape

        # Project and reshape for multi-head: (B, T, n_heads, n_qubits)
        q = self.w_q(x).view(B, T, self.n_heads, self.n_qubits)
        k = self.w_k(x).view(B, T, self.n_heads, self.n_qubits)
        v = self.w_v(x).view(B, T, self.n_heads, self.head_dim)

        # Normalise input to quantum circuit range [-π, π]
        q_norm = torch.tanh(q) * math.pi
        k_norm = torch.tanh(k) * math.pi

        # Apply quantum feature map (batch over heads)
        q_q = self.q_map(q_norm)  # (B, T, n_heads, n_qubits)
        k_q = self.k_map(k_norm)  # (B, T, n_heads, n_qubits)

        # Transpose to (B, n_heads, T, n_qubits) for bmm
        q_q = q_q.transpose(1, 2)
        k_q = k_q.transpose(1, 2)
        v = v.transpose(1, 2)  # (B, n_heads, T, head_dim)

        # Scaled dot-product attention with quantum features
        scores = torch.matmul(q_q, k_q.transpose(-2, -1)) / self.scale  # (B, H, T, T)

        # Causal mask: prevent attending to future tokens
        causal = torch.triu(
            torch.ones(T, T, device=x.device, dtype=torch.bool), diagonal=1
        )
        scores = scores.masked_fill(causal.unsqueeze(0).unsqueeze(0), float("-inf"))
        if mask is not None:
            scores = scores.masked_fill(mask, float("-inf"))

        attn = self.drop(F.softmax(scores, dim=-1))
        out = torch.matmul(attn, v)  # (B, H, T, head_dim)

        # Recombine heads
        out = out.transpose(1, 2).contiguous().view(B, T, -1)
        return self.w_o(out)


# ─────────────────────────────────────────────────────────────────────────────
# 5. QUANTUM FEED-FORWARD NETWORK
# ─────────────────────────────────────────────────────────────────────────────


class QuantumFFN(nn.Module):
    """Feed-forward block with a quantum variational circuit in the middle.

         x → Linear(d_model → n_qubits) → quantum_circuit → Linear(n_qubits → d_model)

    The quantum circuit is a variational layer that can learn non-linear
    quantum feature transformations.  Classical paths are used when no
    quantum backend is available.
    """

    def __init__(
        self,
        d_model: int,
        n_qubits: int,
        n_var_layers: int,
        device,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.down = nn.Linear(d_model, n_qubits)
        self.quantum = QuantumFeatureMapLayer(n_qubits, n_var_layers, device)
        self.up = nn.Linear(n_qubits, d_model)
        self.gate = nn.Linear(d_model, d_model)  # classical gating
        self.norm_inner = nn.LayerNorm(n_qubits)
        self.drop = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Quantum path: project → quantum feature map → project back
        h = F.gelu(self.down(x))
        h = self.norm_inner(h)
        h_norm = torch.tanh(h) * math.pi  # normalise to [-π, π]
        h_q = self.quantum(h_norm)
        out = self.drop(self.up(h_q))
        # Gating: blend quantum output with classical gate
        gate = torch.sigmoid(self.gate(x))
        return gate * out + (1 - gate) * x


# ─────────────────────────────────────────────────────────────────────────────
# 6. QUANTUM TRANSFORMER BLOCK
# ─────────────────────────────────────────────────────────────────────────────


class QuantumTransformerBlock(nn.Module):
    """Pre-norm transformer block with quantum attention and quantum FFN."""

    def __init__(
        self,
        d_model: int,
        n_heads: int,
        n_qubits: int,
        n_var_layers: int,
        device,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.norm1 = nn.LayerNorm(d_model)
        self.attn = QuantumKernelAttention(
            d_model, n_heads, n_qubits, n_var_layers, device, dropout
        )
        self.norm2 = nn.LayerNorm(d_model)
        self.ffn = QuantumFFN(d_model, n_qubits, n_var_layers, device, dropout)

    def forward(
        self, x: torch.Tensor, mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        x = x + self.attn(self.norm1(x), mask)
        x = x + self.ffn(self.norm2(x))
        return x


# ─────────────────────────────────────────────────────────────────────────────
# 7. QUANTUM CODE LLM (MAIN MODEL)
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class QuantumCodeLLMConfig:
    vocab_size: int = 120
    d_model: int = 64
    n_heads: int = 4
    n_layers: int = 2
    n_qubits: int = 4
    n_var_layers: int = 2  # variational layers inside each quantum circuit
    max_seq_len: int = 128
    dropout: float = 0.1
    backend: str = "auto"  # "auto" | "qiskit.aer" | "default.qubit" | "classical"


class QuantumCodeLLM(nn.Module):
    """Quantum-enhanced language model for code generation.

    Embedding → Positional Encoding → N × QuantumTransformerBlock → Output head
    """

    def __init__(self, config: QuantumCodeLLMConfig) -> None:
        super().__init__()
        self.config = config

        # Resolve quantum backend
        if config.backend == "auto":
            self._backend_label, self._qdevice = _make_device(config.n_qubits)
        elif config.backend == "classical":
            self._backend_label, self._qdevice = "classical", None
        else:
            if not _PENNYLANE_AVAILABLE:
                raise RuntimeError(
                    "A non-classical backend was requested but PennyLane is not installed"
                )
            self._backend_label = config.backend
            self._qdevice = qml.device(config.backend, wires=config.n_qubits)

        # Embeddings
        self.token_emb = nn.Embedding(config.vocab_size, config.d_model, padding_idx=0)
        self.pos_emb = nn.Embedding(config.max_seq_len, config.d_model)
        self.emb_drop = nn.Dropout(config.dropout)

        # Transformer blocks
        self.blocks = nn.ModuleList(
            [
                QuantumTransformerBlock(
                    config.d_model,
                    config.n_heads,
                    config.n_qubits,
                    config.n_var_layers,
                    self._qdevice,
                    config.dropout,
                )
                for _ in range(config.n_layers)
            ]
        )

        self.norm = nn.LayerNorm(config.d_model)
        self.head = nn.Linear(config.d_model, config.vocab_size, bias=False)

        # Weight tying: output head shares weights with token embedding
        self.head.weight = self.token_emb.weight

        self._init_weights()

    def _init_weights(self) -> None:
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, nn.Embedding):
                nn.init.normal_(m.weight, std=0.02)

    def forward(
        self, input_ids: torch.Tensor, mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Args:
            input_ids : (B, T) token indices
            mask      : (B, 1, T, T) optional padding mask

        Returns:
            logits : (B, T, vocab_size)
        """
        B, T = input_ids.shape
        if T > self.config.max_seq_len:
            raise ValueError(
                f"input length {T} exceeds max_seq_len={self.config.max_seq_len}; "
                "truncate input_ids before calling forward"
            )
        tok = self.token_emb(input_ids)
        pos = self.pos_emb(torch.arange(T, device=input_ids.device).unsqueeze(0))
        x = self.emb_drop(tok + pos)

        for block in self.blocks:
            x = block(x, mask)

        x = self.norm(x)
        return self.head(x)

    @torch.no_grad()
    def generate(
        self,
        prompt_ids: torch.Tensor,
        max_new_tokens: int = 64,
        temperature: float = 0.8,
        top_k: int = 40,
        eos_id: int = 2,
    ) -> torch.Tensor:
        """Autoregressively generate tokens using temperature + top-k sampling."""
        if prompt_ids.ndim != 2 or prompt_ids.shape[0] != 1:
            raise ValueError("prompt_ids must have shape (1, T)")
        if temperature <= 0:
            raise ValueError("temperature must be > 0")
        if top_k < 0:
            raise ValueError("top_k must be >= 0")

        self.eval()
        ids = prompt_ids.clone()  # (1, T)
        for _ in range(max_new_tokens):
            # Truncate to max_seq_len
            ids_cond = ids[:, -self.config.max_seq_len :]
            logits = self.forward(ids_cond)  # (1, T, vocab)
            next_logits = logits[:, -1, :] / temperature  # (1, vocab)

            # Top-k filtering
            if top_k > 0:
                k = min(top_k, next_logits.shape[-1])
                kth_val = torch.topk(next_logits, k).values[:, -1, None]
                next_logits = next_logits.masked_fill(
                    next_logits < kth_val, float("-inf")
                )

            probs = F.softmax(next_logits, dim=-1)
            next_id = torch.multinomial(probs, num_samples=1)  # (1, 1)
            ids = torch.cat([ids, next_id], dim=1)
            if next_id.item() == eos_id:
                break
        return ids

    @property
    def backend(self) -> str:
        return self._backend_label

    def parameter_count(self) -> dict:
        total = sum(p.numel() for p in self.parameters())
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        return {"total": total, "trainable": trainable}


# ─────────────────────────────────────────────────────────────────────────────
# 8. BUILT-IN CODE DATASET
# ─────────────────────────────────────────────────────────────────────────────

_PYTHON_SNIPPETS = [
    "def add(a, b):\n    return a + b\n",
    "def subtract(a, b):\n    return a - b\n",
    "def multiply(x, y):\n    return x * y\n",
    "def divide(x, y):\n    if y == 0:\n        return None\n    return x / y\n",
    "def square(n):\n    return n * n\n",
    "def cube(n):\n    return n * n * n\n",
    "def is_even(n):\n    return n % 2 == 0\n",
    "def is_odd(n):\n    return n % 2 != 0\n",
    "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)\n",
    "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n - 1) + fibonacci(n - 2)\n",
    "def max_value(lst):\n    return max(lst)\n",
    "def min_value(lst):\n    return min(lst)\n",
    "def sum_list(lst):\n    return sum(lst)\n",
    "def reverse_string(s):\n    return s[::-1]\n",
    "def to_upper(s):\n    return s.upper()\n",
    "def to_lower(s):\n    return s.lower()\n",
    "def count_chars(s):\n    return len(s)\n",
    "def greet(name):\n    return 'Hello, ' + name + '!'\n",
    "class Counter:\n    def __init__(self):\n        self.count = 0\n    def increment(self):\n        self.count += 1\n    def get(self):\n        return self.count\n",
    "class Stack:\n    def __init__(self):\n        self.items = []\n    def push(self, item):\n        self.items.append(item)\n    def pop(self):\n        return self.items.pop()\n    def is_empty(self):\n        return len(self.items) == 0\n",
    "def bubble_sort(lst):\n    n = len(lst)\n    for i in range(n):\n        for j in range(n - i - 1):\n            if lst[j] > lst[j + 1]:\n                lst[j], lst[j + 1] = lst[j + 1], lst[j]\n    return lst\n",
    "def binary_search(lst, target):\n    low, high = 0, len(lst) - 1\n    while low <= high:\n        mid = (low + high) // 2\n        if lst[mid] == target:\n            return mid\n        elif lst[mid] < target:\n            low = mid + 1\n        else:\n            high = mid - 1\n    return -1\n",
    "def flatten(lst):\n    result = []\n    for item in lst:\n        if isinstance(item, list):\n            result.extend(flatten(item))\n        else:\n            result.append(item)\n    return result\n",
    "def gcd(a, b):\n    while b:\n        a, b = b, a % b\n    return a\n",
    "def lcm(a, b):\n    return a * b // gcd(a, b)\n",
    "def is_prime(n):\n    if n < 2:\n        return False\n    for i in range(2, int(n ** 0.5) + 1):\n        if n % i == 0:\n            return False\n    return True\n",
    "def clamp(value, lo, hi):\n    return max(lo, min(hi, value))\n",
    "def average(lst):\n    return sum(lst) / len(lst)\n",
    "def unique(lst):\n    return list(set(lst))\n",
    "def zip_dicts(keys, values):\n    return dict(zip(keys, values))\n",
]


class CodeDataset(Dataset):
    """Next-token prediction dataset from code snippets.

    Each sample is a sequence of max_seq_len tokens.  The target is the
    input shifted by one position.
    """

    def __init__(
        self,
        tokenizer: CodeTokenizer,
        snippets: List[str] = _PYTHON_SNIPPETS,
        seq_len: int = 64,
    ) -> None:
        self.tokenizer = tokenizer
        self.seq_len = seq_len
        # Concatenate all snippets into one long token stream
        full_text = "\n".join(snippets) + "\n"
        self.tokens = tokenizer.encode(full_text, add_bos=False, add_eos=False)

    def __len__(self) -> int:
        return max(0, len(self.tokens) - self.seq_len - 1)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        chunk = self.tokens[idx : idx + self.seq_len + 1]
        # Pad if needed (last chunk)
        while len(chunk) < self.seq_len + 1:
            chunk.append(CodeTokenizer.PAD)
        x = torch.tensor(chunk[:-1], dtype=torch.long)
        y = torch.tensor(chunk[1:], dtype=torch.long)
        return x, y


# ─────────────────────────────────────────────────────────────────────────────
# 9. TRAINER
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class TrainConfig:
    n_epochs: int = 5
    batch_size: int = 8
    lr: float = 3e-3
    weight_decay: float = 1e-4
    warmup_steps: int = 50
    seq_len: int = 64
    grad_clip: float = 1.0
    log_every: int = 20
    device: str = "cpu"
    seed: int = 42
    extra_snippets: List[str] = field(default_factory=list)


class QuantumCodeTrainer:
    """Training loop for QuantumCodeLLM."""

    def __init__(
        self,
        model: QuantumCodeLLM,
        tokenizer: CodeTokenizer,
        train_cfg: TrainConfig,
    ) -> None:
        self.model = model.to(train_cfg.device)
        self.tokenizer = tokenizer
        self.cfg = train_cfg
        self._device = torch.device(train_cfg.device)

        snippets = _PYTHON_SNIPPETS + train_cfg.extra_snippets
        dataset = CodeDataset(tokenizer, snippets, seq_len=train_cfg.seq_len)
        self.loader = DataLoader(
            dataset,
            batch_size=train_cfg.batch_size,
            shuffle=True,
            drop_last=True,
        )

        self.optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=train_cfg.lr,
            weight_decay=train_cfg.weight_decay,
        )
        total_steps = len(self.loader) * train_cfg.n_epochs
        self.scheduler = torch.optim.lr_scheduler.OneCycleLR(
            self.optimizer,
            max_lr=train_cfg.lr,
            total_steps=max(1, total_steps),
            pct_start=0.1,
            anneal_strategy="cos",
        )

    def train(self) -> List[dict]:
        """Run the training loop.  Returns per-epoch metric dicts."""
        torch.manual_seed(self.cfg.seed)
        random.seed(self.cfg.seed)
        np.random.seed(self.cfg.seed)

        history: List[dict] = []
        step = 0

        for epoch in range(1, self.cfg.n_epochs + 1):
            self.model.train()
            epoch_loss = 0.0
            t0 = time.time()

            for batch_idx, (x, y) in enumerate(self.loader):
                x, y = x.to(self._device), y.to(self._device)

                logits = self.model(x)  # (B, T, vocab)
                B, T, V = logits.shape
                loss = F.cross_entropy(
                    logits.view(B * T, V),
                    y.view(B * T),
                    ignore_index=CodeTokenizer.PAD,
                )

                self.optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(self.model.parameters(), self.cfg.grad_clip)
                self.optimizer.step()
                self.scheduler.step()

                epoch_loss += loss.item()
                step += 1

                if step % self.cfg.log_every == 0:
                    lr_now = self.scheduler.get_last_lr()[0]
                    perp = math.exp(min(loss.item(), 20))
                    print(
                        f"  step {step:>5d} | loss {loss.item():.4f} "
                        f"| ppl {perp:.1f} | lr {lr_now:.2e}"
                    )

            avg_loss = epoch_loss / max(1, len(self.loader))
            elapsed = time.time() - t0
            print(
                f"Epoch {epoch}/{self.cfg.n_epochs} — "
                f"avg loss {avg_loss:.4f} | ppl {math.exp(min(avg_loss, 20)):.1f} "
                f"| {elapsed:.1f}s"
            )
            history.append(
                {"epoch": epoch, "loss": avg_loss, "ppl": math.exp(min(avg_loss, 20))}
            )

        return history


# ─────────────────────────────────────────────────────────────────────────────
# 10. PUBLIC ENTRY POINTS
# ─────────────────────────────────────────────────────────────────────────────


def train(
    model_cfg: Optional[dict] = None,
    train_cfg: Optional[dict] = None,
    extra_snippets: Optional[List[str]] = None,
) -> Tuple[QuantumCodeLLM, CodeTokenizer]:
    """Train a QuantumCodeLLM and return (model, tokenizer).

    Args:
        model_cfg : kwargs for QuantumCodeLLMConfig (e.g. n_qubits, d_model)
        train_cfg : kwargs for TrainConfig (e.g. n_epochs, lr)
        extra_snippets : additional Python code strings to train on

    Example::

        model, tok = train({"n_qubits": 4, "d_model": 64}, {"n_epochs": 3})
        print(generate(model, tok, "def hello("))
    """
    model_cfg = model_cfg or {}
    train_cfg = train_cfg or {}
    extra_snippets = extra_snippets or []

    tokenizer = CodeTokenizer()
    mcfg = QuantumCodeLLMConfig(vocab_size=tokenizer.vocab_size, **model_cfg)
    model = QuantumCodeLLM(mcfg)

    print(f"QuantumCodeLLM ready — backend: {model.backend}")
    params = model.parameter_count()
    print(f"Parameters: {params['total']:,} total, {params['trainable']:,} trainable")
    print(f"Vocab size: {tokenizer.vocab_size}")

    tcfg = TrainConfig(extra_snippets=extra_snippets, **train_cfg)
    trainer = QuantumCodeTrainer(model, tokenizer, tcfg)

    print(f"\nStarting training ({tcfg.n_epochs} epochs) ...")
    trainer.train()
    return model, tokenizer


def save_checkpoint(
    model: QuantumCodeLLM,
    tokenizer: CodeTokenizer,
    checkpoint_path: str | Path,
    extra: Optional[Dict[str, Any]] = None,
) -> Path:
    """Persist model + config + tokenizer metadata to a checkpoint file."""
    path = Path(checkpoint_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "model_state": model.state_dict(),
        "config": asdict(model.config),
        "tokenizer": tokenizer.to_dict(),
        "backend": model.backend,
        "saved_at": time.time(),
        "extra": extra or {},
    }
    torch.save(payload, path)
    return path


def load_checkpoint(
    checkpoint_path: str | Path,
    map_location: str | torch.device = "cpu",
    backend_override: Optional[str] = None,
) -> Tuple[QuantumCodeLLM, CodeTokenizer, Dict[str, Any]]:
    """Load a checkpoint created by save_checkpoint.

    Also supports legacy payloads where config was serialized as QuantumCodeLLMConfig.
    """
    path = Path(checkpoint_path)
    if not path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {path}")

    payload = torch.load(path, map_location=map_location, weights_only=False)
    if "model_state" not in payload:
        raise ValueError(f"Invalid checkpoint payload: missing model_state in {path}")

    tokenizer = CodeTokenizer.from_dict(payload.get("tokenizer"))

    raw_config = payload.get("config")
    if isinstance(raw_config, QuantumCodeLLMConfig):
        config = raw_config
    elif isinstance(raw_config, dict):
        config = QuantumCodeLLMConfig(**raw_config)
    else:
        raise ValueError(f"Invalid checkpoint payload: missing valid config in {path}")

    config.vocab_size = tokenizer.vocab_size
    if backend_override is not None:
        config.backend = backend_override

    model = QuantumCodeLLM(config)
    model.load_state_dict(payload["model_state"])
    model.eval()

    metadata = {
        "path": str(path),
        "backend": payload.get("backend", model.backend),
        "saved_at": payload.get("saved_at"),
        "extra": payload.get("extra", {}),
    }
    return model, tokenizer, metadata


def generate(
    model: QuantumCodeLLM,
    tokenizer: CodeTokenizer,
    prompt: str = "def ",
    max_new_tokens: int = 80,
    temperature: float = 0.8,
    top_k: int = 40,
    device: str = "cpu",
) -> str:
    """Generate code continuation from a text prompt.

    Example::

        code = generate(model, tokenizer, "def factorial(n):", max_new_tokens=60)
        print(code)
    """
    if temperature <= 0:
        raise ValueError("temperature must be > 0")
    if top_k < 0:
        raise ValueError("top_k must be >= 0")

    model.eval()
    ids = tokenizer.encode(prompt, add_bos=True, add_eos=False)
    input_tensor = torch.tensor([ids], dtype=torch.long, device=device)
    with torch.no_grad():
        out_ids = model.generate(
            input_tensor,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_k=top_k,
            eos_id=tokenizer.EOS,
        )
    # Strip the prompt prefix, decode only new tokens
    new_ids = out_ids[0, len(ids) :].tolist()
    return prompt + tokenizer.decode(new_ids)


__all__ = [
    "CodeTokenizer",
    "CodeDataset",
    "QuantumFeatureMapLayer",
    "QuantumKernelAttention",
    "QuantumFFN",
    "QuantumTransformerBlock",
    "QuantumCodeLLMConfig",
    "QuantumCodeLLM",
    "TrainConfig",
    "QuantumCodeTrainer",
    "train",
    "generate",
    "save_checkpoint",
    "load_checkpoint",
]
