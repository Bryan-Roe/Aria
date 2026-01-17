# Evaluation Framework — Quick Reference

**Last updated:** December 8, 2025

One-page reference for common evaluation tasks.

## Quick Start Commands

```bash
# Local smoke test (offline, no credentials)
python .\scripts\evaluate_local_model.py --dataset datasets/chat/mixed_chat --max-samples 10 --metric accuracy

# Evaluate LoRA model
python .\scripts\evaluate_lora_model.py --model-path data_out/lora_training/phi35 --dataset datasets/chat/dolly --max-samples 100 --metric accuracy --metric bleu

# Run all evaluations (YAML config)
python .\scripts\evaluation_autorun.py

# Batch evaluate all models in parallel
python .\scripts\batch_evaluator.py --scan-models --evaluate-all

# Export results to HTML
python .\scripts\results_exporter.py --source evaluation_autorun --format html

# Monitor progress live
python .\scripts\status_dashboard.py --watch
```

## Configuration

### evaluation_autorun.yaml Structure

```yaml
version: 1

jobs:
  - name: eval_name
    enabled: true
    model_type: lora|azure|openai|local|quantum
    model_path: data_out/lora_training/phi35
    dataset: datasets/chat/dolly
    max_samples: 100
    metrics:
      - accuracy
      - bleu
      - f1_score
    batch_size: 4
```

**Supported model types:** `lora`, `azure`, `openai`, `local`, `quantum`

**Common metrics:** `accuracy`, `precision`, `recall`, `f1_score`, `bleu`, `rouge`, `response_time`, `determinism`, `perplexity`

## Evaluation Tools

| Tool | Purpose | Speed | Cost |
|------|---------|-------|------|
| `evaluate_local_model.py` | Offline baseline | Fast | Free |
| `evaluate_lora_model.py` | LoRA adapters | ~2-5 samples/min | Free (GPU) |
| `evaluate_quantum_model.py` | Quantum circuits | ~10-50 samples/sec | Free (sim), $ (QPU) |
| `evaluate_azure_model.py` | Azure OpenAI | ~1-5 samples/sec | ~$0.001-0.01/eval |
| `batch_evaluator.py` | Multi-model parallel | ~3x sequential | Depends on models |

## Results Output Structure

```
data_out/
├── evaluation_autorun/
│   ├── eval_name/
│   │   ├── timestamp_1/
│   │   │   ├── result.json
│   │   │   └── stdout.log
│   │   └── timestamp_2/
│   ├── status.json (aggregate)
│   └── evaluation.log
│
├── batch_evaluator/
│   ├── results.json (all results)
│   ├── ranking.json (model ranking)
│   └── status.json
│
└── evaluation_/
    ├── results/
    └── logs/
```

## Key Metrics Reference

```python
# 0..1 range (higher is better)
accuracy        # Exact match rate
precision       # TP / (TP + FP)
recall          # TP / (TP + FN)
f1_score        # 2×(P×R)/(P+R)
bleu            # N-gram overlap (BLEU-4)
rouge           # LCS-based score
determinism     # Consistency across runs

# Other ranges
response_time_ms    # Milliseconds (lower is better)
perplexity          # ≥1 (lower is better)
token_efficiency    # 0..100 % (higher is better)
cost_per_token      # $ (lower is better)
```

## Common Workflows

### 1. Quick validation (5 minutes)

```bash
# Smoke test: fast, offline, no credentials
python .\scripts\evaluate_local_model.py \
  --dataset datasets/chat/mixed_chat \
  --max-samples 10 \
  --metric accuracy \
  --metric determinism
```

### 2. Full model evaluation (30 minutes)

```bash
# Comprehensive evaluation
python .\scripts\evaluate_lora_model.py \
  --model-path data_out/lora_training/phi35 \
  --dataset datasets/chat/dolly \
  --max-samples 200 \
  --metric accuracy \
  --metric bleu \
  --metric rouge \
  --batch-size 4 \
  --save-dir results/phi35_eval
```

### 3. Multi-model comparison (1-2 hours)

```bash
# Parallel batch evaluation
python .\scripts\batch_evaluator.py \
  --config config/evaluation/batch_eval_config.yaml \
  --max-workers 4 \
  --export markdown \
  --export html
```

### 4. CI/CD integration (2-3 minutes)

```bash
# Fast smoke test in CI pipeline
python .\scripts\evaluate_local_model.py \
  --dataset datasets/chat/mixed_chat \
  --max-samples 10 \
  --metric accuracy \
  --save-dir results/ci_eval

# Check threshold
python -c "import json; r = json.load(open('results/ci_eval/result.json')); exit(0 if r['metrics'].get('accuracy', 0) >= 0.7 else 1)"
```

### 5. Production monitoring (continuous)

```bash
# Monitor evaluation trends
python .\scripts\status_dashboard.py --watch

# Export daily report
python .\scripts\results_exporter.py \
  --source evaluation_autorun \
  --format html \
  --output-file exports/daily_report_$(date +%Y%m%d).html
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Model not found | Check path with `ls data_out/lora_training/` |
| Out of memory | Reduce `--batch-size` or `--max-samples` |
| Dataset not found | Verify path, use forward slashes: `datasets/chat/dolly` |
| Slow evaluation | Use `--max-samples 50` for quick validation |
| Azure credentials error | Set `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT` |
| Quantum backend unavailable | Use simulator: `--simulator qiskit_aer` |

## Advanced Usage

### Custom metric

```python
# Add to evaluation_utils.py
def compute_custom_metric(predictions, references):
    return score  # 0..1

# Use in config
metrics:
  - accuracy
  - custom_metric
```

### Export to different formats

```bash
# JSON
python .\scripts\results_exporter.py --source evaluation_autorun --format json

# CSV (Excel)
python .\scripts\results_exporter.py --source evaluation_autorun --format csv

# HTML (interactive)
python .\scripts\results_exporter.py --source evaluation_autorun --format html

# Markdown
python .\scripts\results_exporter.py --source evaluation_autorun --format markdown
```

### Dry-run validation

```bash
# Check configuration without executing
python .\scripts\evaluation_autorun.py --dry-run

# Should print: "Job eval_name validated" for each job
```

## Environment Variables

```powershell
# Optional: Azure OpenAI evaluation
$env:AZURE_OPENAI_API_KEY = "your-key"
$env:AZURE_OPENAI_ENDPOINT = "https://your-resource.openai.azure.com/"
$env:AZURE_OPENAI_DEPLOYMENT = "gpt-4o-mini"
$env:AZURE_OPENAI_API_VERSION = "2024-10-01"

# Optional: Quantum (Azure Quantum)
$env:AZURE_QUANTUM_SUBSCRIPTION = "your-subscription-id"
$env:AZURE_QUANTUM_RESOURCE_GROUP = "your-resource-group"
$env:AZURE_QUANTUM_WORKSPACE = "your-workspace-name"
$env:AZURE_QUANTUM_LOCATION = "eastus"
```

## Health Check

```bash
# Check system status
curl http://localhost:7071/api/ai/status | jq '.evaluation'

# Check evaluation-specific status
python .\scripts\status_dashboard.py --source evaluation_autorun
```

## Integration Points

- **Training pipelines:** Auto-evaluate after `train_and_promote.py`
- **CI/CD:** Fast smoke tests in `evaluation_autorun.py --dry-run` mode
- **Monitoring:** Send results to Azure Monitor, Prometheus, or Datadog
- **Dashboards:** Export HTML reports for stakeholder review

## Key Files

| File | Purpose |
|------|---------|
| `EVALUATION_FRAMEWORK.md` | Complete framework guide |
| `EVALUATION_BEST_PRACTICES.md` | Advanced patterns & customization |
| `config/evaluation/evaluation_autorun.yaml` | Main evaluation config |
| `config/evaluation/batch_eval_config.yaml` | Batch evaluation config |
| `shared/evaluation_utils.py` | Shared evaluation utilities |
| `tests/evaluation_test_utils.py` | Test fixtures & helpers |

## One-Liners

```bash
# Evaluate LoRA in one line
python .\scripts\evaluate_lora_model.py --model-path data_out/lora_training/phi35 --dataset datasets/chat/dolly --max-samples 100 --metric accuracy --metric bleu

# Check if accuracy meets threshold
python -c "import json; d=json.load(open('data_out/evaluation_autorun/eval_name/*/result.json')); print('✓ PASS' if d['metrics']['accuracy'] >= 0.85 else '✗ FAIL')"

# Export all results to HTML
python .\scripts\results_exporter.py --all --format html

# Compare two models
python .\scripts\batch_evaluator.py --compare lora_phi35 azure_baseline --export markdown
```

## Resources

- Full guide: `EVALUATION_FRAMEWORK.md`
- Advanced patterns: `EVALUATION_BEST_PRACTICES.md`
- API docs: `python .\scripts\evaluate_lora_model.py --help`
- Configuration: `config/evaluation/`
- Utilities: `shared/evaluation_utils.py`
