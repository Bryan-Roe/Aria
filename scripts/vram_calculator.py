#!/usr/bin/env python3
"""
VRAM Calculator - Estimate safe batch sizes for GPU training

Probes GPU memory and calculates maximum safe batch size based on:
- Available VRAM
- Model size (parameters)
- LoRA configuration (rank, alpha)
- Sequence length
- Mixed precision mode

Usage:
    python vram_calculator.py --model microsoft/Phi-3.5-mini-instruct --rank 16
    python vram_calculator.py --model microsoft/Phi-3.5-mini-instruct --rank 16 --seq-len 2048 --fp16
    python vram_calculator.py --list-gpus
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List


def get_gpu_info_torch() -> Optional[List[Dict[str, Any]]]:
    """Probe GPU info using torch.cuda (if available)."""
    try:
        import torch
        if not torch.cuda.is_available():
            return None
        
        gpus = []
        for i in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(i)
            mem_info = torch.cuda.mem_get_info(i)
            gpus.append({
                "id": i,
                "name": props.name,
                "total_memory_gb": props.total_memory / (1024**3),
                "free_memory_gb": mem_info[0] / (1024**3),
                "used_memory_gb": (props.total_memory - mem_info[0]) / (1024**3),
                "compute_capability": f"{props.major}.{props.minor}",
                "multi_processor_count": props.multi_processor_count
            })
        return gpus
    except ImportError:
        return None
    except Exception as e:
        print(f"Warning: torch.cuda failed: {e}", file=sys.stderr)
        return None


def get_gpu_info_nvidia_smi() -> Optional[List[Dict[str, Any]]]:
    """Probe GPU info using nvidia-smi (fallback)."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,name,memory.total,memory.free,memory.used", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            return None
        
        gpus = []
        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                continue
            parts = [p.strip() for p in line.split(',')]
            if len(parts) != 5:
                continue
            gpus.append({
                "id": int(parts[0]),
                "name": parts[1],
                "total_memory_gb": float(parts[2]) / 1024,
                "free_memory_gb": float(parts[3]) / 1024,
                "used_memory_gb": float(parts[4]) / 1024,
                "compute_capability": "unknown",
                "multi_processor_count": 0
            })
        return gpus
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Warning: nvidia-smi failed: {e}", file=sys.stderr)
        return None


def get_gpu_info() -> List[Dict[str, Any]]:
    """Get GPU info (try torch first, fallback to nvidia-smi)."""
    gpus = get_gpu_info_torch()
    if gpus:
        return gpus
    
    gpus = get_gpu_info_nvidia_smi()
    if gpus:
        return gpus
    
    return []


def estimate_model_memory(
    model_name: str,
    num_params_billions: Optional[float] = None,
    fp16: bool = False,
    quantize_4bit: bool = False
) -> Dict[str, Any]:
    """
    Estimate model memory requirements.
    
    Args:
        model_name: HuggingFace model name
        num_params_billions: Override number of parameters (billions)
        fp16: Use fp16 instead of fp32
        quantize_4bit: Use 4-bit quantization (BitsAndBytes)
    
    Returns:
        Dictionary with memory estimates
    """
    # Known model sizes (parameters in billions)
    known_models = {
        "microsoft/Phi-3.5-mini-instruct": 3.8,
        "microsoft/Phi-3-mini-4k-instruct": 3.8,
        "microsoft/Phi-3-mini-128k-instruct": 3.8,
        "microsoft/Phi-3-medium-4k-instruct": 14.0,
        "meta-llama/Llama-2-7b-hf": 7.0,
        "meta-llama/Llama-2-13b-hf": 13.0,
        "mistralai/Mistral-7B-v0.1": 7.3,
    }
    
    # Determine params
    if num_params_billions:
        params = num_params_billions
    elif model_name in known_models:
        params = known_models[model_name]
    else:
        # Guess from model name (e.g., "7b", "13b")
        import re
        match = re.search(r'(\d+\.?\d*)b', model_name.lower())
        if match:
            params = float(match.group(1))
        else:
            params = 3.0  # conservative fallback
    
    if quantize_4bit:
        bytes_per_param = 0.5  # 4-bit = 0.5 bytes
        precision = "4-bit"
    elif fp16:
        bytes_per_param = 2
        precision = "fp16"
    else:
        bytes_per_param = 4
        precision = "fp32"
    
    model_memory_gb = (params * 1e9 * bytes_per_param) / (1024**3)
    
    # Add overhead for optimizer states (2x for Adam), gradients, etc.
    # Conservative estimate: 3x model size for full training
    training_overhead = 3.0
    total_training_gb = model_memory_gb * training_overhead
    
    return {
        "model_name": model_name,
        "params_billions": params,
        "precision": precision,
        "model_memory_gb": round(model_memory_gb, 2),
        "training_memory_gb": round(total_training_gb, 2),
    }


def estimate_lora_memory(
    lora_rank: int,
    hidden_size: int = 3072,
    num_layers: int = 32,
    fp16: bool = False
) -> Dict[str, Any]:
    """
    Estimate LoRA adapter memory.
    
    Args:
        lora_rank: LoRA rank (r)
        hidden_size: Model hidden dimension
        num_layers: Number of transformer layers
        fp16: Use fp16 instead of fp32
    
    Returns:
        Dictionary with memory estimates
    """
    # LoRA adds 2 matrices per layer: A (hidden_size x rank) and B (rank x hidden_size)
    # Typically applied to q, k, v, o projections = 4 projections per layer
    params_per_layer = 4 * (hidden_size * lora_rank + lora_rank * hidden_size)
    total_params = params_per_layer * num_layers
    
    bytes_per_param = 2 if fp16 else 4
    lora_memory_gb = (total_params * bytes_per_param) / (1024**3)
    
    return {
        "lora_rank": lora_rank,
        "hidden_size": hidden_size,
        "num_layers": num_layers,
        "trainable_params_millions": round(total_params / 1e6, 2),
        "lora_memory_gb": round(lora_memory_gb, 2),
    }


def estimate_activation_memory(
    batch_size: int,
    seq_len: int,
    hidden_size: int = 3072,
    num_layers: int = 32,
    fp16: bool = False
) -> float:
    """
    Estimate activation memory (forward + backward pass).
    
    Args:
        batch_size: Batch size
        seq_len: Sequence length
        hidden_size: Model hidden dimension
        num_layers: Number of transformer layers
        fp16: Use fp16
    
    Returns:
        Memory in GB
    """
    bytes_per_element = 2 if fp16 else 4
    
    # Activations per layer (conservative estimate):
    # - Attention: batch_size * num_heads * seq_len * seq_len (attention scores)
    # - FFN: batch_size * seq_len * (hidden_size * 4) (intermediate activations)
    # Simplified: batch_size * seq_len * hidden_size * 2 per layer
    activations_per_layer = batch_size * seq_len * hidden_size * 2
    total_activations = activations_per_layer * num_layers
    
    # Gradients roughly equal activations (but only for LoRA params, not full model)
    # For LoRA, gradients are minimal since we don't backprop through frozen layers
    # Use 1.3x multiplier for activations + minimal gradients
    memory_gb = (total_activations * bytes_per_element * 1.3) / (1024**3)
    return round(memory_gb, 2)


def calculate_safe_batch_size(
    gpu_id: int = 0,
    model_name: str = "microsoft/Phi-3.5-mini-instruct",
    lora_rank: int = 16,
    seq_len: int = 2048,
    fp16: bool = True,
    quantize_4bit: bool = False,
    headroom: float = 0.2,
) -> Dict[str, Any]:
    """
    Calculate maximum safe batch size for given configuration.
    
    Args:
        gpu_id: GPU device ID
        model_name: HuggingFace model name
        lora_rank: LoRA rank
        seq_len: Sequence length
        fp16: Use fp16
        quantize_4bit: Use 4-bit quantization
        headroom: Reserve % of VRAM (default 20%)
    
    Returns:
        Dictionary with calculation results
    """
    gpus = get_gpu_info()
    if not gpus:
        return {"error": "No GPU found or unable to query GPU info"}
    
    if gpu_id >= len(gpus):
        return {"error": f"GPU {gpu_id} not found (only {len(gpus)} GPUs available)"}
    
    gpu = gpus[gpu_id]
    available_gb = gpu["free_memory_gb"] * (1 - headroom)
    
    # Estimate model memory
    model_mem = estimate_model_memory(model_name, fp16=fp16, quantize_4bit=quantize_4bit)
    
    # Estimate LoRA memory
    lora_mem = estimate_lora_memory(lora_rank, fp16=fp16)
    
    # Base memory (model + LoRA + overhead)
    # For LoRA training, we only train adapters, so optimizer states are much smaller
    # Use 1.2x multiplier for model + LoRA for conservative estimate
    base_memory_gb = (model_mem["model_memory_gb"] * 1.0 + lora_mem["lora_memory_gb"] * 1.2)
    
    # Calculate max batch size
    remaining_gb = available_gb - base_memory_gb
    if remaining_gb <= 0:
        return {
            "gpu": gpu,
            "model": model_mem,
            "lora": lora_mem,
            "base_memory_gb": round(base_memory_gb, 2),
            "available_gb": round(available_gb, 2),
            "max_batch_size": 0,
            "error": f"Not enough memory. Base: {base_memory_gb:.1f}GB, Available: {available_gb:.1f}GB"
        }
    
    # Binary search for max batch size
    batch_size = 1
    max_safe_batch = 1
    
    while batch_size <= 256:  # reasonable upper limit
        activation_mem = estimate_activation_memory(batch_size, seq_len, fp16=fp16)
        total_mem = base_memory_gb + activation_mem
        
        if total_mem <= available_gb:
            max_safe_batch = batch_size
            batch_size *= 2
        else:
            # Narrow down with linear search
            for bs in range(max_safe_batch + 1, batch_size):
                activation_mem = estimate_activation_memory(bs, seq_len, fp16=fp16)
                total_mem = base_memory_gb + activation_mem
                if total_mem <= available_gb:
                    max_safe_batch = bs
                else:
                    break
            break
    
    # Calculate memory usage at max batch
    activation_mem_at_max = estimate_activation_memory(max_safe_batch, seq_len, fp16=fp16)
    total_mem_at_max = base_memory_gb + activation_mem_at_max
    
    return {
        "gpu": gpu,
        "model": model_mem,
        "lora": lora_mem,
        "base_memory_gb": round(base_memory_gb, 2),
        "activation_memory_gb": round(activation_mem_at_max, 2),
        "total_memory_gb": round(total_mem_at_max, 2),
        "available_gb": round(available_gb, 2),
        "headroom_percent": int(headroom * 100),
        "max_batch_size": max_safe_batch,
        "recommended_batch_size": max(1, max_safe_batch // 2),  # conservative recommendation
        "config": {
            "seq_len": seq_len,
            "fp16": fp16,
            "lora_rank": lora_rank
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Calculate safe batch size for GPU training")
    parser.add_argument("--list-gpus", action="store_true", help="List available GPUs")
    parser.add_argument("--gpu", type=int, default=0, help="GPU device ID (default: 0)")
    parser.add_argument("--model", type=str, default="microsoft/Phi-3.5-mini-instruct", help="Model name")
    parser.add_argument("--rank", type=int, default=16, help="LoRA rank (default: 16)")
    parser.add_argument("--seq-len", type=int, default=2048, help="Sequence length (default: 2048)")
    parser.add_argument("--fp16", action="store_true", help="Use fp16 precision")
    parser.add_argument("--4bit", action="store_true", dest="quantize_4bit", help="Use 4-bit quantization (BitsAndBytes)")
    parser.add_argument("--headroom", type=float, default=0.2, help="Reserve % of VRAM (default: 0.2)")
    parser.add_argument("--quiet", action="store_true", help="Output JSON only")
    
    args = parser.parse_args()
    
    if args.list_gpus:
        gpus = get_gpu_info()
        if not gpus:
            print("No GPUs found", file=sys.stderr)
            sys.exit(1)
        
        if args.quiet:
            print(json.dumps({"gpus": gpus}, indent=2))
        else:
            print("\n=== Available GPUs ===")
            for gpu in gpus:
                print(f"[{gpu['id']}] {gpu['name']}")
                print(f"    Total: {gpu['total_memory_gb']:.1f}GB")
                print(f"    Free: {gpu['free_memory_gb']:.1f}GB ({gpu['free_memory_gb']/gpu['total_memory_gb']*100:.0f}%)")
                print(f"    Used: {gpu['used_memory_gb']:.1f}GB")
        return
    
    # Calculate safe batch size
    result = calculate_safe_batch_size(
        gpu_id=args.gpu,
        model_name=args.model,
        lora_rank=args.rank,
        seq_len=args.seq_len,
        fp16=args.fp16,
        quantize_4bit=args.quantize_4bit,
        headroom=args.headroom
    )
    
    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)
    
    if args.quiet:
        print(json.dumps(result, indent=2))
    else:
        print("\n=== GPU Info ===")
        print(f"Device: [{result['gpu']['id']}] {result['gpu']['name']}")
        print(f"Total VRAM: {result['gpu']['total_memory_gb']:.1f}GB")
        print(f"Free VRAM: {result['gpu']['free_memory_gb']:.1f}GB ({result['gpu']['free_memory_gb']/result['gpu']['total_memory_gb']*100:.0f}%)")
        print(f"Usable VRAM: {result['available_gb']:.1f}GB (after {result['headroom_percent']}% headroom)")
        
        print("\n=== Model Info ===")
        print(f"Model: {result['model']['model_name']}")
        print(f"Parameters: {result['model']['params_billions']}B")
        print(f"Precision: {result['model']['precision']}")
        print(f"Model Memory: {result['model']['model_memory_gb']:.1f}GB")
        
        print("\n=== LoRA Config ===")
        print(f"Rank: {result['lora']['lora_rank']}")
        print(f"Trainable Params: {result['lora']['trainable_params_millions']}M")
        print(f"LoRA Memory: {result['lora']['lora_memory_gb']:.2f}GB")
        
        print("\n=== Memory Breakdown ===")
        print(f"Base (Model + LoRA + Overhead): {result['base_memory_gb']:.1f}GB")
        print(f"Activations (at max batch): {result['activation_memory_gb']:.1f}GB")
        print(f"Total: {result['total_memory_gb']:.1f}GB / {result['available_gb']:.1f}GB")
        
        print("\n=== Recommendations ===")
        print(f"🚀 Maximum Batch Size: {result['max_batch_size']}")
        print(f"✅ Recommended Batch Size: {result['recommended_batch_size']} (50% safety margin)")
        print(f"\nConfiguration: seq_len={result['config']['seq_len']}, rank={result['config']['lora_rank']}, fp16={result['config']['fp16']}")


if __name__ == "__main__":
    main()
