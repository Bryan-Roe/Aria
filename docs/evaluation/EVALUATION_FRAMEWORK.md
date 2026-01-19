# Evaluation Framework — Aria Workspace

**Last updated:** December 8, 2025

Comprehensive guide to evaluating AI models, quantum classifiers, and chat systems in the Aria workspace. This framework covers local testing, CI/CD integration, batch evaluation, and production monitoring.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [Evaluation Types](#evaluation-types)
4. [Tools & Scripts](#tools--scripts)
5. [Configuration](#configuration)
6. [Running Evaluations](#running-evaluations)
7. [Metrics Reference](#metrics-reference)
8. [Integration with Orchestrators](#integration-with-orchestrators)
9. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Run a quick evaluation (2-3 minutes)

```bash
# Local smoke test (offline, no credentials needed)
python .\scripts\evaluate_local_model.py `
  --dataset datasets/chat/mixed_chat `
  --max-samples 10 `
  --metric accuracy `
  --metric determinism

# LoRA adapter evaluation
python .\scripts\evaluate_lora_model.py `
  --model-path data_out/lora_training/phi35 `
  --dataset datasets/chat/dolly `
  --max-samples 50 `
  --metric accuracy `
  --metric bleu
```

### Run batch evaluation (all configured models)

```bash
# Scan available models and evaluate all
python .\scripts\batch_evaluator.py --scan-models --evaluate-all

# Evaluate specific model types
python .\scripts\batch_evaluator.py --compare lora azure local --export markdown

# Export results to HTML report
python .\scripts\results_exporter.py --source batch_evaluator --format html
```

### Run evaluation orchestrator (with YAML config)

```bash
# Dry-run validation (checks all paths/configs, no execution)
python .\scripts\evaluation_autorun.py --dry-run

# Run all enabled jobs in config
python .\scripts\evaluation_autorun.py

# Run specific job
python .\scripts\evaluation_autorun.py --job eval_lora_phi35_full

# List all configured jobs
python .\scripts\evaluation_autorun.py --list

# Watch evaluation status
python .\scripts\status_dashboard.py --watch
```

---

## Architecture Overview

### Core Components

```
Evaluation Framework
├── Local Evaluators (lightweight, offline)
│   ├── evaluate_local_model.py       (echo baseline + metrics)
│   ├── evaluate_lora_model.py        (LoRA adapter evaluation)
│   ├── evaluate_quantum_model.py     (quantum classifier eval)
│   └── evaluate_azure_model.py       (Azure OpenAI evaluation)
│
├── Batch System (parallel evaluation)
│   └── batch_evaluator.py            (multi-model + aggregation)
│
├── Orchestrators (YAML-driven automation)
│   ├── evaluation_autorun.py         (sequential jobs)
│   ├── ci_orchestrator.py            (CI pipeline integration)
│   └── master_orchestrator.py        (cross-service scheduling)
│
├── Analysis & Export
│   ├── results_exporter.py           (JSON/CSV/Excel/HTML/Markdown)
│   ├── training_analytics.py         (performance trends)
│   └── metrics_ranker.py             (model ranking & comparison)
│
└── Configuration
    └── config/evaluation/
        ├── evaluation_autorun.yaml   (job definitions)
        └── batch_eval_config.yaml    (batch task config)
```

### Data Flow

```
Models (LoRA, Azure, Quantum, Local)
    ↓
Evaluators (local scripts)
    ↓
Metrics Computation (accuracy, bleu, f1, etc.)
    ↓
Results → data_out/
    ├── evaluation_autorun/<job>/<timestamp>/
    ├── batch_evaluator/results.json
    └── status.json (unified)
    ↓
Export (JSON/CSV/Excel/HTML/Markdown)
    ↓
exports/
    ├── evaluation_report.html
    ├── model_comparison.csv
    └── training_metrics.json
```

---

## Evaluation Types

### 1. Local (Offline) Evaluation

**Best for:** Unit tests, CI/CD, rapid iteration, no credentials required

- **Purpose:** Fast, credential-free baseline testing
- **Models:** Local provider (echo), any offline model
- **Dataset:** JSONL, JSON array, CSV
- **Metrics:** accuracy, response_time, determinism, basic_bleu
- **Speed:** ~1 sample/sec (minimal compute)

```bash
python .\scripts\evaluate_local_model.py \
  --dataset datasets/chat/mixed_chat \
  --max-samples 20 \
  --metric accuracy
```

### 2. LoRA Adapter Evaluation

**Best for:** Fine-tuned models, post-training validation, adapter comparison

- **Purpose:** Evaluate LoRA-adapted models against baselines
- **Models:** Phi-3.5, TinyLlama with LoRA adapters
- **Dataset:** Chat JSONL (messages with role/content)
- **Metrics:** accuracy, perplexity, bleu, rouge, token_efficiency
- **Speed:** ~2-5 samples/min (depends on model size)

```bash
python .\scripts\evaluate_lora_model.py \
  --model-path data_out/lora_training/phi35 \
  --dataset datasets/chat/dolly \
  --max-samples 100 \
  --metric accuracy \
  --metric bleu
```

### 3. Quantum Model Evaluation

**Best for:** Quantum classifiers, circuit validation, QPU performance testing

- **Purpose:** Evaluate quantum circuits on classical hardware + simulators
- **Models:** Qiskit/Pennylane circuits, quantum classifiers
- **Dataset:** Numerical features (CSV), labels
- **Metrics:** accuracy, precision, recall, f1_score, roc_auc
- **Speed:** ~10-50 samples/sec (simulator), ~1-10 QPU circuits/sec

```bash
python .\scripts\evaluate_quantum_model.py \
  --model quantum-ai/results/heart_disease_model.json \
  --dataset datasets/quantum/heart_disease.csv \
  --metric accuracy \
  --metric f1_score
```

### 4. Azure OpenAI (LLM API) Evaluation

**Best for:** Baseline comparison, production models, cost tracking

- **Purpose:** Evaluate Azure OpenAI deployment against test dataset
- **Models:** gpt-4, gpt-4o, gpt-35-turbo
- **Dataset:** Chat JSONL, structured prompts
- **Metrics:** accuracy, response_time, cost_per_token
- **Speed:** ~1-5 samples/sec (API rate-limited)
- **Cost:** ~$0.001-0.01 per evaluation run

```bash
python .\scripts\evaluate_azure_model.py \
  --deployment gpt-4o-mini \
  --dataset datasets/chat/dolly \
  --max-samples 50 \
  --metric accuracy
```

### 5. Batch Evaluation (Multi-Model)

**Best for:** Model comparison, comprehensive testing, result aggregation

- **Purpose:** Parallel evaluation of multiple models with ranking
- **Concurrency:** 3 models in parallel by default (configurable)
- **Output:** Aggregated results, rankings, comparison reports
- **Speed:** ~3x faster than sequential evaluation

```bash
python .\scripts\batch_evaluator.py \
  --config config/evaluation/batch_eval_config.yaml \
  --evaluate-all \
  --export markdown
```

---

## Tools & Scripts

### `evaluate_local_model.py`

**Lightweight offline evaluator** (no dependencies beyond Python stdlib)

```bash
python .\scripts\evaluate_local_model.py \
  --dataset datasets/chat/mixed_chat \
  --max-samples 20 \
  --metric accuracy \
  --metric determinism \
  --output-format json \
  --save-dir results/local_eval
```

**Metrics:**

- `accuracy` — exact string match against expected/label
- `response_time` — avg ms per prediction
- `determinism` — fraction of consistent predictions (0..1)
- `basic_bleu` — unigram overlap (0..1)

**Output:** `results/local_eval/results.json`

---

### `evaluate_lora_model.py`

**LoRA adapter evaluator** (uses transformers + torch)

```bash
python .\scripts\evaluate_lora_model.py \
  --model-path data_out/lora_training/phi35 \
  --dataset datasets/chat/dolly \
  --max-samples 100 \
  --metric accuracy \
  --metric bleu \
  --metric rouge \
  --batch-size 4 \
  --save-dir results/lora_eval
```

**Metrics:**

- `accuracy` — exact match on responses
- `bleu` — BLEU-4 score
- `rouge` — ROUGE-L score
- `perplexity` — model perplexity
- `token_efficiency` — avg tokens used vs dataset

**Output:** `results/lora_eval/results.json` + model artifact references

---

### `evaluate_quantum_model.py`

**Quantum circuit evaluator** (uses qiskit/pennylane)

```bash
python .\scripts\evaluate_quantum_model.py \
  --model quantum-ai/results/heart_disease_model.json \
  --dataset datasets/quantum/heart_disease.csv \
  --max-samples 200 \
  --metric accuracy \
  --metric precision \
  --metric recall \
  --metric f1_score
```

**Metrics:**

- `accuracy` — classification accuracy
- `precision` — true positives / (true + false positives)
- `recall` — true positives / (true + false negatives)
- `f1_score` — harmonic mean of precision/recall
- `roc_auc` — area under ROC curve
- `cm` — confusion matrix (saved as JSON)

**Output:** `results/quantum_eval/results.json` + circuit analysis

---

### `batch_evaluator.py`

**Multi-model parallel evaluator** (ThreadPoolExecutor)

```bash
# Scan and evaluate all found models
python .\scripts\batch_evaluator.py \
  --scan-models \
  --evaluate-all \
  --export markdown \
  --export html

# Use config file
python .\scripts\batch_evaluator.py \
  --config config/evaluation/batch_eval_config.yaml \
  --max-workers 4

# Compare specific model types
python .\scripts\batch_evaluator.py \
  --compare lora azure openai local \
  --export csv
```

**Output:**

- `data_out/batch_evaluator/results.json` — aggregated results
- `data_out/batch_evaluator/ranking.json` — model ranking
- `data_out/batch_evaluator/status.json` — execution status
- `exports/batch_eval_*.{html,csv,md}` — formatted reports

---

### `evaluation_autorun.py`

**YAML-driven evaluation orchestrator** (sequential job execution)

```bash
# Dry-run (validate all configs without execution)
python .\scripts\evaluation_autorun.py --dry-run

# Run all enabled jobs
python .\scripts\evaluation_autorun.py

# Run specific job
python .\scripts\evaluation_autorun.py --job eval_lora_phi35_full

# List all jobs
python .\scripts\evaluation_autorun.py --list

# Monitor progress
python .\scripts\status_dashboard.py --watch
```

**Config:** `config/evaluation/evaluation_autorun.yaml`

**Output:**

- `data_out/evaluation_autorun/<job>/<timestamp>/results.json`
- `data_out/evaluation_autorun/<job>/last_run.json`
- `data_out/evaluation_autorun/status.json` — aggregate status

---

### `results_exporter.py`

**Multi-format result export** (JSON, CSV, Excel, HTML, Markdown)

```bash
# Export evaluation results
python .\scripts\results_exporter.py \
  --source evaluation_autorun \
  --all \
  --format markdown

# Compare multiple orchestrators
python .\scripts\results_exporter.py \
  --compare autotrain evaluation_autorun batch_evaluator \
  --format html

# Export to Excel
python .\scripts\results_exporter.py \
  --source batch_evaluator \
  --format excel \
  --output-file reports/batch_results.xlsx

# Export with filters
python .\scripts\results_exporter.py \
  --source evaluation_autorun \
  --format csv \
  --status succeeded
```

**Formats:**

- `json` — Raw JSON export
- `csv` — Tabular CSV (Excel-compatible)
- `html` — Interactive HTML report
- `markdown` — Markdown table + summary
- `excel` — Excel workbook with charts

---

### `training_analytics.py`

**Performance trends & insights**

```bash
# View training performance trends
python .\scripts\training_analytics.py

# Export training metrics
python .\scripts\training_analytics.py --export markdown

# Identify performance degradation
python .\scripts\training_analytics.py --analysis degradation

# Compare model variants
python .\scripts\training_analytics.py --compare phi35_lr_low phi35_lr_high
```

**Output:**

- Mean/median/max accuracy
- Performance improvement rates
- Plateau detection
- Model variant comparison

---

### `metrics_ranker.py`

**Model ranking & comparison**

```bash
# Rank models by composite score
python .\scripts\metrics_ranker.py --ranking

# Generate comparison report
python .\scripts\metrics_ranker.py --compare --export html

# Identify best model per category
python .\scripts\metrics_ranker.py --best-per-category
```

---

## Configuration

### `config/evaluation/evaluation_autorun.yaml`

YAML-based job configuration for sequential evaluation runs.

```yaml
version: 1

jobs:
  # Smoke test (fast, minimal samples)
  - name: eval_smoke_test
    enabled: true
    model_type: lora
    model_path: data_out/lora_training/phi35
    dataset: datasets/chat/mixed_chat
    max_samples: 10
    metrics:
      - accuracy
      - response_time
    output_format: json
    save_results: true

  # Full evaluation (comprehensive)
  - name: eval_lora_phi35_full
    enabled: true
    model_type: lora
    model_path: data_out/lora_training/phi35
    dataset: datasets/chat/dolly
    max_samples: 100
    metrics:
      - accuracy
      - bleu
      - rouge
      - response_time
      - token_efficiency
    output_format: json
    batch_size: 4

  # Quantum evaluation
  - name: eval_quantum_heart
    enabled: true
    model_type: quantum
    model_path: quantum-ai/results/heart_disease_model.json
    dataset: datasets/quantum/heart_disease.csv
    metrics:
      - accuracy
      - f1_score
    output_format: json

  # Azure baseline (credentials required)
  - name: eval_azure_baseline
    enabled: false
    model_type: azure
    azure_deployment: gpt-4o-mini
    dataset: datasets/chat/mixed_chat
    max_samples: 50
    metrics:
      - accuracy
```

**Job Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | ✓ | Unique job identifier |
| enabled | bool | ✓ | Skip job if false |
| model_type | string | ✓ | lora, azure, openai, local, quantum |
| model_path | string | ✓ | Path to model (or deployment name for azure) |
| dataset | string | ✓ | Path to evaluation dataset |
| max_samples | int/null | ✗ | Max samples to evaluate (null = all) |
| metrics | list[string] | ✓ | List of metric names |
| batch_size | int | ✗ | Batch size (default: 8) |
| output_format | string | ✗ | json, csv, html (default: json) |
| save_results | bool | ✗ | Save results to data_out/ (default: true) |

### `config/evaluation/batch_eval_config.yaml`

Configuration for parallel batch evaluation.

```yaml
evaluation_tasks:
  - model_id: lora_phi35_mixed
    model_type: lora
    model_path: data_out/lora_training/phi35_mixed_chat
    dataset: datasets/chat/mixed_chat
    metrics:
      - accuracy
      - bleu
    max_samples: 100
    batch_size: 8

  - model_id: lora_phi35_dolly
    model_type: lora
    model_path: data_out/lora_training/phi35_dolly
    dataset: datasets/chat/dolly
    metrics:
      - accuracy
      - f1_score
    max_samples: 100

  - model_id: quantum_heart
    model_type: quantum
    model_path: quantum-ai/results/heart_disease_model.json
    dataset: datasets/quantum/heart_disease.csv
    metrics:
      - accuracy
      - precision
      - recall

  - model_id: local_baseline
    model_type: local
    dataset: datasets/chat/mixed_chat
    metrics:
      - accuracy
      - response_time
    max_samples: 50
```

---

## Running Evaluations

### Basic Workflow

#### 1. Evaluate a single model (quick test)

```bash
# LoRA model on small sample
python .\scripts\evaluate_lora_model.py \
  --model-path data_out/lora_training/phi35 \
  --dataset datasets/chat/mixed_chat \
  --max-samples 20 \
  --metric accuracy \
  --metric bleu
```

#### 2. Run batch evaluation (all models)

```bash
# Scan available models and evaluate in parallel
python .\scripts\batch_evaluator.py --scan-models --evaluate-all

# View results
python .\scripts\results_exporter.py \
  --source batch_evaluator \
  --format markdown
```

#### 3. Run orchestrated evaluation (YAML-driven)

```bash
# Validate configuration
python .\scripts\evaluation_autorun.py --dry-run

# Execute all jobs
python .\scripts\evaluation_autorun.py

# Monitor progress
python .\scripts\status_dashboard.py --watch

# Export final results
python .\scripts\results_exporter.py \
  --source evaluation_autorun \
  --format html
```

### Integration with CI/CD

```bash
# In CI pipeline: fast local smoke test (2-3 minutes)
python .\scripts\evaluate_local_model.py \
  --dataset datasets/chat/mixed_chat \
  --max-samples 10 \
  --metric accuracy \
  --metric determinism

# Check if accuracy met threshold
$results = Get-Content results/local_eval/results.json | ConvertFrom-Json
if ($results.summary.accuracy -lt 0.7) {
  Write-Error "Accuracy below threshold"
  exit 1
}
```

### Integration with Training Pipelines

```bash
# After training: immediate evaluation
python .\scripts\train_and_promote.py \
  --quick \
  --auto-promote \
  --auto-evaluate  # Triggers evaluation_autorun on trained models
```

---

## Metrics Reference

### Common Metrics

| Metric | Type | Range | Formula | Notes |
|--------|------|-------|---------|-------|
| accuracy | Classification | 0..1 | correct / total | Exact match |
| precision | Classification | 0..1 | TP / (TP+FP) | Positive predictive value |
| recall | Classification | 0..1 | TP / (TP+FN) | Sensitivity, true positive rate |
| f1_score | Classification | 0..1 | 2×(P×R)/(P+R) | Harmonic mean of P & R |
| roc_auc | Classification | 0..1 | Area under ROC | Threshold-independent |
| bleu | Language | 0..1 | N-gram precision | BLEU-4 default |
| rouge | Language | 0..1 | F1 of n-grams | ROUGE-L default |
| perplexity | Language | 1..∞ | exp(avg_loss) | Lower is better |
| response_time | Performance | ms | wall-clock time | Per-prediction average |
| token_efficiency | Language | 0..100 | used / budget % | Avg tokens vs budget |
| determinism | Consistency | 0..1 | matches / runs | Run twice, compare |

### Model-Specific Metrics

**LoRA Adapters:**

- accuracy, perplexity, bleu, rouge, token_efficiency, response_time

**Quantum Classifiers:**

- accuracy, precision, recall, f1_score, roc_auc, confusion_matrix

**Azure OpenAI:**

- accuracy, response_time, cost_per_token, tokens_per_call

**Local (Echo):**

- accuracy, response_time, determinism, basic_bleu

---

## Integration with Orchestrators

### With `autotrain.py`

After training jobs complete, optionally trigger evaluation:

```bash
# In autotrain.yaml, add post-train hook
on_job_complete:
  - trigger: evaluation_autorun
    jobs:
      - eval_lora_phi35_full
```

### With `master_orchestrator.py`

Schedule regular evaluation cycles:

```yaml
# config/master_orchestrator.yaml
workflows:
  evaluation_cycle:
    schedule: "0 3 * * *"  # 3 AM daily
    steps:
      - action: run_evaluation_autorun
        all_jobs: true
      - action: export_results
        format: html
        destination: exports/daily_report.html
```

### With CI/CD Pipelines

```bash
# In .github/workflows/ci.yml or similar
- name: Run evaluation tests
  run: |
    python .\scripts\evaluate_local_model.py \
      --dataset datasets/chat/mixed_chat \
      --max-samples 10 \
      --metric accuracy \
    
    # Fail if accuracy drops below threshold
    python -c "
    import json
    with open('results/local_eval/results.json') as f:
      data = json.load(f)
      if data['summary']['accuracy'] < 0.7:
        exit(1)
    "
```

---

## Troubleshooting

### Common Issues

#### 1. "Model not found" error

```bash
# Check if model path is correct
ls data_out/lora_training/

# Verify required files (for LoRA)
# Should have: adapter_config.json, adapter_model.safetensors, tokenizer.json
```

#### 2. "Dataset file not found"

```bash
# List available datasets
ls datasets/chat/
ls datasets/quantum/

# Check if path uses forward slashes
# Should be: datasets/chat/dolly (not datasets\chat\dolly)
```

#### 3. "Out of memory" during evaluation

```bash
# Reduce batch size
python .\scripts\evaluate_lora_model.py \
  --model-path data_out/lora_training/phi35 \
  --dataset datasets/chat/dolly \
  --batch-size 2  # Smaller batches

# Or reduce max_samples
python .\scripts\evaluate_lora_model.py \
  --model-path data_out/lora_training/phi35 \
  --dataset datasets/chat/dolly \
  --max-samples 50
```

#### 4. "Provider not detected" (Azure OpenAI)

```bash
# Check environment variables
echo $env:AZURE_OPENAI_API_KEY
echo $env:AZURE_OPENAI_ENDPOINT
echo $env:AZURE_OPENAI_DEPLOYMENT
echo $env:AZURE_OPENAI_API_VERSION

# Set if missing
$env:AZURE_OPENAI_API_KEY = "your-key"
$env:AZURE_OPENAI_ENDPOINT = "https://your-resource.openai.azure.com/"
$env:AZURE_OPENAI_DEPLOYMENT = "gpt-4o-mini"
$env:AZURE_OPENAI_API_VERSION = "2024-10-01"
```

#### 5. "Quantum backend not available"

```bash
# For local simulator (no credentials needed)
python .\scripts\evaluate_quantum_model.py \
  --model quantum-ai/results/heart_disease_model.json \
  --dataset datasets/quantum/heart_disease.csv \
  --simulator qiskit_aer  # Use local simulator

# For Azure Quantum (requires credentials)
# Ensure AZURE_QUANTUM_SUBSCRIPTION and other vars are set
echo $env:AZURE_QUANTUM_SUBSCRIPTION
```

### Debug Modes

```bash
# Run with verbose logging
python .\scripts\evaluate_lora_model.py \
  --model-path data_out/lora_training/phi35 \
  --dataset datasets/chat/dolly \
  --verbose

# Run with debug output
python .\scripts\batch_evaluator.py \
  --scan-models \
  --debug

# Save intermediate results
python .\scripts\evaluation_autorun.py \
  --job eval_lora_phi35_full \
  --save-intermediates
```

### Monitoring & Observability

```bash
# Watch evaluation progress in real-time
python .\scripts\status_dashboard.py --watch

# Check health status
curl http://localhost:7071/api/ai/status | jq '.evaluation'

# View logs
tail -f data_out/evaluation_autorun/evaluation.log

# Export diagnostics
python .\scripts\results_exporter.py \
  --source evaluation_autorun \
  --include-metadata \
  --format json
```

---

## Advanced Usage

### Custom Evaluation Metrics

To add a custom metric, extend the evaluator:

```python
# In evaluate_lora_model.py, add custom metric function

def compute_custom_metric(predictions, references, **kwargs):
    """Custom metric implementation."""
    # Your logic here
    return score

# Register metric
METRICS["my_custom_metric"] = compute_custom_metric

# Use in config
metrics:
  - accuracy
  - my_custom_metric  # New custom metric
```

### Distributed Evaluation

```bash
# Run batch evaluation with more workers (parallel)
python .\scripts\batch_evaluator.py \
  --config config/evaluation/batch_eval_config.yaml \
  --max-workers 8  # More parallel jobs

# Monitor resource usage during eval
python .\scripts\resource_monitor.py --stream --duration 300
```

### Automated Threshold Checks

```bash
# Create a threshold check script
$results = python .\scripts\evaluate_lora_model.py \
  --model-path data_out/lora_training/phi35 \
  --dataset datasets/chat/dolly \
  --metric accuracy | ConvertFrom-Json

if ($results.summary.accuracy -lt 0.85) {
  Write-Warning "Accuracy below 0.85 threshold"
} elseif ($results.summary.accuracy -gt 0.95) {
  Write-Host "Model ready for promotion!"
  # Trigger deployment
  python .\scripts\model_deployer.py --deploy best
}
```

---

## Best Practices

1. **Always start with small samples** — Use `--max-samples 10-20` for quick validation
2. **Use local evaluation in CI** — Avoid Azure/OpenAI API costs in CI pipelines
3. **Save results consistently** — Always use `--save-results` and check `status.json`
4. **Monitor resource usage** — Run `resource_monitor.py --stream` during evaluations
5. **Version your evaluation configs** — Track `evaluation_autorun.yaml` in git
6. **Compare against baselines** — Always include a local/echo baseline for comparison
7. **Export results for sharing** — Use HTML/Markdown formats for easy sharing
8. **Schedule regular evals** — Use `master_orchestrator.py` for daily/weekly eval cycles

---

## Summary

The evaluation framework provides:

✅ **Multiple evaluation tools** — Local, LoRA, Quantum, Azure, Batch  
✅ **YAML-driven orchestration** — Declarative job definitions  
✅ **Comprehensive metrics** — Accuracy, BLEU, F1, response time, etc.  
✅ **Flexible export** — JSON, CSV, Excel, HTML, Markdown  
✅ **CI/CD integration** — Fast offline smoke tests  
✅ **Monitoring & observability** — Status dashboards, analytics, logging  

Use evaluation results to:

- Validate models before deployment
- Compare model variants (hyperparameter tuning)
- Track performance over time
- Detect performance degradation
- Generate reports for stakeholders
- Guide automated model promotion

For questions or issues, check the [Troubleshooting](#troubleshooting) section or review `scripts/evaluation/evaluation_autorun.py --help`.
