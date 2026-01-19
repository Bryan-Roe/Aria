# Evaluation Framework — Index & Navigation

**Last updated:** December 8, 2025

Central index for navigating the evaluation framework documentation and code.

## 📚 Documentation

### For Quick Start (5-10 minutes)

👉 **Start here:** [`EVALUATION_QUICKREF.md`](EVALUATION_QUICKREF.md)

- One-page quick reference
- Common command examples
- Troubleshooting cheat sheet
- Environment setup

### For Complete Understanding (1-2 hours)

👉 **Main guide:** [`EVALUATION_FRAMEWORK.md`](EVALUATION_FRAMEWORK.md)

- Architecture overview
- 5 evaluation types (Local, LoRA, Quantum, Azure, Batch)
- 8 evaluation tools
- Configuration reference
- Metrics definitions
- CI/CD integration
- Troubleshooting with examples

### For Advanced Usage (2-3 hours)

👉 **Advanced patterns:** [`EVALUATION_BEST_PRACTICES.md`](EVALUATION_BEST_PRACTICES.md)

- Custom evaluation metrics
- Extending evaluators
- Integration patterns
- Performance optimization
- Distributed evaluation
- Monitoring & observability
- Data management & versioning

### For Implementation Summary

👉 **What was added:** [`EVALUATION_FRAMEWORK_SUMMARY.md`](EVALUATION_FRAMEWORK_SUMMARY.md)

- Overview of new components
- Key features
- Integration points
- Testing approach
- Best practices included

---

## 💻 Code & Utilities

### Core Evaluation Utilities

**File:** `shared/evaluation_utils.py` (700+ lines)

**Key Classes:**

- `EvaluationMetrics` — Container for evaluation metrics
- `EvaluationResult` — Complete evaluation result with metadata
- `AggregatedResults` — Multi-evaluation aggregation and statistics
- `QualityThresholds` — Quality gate definitions

**Metric Functions:**

- `compute_accuracy()` — Exact match rate
- `compute_bleu()` — BLEU-4 unigram overlap
- `compute_rouge_l()` — LCS-based score
- `compute_precision()`, `compute_recall()`, `compute_f1_score()`
- `compute_perplexity()` — Language model perplexity
- `compute_determinism()` — Consistency across runs
- `compute_token_efficiency()` — Token usage metrics

**Dataset Functions:**

- `load_dataset()` — Auto-detect JSONL/JSON/CSV
- `load_jsonl_dataset()`, `load_json_dataset()`, `load_csv_dataset()`

**Utility Functions:**

- `setup_evaluation_logging()` — Configure logging
- Result serialization (save/load JSON)
- Quality gate checking

### Test Utilities

**File:** `tests/evaluation_test_utils.py` (600+ lines)

**Test Fixtures:**

- `sample_jsonl_dataset` — JSONL test dataset
- `sample_json_dataset` — JSON test dataset
- `sample_csv_dataset` — CSV test dataset
- `sample_evaluation_result` — Test result object
- `sample_aggregated_results` — Test aggregated results
- `evaluation_temp_dir` — Temporary directory fixture
- `eval_test_context` — Test context manager

**Mock Evaluators:**

- `MockLORAEvaluator` — Simulate LoRA evaluation
- `MockQuantumEvaluator` — Simulate quantum evaluation

**Assertion Helpers:**

- `assert_evaluation_result_valid()` — Validate structure
- `assert_metrics_in_range()` — Check metric bounds
- `assert_result_passes_threshold()` — Quality gate validation

**Comparison Helpers:**

- `compare_results()` — Compare two results
- `rank_results()` — Rank by composite score

---

## 🛠️ Evaluation Scripts

### Local Evaluation (Offline)

**Script:** `scripts/evaluate_local_model.py`

- No dependencies beyond Python stdlib
- Echo baseline predictor
- Fast (~1 sample/sec)
- Free, no credentials
- **Best for:** CI/CD, quick validation, offline testing

```bash
python .\scripts\evaluate_local_model.py \
  --dataset datasets/chat/mixed_chat \
  --max-samples 10 \
  --metric accuracy
```

### LoRA Adapter Evaluation

**Script:** `scripts/evaluate_lora_model.py`

- Phi-3.5, TinyLlama support
- Fine-tuned model evaluation
- ~2-5 samples/min
- Free (GPU required)
- **Best for:** Production models, post-training validation

```bash
python .\scripts\evaluate_lora_model.py \
  --model-path data_out/lora_training/phi35 \
  --dataset datasets/chat/dolly \
  --max-samples 100 \
  --metric accuracy \
  --metric bleu
```

### Quantum Model Evaluation

**Script:** `scripts/evaluate_quantum_model.py`

- Qiskit/Pennylane circuits
- Classifier validation
- ~10-50 samples/sec (simulator)
- Free (simulator), costs vary (QPU)
- **Best for:** Quantum circuits, classifier validation

```bash
python .\scripts\evaluate_quantum_model.py \
  --model quantum-ai/results/heart_disease_model.json \
  --dataset datasets/quantum/heart_disease.csv \
  --metric accuracy \
  --metric f1_score
```

### Azure OpenAI Evaluation

**Script:** `scripts/evaluate_azure_model.py`

- gpt-4, gpt-4o, gpt-35-turbo
- Baseline comparison
- ~1-5 samples/sec
- ~$0.001-0.01 per eval
- **Best for:** Production baselines, multi-provider comparison

```bash
python .\scripts\evaluate_azure_model.py \
  --deployment gpt-4o-mini \
  --dataset datasets/chat/dolly \
  --max-samples 50 \
  --metric accuracy
```

### Batch Multi-Model Evaluation

**Script:** `scripts/batch_evaluator.py`

- Parallel evaluation (ThreadPoolExecutor)
- Model comparison
- Aggregated results & ranking
- ~3x faster than sequential
- **Best for:** Model comparison, comprehensive testing

```bash
python .\scripts\batch_evaluator.py \
  --scan-models \
  --evaluate-all \
  --max-workers 4 \
  --export markdown \
  --export html
```

### YAML-Driven Orchestrator

**Script:** `scripts/evaluation/evaluation_autorun.py`

- Sequential job execution
- Configuration-driven (YAML)
- Dry-run validation
- Comprehensive logging
- **Best for:** Production evaluation workflows

```bash
# Validate
python .\scripts\evaluation_autorun.py --dry-run

# Run all
python .\scripts\evaluation_autorun.py

# Run specific job
python .\scripts\evaluation_autorun.py --job eval_lora_phi35_full

# List jobs
python .\scripts\evaluation_autorun.py --list
```

### Results Export

**Script:** `scripts/results_exporter.py`

- Multi-format export
- Aggregation & filtering
- Comparison reports
- **Best for:** Sharing results, reporting

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

### Analytics & Insights

**Script:** `scripts/training_analytics.py`

- Performance trends
- Degradation detection
- Model variant comparison

**Script:** `scripts/metrics_ranker.py`

- Model ranking by score
- Comparative analysis
- Category-wise best models

---

## ⚙️ Configuration

### Main Evaluation Config

**File:** `config/evaluation/evaluation_autorun.yaml`

Structure:

```yaml
version: 1
jobs:
  - name: eval_name
    enabled: true
    model_type: lora|azure|openai|local|quantum
    model_path: path/to/model
    dataset: path/to/dataset
    max_samples: 100
    metrics: [accuracy, bleu, f1_score]
    batch_size: 4
    output_format: json
    save_results: true
```

**Example jobs included:**

- `eval_smoke_test` — Quick validation (10 samples)
- `eval_lora_phi35_full` — Comprehensive LoRA evaluation (100 samples)
- `eval_azure_baseline` — Azure OpenAI baseline
- `eval_quantum_heart` — Quantum classifier evaluation
- `eval_local_baseline` — Local baseline (echo)
- `eval_phi35_lr_low/high` — Hyperparameter variants

### Batch Evaluation Config

**File:** `config/evaluation/batch_eval_config.yaml`

Structure:

```yaml
evaluation_tasks:
  - model_id: id
    model_type: lora|azure|quantum|local
    model_path: path
    dataset: path
    metrics: [metric1, metric2]
    max_samples: 100
    batch_size: 8
```

---

## 📊 Output Structure

```
data_out/
├── evaluation_autorun/
│   ├── eval_job_name/
│   │   ├── 2024-12-08_10-30-45/
│   │   │   ├── result.json
│   │   │   └── stdout.log
│   │   ├── 2024-12-08_14-15-20/
│   │   └── last_run.json
│   ├── status.json
│   └── evaluation.log
│
├── batch_evaluator/
│   ├── results.json (all results)
│   ├── ranking.json (ranked models)
│   ├── status.json (execution status)
│   └── evaluation.log
│
└── evaluation_*/
    └── results/
```

**Result JSON Structure:**

```json
{
  "model_id": "model_name",
  "model_type": "lora|azure|quantum|local|batch",
  "dataset": "datasets/chat/dolly",
  "timestamp": "2024-12-08T10:30:45+00:00",
  "status": "succeeded|failed|pending",
  "samples_evaluated": 100,
  "duration_seconds": 45.0,
  "metrics": {
    "accuracy": 0.95,
    "bleu": 0.87,
    "f1_score": 0.93,
    "response_time_ms": 150.0
  },
  "error": null,
  "config": { ... }
}
```

---

## 🚀 Quick Start Paths

### Path 1: Just want to evaluate a model? (10 minutes)

1. Read: [`EVALUATION_QUICKREF.md`](EVALUATION_QUICKREF.md)
2. Run: `python .\scripts\evaluate_local_model.py --dataset datasets/chat/mixed_chat --max-samples 10 --metric accuracy`
3. Adapt: Change `--dataset`, `--max-samples`, `--metric` as needed
4. Done! Results in `results/local_eval/results.json`

### Path 2: Want to understand the full framework? (1-2 hours)

1. Start: [`EVALUATION_FRAMEWORK.md`](EVALUATION_FRAMEWORK.md) → Quick Start section
2. Learn: Read each evaluation type section
3. Configure: Review `config/evaluation/evaluation_autorun.yaml`
4. Run: `python .\scripts\evaluation_autorun.py --dry-run` → `python .\scripts\evaluation_autorun.py`
5. Export: `python .\scripts\results_exporter.py --source evaluation_autorun --format html`

### Path 3: Need advanced customization? (2-3 hours)

1. Foundation: [`EVALUATION_BEST_PRACTICES.md`](EVALUATION_BEST_PRACTICES.md)
2. Custom metrics: Implement in `shared/evaluation_utils.py`
3. Custom evaluator: Copy `scripts/evaluate_lora_model.py` and adapt
4. Integration: Modify training/CI scripts to call evaluation
5. Test: Use `tests/evaluation_test_utils.py` fixtures

### Path 4: Integrating with CI/CD? (30 minutes)

1. Reference: [`EVALUATION_FRAMEWORK.md`](EVALUATION_FRAMEWORK.md) → CI/CD Integration section
2. Copy template from "Integration with CI/CD Pipelines"
3. Adapt to your CI system (.github/workflows, GitLab CI, etc.)
4. Test locally: `python .\scripts\evaluate_local_model.py --max-samples 10 --metric accuracy`
5. Deploy & validate

---

## 📋 Metrics Reference

### Classification (0..1)

- `accuracy` — Exact match rate
- `precision` — TP / (TP + FP)
- `recall` — TP / (TP + FN)
- `f1_score` — Harmonic mean of precision/recall
- `roc_auc` — Area under ROC curve

### Language Models (0..1 or varies)

- `bleu` — BLEU-4 unigram overlap score
- `rouge` — ROUGE-L LCS-based score
- `perplexity` — exp(mean_loss), ≥1 (lower better)
- `token_efficiency` — % tokens vs budget (0..100)

### Performance

- `response_time_ms` — Milliseconds (lower better)
- `cost_per_token` — $ (lower better)
- `determinism` — Consistency across runs (0..1)

---

## 🔗 Integration Checklist

- [ ] Reviewed `EVALUATION_FRAMEWORK.md` for architecture
- [ ] Read relevant section for your evaluation type
- [ ] Set up environment variables (if Azure/Quantum)
- [ ] Created/updated `config/evaluation/evaluation_autorun.yaml`
- [ ] Ran dry-run: `python .\scripts\evaluation_autorun.py --dry-run`
- [ ] Executed evaluation: `python .\scripts\evaluation_autorun.py`
- [ ] Exported results: `python .\scripts\results_exporter.py --format html`
- [ ] Integrated with training/CI as needed
- [ ] Set up monitoring/alerting (optional)

---

## 📞 Support

**Questions?**

- Quick answers: See [`EVALUATION_QUICKREF.md`](EVALUATION_QUICKREF.md) Troubleshooting section
- Detailed help: See [`EVALUATION_FRAMEWORK.md`](EVALUATION_FRAMEWORK.md) Troubleshooting section
- Advanced patterns: See [`EVALUATION_BEST_PRACTICES.md`](EVALUATION_BEST_PRACTICES.md)

**Found an issue?**

1. Check troubleshooting guides above
2. Review script help: `python .\scripts\evaluate_lora_model.py --help`
3. Check logs: `tail -f data_out/evaluation_autorun/evaluation.log`
4. Run with `--verbose` flag for detailed output

**Want to contribute?**

- Add custom metrics to `shared/evaluation_utils.py`
- Create new evaluator script (follow pattern from existing scripts)
- Add test cases to `tests/evaluation_test_utils.py`
- Update configuration examples

---

## 🎯 Key Files Summary

| File | Purpose | Size |
|------|---------|------|
| `EVALUATION_FRAMEWORK.md` | Complete guide | 8,000+ words |
| `EVALUATION_BEST_PRACTICES.md` | Advanced patterns | 6,000+ words |
| `EVALUATION_QUICKREF.md` | One-page cheat sheet | 500+ words |
| `shared/evaluation_utils.py` | Core utilities | 700+ lines |
| `tests/evaluation_test_utils.py` | Test infrastructure | 600+ lines |
| `config/evaluation/evaluation_autorun.yaml` | Job definitions | 130+ lines |
| `config/evaluation/batch_eval_config.yaml` | Batch config | 50+ lines |

---

**Ready to get started?** 👇

**Start here:** [`EVALUATION_QUICKREF.md`](EVALUATION_QUICKREF.md) for quick reference, or [`EVALUATION_FRAMEWORK.md`](EVALUATION_FRAMEWORK.md) for the complete guide.
