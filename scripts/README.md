# Scripts

This folder contains automation utilities, orchestrators, and tools for the QAI workspace.

## 🎯 Quick Start Commands

### Directory Layout (CLI grouping)
- Training CLI: [training/cli](training/cli) (auto_data_train, analyze_learning_progress, self_train_synthetic, self_learning_chat, fast_validate, final_validation)
- Monitoring CLI: [monitoring/cli](monitoring/cli) (aria_diagnostic, validate_dashboard, validate_buttons, validate_workflows)
- Shims: legacy paths in [scripts/](.) still dispatch to the moved files for backwards compatibility.

### Training Automation

```powershell
# Quick multi-model training with evaluation
python .\scripts\automated_training_pipeline.py --quick

# TinyLlama ultrafast iteration
python .\scripts\automated_training_pipeline.py --models tinyllama --quick

# Parallel training (Phi + Qwen)
python .\scripts\parallel_train.py --models phi,qwen --quick

# Single model training
python .\scripts\auto_data_train.py --model phi --quick
```

### Testing & Validation

```powershell
# Run all fast tests
python .\scripts\test_runner.py --all

# Unit tests only
python .\scripts\test_runner.py --unit

# Full CI pipeline
python .\scripts\ci_orchestrator.py --ci-pipeline

# Validate orchestrators
python .\scripts\ci_orchestrator.py --validate-all
```

### Quantum Operations

```powershell
# Run quantum training jobs
python .\scripts\quantum_autorun.py --dry-run

# Validate quantum environment
python -m pytest tests\test_validate_qiskit_env.py -v
```

## 📚 Core Automation Tools

### Training Orchestrators

#### `automated_training_pipeline.py`
**Purpose:** Single entry point for multi-model LoRA training with data generation, evaluation, and Azure ML spec emission.

**Key Features:**
- Generate synthetic data (phi, qwen, tinyllama)
- Sequential or parallel model training
- Evaluation with perplexity & diversity metrics
- Multiple ranking strategies (improvement, diversity, combined)
- Azure ML job spec emission
- Checkpoint cleanup

**Usage:**
```powershell
# Quick both models with evaluation
python .\scripts\automated_training_pipeline.py --quick

# Custom samples and ranking
python .\scripts\automated_training_pipeline.py --models phi --samples 300 --ranking-metric diversity_avg

# Generate data only
python .\scripts\automated_training_pipeline.py --generate-only --samples 200

# Emit Azure ML spec
python .\scripts\automated_training_pipeline.py --azure-ml-spec --quick --models phi,qwen
```

#### `parallel_train.py`
**Purpose:** Parallel execution of multiple LoRA training jobs with shared evaluation and ranking.

**Key Features:**
- Concurrent training via ThreadPoolExecutor
- Shared evaluation step (perplexity, diversity, echo ratio)
- Configurable ranking metrics
- Append-only status history
- Supports 5+ ranking strategies

**Usage:**
```powershell
# Train all models in parallel
python .\scripts\parallel_train.py --models phi,qwen,tinyllama --quick

# Custom ranking metric
python .\scripts\parallel_train.py --models phi,qwen --ranking-metric combined_improvement
```

#### `auto_data_train.py`
**Purpose:** Generate synthetic training data + single model LoRA training.

**Usage:**
```powershell
# Phi model with synthetic data
python .\scripts\auto_data_train.py --model phi --quick

# TinyLlama with custom samples
python .\scripts\auto_data_train.py --model tinyllama --samples 300
```

### Master Orchestrators

#### `master_orchestrator.py`
**Purpose:** High-level workflow coordination for complex training pipelines.

**Workflows:**
- `quick_validation`: Validate all configs
- `full_training`: Complete training cycle
- `evaluation_only`: Run evaluations on existing models

**Usage:**
```powershell
# Quick validation
python .\scripts\master_orchestrator.py --workflow quick_validation

# Check status
python .\scripts\master_orchestrator.py --status
```

#### `autotrain.py`
**Purpose:** HuggingFace AutoTrain wrapper with multi-job support.

**Usage:**
```powershell
# Dry run validation
python .\scripts\autotrain.py --dry-run

# Run all jobs
python .\scripts\autotrain.py

# Single job
python .\scripts\autotrain.py --job phi36_mixed_chat
```

### Testing Infrastructure

#### `test_runner.py` ⭐ **Recommended**
**Purpose:** Centralized test orchestrator with intelligent filtering and result aggregation.

**Test Suites:**
- `unit`: 40 fast tests (~0.5s)
- `integration`: 30 external service tests (~3s)
- `all_fast`: 83 tests excluding slow/azure (~10s)
- `autotrain`, `quantum`, `database`, `chat`: Focused suites

**Usage:**
```powershell
# Run all fast tests
python .\scripts\test_runner.py --all

# Unit tests with coverage
python .\scripts\test_runner.py --unit --coverage

# Watch mode (re-run on change)
python .\scripts\test_runner.py --unit --integration --watch

# List available suites
python .\scripts\test_runner.py --list-suites
```

**Features:**
- ANSI escape code handling
- Regex-based pytest output parsing
- Marker filtering (`not slow and not azure`)
- JSON + Markdown result reports
- Parallel suite execution
- Coverage integration

#### `ci_orchestrator.py`
**Purpose:** Continuous integration pipeline with 10 validation steps.

**Steps:**
1. Orchestrator validations (autotrain, quantum, evaluation)
2. Unit tests (via test_runner)
3. Dataset validation
4. Integration tests
5. Code quality checks
6. Security scanning
7. Deployment preparation
8. Azure ML validation

**Usage:**
```powershell
# Full CI pipeline
python .\scripts\ci_orchestrator.py --ci-pipeline

# Validate orchestrators only
python .\scripts\ci_orchestrator.py --validate-all
```

**Current Status:** 5/10 passing (all critical steps ✅)

### Evaluation & Analysis

#### `batch_evaluator.py`
**Purpose:** Parallel evaluation of multiple models with comprehensive result aggregation.

**Features:**
- Parallel model evaluation (ThreadPoolExecutor)
- Support for LoRA, Azure, OpenAI, Local, Quantum models
- Configurable metrics per model type
- Result ranking and comparison
- Export to JSON/Markdown/CSV

**Usage:**
```powershell
# Scan and evaluate all models
python .\scripts\batch_evaluator.py --scan-models --evaluate-all

# Compare specific models
python .\scripts\batch_evaluator.py --compare lora azure openai

# Export results
python .\scripts\batch_evaluator.py --export markdown --output report.md
```

#### `training_analytics.py`
**Purpose:** Analyze training metrics and generate performance reports.

**Usage:**
```powershell
# Analyze recent training runs
python .\scripts\training_analytics.py --recent 5

# Generate comparison report
python .\scripts\training_analytics.py --compare phi qwen tinyllama
```

### Azure ML Integration

#### `azureml_ci_validate.py`
**Purpose:** Validate and optionally submit Azure ML job specs.

**Features:**
- YAML schema validation
- Environment spec checking
- `.env` placeholder gating (prevents submission with unresolved credentials)
- Graceful fallback when Azure CLI not installed

**Usage:**
```powershell
# Validate latest job spec
python .\scripts\azureml_ci_validate.py

# Validate and submit
python .\scripts\azureml_ci_validate.py --submit

# Force submit (bypass gating)
python .\scripts\azureml_ci_validate.py --submit --force-submit
```

### Dataset Management

#### `validate_datasets.py`
**Purpose:** Validate dataset integrity across all categories.

**Categories:** `quantum`, `chat`, `all`

**Usage:**
```powershell
# Validate chat datasets
python .\scripts\validate_datasets.py --category chat

# Validate all
python .\scripts\validate_datasets.py --category all
```

#### `download_datasets.py`
**Purpose:** Download and organize datasets from HuggingFace.

**Usage:**
```powershell
# Download all configured datasets
python .\scripts\download_datasets.py

# Download specific dataset
python .\scripts\download_datasets.py --dataset dolly-15k
```

### Monitoring & Diagnostics

#### `resource_monitor.py`
**Purpose:** Monitor system resources during training.

**Usage:**
```powershell
# Single snapshot
python .\scripts\resource_monitor.py --snapshot

# Stream for 60 seconds
python .\scripts\resource_monitor.py --stream --duration 60
```

#### `system_health_check.py`
**Purpose:** Comprehensive system health validation.

**Checks:**
- Python environment
- Required packages
- GPU availability
- Disk space
- Dataset accessibility

**Usage:**
```powershell
python .\scripts\system_health_check.py
```

### SQL Integration

#### `sql_migrate.py`
**Purpose:** Database migration tool for chat/telemetry tables.

**Usage:**
```powershell
# Run migrations
python .\scripts\sql_migrate.py
```

#### `sql_health_monitor.py`
**Purpose:** Monitor SQL connection pool and query performance.

**Usage:**
```powershell
python .\scripts\sql_health_monitor.py
```

## 🔧 Utility Scripts

### PowerShell Scripts

- `Start-LocalLoraTraining.ps1`: Task Scheduler-friendly training wrapper
- `Analyze-TrainingLogs.ps1`: Parse and analyze training logs
- `quick_status.ps1`: Quick system status check
- `fast_train.ps1`: Rapid training shortcut

### Python Utilities

- `env_autofix.py`: Auto-fix environment issues
- `pre_commit_check.py`: Pre-commit validation hooks
- `metrics_ranker.py`: Rank models by custom metrics
- `results_exporter.py`: Export results to multiple formats

## 📖 Legacy Scripts (Reference)

### run_local_lora_training.py

One-command offline LoRA training for TinyLlama on CPU. It auto-creates a venv under `AI/microsoft_phi-silica-3.6_v1/local_train`, installs requirements, and runs the training script with a small dataset and minimal epochs so it completes quickly on Windows.

Usage (PowerShell):

```powershell
# From repo root
python .\scripts\run_local_lora_training.py

# Customize
python .\scripts\run_local_lora_training.py --max-samples 50 --epochs 2 --config local_config.yaml

# Force reinstall deps in the venv
python .\scripts\run_local_lora_training.py --reinstall

# Preview without training
python .\scripts\run_local_lora_training.py --dry-run
```

Outputs are written to `AI/microsoft_phi-silica-3.6_v1/local_train/outputs/final` (LoRA adapter + tokenizer files).

Notes:

- 4-bit quantization is disabled by default for Windows/CPU; the tiny training still runs fast with TinyLlama.
- The runner sets `HF_HUB_DISABLE_SYMLINKS_WARNING=1` to reduce warnings on Windows filesystems.

## Start-LocalLoraTraining.ps1 (Windows Task Scheduler friendly)

PowerShell wrapper that resolves paths, sets env, logs to a timestamped file, and runs the Python runner.

Usage (PowerShell):

```powershell
# From repo root (or any folder)
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-LocalLoraTraining.ps1 -MaxSamples 10 -Epochs 1 -Config local_config.yaml

# Optional flags
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-LocalLoraTraining.ps1 -Reinstall
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-LocalLoraTraining.ps1 -DryRun
```

Logs:

- Default log directory: `AI/microsoft_phi-silica-3.6_v1/local_train/logs`
- File name: `train_YYYYMMDD_HHMMSS.log`

Task Scheduler tip:

- Action: `Start a program`
- Program/script: `powershell.exe`
- Add arguments:
  `-NoProfile -ExecutionPolicy Bypass -File "C:\Users\Bryan\OneDrive\AI\scripts\Start-LocalLoraTraining.ps1" -MaxSamples 10 -Epochs 1`
- Start in: `C:\Users\Bryan\OneDrive\AI`

## VS Code task: one-click run

A task labeled `Run: Local LoRA training` is available. Open the Command Palette → “Run Task…” → select it to run.
