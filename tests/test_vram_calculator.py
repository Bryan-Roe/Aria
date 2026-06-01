"""Tests for scripts/vram_calculator.py — GPU-aware batch size calculator."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from vram_calculator import (
    _BYTES_PER_PARAM,
    KNOWN_MODELS,
    _get_arch,
    calculate_safe_batch_size,
    estimate_activation_memory_gb,
    estimate_lora_overhead_gb,
    estimate_model_memory_gb,
    probe_vram,
)

# Ensure scripts/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

_GPU_24GB = {
    "available": True,
    "total_gb": 24.0,
    "free_gb": 20.0,
    "used_gb": 4.0,
    "gpu_name": "NVIDIA RTX 4090",
    "source": "test",
}

_GPU_8GB = {
    "available": True,
    "total_gb": 8.0,
    "free_gb": 6.0,
    "used_gb": 2.0,
    "gpu_name": "NVIDIA RTX 3070",
    "source": "test",
}

_NO_GPU = {
    "available": False,
    "total_gb": 0.0,
    "free_gb": 0.0,
    "used_gb": 0.0,
    "gpu_name": "No GPU",
    "source": "none",
}


# ---------------------------------------------------------------------------
# estimate_model_memory_gb
# ---------------------------------------------------------------------------


class TestEstimateModelMemory:
    def test_fp16_1b_params(self):
        # 1B params × 2 bytes / 1e9 ≈ 1.86 GB
        gb = estimate_model_memory_gb(1.0, "fp16")
        assert 1.7 < gb < 2.0

    def test_fp32_larger_than_fp16(self):
        fp32 = estimate_model_memory_gb(3.82, "fp32")
        fp16 = estimate_model_memory_gb(3.82, "fp16")
        assert fp32 == pytest.approx(fp16 * 2, rel=0.01)

    def test_int4_smaller_than_int8(self):
        assert estimate_model_memory_gb(7.0, "int4") < estimate_model_memory_gb(7.0, "int8")

    def test_unknown_dtype_defaults(self):
        # _BYTES_PER_PARAM.get(unknown, 2) → fp16 behaviour
        gpu = estimate_model_memory_gb(1.0, "fp16")
        unk = estimate_model_memory_gb(1.0, "unknown_dtype")
        assert gpu == unk

    def test_all_known_dtypes(self):
        for dtype in _BYTES_PER_PARAM:
            gb = estimate_model_memory_gb(1.0, dtype)
            assert gb > 0


# ---------------------------------------------------------------------------
# estimate_lora_overhead_gb
# ---------------------------------------------------------------------------


class TestEstimateLoraOverhead:
    def test_positive(self):
        gb = estimate_lora_overhead_gb(16, 2048, 22)
        assert gb > 0

    def test_higher_rank_more_memory(self):
        low = estimate_lora_overhead_gb(8, 2048, 22)
        high = estimate_lora_overhead_gb(64, 2048, 22)
        assert high > low * 4  # rank doubled twice → 4× overhead

    def test_more_layers_more_memory(self):
        fewer = estimate_lora_overhead_gb(16, 2048, 12)
        more = estimate_lora_overhead_gb(16, 2048, 32)
        assert more > fewer


# ---------------------------------------------------------------------------
# estimate_activation_memory_gb
# ---------------------------------------------------------------------------


class TestEstimateActivationMemory:
    def test_scales_with_batch(self):
        bs1 = estimate_activation_memory_gb(1, 512, 2048, 22)
        bs4 = estimate_activation_memory_gb(4, 512, 2048, 22)
        assert bs4 == pytest.approx(bs1 * 4, rel=0.01)

    def test_scales_with_seq_len(self):
        s256 = estimate_activation_memory_gb(1, 256, 2048, 22)
        s512 = estimate_activation_memory_gb(1, 512, 2048, 22)
        # rounding to 3 dp means ratio is approximate; allow 5% tolerance
        assert s512 == pytest.approx(s256 * 2, rel=0.05)

    def test_positive(self):
        assert estimate_activation_memory_gb(4, 512, 2048, 22) > 0


# ---------------------------------------------------------------------------
# _get_arch
# ---------------------------------------------------------------------------


class TestGetArch:
    def test_known_tinyllama(self):
        hidden_size, num_layers = _get_arch("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
        assert hidden_size == 2048 and num_layers == 22

    def test_known_phi_mini(self):
        hidden_size, num_layers = _get_arch("microsoft/phi-3.5-mini-instruct")
        assert hidden_size == 3072 and num_layers == 32

    def test_unknown_returns_defaults(self):
        hidden_size, num_layers = _get_arch("some-unknown-model/v1")
        assert hidden_size == 2048 and num_layers == 24


# ---------------------------------------------------------------------------
# calculate_safe_batch_size — no GPU
# ---------------------------------------------------------------------------


class TestCalculateSafeBatchNoGPU:
    def test_available_false(self):
        result = calculate_safe_batch_size(
            model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            vram_info=_NO_GPU,
        )
        assert result["available"] is False

    def test_safe_batch_is_1(self):
        result = calculate_safe_batch_size(vram_info=_NO_GPU)
        assert result["safe_batch_size"] == 1

    def test_has_error_key(self):
        result = calculate_safe_batch_size(vram_info=_NO_GPU)
        assert "error" in result

    def test_model_memory_still_computed(self):
        result = calculate_safe_batch_size(
            model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            vram_info=_NO_GPU,
        )
        assert result["model_memory_gb"] > 0


# ---------------------------------------------------------------------------
# calculate_safe_batch_size — with GPU
# ---------------------------------------------------------------------------


class TestCalculateSafeBatchWithGPU:
    def test_available_true(self):
        result = calculate_safe_batch_size(
            model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            vram_info=_GPU_24GB,
        )
        assert result["available"] is True

    def test_batch_size_positive(self):
        result = calculate_safe_batch_size(
            model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            vram_info=_GPU_24GB,
        )
        assert result["safe_batch_size"] >= 1

    def test_large_model_on_small_gpu_batch_1(self):
        # Llama-7B on 8GB with some already used — should be batch 1
        result = calculate_safe_batch_size(
            model_name="meta-llama/Llama-2-7b-hf",
            vram_info=_GPU_8GB,
        )
        assert result["safe_batch_size"] == 1

    def test_small_model_on_large_gpu_high_batch(self):
        result = calculate_safe_batch_size(
            model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            vram_info=_GPU_24GB,
            lora_rank=8,
            seq_len=256,
        )
        assert result["safe_batch_size"] >= 8

    def test_all_required_keys_present(self):
        result = calculate_safe_batch_size(
            model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            vram_info=_GPU_24GB,
        )
        for key in [
            "available",
            "gpu_name",
            "total_gb",
            "free_gb",
            "model_memory_gb",
            "lora_overhead_gb",
            "activation_memory_gb",
            "total_estimated_gb",
            "safe_batch_size",
            "reasoning",
        ]:
            assert key in result, f"Missing key: {key}"

    def test_reasoning_is_list_of_strings(self):
        result = calculate_safe_batch_size(
            model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            vram_info=_GPU_24GB,
        )
        assert isinstance(result["reasoning"], list)
        assert all(isinstance(r, str) for r in result["reasoning"])

    def test_params_b_override(self):
        result = calculate_safe_batch_size(params_b=0.5, vram_info=_GPU_24GB)
        assert result["params_b"] == 0.5

    def test_dtype_fp32_reduces_batch(self):
        r_fp16 = calculate_safe_batch_size(
            model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            vram_info=_GPU_8GB,
            dtype="fp16",
        )
        r_fp32 = calculate_safe_batch_size(
            model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            vram_info=_GPU_8GB,
            dtype="fp32",
        )
        # fp32 needs 2× memory, so batch should be ≤ fp16 batch
        assert r_fp32["safe_batch_size"] <= r_fp16["safe_batch_size"]

    def test_total_estimated_covers_model_and_lora(self):
        result = calculate_safe_batch_size(
            model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            vram_info=_GPU_24GB,
        )
        floor = result["model_memory_gb"] + result["lora_overhead_gb"]
        assert result["total_estimated_gb"] > floor


# ---------------------------------------------------------------------------
# probe_vram — smoke test (may or may not have GPU)
# ---------------------------------------------------------------------------


class TestProbeVram:
    def test_returns_dict(self):
        result = probe_vram()
        assert isinstance(result, dict)

    def test_has_available_key(self):
        result = probe_vram()
        assert "available" in result

    def test_consistent_types(self):
        result = probe_vram()
        assert isinstance(result["available"], bool)
        assert isinstance(result["total_gb"], float)
        assert isinstance(result["free_gb"], float)
        assert isinstance(result["source"], str)


# ---------------------------------------------------------------------------
# KNOWN_MODELS / _BYTES_PER_PARAM constants
# ---------------------------------------------------------------------------


class TestConstants:
    def test_known_models_nonempty(self):
        assert len(KNOWN_MODELS) > 0

    def test_all_params_positive(self):
        for name, params in KNOWN_MODELS.items():
            assert params > 0, f"Invalid param count for {name}"

    def test_bytes_per_param_keys(self):
        for dtype in ("fp16", "fp32", "bf16", "int8", "int4"):
            assert dtype in _BYTES_PER_PARAM
