"""Unit tests for ai-projects/chat-cli/src/quantum_provider.py."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

pytest.importorskip("torch", reason="torch is not installed")
import torch  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
CHAT_CLI_SRC = REPO_ROOT / "ai-projects" / "chat-cli" / "src"
if str(CHAT_CLI_SRC) not in sys.path:
    sys.path.insert(0, str(CHAT_CLI_SRC))

_QP_PATH = CHAT_CLI_SRC / "quantum_provider.py"
_spec = importlib.util.spec_from_file_location("_test_quantum_provider", _QP_PATH)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Unable to load quantum_provider module from {_QP_PATH}")
quantum_provider = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(quantum_provider)


@pytest.mark.unit
def test_resolve_checkpoint_path_prefers_best(tmp_path: Path) -> None:
    provider = quantum_provider.QuantumLLMChatProvider.__new__(
        quantum_provider.QuantumLLMChatProvider
    )
    provider.model_path = tmp_path

    (tmp_path / "final_model.pt").write_bytes(b"x")
    (tmp_path / "best_quantum_llm.pt").write_bytes(b"x")

    resolved = provider._resolve_checkpoint_path()
    assert resolved.name == "best_quantum_llm.pt"


@pytest.mark.unit
def test_resolve_checkpoint_path_uses_status_metadata_first(tmp_path: Path) -> None:
    provider = quantum_provider.QuantumLLMChatProvider.__new__(
        quantum_provider.QuantumLLMChatProvider
    )
    provider.model_path = tmp_path

    status_payload = {
        "best_checkpoint_path": "best_quantum_llm.pt",
        "checkpoint_path": "final_model.pt",
    }
    (tmp_path / "status.json").write_text(json.dumps(status_payload), encoding="utf-8")
    (tmp_path / "final_model.pt").write_bytes(b"x")
    (tmp_path / "best_quantum_llm.pt").write_bytes(b"x")

    resolved = provider._resolve_checkpoint_path()
    assert resolved.name == "best_quantum_llm.pt"


@pytest.mark.unit
def test_resolve_checkpoint_path_accepts_direct_file(tmp_path: Path) -> None:
    checkpoint = tmp_path / "some_model.pt"
    checkpoint.write_bytes(b"x")

    provider = quantum_provider.QuantumLLMChatProvider.__new__(
        quantum_provider.QuantumLLMChatProvider
    )
    provider.model_path = checkpoint

    resolved = provider._resolve_checkpoint_path()
    assert resolved == checkpoint


@pytest.mark.unit
def test_derive_model_config_modern_schema() -> None:
    provider = quantum_provider.QuantumLLMChatProvider.__new__(
        quantum_provider.QuantumLLMChatProvider
    )

    cfg = provider._derive_model_config(
        {
            "model_config": {
                "vocab_size": 320,
                "d_model": 96,
                "n_heads": 6,
                "n_transformer_layers": 3,
                "n_qubits": 5,
                "n_quantum_layers": 2,
                "max_seq_len": 64,
                "entanglement": "linear",
                "dropout": 0.15,
                "use_quantum_attention": False,
                "use_quantum_ffn": True,
                "tie_embeddings": False,
            }
        }
    )

    assert cfg["vocab_size"] == 320
    assert cfg["n_transformer_layers"] == 3
    assert cfg["max_seq_len"] == 64
    assert cfg["entanglement"] == "linear"
    assert cfg["use_quantum_attention"] is False


@pytest.mark.unit
def test_derive_model_config_legacy_schema() -> None:
    provider = quantum_provider.QuantumLLMChatProvider.__new__(
        quantum_provider.QuantumLLMChatProvider
    )

    cfg = provider._derive_model_config(
        {
            "vocab_size": 256,
            "d_model": 64,
            "n_heads": 4,
            "n_layers": 2,
            "n_qubits": 4,
            "n_quantum_layers": 1,
            "max_seq_length": 128,
        }
    )

    assert cfg["vocab_size"] == 256
    assert cfg["n_transformer_layers"] == 2
    assert cfg["max_seq_len"] == 128


@pytest.mark.unit
def test_encode_text_uses_char_map_then_ord_fallback() -> None:
    provider = quantum_provider.QuantumLLMChatProvider.__new__(
        quantum_provider.QuantumLLMChatProvider
    )
    provider.device = torch.device("cpu")
    provider.vocab_size = 256
    provider.char_to_idx = {"A": 7}

    encoded = provider._encode_text("AB")
    assert encoded.tolist() == [7, ord("B") % 256]


@pytest.mark.unit
def test_decode_tokens_ascii_fallback_when_no_idx_map() -> None:
    provider = quantum_provider.QuantumLLMChatProvider.__new__(
        quantum_provider.QuantumLLMChatProvider
    )
    provider.idx_to_char = {}

    out = provider._decode_tokens(torch.tensor([72, 10, 105], dtype=torch.long))
    assert out == "Hi"


@pytest.mark.unit
def test_generate_prefers_model_generate() -> None:
    class _FakeModel:
        def generate(
            self, context, max_new_tokens: int, temperature: float, top_k: int
        ):
            # Preserve prompt tokens and append 'Hi'
            base = context[0].tolist()
            return torch.tensor([base + [72, 105]], dtype=torch.long)

    provider = quantum_provider.QuantumLLMChatProvider.__new__(
        quantum_provider.QuantumLLMChatProvider
    )
    provider.model = _FakeModel()
    provider.temperature = 0.8
    provider.max_seq_len = 128
    provider.device = torch.device("cpu")
    provider.vocab_size = 256
    provider.char_to_idx = {}
    provider.idx_to_char = {}

    out = provider._generate("AB", max_tokens=4)
    assert out == "Hi"


@pytest.mark.unit
def test_stream_response_preserves_text_in_nonempty_chunks() -> None:
    provider = quantum_provider.QuantumLLMChatProvider.__new__(
        quantum_provider.QuantumLLMChatProvider
    )

    response = "🔬 [Quantum LLM] hello world\nnext line"
    chunks = list(provider._stream_response(response))

    assert chunks
    assert all(chunks)
    assert "".join(chunks) == response
    assert any(len(chunk) > 1 for chunk in chunks)


@pytest.mark.unit
def test_stream_response_empty_text_yields_no_chunks() -> None:
    provider = quantum_provider.QuantumLLMChatProvider.__new__(
        quantum_provider.QuantumLLMChatProvider
    )

    chunks = list(provider._stream_response(""))
    assert chunks == []


@pytest.mark.unit
def test_create_quantum_llm_provider_returns_choice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _DummyProvider:
        def __init__(
            self, model_path: str, temperature: float, max_output_tokens: int, **kwargs
        ):
            self.model_path = model_path
            self.temperature = temperature
            self.max_output_tokens = max_output_tokens

    monkeypatch.setattr(quantum_provider, "QuantumLLMChatProvider", _DummyProvider)
    monkeypatch.setattr(quantum_provider, "QUANTUM_LLM_AVAILABLE", True)

    provider, info = quantum_provider.create_quantum_llm_provider(
        model_path="data_out/quantum_llm_training",
        temperature=0.55,
        max_output_tokens=42,
    )

    assert provider.model_path == "data_out/quantum_llm_training"
    assert info.name == "quantum-llm"
    assert "quantum-llm" in info.model


@pytest.mark.unit
def test_create_quantum_llm_provider_raises_when_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(quantum_provider, "QUANTUM_LLM_AVAILABLE", False)
    with pytest.raises(ImportError, match="QuantumLLM not available"):
        quantum_provider.create_quantum_llm_provider("data_out/model")
