"""Unit tests for the quantum code LLM module."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "quantum-ai" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from quantum_code_llm import (  # noqa: E402
    CodeTokenizer,
    QuantumCodeLLM,
    QuantumCodeLLMConfig,
    generate,
)


@pytest.fixture
def tiny_model() -> tuple[QuantumCodeLLM, CodeTokenizer]:
    tokenizer = CodeTokenizer()
    config = QuantumCodeLLMConfig(
        vocab_size=tokenizer.vocab_size,
        d_model=32,
        n_heads=4,
        n_layers=1,
        n_qubits=2,
        backend="classical",
    )
    model = QuantumCodeLLM(config)
    return model, tokenizer


@pytest.mark.unit
def test_tokenizer_round_trip() -> None:
    tokenizer = CodeTokenizer()
    text = "def add(a,b): return a+b"
    ids = tokenizer.encode(text, add_bos=False, add_eos=False)
    assert tokenizer.decode(ids) == text


@pytest.mark.unit
def test_forward_rejects_too_long_input(
    tiny_model: tuple[QuantumCodeLLM, CodeTokenizer],
) -> None:
    model, tokenizer = tiny_model
    token_ids = tokenizer.encode("def add(a,b): return a+b", add_bos=False, add_eos=False)
    too_long = torch.tensor([token_ids + [tokenizer.EOS] * (model.config.max_seq_len + 1)], dtype=torch.long)

    with pytest.raises(ValueError, match="exceeds max_seq_len"):
        model.forward(too_long)


@pytest.mark.unit
def test_generate_parameter_validation(
    tiny_model: tuple[QuantumCodeLLM, CodeTokenizer],
) -> None:
    model, tokenizer = tiny_model
    prompt = torch.tensor([[tokenizer.BOS, tokenizer.EOS]], dtype=torch.long)

    with pytest.raises(ValueError, match="temperature"):
        model.generate(prompt, temperature=0)

    with pytest.raises(ValueError, match="top_k"):
        model.generate(prompt, top_k=-1)

    with pytest.raises(ValueError, match=r"shape \(1, T\)"):
        model.generate(prompt.repeat(2, 1))

    with pytest.raises(ValueError, match="temperature"):
        generate(model, tokenizer, prompt="def ", temperature=0)

    with pytest.raises(ValueError, match="top_k"):
        generate(model, tokenizer, prompt="def ", top_k=-5)


@pytest.mark.unit
def test_checkpoint_round_trip(tmp_path: Path, tiny_model: tuple[QuantumCodeLLM, CodeTokenizer]) -> None:
    model, tokenizer = tiny_model
    checkpoint_path = tmp_path / "quantum_code_llm.pt"

    saved_path = save_checkpoint(model, tokenizer, checkpoint_path, extra={"run": "unit"})
    assert saved_path.exists()

    loaded_model, loaded_tokenizer, metadata = load_checkpoint(checkpoint_path)

    assert loaded_tokenizer.vocab_size == tokenizer.vocab_size
    assert metadata["extra"]["run"] == "unit"

    original_weight = next(model.parameters()).detach()
    restored_weight = next(loaded_model.parameters()).detach()
    assert torch.allclose(original_weight, restored_weight)


@pytest.mark.unit
def test_load_legacy_checkpoint_payload(tmp_path: Path, tiny_model: tuple[QuantumCodeLLM, CodeTokenizer]) -> None:
    model, _ = tiny_model
    checkpoint_path = tmp_path / "legacy.pt"

    # Simulate the old payload shape used before save_checkpoint/load_checkpoint.
    torch.save({"model_state": model.state_dict(), "config": model.config}, checkpoint_path)

    loaded_model, loaded_tokenizer, _ = load_checkpoint(
        checkpoint_path,
        backend_override="classical",
    )

    assert loaded_model.backend == "classical"
    assert loaded_tokenizer.vocab_size == model.config.vocab_size
