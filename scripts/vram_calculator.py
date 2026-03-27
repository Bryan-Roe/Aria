"""
VRAM-Aware Batch Size Calculator for QAI Dashboard (Phase 26 Feature 2).

Probes available GPU VRAM and recommends safe training batch sizes, taking into
account model size, LoRA adapter overhead, and activation memory.

Usage:
    python scripts/vram_calculator.py
    python scripts/vram_calculator.py --model TinyLlama/TinyLlama-1.1B-Chat-v1.0
    python scripts/vram_calculator.py --params-b 7.0 --lora-rank 16 --seq-len 512
    python scripts/vram_calculator.py --json
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Optional

# ---------------------------------------------------------------------------
# Known model parameter counts (billions)
# ---------------------------------------------------------------------------
KNOWN_MODELS: dict[str, float] = {
    "microsoft/phi-3.5-mini-instruct": 3.82,
    "microsoft/phi-3-mini-4k-instruct": 3.82,
    "microsoft/phi-2": 2.7,
    "TinyLlama/TinyLlama-1.1B-Chat-v1.0": 1.1,
    "TinyLlama/TinyLlama-1.1B": 1.1,
    "meta-llama/Llama-2-7b-hf": 7.0,
    "meta-llama/Llama-2-13b-hf": 13.0,
    "mistralai/Mistral-7B-v0.1": 7.0,
    "mistralai/Mixtral-8x7B-v0.1": 46.7,
    "tiiuae/falcon-7b": 7.0,
    "google/flan-t5-large": 0.78,
    "gpt2": 0.117,
    "gpt2-medium": 0.345,
}

# Hidden-size and layer counts for memory estimates per model family
_MODEL_ARCH: dict[str, tuple[int, int]] = {
    # (hidden_size, num_layers)
    "microsoft/phi-3.5-mini": (3072, 32),
    "microsoft/phi-3-mini": (3072, 32),
    "microsoft/phi-2": (2560, 32),
    "TinyLlama/TinyLlama": (2048, 22),
    "meta-llama/Llama-2-7b": (4096, 32),
    "meta-llama/Llama-2-13b": (5120, 40),
    "mistralai/Mistral-7B": (4096, 32),
    "tiiuae/falcon-7b": (4544, 32),
    "gpt2": (768, 12),
}

_VRAM_HEADROOM = 0.20  # Reserve 20% for OS/driver
_BYTES_PER_PARAM = {"fp32": 4, "fp16": 2, "bf16": 2, "int8": 1, "int4": 0.5}


# ---------------------------------------------------------------------------
# VRAM probing
# ---------------------------------------------------------------------------

def probe_vram() -> dict:
    """Probe GPU VRAM via torch (preferred) or nvidia-smi fallback.

    Returns a dict with keys: ``available``, ``total_gb``, ``free_gb``,
    ``used_gb``, ``gpu_name``, ``source``.  On no-GPU systems returns
    ``available=False``.
    """
    # --- Try torch first ---
    try:
        import torch  # type: ignore[import]
        if torch.cuda.is_available():
            props = torch.cuda.get_device_properties(0)
            total_b = props.total_memory
            reserved_b = torch.cuda.memory_reserved(0)
            allocated_b = torch.cuda.memory_allocated(0)
            free_b = total_b - reserved_b
            total_gb = total_b / 1024 ** 3
            free_gb = free_b / 1024 ** 3
            used_gb = allocated_b / 1024 ** 3
            return {
                "available": True,
                "total_gb": round(total_gb, 2),
                "free_gb": round(free_gb, 2),
                "used_gb": round(used_gb, 2),
                "gpu_name": props.name,
                "source": "torch",
            }
    except Exception:
        pass

    # --- Fallback: nvidia-smi ---
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.free,memory.total,memory.used",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = [p.strip() for p in result.stdout.strip().split(",")]
            if len(parts) >= 4:
                name = parts[0]
                free_mib = float(parts[1])
                total_mib = float(parts[2])
                used_mib = float(parts[3])
                return {
                    "available": True,
                    "total_gb": round(total_mib / 1024, 2),
                    "free_gb": round(free_mib / 1024, 2),
                    "used_gb": round(used_mib / 1024, 2),
                    "gpu_name": name,
                    "source": "nvidia-smi",
                }
    except Exception:
        pass

    return {
        "available": False,
        "total_gb": 0.0,
        "free_gb": 0.0,
        "used_gb": 0.0,
        "gpu_name": "No GPU",
        "source": "none",
    }


# ---------------------------------------------------------------------------
# Memory estimation helpers
# ---------------------------------------------------------------------------

def estimate_model_memory_gb(params_b: float, dtype: str = "fp16") -> float:
    """Convert billions of parameters to approximate GB of GPU memory."""
    bytes_per_param = _BYTES_PER_PARAM.get(dtype, 2)
    return round(params_b * 1e9 * bytes_per_param / 1024 ** 3, 2)


def estimate_lora_overhead_gb(
    lora_rank: int, hidden_size: int, num_layers: int
) -> float:
    """Approximate LoRA adapter memory: rank × 2 × hidden_size × layers × fp16."""
    lora_params = lora_rank * 2 * hidden_size * num_layers
    return round(lora_params * 2 / 1024 ** 3, 3)  # fp16 = 2 bytes


def estimate_activation_memory_gb(
    batch_size: int, seq_len: int, hidden_size: int, num_layers: int
) -> float:
    """Rough activation memory: batch × seq × hidden × layers × fp16."""
    activation_bytes = batch_size * seq_len * hidden_size * num_layers * 2
    return round(activation_bytes / 1024 ** 3, 3)


# ---------------------------------------------------------------------------
# Safe batch-size calculation
# ---------------------------------------------------------------------------

def _get_arch(model_name: str) -> tuple[int, int]:
    """Return (hidden_size, num_layers) for known model prefix or defaults."""
    for prefix, arch in _MODEL_ARCH.items():
        if model_name.startswith(prefix):
            return arch
    return (2048, 24)  # safe defaults for unknown models


def calculate_safe_batch_size(
    *,
    model_name: str = "",
    params_b: Optional[float] = None,
    lora_rank: int = 16,
    seq_len: int = 512,
    dtype: str = "fp16",
    vram_info: Optional[dict] = None,
) -> dict:
    """Return a dict with VRAM info, memory estimates, and safe batch size.

    Parameters
    ----------
    model_name: HuggingFace model name (used for param lookup and arch).
    params_b: Override parameter count in billions.
    lora_rank: LoRA rank for adapter overhead estimate.
    seq_len: Maximum sequence length for activation estimate.
    dtype: Precision — 'fp16', 'fp32', 'bf16', 'int8', 'int4'.
    vram_info: Pre-probed VRAM dict (omit to probe now).
    """
    if vram_info is None:
        vram_info = probe_vram()

    # Resolve parameter count
    if params_b is None:
        params_b = KNOWN_MODELS.get(model_name, 1.1)

    hidden_size, num_layers = _get_arch(model_name)

    # Memory estimates
    model_mem_gb = estimate_model_memory_gb(params_b, dtype)
    lora_mem_gb = estimate_lora_overhead_gb(lora_rank, hidden_size, num_layers)
    fixed_overhead_gb = model_mem_gb + lora_mem_gb

    if not vram_info.get("available"):
        return {
            "available": False,
            "gpu_name": vram_info.get("gpu_name", "No GPU"),
            "error": "No GPU detected",
            "safe_batch_size": 1,
            "model_memory_gb": model_mem_gb,
            "lora_overhead_gb": lora_mem_gb,
            "recommendation": "CPU-only mode — batch size 1 recommended.",
        }

    total_gb = vram_info["total_gb"]
    free_gb = vram_info["free_gb"]

    # Budget after headroom + fixed model/LoRA costs
    headroom_gb = total_gb * _VRAM_HEADROOM
    budget_gb = free_gb - headroom_gb - fixed_overhead_gb

    # Binary-search for the largest batch_size such that activation fits
    safe_batch = 1
    if budget_gb > 0:
        for bs in [32, 16, 12, 8, 6, 4, 2, 1]:
            activation_gb = estimate_activation_memory_gb(
                bs, seq_len, hidden_size, num_layers
            )
            if activation_gb <= budget_gb:
                safe_batch = bs
                break

    activation_at_safe = estimate_activation_memory_gb(
        safe_batch, seq_len, hidden_size, num_layers
    )
    total_estimated_gb = fixed_overhead_gb + activation_at_safe

    free_pct = round(free_gb / total_gb * 100, 1) if total_gb > 0 else 0.0

    reasoning: list[str] = []
    if not vram_info.get("available"):
        reasoning.append("No GPU — CPU-only mode.")
    else:
        reasoning.append(
            f"GPU: {vram_info.get('gpu_name', 'Unknown')} — "
            f"{free_gb:.1f} GB free of {total_gb:.1f} GB ({free_pct}%)"
        )
    reasoning.append(
        f"Model ({params_b:.1f}B {dtype}): ~{model_mem_gb:.1f} GB"
    )
    reasoning.append(
        f"LoRA overhead (rank={lora_rank}): ~{lora_mem_gb:.3f} GB")
    reasoning.append(
        f"Activations (bs={safe_batch}, seq={seq_len}): ~{activation_at_safe:.3f} GB"
    )
    reasoning.append(
        f"Total estimated: {total_estimated_gb:.1f} GB "
        f"(budget was {max(budget_gb, 0):.1f} GB with 20% headroom)"
    )

    return {
        "available": True,
        "gpu_name": vram_info.get("gpu_name", "Unknown"),
        "total_gb": total_gb,
        "free_gb": free_gb,
        "used_gb": vram_info.get("used_gb", 0.0),
        "free_pct": free_pct,
        "source": vram_info.get("source", ""),
        "model_name": model_name,
        "params_b": params_b,
        "dtype": dtype,
        "lora_rank": lora_rank,
        "seq_len": seq_len,
        "model_memory_gb": model_mem_gb,
        "lora_overhead_gb": lora_mem_gb,
        "activation_memory_gb": activation_at_safe,
        "total_estimated_gb": round(total_estimated_gb, 2),
        "safe_batch_size": safe_batch,
        "reasoning": reasoning,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="VRAM-Aware Batch Size Calculator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--model", default="", help="HuggingFace model name")
    p.add_argument(
        "--params-b",
        type=float,
        default=None,
        help="Override model parameter count in billions",
    )
    p.add_argument(
        "--lora-rank", type=int, default=16, help="LoRA rank (default: 16)"
    )
    p.add_argument(
        "--seq-len",
        type=int,
        default=512,
        help="Maximum sequence length (default: 512)",
    )
    p.add_argument(
        "--dtype",
        choices=list(_BYTES_PER_PARAM.keys()),
        default="fp16",
        help="Model precision (default: fp16)",
    )
    p.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Output JSON only (for scripting)",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    args = _build_parser().parse_args(argv)
    result = calculate_safe_batch_size(
        model_name=args.model,
        params_b=args.params_b,
        lora_rank=args.lora_rank,
        seq_len=args.seq_len,
        dtype=args.dtype,
    )

    if args.output_json:
        print(json.dumps(result, indent=2))
        return

    # Human-readable output
    print("\n=== VRAM-Aware Batch Size Calculator ===\n")
    if result.get("available"):
        print(f"GPU:              {result['gpu_name']}")
        print(
            f"VRAM:             {result['free_gb']:.1f} GB free / "
            f"{result['total_gb']:.1f} GB total ({result['free_pct']}%)"
        )
    else:
        print("GPU:              Not available (CPU mode)")
    print(
        f"\nModel:            {result.get('model_name') or '(unknown)'} ({result['params_b']:.1f}B params)")
    print(f"Precision:        {result['dtype']}")
    print(f"LoRA rank:        {result['lora_rank']}")
    print(f"Sequence length:  {result['seq_len']}")
    print(f"\nModel memory:     ~{result['model_memory_gb']:.1f} GB")
    print(f"LoRA overhead:    ~{result['lora_overhead_gb']:.3f} GB")
    print(f"Activations:      ~{result['activation_memory_gb']:.3f} GB")
    print(f"Total estimated:  ~{result['total_estimated_gb']:.1f} GB")
    print(f"\n>>> Safe batch size: {result['safe_batch_size']} <<<\n")
    print("Reasoning:")
    for r in result.get("reasoning", []):
        print(f"  • {r}")
    print()


if __name__ == "__main__":
    main()
