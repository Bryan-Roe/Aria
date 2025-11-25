# Extended Marathon Training Session
# ====================================
# Multi-hour comprehensive AI training with automatic data generation
# 
# Created: 2025-11-25
# Estimated Runtime: 4-6 hours
# Expected Output: 13 trained LoRA adapters

## Overview

This configuration enables extended AI training across multiple datasets and models:

### 1. Data Generation (Completed)
- **2,000 synthetic chat samples** generated via `auto_data_train.py`
- Sources: Template-based + Repository Q&A + Augmentation
- Location: `datasets/chat/mega_synthetic/`

### 2. Training Jobs (13 total)

#### Synthetic Data Training (2 jobs, ~30-45 min each)
- `phi35_mega_synthetic_full` - Phi-3.5 on new synthetic data (3 epochs, all samples)
- `qwen25_mega_synthetic_full` - Qwen2.5 on new synthetic data (3 epochs, all samples)

#### Comprehensive Dataset Marathon (2 jobs, ~45-60 min each)
- `phi35_comprehensive_marathon` - 5 epochs, 3000 samples
- `qwen25_comprehensive_marathon` - 5 epochs, 3000 samples

#### Dolly Full Dataset (2 jobs, ~60-90 min each)
- `phi35_dolly_marathon` - 5 epochs, 5000 samples
- `qwen25_dolly_marathon` - 5 epochs, 5000 samples

#### Mixed Chat Extended (2 jobs, ~30-40 min each)
- `phi35_mixed_extended` - 5 epochs, 2000 samples
- `qwen25_mixed_extended` - 5 epochs, 2000 samples

#### Repository-Augmented Extended (2 jobs, ~25-35 min each)
- `phi35_repo_marathon` - 4 epochs, 1500 samples
- `qwen25_repo_marathon` - 4 epochs, 1500 samples

#### Hyperparameter Exploration (3 jobs, ~30-40 min each)
- `phi35_comprehensive_lr_low_extended` - Low LR (0.0001), 5 epochs
- `phi35_comprehensive_lr_high_extended` - High LR (0.0004), 4 epochs
- `qwen25_comprehensive_dropout_test` - Higher dropout (0.15), 4 epochs

### 3. Expected Outputs

Each job produces:
- `data_out/lora_training/marathon/<job_name>/` - Trained adapter
- `data_out/autotrain/<job_name>/<timestamp>/stdout.log` - Training logs
- `data_out/autotrain/<job_name>/last_run.json` - Job metadata
- `data_out/autotrain/status.json` - Overall progress

### 4. Launch Commands

```powershell
# Dry-run to validate all jobs (recommended first)
python .\scripts\autotrain.py --config autotrain_extended_marathon.yaml --dry-run

# Launch full marathon training
python .\scripts\autotrain.py --config autotrain_extended_marathon.yaml

# Resume if interrupted (skip completed jobs)
python .\scripts\autotrain.py --config autotrain_extended_marathon.yaml --resume

# Run specific job only
python .\scripts\autotrain.py --config autotrain_extended_marathon.yaml --job phi35_mega_synthetic_full
```

### 5. Monitoring Progress

```powershell
# Check overall status
python .\scripts\master_orchestrator.py --status

# Watch training logs (during job execution)
Get-Content data_out\autotrain\<job_name>\<timestamp>\stdout.log -Wait

# View status JSON (programmatic)
Get-Content data_out\autotrain\status.json | ConvertFrom-Json | Format-List
```

### 6. Resource Requirements

- **GPU**: CUDA-compatible GPU recommended (10x+ faster)
  - Without GPU: Expect 2-3x longer runtime (10-15 hours total)
- **RAM**: 8GB minimum, 16GB recommended
- **Disk**: ~10GB for all outputs
- **Active monitoring**: Optional but recommended for first hour

### 7. Safety Features

- **Incremental status updates**: `status.json` updated after each job
- **Resume capability**: `--resume` flag skips succeeded jobs
- **PID tracking**: Each job's PID saved for cancellation support
- **DB logging**: Successful runs logged to SQL (if configured)

### 8. Post-Training Analysis

After completion, use these tools:

```powershell
# Evaluate all trained models
python .\scripts\batch_evaluator.py --scan-models --evaluate-all

# Rank and promote best model
python .\scripts\batch_evaluator.py --promote-best

# Export results to markdown
python .\scripts\results_exporter.py --all --format markdown

# Compare metrics
python .\scripts\training_analytics.py --compare-all
```

### 9. Expected Timeline

| Phase | Duration | Jobs |
|-------|----------|------|
| Synthetic Data Training | 1-1.5 hrs | 2 |
| Comprehensive Marathon | 1.5-2 hrs | 2 |
| Dolly Full Dataset | 2-3 hrs | 2 |
| Mixed Chat Extended | 1-1.5 hrs | 2 |
| Repo Extended | 1 hr | 2 |
| HPO Variations | 1.5-2 hrs | 3 |
| **Total** | **4-6 hrs** | **13** |

*Times assume GPU acceleration. CPU-only systems: multiply by 2-3x*

### 10. Troubleshooting

**Out of Memory**:
```yaml
# Reduce max_train_samples in YAML (e.g., 3000 → 1500)
# Or add to job config:
no_stream: true  # Disable streaming for stability
```

**Training stuck**:
```powershell
# Find running job PID
Get-Content data_out\autotrain\*.pid

# Kill if needed
Stop-Process -Id <PID>

# Resume from last completed
python .\scripts\autotrain.py --config autotrain_extended_marathon.yaml --resume
```

**Low GPU utilization**:
- Check `device: auto` is set (not `cpu`)
- Verify CUDA: `python -c "import torch; print(torch.cuda.is_available())"`
- Install GPU torch: `pip install torch --index-url https://download.pytorch.org/whl/cu121`

## Next Steps

1. ✅ Data generation complete (`datasets/chat/mega_synthetic/`)
2. ✅ Configuration created (`autotrain_extended_marathon.yaml`)
3. ⏳ **Ready to launch marathon training**
4. ⏳ Post-training evaluation & promotion

---
*For questions or issues, check `AUTOTRAIN_README.md` and `.github/copilot-instructions.md`*
