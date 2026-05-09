"""Regression tests for scripts/train_quantum_llm_chat.py constructor compatibility."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace


def _load_train_module():
    script_path = Path(__file__).parent.parent / "scripts" / "train_quantum_llm_chat.py"
    spec = importlib.util.spec_from_file_location("train_quantum_llm_chat", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _build_args():
    return SimpleNamespace(
        d_model=32,
        n_heads=2,
        seq_len=32,
        n_qubits=2,
        n_layers=2,
    )


def test_build_quantum_llm_prefers_n_transformer_layers_when_available():
    mod = _load_train_module()
    args = _build_args()

    class ModernModel:
        def __init__(
            self,
            vocab_size,
            d_model,
            n_heads,
            n_transformer_layers,
            max_seq_len,
            n_qubits,
            n_quantum_layers,
            dropout,
            use_quantum_attention,
            use_quantum_ffn,
        ):
            self.layer_count = n_transformer_layers

    model, kwarg = mod._build_quantum_llm(ModernModel, args, vocab_size=45)

    assert kwarg == "n_transformer_layers"
    assert model.layer_count == 2


def test_build_quantum_llm_falls_back_to_n_layers_for_legacy_signature():
    mod = _load_train_module()
    args = _build_args()

    class LegacyModel:
        def __init__(
            self,
            vocab_size,
            d_model,
            n_heads,
            n_layers,
            max_seq_len,
            n_qubits,
            n_quantum_layers,
            dropout,
            use_quantum_attention,
            use_quantum_ffn,
        ):
            self.layer_count = n_layers

    model, kwarg = mod._build_quantum_llm(LegacyModel, args, vocab_size=45)

    assert kwarg == "n_layers"
    assert model.layer_count == 2


def test_build_quantum_llm_defaults_to_n_transformer_layers_if_undetectable():
    mod = _load_train_module()
    args = _build_args()

    class FlexibleModel:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    model, kwarg = mod._build_quantum_llm(FlexibleModel, args, vocab_size=45)

    assert kwarg == "n_transformer_layers"
    assert model.kwargs["n_transformer_layers"] == 2
