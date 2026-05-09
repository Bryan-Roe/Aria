# Batch Evaluation & Promotion - Quick Reference

## Core Commands

### Evaluate All Models
```powershell
python .\scripts\batch_evaluator.py --scan-models --evaluate-all
```

### Evaluate and Promote Best Model
```powershell
python .\scripts\batch_evaluator.py --scan-models --evaluate-all --promote-best
```

### Dry-Run Mode
```powershell
python .\scripts\batch_evaluator.py --scan-models --evaluate-all --promote-best --dry-run
```

---

## What Gets Measured

- **Perplexity**: Language model quality (lower = better, ~10-100 typical)
- **Diversity**: Unique token ratio (0.0-1.0, higher = better)
- **Response Length**: Avg tokens per response
- **Coherence**: Complete sentence ratio (0.0-1.0)

---

## Promoted Model Location

After promotion: `deployed_models/<model_id>_<timestamp>/`

Contains:
- All adapter files (adapter_model.safetensors, config, etc.)
- `promotion_metadata.json` (metrics, rank, timestamp)
- `../LATEST.txt` points to this directory

---

## Example Workflow

```powershell
# 1. Train models
python .\scripts\autotrain.py

# 2. Evaluate and promote best
python .\scripts\batch_evaluator.py --scan-models --evaluate-all --promote-best

# 3. Use promoted model
$latest = Get-Content .\deployed_models\LATEST.txt
# Now use: .\deployed_models\$latest\
```

---

## Troubleshooting

- **No models found**: Train first with `autotrain.py` or `train_lora.py`
- **Missing transformers**: Run `pip install transformers peft torch`
- **Symlink error (WinError 1314)**: Normal on Windows, uses LATEST.txt fallback

---

**Last Updated**: 2025-11-24
