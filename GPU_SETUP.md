# GPU Acceleration Setup

## Changes Applied ✓

All training configurations have been updated to use **CUDA GPU** instead of CPU:

### 1. **Training Jobs** (`config/training/autotrain.yaml`)
   - All 14+ training jobs now use `device: cuda`
   - Includes: Phi-3.5, Qwen2.5, anime avatar, hyperparameter exploration jobs

### 2. **Autonomous Training** (`config/autonomous_training.yaml`)
   - Resource management set to:
     - `max_gpu_memory_gb: 0` (use all available GPU memory)
     - `max_cpu_cores: 0` (GPU preferred)
     - `device: cuda` (force GPU training)

## Quick Start

### Check GPU Availability
```bash
# Check if CUDA is available
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
python -c "import torch; print(f'GPU count: {torch.cuda.device_count()}')"
python -c "import torch; print(f'GPU name: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')"
```

### Run Training with GPU
```bash
# Quick training (TinyLlama)
python scripts/automated_training_pipeline.py --quick

# Full AutoTrain job
python scripts/training/autotrain.py --dry-run  # Validate first
python scripts/training/autotrain.py             # Run all jobs

# Autonomous training (continuous cycles)
nohup python scripts/training/autonomous_training_orchestrator.py > data_out/autonomous_training.log 2>&1 &
```

### Monitor GPU Usage
```bash
# Real-time GPU monitoring
watch -n 1 nvidia-smi

# Or use the resource monitor
python scripts/resource_monitor.py --stream

# Check training progress
tail -f data_out/autonomous_training.log
```

## Performance Tips

### Memory Optimization
- **Batch Size**: Increase for faster training (if GPU memory allows)
- **Gradient Accumulation**: Use `gradient_accumulation_steps` if OOM errors
- **Mixed Precision**: Enabled by default (bfloat16 for efficiency)

### Multi-GPU Setup
```bash
# Set visible GPUs (e.g., use GPU 0 and 1)
export CUDA_VISIBLE_DEVICES=0,1

# For distributed training
export CUDA_VISIBLE_DEVICES=0,1,2,3
```

### Troubleshooting

**"CUDA out of memory" error:**
```bash
# Reduce batch size
# Edit config/training/autotrain.yaml:
# max_train_samples: 256  (instead of 500+)
```

**GPU not detected:**
```bash
# Install/update CUDA toolkit
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Or for newer GPUs (RTX 40 series)
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

**Check PyTorch GPU compatibility:**
```bash
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
```

## Configuration Reference

| Setting | Value | Effect |
|---------|-------|--------|
| `device: cuda` | GPU training | ~10-50x faster than CPU |
| `max_gpu_memory_gb: 0` | Use all available | Maximizes throughput |
| `mixed_precision` | bfloat16 (default) | Reduces memory ~50% |
| `workers: 20` | Parallel data loading | Speeds up data pipeline |

## Expected Speedup

- **Training time**: 10-50x faster (depending on GPU model)
- **Data loading**: 5-10x faster with parallel workers
- **Inference**: 20-100x faster (depending on batch size and model)

## Next Steps

1. ✓ GPU configs applied
2. Run health check: `curl http://localhost:7071/api/ai/status | jq`
3. Start training: `python scripts/automated_training_pipeline.py --quick`
4. Monitor: `nvidia-smi` or `python scripts/resource_monitor.py --stream`

---

**Status**: GPU acceleration enabled on all training pipelines
**Date**: January 17, 2026
