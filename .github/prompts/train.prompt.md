---
description: "Plan, execute, and monitor training runs — LoRA fine-tuning, dataset validation, performance analysis, and model deployment."
name: "Train"
argument-hint: "Training goal + dataset + model path (example: goal + dataset path + base model + adapter output path)"
agent: autonomous-trainer
---

Handle the following training-related task using the autonomous training framework.

**Before any training:**
1. Validate orchestrator config: `python scripts/autotrain.py --dry-run`
2. Check dataset integrity: `python scripts/validate_datasets.py --category chat`
3. Verify system resources: `python scripts/resource_monitor.py --snapshot`

**Training execution options:**
```bash
# Quick LoRA (TinyLlama, fast iteration)
python scripts/automated_training_pipeline.py --models tinyllama --quick

# Full training with auto-promotion
python scripts/train_and_promote.py --quick --auto-promote

# Autonomous continuous training (30-min cycles)
nohup python scripts/autonomous_training_orchestrator.py > data_out/autonomous_training.log 2>&1 &
```

**Monitor progress:**
```bash
python scripts/monitor_autonomous_training.py --watch   # Real-time dashboard
python scripts/training_analytics.py                     # Performance trends
cat data_out/autonomous_training_status.json             # Cycle status
```

**Key rules:**
- ALWAYS `--dry-run` before GPU execution
- NEVER modify files in `datasets/` (read-only)
- All outputs write to `data_out/<orchestrator>/`
- Valid LoRA adapter = `adapter_config.json` + `adapter_model.safetensors`
- Auto-deploy threshold: accuracy > 0.90
- Degradation alert: >5% accuracy drop between cycles
