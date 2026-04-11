---
applyTo: "scripts/batch_evaluator.py,scripts/evaluate_*,scripts/training_analytics*"
---

# Evaluation & Analytics — Instruction Guide

## Batch Evaluator

### Pipeline
```
load_config(YAML) or scan_models() → List[EvaluationTask]
    ↓
ThreadPoolExecutor(max_workers=3) → parallel evaluation
    ↓
evaluate_model(task) → subprocess → evaluate_lora_model.py
    ↓
List[EvaluationResult] → aggregation → export
```

### EvaluationTask Fields
- `model_id` — unique identifier
- `model_type` — "lora", "base", etc.
- `model_path` — path to model/adapter
- `dataset` — evaluation dataset path
- `metrics` — list: accuracy, perplexity, f1
- `max_samples` — limit evaluation samples
- `batch_size` — inference batch size

### Constraints
- Timeout: 30 minutes per evaluation
- Max parallel workers: 3 (configurable)
- Output directory: `data_out/batch_evaluator/`
- Error handling: catches subprocess failures, returns status + error

## Training Analytics

### Tracked Metrics
- `mean_accuracy` — average across evaluation samples
- `median_accuracy` — middle value (robust to outliers)
- `max_accuracy` — best single result
- `improvement_rate` — accuracy delta between cycles
- `successful_count` — models passing threshold
- `exceptional_models` — models with accuracy > 0.90

### Plateau Detection
Identifies when accuracy improvement rate drops below threshold across consecutive cycles.

### Degradation Alerts
Auto-detect > 5% accuracy drops between training cycles.

## Coding Conventions

- Always `--dry-run` before GPU execution
- Datasets in `datasets/` are READ-ONLY
- All outputs go to `data_out/<evaluator>/`
- Subprocess evaluations should be timeout-guarded
- Log evaluation results to `status.json` for dashboard consumption
