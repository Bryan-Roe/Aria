# AutoTrain – Declarative Fine-Tuning Orchestration

**AutoTrain** is a zero-dependency orchestrator for running LoRA fine-tuning jobs defined in YAML. It runs fully offline (after initial model download), supports both **HuggingFace** and **local** runners, and produces machine-readable status files for monitoring.

---

## Features

- **Declarative config** – Define jobs once in `autotrain.yaml`; run repeatedly without boilerplate.
- **Two runners** – Choose between the full HF stack (`train_lora.py`) or the streamlined local runner (`run_local_lora_training.py`).
- **Dry-run mode** – Validate configs, check file paths, and build commands without executing expensive GPU work.
- **Status tracking** – Every run writes JSON logs (`data_out/autotrain/<job>/last_run.json` and `data_out/autotrain/status.json`).
- **VS Code tasks** – Pre-configured tasks for quick access (dry-run and full run).
- **Azure Functions integration** – The `/api/ai/status` endpoint now surfaces the latest AutoTrain summary.

---

## Quick Start

### 1. Define Jobs in `autotrain.yaml`

Edit the top-level `autotrain.yaml` to declare one or more fine-tuning jobs:

```yaml
version: 1
jobs:
  - name: phi36_mixed_chat
    runner: hf
    config: AI/microsoft_phi-silica-3.6_v1/lora/lora.yaml
    dataset: datasets/chat/mixed_chat
    save_dir: data_out/lora_training
    epochs: 1
    max_train_samples: 64
    max_eval_samples: 16
    learning_rate: 0.0002
    lora_dropout: 0.1
```

**Key fields:**

- `name` (required) – Unique job identifier.
- `runner` (required) – `"hf"` or `"local"`.
- `dataset` (optional for local) – Path to dataset directory (train.json/test.json).
- `config` (optional) – Path to YAML config (lora.yaml or local_config.yaml).
- `save_dir` (optional) – Where to write checkpoints/adapters.
- `epochs`, `learning_rate`, `lora_dropout`, `max_train_samples`, etc. – Overrides from config.

### 2. Validate with Dry-Run

Check that paths exist, commands are valid, and dataset metadata is correct without starting training:

```powershell
python .\scripts\autotrain.py --dry-run
```

**Output:** JSON for each job with `"status": "validated"` or `"status": "missing"` (if files are absent).

### 3. Run a Single Job

Execute just one named job:

```powershell
python .\scripts\autotrain.py --job phi36_mixed_chat
```

**Result:** Logs to `data_out/autotrain/phi36_mixed_chat/<timestamp>/stdout.log` and `last_run.json`.

### 4. Run All Jobs

If you have multiple jobs defined, run them sequentially:

```powershell
python .\scripts\autotrain.py
```

**Result:** Each job executes in order. Non-zero exit if any fail.

---

## Job Runners

### HuggingFace Runner (`hf`)

- **Script:** `AI/microsoft_phi-silica-3.6_v1/scripts/train_lora.py`
- **Features:** Full HF Trainer stack, DeepSpeed support, streaming datasets, Azure Blob manifests, metrics logging.
- **When to use:** Production-scale runs, multi-GPU, cloud storage integrations.
- **Example job:**

  ```yaml
  - name: phi36_dolly_full
    runner: hf
    config: AI/microsoft_phi-silica-3.6_v1/lora/lora.yaml
    dataset: datasets/chat/dolly
    epochs: 3
    hf_model_id: microsoft/Phi-3.5-mini-instruct
  ```

### Local Runner (`local`)

- **Script:** `scripts/run_local_lora_training.py`
- **Features:** Lightweight, QLoRA-friendly, offline-first, simple YAML config (`local_config.yaml`).
- **When to use:** CPU-only or consumer GPU (RTX 3060, M1/M2), quick experiments, no Azure deps.
- **Example job:**

  ```yaml
  - name: local_quick_test
    runner: local
    config: AI/microsoft_phi-silica-3.6_v1/local_train/local_config.yaml
    epochs: 1
    max_train_samples: 10
  ```

---

## CLI Reference

```bash
python scripts/training/autotrain.py [OPTIONS]

Options:
  --config PATH      Path to autotrain.yaml (default: autotrain.yaml at repo root)
  --job NAME         Run only the named job
  --dry-run          Validate and print commands; do not execute
  --list             List configured jobs and exit (JSON)
  --reinstall        Force reinstall for local runner jobs (sets job.reinstall=true)
```

**Examples:**

```powershell
# Validate all jobs
python .\scripts\autotrain.py --dry-run

# List jobs
python .\scripts\autotrain.py --list

# Run a specific job
python .\scripts\autotrain.py --job phi36_mixed_chat

# Force venv reinstall for local runner jobs
python .\scripts\autotrain.py --job local_quick_test --reinstall

# Run all jobs
python .\scripts\autotrain.py
```

---

## Output Structure

```bash
data_out/
  autotrain/
    <job_name>/
      <timestamp>/
        stdout.log           # Verbatim subprocess output
      last_run.json          # Latest run metadata
    status.json              # Summary of all recent runs
```

**`last_run.json` schema:**

```json
{
  "name": "phi36_mixed_chat",
  "runner": "hf",
  "cmd": ["python", "AI/microsoft_phi-silica-3.6_v1/scripts/train_lora.py", ...],
  "start_time": "20251116T120530Z",
  "status": "succeeded",
  "return_code": 0,
  "duration_sec": 183.45,
  "log": "data_out/autotrain/phi36_mixed_chat/20251116T120530Z/stdout.log",
  "output_dir": "data_out/lora_training"
}
```

**`status.json` schema:**

```json
{
  "generated_at": "2025-11-16T12:08:53Z",
  "jobs": [ ... ]  // Array of last_run objects for each job
}
```

---

## VS Code Tasks

Pre-configured tasks in `.vscode/tasks.json`:

- **Run: AutoTrain (dry-run)** – Validate configs without running training.
- **Run: AutoTrain (all)** – Execute all configured jobs sequentially.

**Access via:** `Terminal > Run Task...` → select the desired AutoTrain task.

---

## Azure Functions Integration

The HTTP status endpoint (`/api/ai/status`) now includes the latest AutoTrain summary:

```json
{
  "active_provider": "local",
  "model": "fallback",
  "lora": { ... },
  "autotrain": {
    "generated_at": "2025-11-16T12:08:53Z",
    "jobs": [ ... ]
  },
  "status": "ok"
}
```

**Use cases:**

- Monitor last job status from CI/CD.
- Surface training state in web UI.
- Track multi-job pipelines.

---

## Common Workflows

### Quick Smoke Test (10 samples, 1 epoch)

```yaml
- name: smoke_test
  runner: hf
  dataset: datasets/chat/mixed_chat
  config: AI/microsoft_phi-silica-3.6_v1/lora/lora.yaml
  epochs: 1
  max_train_samples: 10
  max_eval_samples: 4
```

```powershell
python .\scripts\autotrain.py --job smoke_test
```

### CPU-Only Local Training (QLoRA-friendly)

```yaml
- name: cpu_local
  runner: local
  config: AI/microsoft_phi-silica-3.6_v1/local_train/local_config.yaml
  epochs: 1
  max_train_samples: 50
```

Make sure `local_config.yaml` has:

```yaml
use_4bit: true
max_seq_length: 256
gradient_checkpointing: true
batch_size: 1
gradient_accumulation_steps: 8
```

### Multi-Job Pipeline

```yaml
jobs:
  - name: baseline
    runner: hf
    dataset: datasets/chat/mixed_chat
    epochs: 1
    max_train_samples: 64

  - name: extended
    runner: hf
    dataset: datasets/chat/dolly
    epochs: 3
    max_train_samples: 500
```

```powershell
python .\scripts\autotrain.py
```

Jobs run sequentially. If `baseline` fails, `extended` is skipped. Check `status.json` for details.

---

## Troubleshooting

### Missing Config File

**Error:** `Config not found: autotrain.yaml`
**Fix:** Ensure you're running from the repo root or specify `--config` with the full path.

### Job Not Found

**Error:** `Job not found in config: my_job`
**Fix:** Verify the job name in `autotrain.yaml` matches exactly (case-sensitive).

### Dry-Run Shows Missing Files

**Output:** `"status": "missing"`, `"missing": ["datasets/chat/missing_data"]`
**Fix:** Update dataset paths to point to existing directories or create placeholder data.

### Training Fails with Return Code 1

**Output:** `"status": "failed"`, `"return_code": 1`
**Fix:** Open the stdout.log at `data_out/autotrain/<job>/<timestamp>/stdout.log` for detailed error traces (OOM, missing deps, etc.).

### Local Runner Venv Issues

**Symptom:** `ModuleNotFoundError` after updating dependencies.
**Fix:** Add `reinstall: true` to the job config or use `--reinstall` flag:

```powershell
python .\scripts\autotrain.py --job my_local_job --reinstall
```

---

## Design Rationale

**Why YAML?** Declarative configs reduce boilerplate and improve reproducibility. A single file defines all experiments.

**Why sequential execution?** Simplicity. Parallel multi-GPU jobs are better handled by dedicated schedulers (Kubernetes, Azure Container Apps Jobs, etc.). AutoTrain is for local/dev workflows.

**Why two runners?** The HF runner (`train_lora.py`) offers production-scale features (DeepSpeed, Azure Blob, observability). The local runner (`run_local_lora_training.py`) is streamlined for quick iteration on consumer hardware.

**Status JSON format?** Machine-readable logs enable CI/CD integration, web UIs, and progress monitoring without parsing unstructured logs.

---

## Next Steps

- **Hyperparameter sweeps:** Use `extra_args` to pass per-job custom flags.
- **Multi-GPU local:** Invoke `accelerate launch` directly in `extra_args` for the HF runner.
- **Cloud integration:** Adapt `autotrain.py` to submit jobs to Azure Container Apps Jobs or AWS Batch.
- **Web UI:** Build a simple dashboard that reads `status.json` and displays job history, perplexity trends, and artifact links.

---

## Related Docs

- **Training scripts:**
  - `AI/microsoft_phi-silica-3.6_v1/scripts/train_lora.py` (HF runner)
  - `scripts/run_local_lora_training.py` (local runner)
  - `AI/microsoft_phi-silica-3.6_v1/local_train/README.md` (local setup details)
- **Azure Functions:**
  - `http_ai_status/__init__.py` (status endpoint integration)
  - `function_app.py` (root function handler)
- **Datasets:**
  - `datasets/chat/mixed_chat/` (example chat dataset)
  - `DATASETS_QUICK_REF.md` (catalog)

---

## FAQ

**Q: Can I use multiple configs in one job?**
A: No. Each job uses one config file. For different hyperparams, define separate jobs.

**Q: Can I run AutoTrain in CI/CD?**
A: Yes. Use `--dry-run` in CI to validate configs. For training, run in GitHub Actions with self-hosted runners or cloud VMs with GPUs.

**Q: How do I resume a failed job?**
A: The HF runner supports `--resume-from <checkpoint-dir>`. Add it to `extra_args`:

```yaml
extra_args: ["--resume-from", "data_out/lora_training/checkpoint-500"]
```

**Q: Can I schedule jobs to run automatically?**
A: Not yet. Use OS-level schedulers (Windows Task Scheduler, cron) or integrate AutoTrain into Azure Container Apps Jobs with a timer trigger.

**Q: Does AutoTrain support other models (GPT-2, Llama)?**
A: Yes. Update `hf_model_id` and ensure the training script supports the model architecture. The HF runner is model-agnostic.

---

**AutoTrain is designed for simplicity, reproducibility, and offline-first workflows. Feedback and contributions welcome!**
