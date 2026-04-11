"""
Quantum LLM Chat Provider
Uses a trained quantum-enhanced language model for chat interactions
Integrates real quantum circuits in the attention mechanism
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, Iterator, List

import torch
import torch.nn.functional as F

from chat_providers import BaseChatProvider  # type: ignore[attr-defined]
from chat_providers import ProviderChoice, RoleMessage

# Add quantum-ml to path
repo_root = Path(__file__).resolve().parent.parent.parent.parent
quantum_ml_path = repo_root / "ai-projects" / "quantum-ml"
quantum_ml_src = quantum_ml_path / "src"
for p in [str(quantum_ml_path), str(quantum_ml_src)]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from quantum_transformer import QUANTUM_AVAILABLE, QuantumLLM

    QUANTUM_LLM_AVAILABLE = True
except ImportError as e:
    QuantumLLM = None  # type: ignore[assignment]
    QUANTUM_AVAILABLE = False
    QUANTUM_LLM_AVAILABLE = False
    logging.warning(f"QuantumLLM not available: {e}")


logger = logging.getLogger(__name__)


class QuantumLLMChatProvider(BaseChatProvider):
    """
    Chat provider using a trained quantum-enhanced language model.

    Loads a checkpoint from training and uses the quantum LLM for text generation.
    Quantum circuits are integrated in the attention mechanism.
    """

    def __init__(
        self,
        model_path: str,
        temperature: float = 0.8,
        max_output_tokens: int = 200,
        **kwargs,
    ):
        super().__init__()
        self.model_path = Path(model_path)
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Load model
        self.model = None
        self.model_config: Dict[str, Any] = {}
        self.char_to_idx = {}
        self.idx_to_char = {}
        self.vocab_size = 0
        self.max_seq_len = 128

        if not QUANTUM_LLM_AVAILABLE:
            logger.error("QuantumLLM not available - cannot initialize provider")
            raise ImportError("QuantumLLM not available")

        try:
            self._load_model()
            logger.info(f"Quantum LLM loaded from {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load quantum LLM: {e}")
            raise

    def _resolve_checkpoint_path(self) -> Path:
        """Resolve checkpoint file path from directory or direct file input."""
        if self.model_path.is_file():
            return self.model_path

        status_file = self.model_path / "status.json"
        if status_file.exists():
            try:
                import json

                with open(status_file, "r", encoding="utf-8") as status_handle:
                    status_payload = json.load(status_handle)

                checkpoint_ref = (
                    status_payload.get("best_checkpoint_path")
                    or status_payload.get("checkpoint_path")
                    or status_payload.get("last_checkpoint_path")
                )
                if checkpoint_ref:
                    checkpoint_path = Path(checkpoint_ref)
                    if not checkpoint_path.is_absolute():
                        direct_candidate = self.model_path / checkpoint_path
                        checkpoint_path = (
                            direct_candidate
                            if direct_candidate.exists()
                            else repo_root / checkpoint_path
                        )
                    if checkpoint_path.exists():
                        return checkpoint_path
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Failed to read Quantum LLM status metadata from %s: %s",
                    status_file,
                    exc,
                )

        candidates = [
            self.model_path / "best_quantum_llm.pt",
            self.model_path / "quantum_llm_checkpoint.pt",
            self.model_path / "final_model.pt",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate

        attempted = "\n  - " + "\n  - ".join(str(p) for p in candidates)
        raise FileNotFoundError(
            f"No Quantum LLM checkpoint found in {self.model_path}. Tried:{attempted}"
        )

    def _derive_model_config(self, checkpoint: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize model config across legacy and modern checkpoint schemas."""
        model_cfg = checkpoint.get("model_config", {})

        if isinstance(model_cfg, dict) and model_cfg:
            return {
                "vocab_size": int(
                    model_cfg.get("vocab_size", checkpoint.get("vocab_size", 256))
                ),
                "d_model": int(model_cfg.get("d_model", checkpoint.get("d_model", 64))),
                "n_heads": int(model_cfg.get("n_heads", checkpoint.get("n_heads", 4))),
                "n_transformer_layers": int(
                    model_cfg.get(
                        "n_transformer_layers",
                        model_cfg.get("n_layers", checkpoint.get("n_layers", 2)),
                    )
                ),
                "n_qubits": int(
                    model_cfg.get("n_qubits", checkpoint.get("n_qubits", 4))
                ),
                "n_quantum_layers": int(
                    model_cfg.get(
                        "n_quantum_layers", checkpoint.get("n_quantum_layers", 2)
                    )
                ),
                "max_seq_len": int(
                    model_cfg.get(
                        "max_seq_len",
                        model_cfg.get(
                            "max_seq_length", checkpoint.get("max_seq_length", 128)
                        ),
                    )
                ),
                "entanglement": model_cfg.get("entanglement", "circular"),
                "dropout": float(model_cfg.get("dropout", 0.0)),
                "use_quantum_attention": bool(
                    model_cfg.get("use_quantum_attention", True)
                ),
                "use_quantum_ffn": bool(model_cfg.get("use_quantum_ffn", True)),
                "tie_embeddings": bool(model_cfg.get("tie_embeddings", True)),
            }

        # Legacy checkpoint layout
        return {
            "vocab_size": int(checkpoint.get("vocab_size", 256)),
            "d_model": int(checkpoint.get("d_model", 64)),
            "n_heads": int(checkpoint.get("n_heads", 4)),
            "n_transformer_layers": int(
                checkpoint.get("n_layers", checkpoint.get("n_transformer_layers", 2))
            ),
            "n_qubits": int(checkpoint.get("n_qubits", 4)),
            "n_quantum_layers": int(checkpoint.get("n_quantum_layers", 2)),
            "max_seq_len": int(
                checkpoint.get("max_seq_length", checkpoint.get("max_seq_len", 128))
            ),
            "entanglement": checkpoint.get("entanglement", "circular"),
            "dropout": float(checkpoint.get("dropout", 0.0)),
            "use_quantum_attention": bool(
                checkpoint.get("use_quantum_attention", True)
            ),
            "use_quantum_ffn": bool(checkpoint.get("use_quantum_ffn", True)),
            "tie_embeddings": bool(checkpoint.get("tie_embeddings", True)),
        }

    def _load_model(self):
        """Load the trained quantum LLM from checkpoint."""
        if QuantumLLM is None:
            raise RuntimeError("QuantumLLM class is unavailable")

        checkpoint_path = self._resolve_checkpoint_path()
        logger.info(f"Loading checkpoint from {checkpoint_path}")
        checkpoint = torch.load(checkpoint_path, map_location=self.device)

        model_state_dict = checkpoint.get("model_state_dict") or checkpoint.get(
            "state_dict"
        )
        if not isinstance(model_state_dict, dict):
            raise KeyError("Checkpoint missing 'model_state_dict' or 'state_dict'.")

        self.model_config = self._derive_model_config(checkpoint)
        self.vocab_size = int(self.model_config["vocab_size"])
        self.max_seq_len = int(self.model_config["max_seq_len"])

        # Build model using the current quantum_transformer API.
        if hasattr(QuantumLLM, "from_config"):
            self.model = QuantumLLM.from_config(
                {"quantum_transformer": self.model_config}
            ).to(self.device)
        else:  # defensive fallback for older implementations
            self.model = QuantumLLM(
                vocab_size=self.model_config["vocab_size"],
                d_model=self.model_config["d_model"],
                n_heads=self.model_config["n_heads"],
                n_transformer_layers=self.model_config["n_transformer_layers"],
                n_qubits=self.model_config["n_qubits"],
                n_quantum_layers=self.model_config["n_quantum_layers"],
                max_seq_len=self.model_config["max_seq_len"],
                entanglement=self.model_config["entanglement"],
                dropout=self.model_config["dropout"],
                use_quantum_attention=self.model_config["use_quantum_attention"],
                use_quantum_ffn=self.model_config["use_quantum_ffn"],
                tie_embeddings=self.model_config["tie_embeddings"],
            ).to(self.device)

        incompat = self.model.load_state_dict(model_state_dict, strict=False)
        missing_keys = getattr(incompat, "missing_keys", [])
        unexpected_keys = getattr(incompat, "unexpected_keys", [])
        if missing_keys or unexpected_keys:
            logger.warning(
                "Checkpoint compatibility: missing_keys=%d unexpected_keys=%d",
                len(missing_keys),
                len(unexpected_keys),
            )

        # Optional tokenizer maps from older checkpoints.
        char_to_idx = checkpoint.get("char_to_idx")
        idx_to_char = checkpoint.get("idx_to_char")
        if isinstance(char_to_idx, dict) and isinstance(idx_to_char, dict):
            self.char_to_idx = {str(k): int(v) for k, v in char_to_idx.items()}
            self.idx_to_char = {int(k): str(v) for k, v in idx_to_char.items()}
        else:
            # Lightweight fallback mapping when checkpoint has no tokenizer metadata.
            fallback_vocab = min(self.vocab_size, 128)
            self.char_to_idx = {chr(i): i for i in range(fallback_vocab)}
            self.idx_to_char = {i: chr(i) for i in range(fallback_vocab)}

        self.model.eval()
        logger.info(
            "Model loaded: vocab=%d, qubits=%d, layers=%d, max_seq_len=%d",
            self.vocab_size,
            self.model_config["n_qubits"],
            self.model_config["n_transformer_layers"],
            self.max_seq_len,
        )

    def _encode_text(self, text: str) -> torch.Tensor:
        """Encode text to token IDs."""
        if not text:
            return torch.tensor([0], dtype=torch.long, device=self.device)

        indices: List[int] = []
        for c in text:
            if self.char_to_idx:
                indices.append(self.char_to_idx.get(c, ord(c) % self.vocab_size))
            else:
                indices.append(ord(c) % self.vocab_size)
        return torch.tensor(indices, dtype=torch.long, device=self.device)

    def _decode_tokens(self, tokens: torch.Tensor) -> str:
        """Decode token IDs to text."""
        indices = tokens.cpu().tolist()
        chars = []
        for i in indices:
            i = int(i)
            if self.idx_to_char:
                ch = self.idx_to_char.get(i)
                if ch is not None:
                    chars.append(ch)
                    continue

            # Fallback ASCII decode if tokenizer metadata isn't available.
            ascii_i = i % 128
            chars.append(chr(ascii_i) if 32 <= ascii_i < 127 else "")
        return "".join(chars)

    def _generate(self, prompt: str, max_tokens: int) -> str:
        """Generate text using the quantum LLM."""
        if self.model is None:
            raise RuntimeError("Quantum model not loaded")

        model = self.model

        # Encode prompt
        context = self._encode_text(prompt)

        # Limit context length
        max_context = max(1, int(self.max_seq_len))
        if len(context) > max_context:
            context = context[-max_context:]

        context = context.unsqueeze(0)  # Add batch dimension

        # Prefer model-native generation when available.
        if hasattr(self.model, "generate"):
            with torch.no_grad():
                generated_ids = model.generate(
                    context,
                    max_new_tokens=int(max_tokens),
                    temperature=float(self.temperature),
                    top_k=20,
                )

            new_token_ids = generated_ids[0, context.size(1) :]
            return self._decode_tokens(new_token_ids)

        generated = []

        with torch.no_grad():
            for _ in range(max_tokens):
                # Forward pass
                logits = model(context)  # [1, seq_len, vocab_size]

                # Get logits for last position
                next_logits = logits[0, -1, :] / self.temperature

                # Sample next token
                probs = F.softmax(next_logits, dim=-1)
                next_token = torch.multinomial(probs, num_samples=1)

                # Append to context
                context = torch.cat([context, next_token.unsqueeze(0)], dim=1)

                # Keep context window manageable
                if context.size(1) > max_context:
                    context = context[:, -max_context:]

                # Decode and collect
                char = self.idx_to_char.get(int(next_token.item()), "")
                generated.append(char)

                # Stop on newline after some content
                if char == "\n" and len(generated) > 20:
                    break

        return "".join(generated)

    def complete(
        self, messages: List[RoleMessage], stream: bool = False
    ) -> str | Iterator[str]:
        """
        Generate a response using the quantum LLM.

        Args:
            messages: Conversation history
            stream: Whether to stream the response

        Returns:
            Response string or iterator of response chunks
        """
        if not self.model:
            error_msg = "Model not loaded"
            logger.error(error_msg)
            return error_msg if not stream else iter([error_msg])

        # Build prompt from conversation
        prompt_parts = []
        for msg in messages[-5:]:  # Use last 5 messages for context
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "user":
                prompt_parts.append(f"User: {content}\n")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}\n")

        prompt_parts.append("Assistant: ")
        prompt = "".join(prompt_parts)

        # Generate response
        try:
            response = self._generate(prompt, self.max_output_tokens)
            response = response.strip()

            # Add quantum indicator
            response = f"🔬 [Quantum LLM] {response}"

            if stream:
                return self._stream_response(response)
            else:
                return response

        except Exception as e:
            error_msg = f"Generation failed: {e}"
            logger.error(error_msg)
            return error_msg if not stream else iter([error_msg])

    def _stream_response(self, response: str) -> Iterator[str]:
        """Stream a response in small, non-empty chunks.

        Chunking on whitespace/newlines reduces overhead versus yielding one
        character at a time while still keeping the UI responsive.
        """
        text = str(response)
        if not text:
            return

        buffer: list[str] = []
        for char in text:
            buffer.append(char)
            should_flush = (
                char == "\n"
                or len(buffer) >= 16
                or (char.isspace() and len(buffer) >= 8)
            )
            if should_flush:
                chunk = "".join(buffer)
                if chunk:
                    yield chunk
                buffer.clear()

        if buffer:
            yield "".join(buffer)


def create_quantum_llm_provider(
    model_path: str, temperature: float = 0.8, max_output_tokens: int = 200, **kwargs
) -> tuple[QuantumLLMChatProvider, ProviderChoice]:
    """
    Factory function to create a quantum LLM chat provider.

    Args:
        model_path: Path to trained model directory
        temperature: Sampling temperature
        max_output_tokens: Maximum tokens to generate
        **kwargs: Additional arguments

    Returns:
        Tuple of (provider instance, provider info)
    """
    if not QUANTUM_LLM_AVAILABLE:
        raise ImportError("QuantumLLM not available - cannot create provider")

    provider = QuantumLLMChatProvider(
        model_path=model_path,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        **kwargs,
    )

    info = ProviderChoice(
        name="quantum-llm",
        model=f"quantum-llm ({Path(model_path).name})",
    )

    return provider, info
