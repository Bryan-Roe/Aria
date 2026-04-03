# Automation Quick Reference

## One-Command Training Pipelines

### Quick Training & Auto-Promote
```powershell
python .\scripts\train_and_promote.py --quick --auto-promote
```
**What it does**: Train 64 samples, 1 epoch → Evaluate → Promote best model (~7 min)

### Standard Training & Auto-Promote
```powershell
python .\scripts\train_and_promote.py --standard --auto-promote
```
**What it does**: Train 500 samples, 3 epochs → Evaluate → Promote (~30 min)

### Full Training & Auto-Promote
```powershell
python .\scripts\train_and_promote.py --full --auto-promote
```
**What it does**: Train all samples, 5 epochs → Evaluate → Promote (~2-4 hours)

---

## Scheduled Automation

### Nightly Training (Runs at 2 AM daily)
```powershell
python .\scripts\training_scheduler.py --start nightly
```

### Continuous Training (Retrains when data changes)
```powershell
python .\scripts\training_scheduler.py --start continuous --check-interval 3600
```

### One-Off Scheduled Job
```powershell
python .\scripts\training_scheduler.py --run-once --preset standard
```

---

## Hyperparameter Optimization

### Grid Search (Auto-tune hyperparameters)
```powershell
python .\scripts\training_scheduler.py --grid-search
```

### Custom Grid Search
```powershell
python .\scripts\training_scheduler.py --grid-search `
    --learning-rates 1e-5 2e-5 5e-5 `
    --batch-sizes 4 8 16 `
    --epochs-list 2 3 5
```

---

## VS Code Tasks

Press `Ctrl+Shift+P` → "Tasks: Run Task" → Select:

- **Automate: Train & Promote (Quick)** - 64 samples, auto-deploy
- **Automate: Train & Promote (Standard)** - 500 samples, auto-deploy
- **Automate: Grid Search** - Find best hyperparameters
- **Automate: Start Nightly Training** - Background daemon
- **Automate: Full Pipeline** - Complete training + deploy

---

## Output Locations

### Trained Models
`data_out/lora_training/<timestamp>/`

### Deployed Models
`deployed_models/<model_id>_<timestamp>/`

Latest: Read `deployed_models/LATEST.txt`

### Pipeline Reports
`data_out/train_and_promote/pipeline_<timestamp>.json`

### Evaluation Results
`data_out/batch_evaluator/results_<timestamp>.json`

### Scheduler State
`data_out/training_scheduler/scheduler_state.json`

---

## Advanced Usage

### Custom Training + Promotion
```powershell
python .\scripts\train_and_promote.py `
    --dataset datasets/chat/coding `
    --max-train-samples 200 `
    --epochs 2 `
    --learning-rate 3e-5 `
    --batch-size 4 `
    --auto-promote
```

### Dry-Run (Preview without deploying)
```powershell
python .\scripts\train_and_promote.py --quick --auto-promote --dry-run
```

### Skip Evaluation (Training only)
```powershell
python .\scripts\train_and_promote.py --standard --skip-eval
```

### With Webhook Notification
```powershell
python .\scripts\train_and_promote.py --quick --auto-promote `
    --webhook https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

---

## Typical Workflows

### Development Workflow
```powershell
# 1. Quick validation (7 min)
python .\scripts\train_and_promote.py --quick --auto-promote

# 2. Use deployed model
$latest = Get-Content .\deployed_models\LATEST.txt
# Test at: .\deployed_models\$latest\
```

### Production Deployment
```powershell
# 1. Full training with grid search
python .\scripts\training_scheduler.py --grid-search

# 2. Deploy best model
python .\scripts\train_and_promote.py --standard --auto-promote

# 3. Verify deployment
Get-Content .\deployed_models\LATEST.txt
Get-Content ".\deployed_models\$(Get-Content .\deployed_models\LATEST.txt)\promotion_metadata.json"
```

### Continuous Improvement
```powershell
# Start background daemon (retrains when data updated)
python .\scripts\training_scheduler.py --start continuous --check-interval 1800
```

---

## Monitoring

### Check Pipeline Status
```powershell
Get-ChildItem .\data_out\train_and_promote\pipeline_*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content | ConvertFrom-Json
```

### Check Latest Evaluation
```powershell
Get-ChildItem .\data_out\batch_evaluator\results_*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content | ConvertFrom-Json
```

### Check Scheduler State
```powershell
Get-Content .\data_out\training_scheduler\scheduler_state.json | ConvertFrom-Json
```

---

## Troubleshooting

### Pipeline fails at training
- Check dataset exists: `Test-Path .\datasets\chat\mixed_chat`
- Check venv active: `python --version`
- Check dependencies: `pip list | Select-String "transformers|peft|torch"`

### Evaluation succeeds but metrics empty
- Check `evaluate_lora_model.py` ran successfully
- Look in `data_out/batch_evaluator/<model_id>/results.json`

### Promotion fails with permissions error
- Normal on Windows (symlink requires admin)
- Uses `LATEST.txt` fallback automatically

### Scheduler doesn't run jobs
- Check scheduler state: `Get-Content .\data_out\training_scheduler\scheduler_state.json`
- Verify job schedule matches current time
- Check logs in terminal output

---

**Last Updated**: 2025-11-25
