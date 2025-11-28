# Training Commands Quick Reference

Last updated: November 23, 2025

## Chat/LLM Training

### AutoTrain Pipeline (Sequential Jobs)

```powershell
# Dry-run validation
python .\scripts\autotrain.py --dry-run

# Run all configured training jobs
python .\scripts\autotrain.py

# Check status
python .\scripts\autotrain.py --status
```

### Smart Orchestrator (Pipeline with Dependencies)

```powershell
# Run variants pipeline (hyperparameter exploration)
python .\scripts\smart_orchestrator.py --pipeline variants

# Run full pipeline (train + eval + deploy)
python .\scripts\smart_orchestrator.py --pipeline full

# Quick validation pipeline
python .\scripts\smart_orchestrator.py --pipeline quick

# Watch active jobs
python .\scripts\smart_orchestrator.py --watch

# Dry-run
python .\scripts\smart_orchestrator.py --pipeline variants --dry-run
```

### Direct LoRA Training

```powershell
cd AI\microsoft_phi-silica-3.6_v1

# Train on specific dataset
python .\scripts\train_lora.py `
    --dataset ..\..\datasets\chat\comprehensive `
    --hf-model-id microsoft/Phi-3.5-mini-instruct `
    --epochs 3 `
    --learning-rate 0.0002 `
    --device auto

# Quick smoke test (CPU friendly)
python .\scripts\train_lora.py `
    --dataset ..\..\datasets\chat\mixed_chat `
    --max-train-samples 64 `
    --max-eval-samples 16 `
    --epochs 1 `
    --device cpu
```

## Quantum AI Training

### Correct Arguments

```powershell
cd quantum-ai

# Train on custom CSV
python .\train_custom_dataset.py `
    --csv ..\datasets\massive_quantum\synthetic_blobs_1092s_37f_3c_0116.csv `
    --n-qubits 5 `
    --epochs 2 `
    --batch-size 64

# Use preset dataset
python .\train_custom_dataset.py `
    --preset heart `
    --n-qubits 5 `
    --epochs 5 `
    --batch-size 16

# Other presets: ionosphere, sonar, banknote
```

### ❌ WRONG Arguments (Common Mistakes)

```powershell
# ❌ Don't use --dataset (use --csv)
# ❌ Don't use --qubits (use --n-qubits)
# ❌ Don't use --layers (not supported - layers controlled by config)
```

### Quantum AutoRun Pipeline

```powershell
# Dry-run
python .\scripts\quantum_autorun.py --dry-run

# Run all quantum jobs
python .\scripts\quantum_autorun.py

# Check status
python .\scripts\quantum_autorun.py --status
```

## Data Generation

### Synthetic Quantum Datasets

```powershell
# Generate 200 diverse quantum datasets
python .\scripts\generate_synthetic_datasets.py `
    --count 200 `
    --min-samples 200 `
    --max-samples 10000 `
    --min-features 2 `
    --max-features 50 `
    --min-classes 2 `
    --max-classes 8
```

### Synthetic Chat Datasets

```powershell
# Generate from repository code
python .\scripts\generate_repo_training_dataset.py --max-records 500

# Augment dataset (3x expansion)
python .\AI\microsoft_phi-silica-3.6_v1\scripts\data_augmenter.py `
    --input .\datasets\chat\app_repo\train.json `
    --output .\datasets\chat\app_repo_augmented\train.json `
    --num-aug 2 `
    --prob 0.15
```

### Merge Datasets

```powershell
# Combine multiple chat datasets
python .\scripts\merge_chat_datasets.py `
    --source .\datasets\chat\mixed_chat .\datasets\chat\dolly .\datasets\chat\app_repo_augmented `
    --out-dir .\datasets\chat\comprehensive `
    --train-ratio 0.9
```

## Testing & Validation

### Run Tests

```powershell
# Quick tests (non-slow)
python -m pytest -m "not slow" -q

# All tests
python -m pytest

# Specific test file
python -m pytest tests\test_autotrain.py -v

# With coverage
python -m pytest --cov=. --cov-report=html
```

### Environment Health Check

```powershell
# Check model venv health
python .\scripts\env_autofix.py --dry-run

# Force rebuild if needed
python .\scripts\env_autofix.py --force
```

## Monitoring & Results

### Check Training Progress

```powershell
# View autotrain logs
Get-Content .\data_out\autotrain\phi35_comprehensive_full\*\stdout.log -Wait

# Check orchestrator status
cat .\data_out\smart_orchestrator\variants_summary.json

# View metrics ranking
cat .\data_out\metrics_ranker\ranking_summary.json
```

### Dashboard

```powershell
# Start status dashboard
python .\scripts\status_dashboard.py

# Access at http://localhost:5000
```

## Current Training Status

### Active Jobs (as of last run)

- **Chat Training**: 11 jobs (comprehensive, baselines, domain-specific, hyperparameters)
- **Quantum Training**: 198 synthetic datasets available
- **Total Training Data**: 15,277 chat samples, 198 quantum datasets

### Dataset Locations

- Chat (comprehensive): `datasets/chat/comprehensive/` (15.2K samples)
- Chat (augmented repo): `datasets/chat/app_repo_augmented/` (1.5K samples)
- Quantum (synthetic): `datasets/massive_quantum/` (198 datasets)
- Quantum (UCI): `datasets/quantum/` (29 datasets)

## Tips

1. **Always run dry-run first** to validate configuration
2. **Use `--device auto`** for GPU training (falls back to CPU if needed)
3. **Start with small datasets** for quick iteration (max-train-samples)
4. **Monitor GPU usage**: `nvidia-smi -l 1` (if available)
5. **Check logs regularly** to catch issues early
6. **Run tests after major changes** to ensure no regressions
