---
description: "Evaluate and benchmark AI models using the batch evaluator"
name: "Evaluate"
argument-hint: "Model paths + metrics + dataset (example: adapter path + accuracy/loss metrics + eval dataset)"
agent: data-pipeline
---
# Evaluate

Run model evaluation and benchmarking using the Aria batch evaluation pipeline.

## Evaluation Modes

### Single Model
```bash
python scripts/evaluate_lora_model.py \
  --model-path data_out/lora_training/my-model \
  --dataset datasets/chat/eval_set.jsonl \
  --metrics accuracy perplexity f1
```

### Batch Evaluation (Parallel)
```bash
python scripts/batch_evaluator.py --config config/evaluation/eval_config.yaml
```

### Auto-Scan All Models
```bash
python scripts/batch_evaluator.py --scan  # Discovers models in data_out/lora_training/
```

## Metrics

| Metric | Description | Good Range |
|--------|-------------|------------|
| accuracy | Exact match ratio | > 0.70 |
| perplexity | Cross-entropy exp (lower = better) | < 50 |
| f1 | Precision/recall harmonic mean | > 0.75 |
| mean_accuracy | Average across samples | > 0.70 |
| improvement_rate | Delta between cycles | > 0 |

## Performance Analysis
```bash
python scripts/training_analytics.py  # Trends, plateau detection, improvement rates
```

## Safety Rules

- **Dataset immutability**: Never modify files in `datasets/` — use `data_out/` for outputs
- **Timeout**: 30 minutes per evaluation (configurable)
- **Resources**: Max 3 parallel evaluations (ThreadPoolExecutor)
- **Always dry-run first**: Validate config before GPU execution

Evaluate: {{input}}
