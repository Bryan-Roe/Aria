# Fast Training Guide

## Quick Start

Run optimized training in under 10 minutes:

```powershell
.\scripts\fast_train.ps1 -Mode quick
```

## Training Modes

### Quick Mode (5-10 minutes)
- 64 samples per model
- 2 models: Phi-3.5 + Qwen2.5-3B
- Perfect for testing and validation
```powershell
.\scripts\fast_train.ps1 -Mode quick
```

### Medium Mode (20-30 minutes)
- 256 samples per model
- Better model quality
- Good balance of speed/performance
```powershell
.\scripts\fast_train.ps1 -Mode medium
```

### Focused Mode (40-60 minutes)
- 500 samples per model
- Comprehensive dataset
- Production-ready models
```powershell
.\scripts\fast_train.ps1 -Mode focused
```

## Parallel Training

Run multiple jobs simultaneously (requires adequate RAM/GPU):

```powershell
# 2 concurrent jobs (default)
.\scripts\fast_train.ps1 -Mode quick -Parallel 2

# 4 concurrent jobs (if you have 4 GPUs or 32GB+ RAM)
.\scripts\fast_train.ps1 -Mode medium -Parallel 4
```

## Model Selection

Train specific models only:

```powershell
# Only Phi-3.5 models
.\scripts\fast_train.ps1 -Mode quick -Model phi35

# Only Qwen2.5 models
.\scripts\fast_train.ps1 -Mode quick -Model qwen25
```

## Speed Optimizations

The fast training configuration includes:

1. **Reduced Sample Sizes**: 64-500 vs 1000-15000 in full training
2. **Smaller LoRA Rank**: 4-8 vs 16 (50% faster, minimal quality loss)
3. **Optimized Batch Sizes**: 2-16 vs 1 (better GPU utilization)
4. **Shorter Sequences**: 384 vs 512 tokens (20% speedup)
5. **Parallel Execution**: 2-4 jobs concurrently
6. **Gradient Checkpointing**: Enabled for memory efficiency
7. **Fast Attention**: Enabled if hardware supports it

## Azure ML Training

For even faster training with dedicated GPU:

```powershell
# Deploy to Azure ML with V100 GPU
.\scripts\deploy_training_to_azure.ps1 `
    -SubscriptionId "your-subscription-id" `
    -JobFilter "phi35_quick*"

# Monitor at: https://ml.azure.com/
```

**Benefits:**
- V100 GPU (3-5x faster than CPU)
- Auto-scales to $0 when idle
- Parallel job execution across multiple nodes
- ~$3/hour when running

## Monitor Progress

Real-time monitoring:

```powershell
# Check status once
python .\scripts\parallel_train.py --list

# Continuous monitoring
Get-Content .\data_out\parallel_training\status.json
```

## Expected Training Times

| Mode | Samples | Local CPU | Local GPU | Azure V100 |
|------|---------|-----------|-----------|------------|
| Quick | 64 | 5-10 min | 2-3 min | 1-2 min |
| Medium | 256 | 20-30 min | 8-12 min | 4-6 min |
| Focused | 500 | 40-60 min | 15-20 min | 8-12 min |

## Results Location

- **Models**: `data_out/lora_training/<model_name>/`
- **Logs**: `data_out/parallel_training/<job_name>/*/stdout.log`
- **Status**: `data_out/parallel_training/status.json`

## Comparison: Full vs Fast Training

| Metric | Full Training | Fast Training | Speedup |
|--------|--------------|---------------|---------|
| Samples | 1000-15000 | 64-500 | 3-20x fewer |
| Time per job | 2-8 hours | 5-60 min | 3-10x faster |
| Total time (11 jobs) | 20-80 hours | 1-6 hours | 10-20x faster |
| Model quality | 100% | 90-95% | Minimal loss |
| Cost (Azure) | $60-240 | $3-18 | 10-20x cheaper |

## Tips

1. **Start with quick mode** to validate everything works
2. **Use parallel=2** unless you have 4+ GPUs or 64GB+ RAM
3. **Monitor GPU memory** - reduce parallel count if OOM errors occur
4. **Azure ML recommended** for production training (much faster)
5. **Fast training good for**: rapid iteration, hyperparameter tuning, CI/CD
6. **Full training needed for**: production deployment, maximum quality

## Troubleshooting

**Out of Memory**:
```powershell
# Reduce parallel jobs
.\scripts\fast_train.ps1 -Mode quick -Parallel 1

# Or reduce batch size in lora_fast.yaml
```

**Slow on CPU**:
```powershell
# Use Azure ML for GPU acceleration
.\scripts\deploy_training_to_azure.ps1 -SubscriptionId "..."
```

**Jobs failing**:
```powershell
# Check logs
Get-Content data_out\parallel_training\<job_name>\*\stdout.log
```

## Next Steps

After fast training completes:
1. Test models with `ai-projects/chat-cli/src/chat_cli.py`
2. Deploy best model to Azure Functions
3. Run evaluation suite for quality metrics
4. If quality insufficient, run focused or full training
