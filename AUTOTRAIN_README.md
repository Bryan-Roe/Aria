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

- **Script:** `lora/scripts/train_lora.py`
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
    config: lora/local_train/local_config.yaml
    epochs: 1
    max_train_samples: 10
  ```

---

## CLI Reference

```bash
python scripts/autotrain.py [OPTIONS]

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
  "cmd": ["python", "lora/scripts/train_lora.py", ...],
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
