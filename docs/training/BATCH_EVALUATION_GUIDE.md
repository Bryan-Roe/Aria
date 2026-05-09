# Batch Evaluation & Model Promotion Guide

## Overview

The batch evaluation system provides:

- **Parallel model evaluation** with real metrics
- **Automatic best-model promotion** to `deployed_models/`
- **Comprehensive reporting** (JSON, Markdown)

---

## Quick Start

### 1. Evaluate All Trained Models

```powershell
python .\scripts\batch_evaluator.py --scan-models --evaluate-all
```

This will:
- Scan `data_out/lora_training/` for LoRA adapters
- Evaluate each model with default metrics
- Save results to `data_out/batch_evaluator/results_<timestamp>.json`

### 2. Evaluate and Promote Best Model

```powershell
python .\scripts\batch_evaluator.py --scan-models --evaluate-all --promote-best
```

This will:
- Evaluate all models
- Promote the best model to `deployed_models/<model_id>_<timestamp>/`
- Create `deployed_models/LATEST.txt` pointing to the promoted model
- Save promotion metadata with metrics and timestamp

### 3. Dry-Run Mode

```powershell
python .\scripts\batch_evaluator.py --scan-models --evaluate-all --promote-best --dry-run
```

Preview what would be promoted without making changes.

---

## Metrics

The evaluation system computes the following metrics:

### Perplexity
- **Description**: Language model quality (lower is better)
- **Range**: Typically 1-100 for fine-tuned models
- **Interpretation**: Measures how "surprised" the model is by the test data
- **Note**: Uses fallback heuristic for compatibility with some model versions

### Diversity
- **Description**: Unique token ratio in responses
- **Range**: 0.0-1.0 (higher is better)
- **Interpretation**: Measures vocabulary richness and variation

### Response Length
- **Description**: Average response length in tokens
- **Range**: Variable (depends on dataset)
- **Interpretation**: Helps ensure responses are appropriately sized

### Coherence
- **Description**: Ratio of complete sentences
- **Range**: 0.0-1.0 (higher is better)
- **Interpretation**: Simple heuristic for response completeness

---

## Command Reference

### Scan and Evaluate

```powershell
# Evaluate all models with default settings
python .\scripts\batch_evaluator.py --scan-models --evaluate-all

# Control parallelism (default: 3 workers)
python .\scripts\batch_evaluator.py --scan-models --evaluate-all --max-workers 1

# Load tasks from config file
python .\scripts\batch_evaluator.py --config batch_eval_config.yaml
```

### Promotion

```powershell
# Promote best model (default target: deployed_models/)
python .\scripts\batch_evaluator.py --scan-models --evaluate-all --promote-best

# Custom promotion target
python .\scripts\batch_evaluator.py --scan-models --evaluate-all --promote-best --promote-target c:\my\models

# Dry-run (show what would be done)
python .\scripts\batch_evaluator.py --scan-models --evaluate-all --promote-best --dry-run
```

### Reporting

```powershell
# Export results as JSON
python .\scripts\batch_evaluator.py --export json --output report.json

# Export results as Markdown
python .\scripts\batch_evaluator.py --export markdown --output report.md

# Export both formats
python .\scripts\batch_evaluator.py --export both --output report
```

### Comparison

```powershell
# Compare specific models
python .\scripts\batch_evaluator.py --compare checkpoint-64 lora_adapter
```

---

## Promoted Model Structure

After promotion, the `deployed_models/` directory contains:

```
deployed_models/
├── checkpoint-64_20251124_234342/      # Promoted model directory
│   ├── adapter_config.json
│   ├── adapter_model.safetensors       # LoRA weights
│   ├── promotion_metadata.json         # Metrics, rank, timestamp
│   ├── tokenizer.json
│   ├── tokenizer_config.json
│   └── ... (all adapter files)
└── LATEST.txt                          # Points to latest promotion
```

### promotion_metadata.json

```json
{
  "model_id": "checkpoint-64",
  "source_path": "C:\\...\\data_out\\lora_training\\checkpoint-64",
  "deployment_name": "checkpoint-64_20251124_234342",
  "deployment_path": "C:\\...\\deployed_models\\checkpoint-64_20251124_234342",
  "metrics": {
    "perplexity": 10.188461538461539
  },
  "promoted_at": "2025-11-25T07:43:42.329423Z",
  "rank": 1
}
```

---

## Integration with Training

### Automated Workflow

1. **Train models** with `autotrain.py` or `train_lora.py`
2. **Evaluate all adapters**:
   ```powershell
   python .\scripts\batch_evaluator.py --scan-models --evaluate-all --promote-best
   ```
3. **Use promoted model** from `deployed_models/latest/` (or read `LATEST.txt`)

### Example CI/CD Pipeline

```powershell
# 1. Train
python .\scripts\autotrain.py

# 2. Evaluate and promote
python .\scripts\batch_evaluator.py --scan-models --evaluate-all --promote-best

# 3. Read promoted model path
$latestModel = Get-Content .\deployed_models\LATEST.txt

# 4. Deploy to production (example)
Copy-Item ".\deployed_models\$latestModel" -Destination "C:\production\models\" -Recurse
```

---

## Configuration File Format

`batch_eval_config.yaml`:

```yaml
evaluation_tasks:
  - model_id: phi35_mixed_chat
    model_type: lora
    model_path: data_out/lora_training/phi35_mixed_chat
    dataset: datasets/chat/mixed_chat
    metrics:
      - perplexity
      - diversity
      - response_length
      - coherence
    max_samples: 100

  - model_id: phi35_coding
    model_type: lora
    model_path: data_out/lora_training/phi35_coding
    dataset: datasets/chat/coding
    metrics:
      - perplexity
      - diversity
    max_samples: 50
```

---

## Ranking Logic

Models are ranked by:
1. **Perplexity** (lower is better) - if available
2. **Accuracy** (higher is better) - if available
3. **First evaluated** - fallback if no metrics

The top-ranked model is promoted when `--promote-best` is used.

---

## Troubleshooting

### No models found during scan

**Cause**: No LoRA adapters in `data_out/lora_training/`

**Solution**: Train models first:
```powershell
python .\scripts\autotrain.py
```

### Evaluation fails with "transformers not found"

**Cause**: Missing dependencies

**Solution**: Install evaluation dependencies:
```powershell
pip install transformers peft torch
```

### Promotion fails with "WinError 1314"

**Cause**: Insufficient privileges to create symlinks on Windows

**Behavior**: Automatically falls back to creating `LATEST.txt` instead

**No action needed** - the fallback works identically for reading the latest model.

---

## Advanced Usage

### Custom Metrics

Extend `evaluate_lora_model.py` to add new metrics:

```python
def compute_custom_metric(texts: List[str]) -> float:
    # Your metric logic here
    return score

# Add to evaluation:
if "custom" in metrics:
    results["custom"] = compute_custom_metric(texts)
```

### Parallel Evaluation Tuning

```powershell
# Low parallelism for limited CPU/GPU
python .\scripts\batch_evaluator.py --max-workers 1

# High parallelism for powerful machines
python .\scripts\batch_evaluator.py --max-workers 8
```

### Filter Models by Type

Modify `scan_models()` in `batch_evaluator.py` to filter by directory name patterns.

---

## Next Steps

- **Automate evaluations** with `evaluation_autorun.py` (scheduled runs)
- **Compare training configs** by evaluating multiple hyperparameter variants
- **Monitor model quality** over time by tracking promoted model metrics

---

**Last Updated**: 2025-11-24
