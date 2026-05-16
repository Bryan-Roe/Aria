---
name: "Training-Scripts"
description: "Guidance for training orchestration scripts"
applyTo: "scripts/*train*"
---
# Training Scripts — Implementation Guidance

- All training orchestrators are YAML-driven with matching config files.
- **Always** `--dry-run` before GPU/QPU execution.
- Config precedence: `YAML base` < `CLI flags` < `per-job YAML` < `env vars`.

## Key Scripts

| Script | Config | Purpose |
| -------- | -------- | --------- |
| `autotrain.py` | `autotrain.yaml` | LoRA fine-tuning job orchestration |
| `automated_training_pipeline.py` | — | End-to-end training pipeline |
| `train_and_promote.py` | — | Train + auto-deploy best model |
| `autonomous_training_orchestrator.py` | `config/autonomous_training.yaml` | Continuous self-managing cycles |
| `master_orchestrator.py` | `config/master_orchestrator.yaml` | Coordinates all sub-orchestrators |

## Data Conventions
- Read-only: `datasets/<category>/<name>/train.json` + `test.json`
- Write-only: `data_out/<orchestrator>/`
- Status: `data_out/<orchestrator>/status.json` — `{total_jobs, succeeded, failed, running, last_updated, avg_duration}`
- Chat dataset format: `[{"messages": [{"role": "user|assistant", "content": "..."}]}]`

## LoRA Adapter Requirements
- Valid adapter = `adapter_config.json` + `adapter_model.safetensors`
- Validate: `python scripts/validate_datasets.py --category chat`

## Metrics
- Tracked: mean_accuracy, median_accuracy, max_accuracy, successful_count, exceptional_models
- Degradation: auto-detect >5% accuracy drops between cycles
- Auto-promote: when accuracy > 0.90 (configurable)
