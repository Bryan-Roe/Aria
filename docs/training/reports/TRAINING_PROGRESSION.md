# Training Progression Guide

## Three-Phase Training Workflow

**Quick → Standard → Full**

GPU acceleration is now enabled across all training jobs. Start with quick mode, validate GPU setup, then scale up.

### Phase 1: QUICK ⚡ (5-15 minutes)

Minimal test to validate GPU setup, data pipeline, and LoRA adapter creation.

```bash
# Run quick validation
python scripts/training/progressive_training.py --phase quick

# Or specific job
python scripts/training/autotrain.py --job phi35_mixed_chat_lr_low
```

**What happens:**
- ✓ Tests CUDA availability and GPU memory
- ✓ Creates LoRA adapter structure
- ✓ Validates data loading pipeline
- ✓ Single epoch, 64 samples (1-2 min per job)

**Expected output:**
```
data_out/lora_training/phi35_lr_low/
├── adapter_config.json
├── adapter_model.safetensors
├── training_args.bin
└── metrics.json
```

**Metrics to check:**
- Training loss should decrease
- GPU memory usage: monitor with `nvidia-smi`
- Speed: should see ~100+ samples/sec on GPU

---

### Phase 2: STANDARD 📊 (30-60 minutes)

Medium-sized training with reasonable data volumes to compare models.

```bash
# Run standard training
python scripts/training/progressive_training.py --phase standard

# Or specific jobs
python scripts/training/autotrain.py --job phi35_mixed_chat
python scripts/training/autotrain.py --job qwen25_3b_mixed_chat
```

**What happens:**
- ✓ Trains Phi-3.5 and Qwen2.5 baseline models
- ✓ 500 train samples, 50 eval samples
- ✓ 1 epoch each
- ✓ Compares model performance

**Jobs:**
1. `phi35_mixed_chat` - Microsoft Phi-3.5 baseline
2. `qwen25_3b_mixed_chat` - Qwen2.5-3B baseline

**Metrics to compare:**
```
Model               Train Loss    Eval Loss    Speed
phi35_mixed_chat    0.XX          0.XX         XXX samples/sec
qwen25_3b_mixed     0.XX          0.XX         XXX samples/sec
```

---

### Phase 3: FULL 🚀 (2-8 hours)

Complete training suite with all 12 jobs: comprehensive datasets, domain-specific, hyperparameter exploration, anime avatar.

```bash
# Run full training
python scripts/training/progressive_training.py --phase full

# Or run all phases sequentially
python scripts/training/progressive_training.py --all

# With auto-promote (deploys best model)
python scripts/training/progressive_training.py --all --auto-promote
```

**Jobs (12 total):**

**Comprehensive (2 jobs)** - Full merged datasets
- `phi35_comprehensive_full` - 1000 samples
- `qwen25_comprehensive_full` - 1000 samples

**Baseline (3 jobs)** - Original datasets
- `phi35_mixed_chat` - 500 samples
- `qwen25_3b_mixed_chat` - 500 samples
- `phi35_max_performance` - 1000 samples (Dolly)

**Domain-specific (2 jobs)** - Code/repo understanding
- `phi35_repo_augmented` - 500 repo samples
- `qwen25_repo_augmented` - 500 repo samples

**Hyperparameter exploration (3 jobs)** - Learning rate & dropout search
- `phi35_mixed_chat_lr_low` (LR=0.0001)
- `phi35_mixed_chat_lr_high` (LR=0.0003)
- `phi35_mixed_chat_dropout_high` (dropout=0.15)

**Anime avatar (1 job)** - Custom persona
- `anime_avatar` - 10 epochs

---

## GPU Performance Monitoring

### Real-time GPU stats
```bash
# Watch GPU utilization
watch -n 1 nvidia-smi

# Check memory allocation
nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv

# Monitor process-specific GPU
nvidia-smi --query-processes=pid,process_name,gpu_memory_usage --format=csv
```

### During training, expected GPU metrics:
- **GPU Utilization:** 90-99%
- **GPU Memory:** 80-95% of available
- **Temperature:** 50-80°C (normal range)
- **Power Draw:** 70-100% (depends on GPU model)

### Training speed benchmarks (relative to CPU):
- Batch size 32: ~15-20x faster
- Batch size 64: ~20-50x faster
- Batch size 128+: ~30-100x faster (depending on GPU)

---

## Troubleshooting

### GPU not detected
```bash
python -c "import torch; print(torch.cuda.is_available())"
```

**Solution:**
- Install CUDA toolkit: `pip install torch --index-url https://download.pytorch.org/whl/cu118`
- Check GPU drivers: `nvidia-smi`
- Verify CUDA version: `nvcc --version`

### Out of memory (OOM)
```
RuntimeError: CUDA out of memory
```

**Solutions:**
1. Reduce batch size in config
2. Reduce max_train_samples (e.g., 256 instead of 500)
3. Enable gradient checkpointing
4. Use mixed precision (already enabled via bfloat16)

### Slow training on GPU
If GPU utilization is low (~20-30%):
1. Check data loading: increase `workers` in config
2. Check batch size: should be 16-64 minimum
3. Check GPU memory: might be swapping to RAM

---

## Status Files

After each phase, check:
```bash
# Quick phase results
cat data_out/training_quick_status.json

# Standard phase results
cat data_out/training_standard_status.json

# Full phase results
cat data_out/training_full_status.json

# Individual job results
ls -la data_out/lora_training/*/last_run.json
ls -la data_out/autotrain/*/status.json
```

---

## Next Steps After Training

### 1. Evaluate models
```bash
python scripts/evaluate_lora_models.py
```

### 2. Compare performance
```bash
python scripts/model_comparator.py data_out/lora_training/
```

### 3. Deploy best model
```bash
python scripts/model_deployer.py --scan
python scripts/model_deployer.py --deploy-best
```

### 4. Auto-promote with health checks
```bash
python scripts/train_and_promote.py --full --auto-promote
```

---

## Configuration Reference

All configs use GPU by default now:

**config/training/autotrain.yaml:**
- `device: cuda` for all jobs
- `workers: 20` for parallel data loading
- Epochs: 1 (quick/standard), 10+ (anime avatar)

**config/autonomous_training.yaml:**
- `device: cuda` (force GPU training)
- `max_gpu_memory_gb: 0` (use all available)
- `max_cpu_cores: 0` (GPU preferred)

---

## Commands Quick Reference

```bash
# Phase 1: Quick test
python scripts/training/progressive_training.py --phase quick

# Phase 2: Standard training
python scripts/training/progressive_training.py --phase standard

# Phase 3: Full training
python scripts/training/progressive_training.py --phase full

# All phases
python scripts/training/progressive_training.py --all

# With auto-deployment
python scripts/training/progressive_training.py --all --auto-promote

# Single job
python scripts/training/autotrain.py --job phi35_mixed_chat --dry-run
python scripts/training/autotrain.py --job phi35_mixed_chat

# Monitor
watch -n 1 nvidia-smi
tail -f data_out/training_quick_status.json
```

---

**Start now:**
```bash
python scripts/training/progressive_training.py --phase quick
```
