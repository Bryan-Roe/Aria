---
name: lora-adapter-debug-workflow
description: Debug LoRA fine-tuning failures, adapter readiness issues, dataset validation errors, training job crashes, and model promotion problems. Use when LoRA training fails to complete, adapter files are missing or corrupt, perplexity/diversity metrics look wrong, or the inference bridge can't load an adapter.
argument-hint: "Describe the failure: training crash, bad metrics, adapter not loading, promotion not firing, or dataset error."
---

# LoRA Adapter Debug Workflow

## What This Skill Produces
A root-cause diagnosis and targeted fix for LoRA fine-tuning and adapter lifecycle issues — covering dataset shape, training scripts, adapter file validity, ranking metrics, and model promotion gates.

## When to Use

Trigger phrases:
- "LoRA training failed"
- "adapter not loading"
- "perplexity not improving"
- "train and promote not promoting"
- "adapter_model.safetensors missing"
- "dataset validation failed"
- "diversity score wrong"
- "lora infer bridge error"
- "fine-tuning crash"
- "training job output empty"

## Procedure

### Step 1 — Validate Config Dry-Run
```bash
python scripts/autotrain.py --dry-run
python scripts/train_and_promote.py --quick --auto-promote --dry-run
```
Check that YAML parses cleanly and all job paths resolve. Fix schema errors before running GPU jobs.

### Step 2 — Validate Datasets
```bash
python scripts/validate_datasets.py --category chat
```
Each dataset must be at `datasets/chat/<name>/{train.json,test.json}` with `messages[]` entries using `role: user|assistant`. `datasets/` is read-only — never modify it.

### Step 3 — Check Adapter Readiness
Adapter directories under `data_out/lora_training/<job>/lora_adapter/` must contain **both**:
- `adapter_config.json`
- `adapter_model.safetensors`

If either is missing, the training job did not complete — check `data_out/lora_training/<job>/status.json` for error fields.

### Step 4 — Inspect Training Output
```bash
cat data_out/lora_training/<job>/status.json | python -m json.tool
```
Key fields: `succeeded`, `failed`, `last_error`, `epochs_completed`, `best_accuracy`.
Ranking metrics: `perplexity_improvement`, `diversity_avg` (aka `distinct_diversity`), `combined_improvement`.

### Step 5 — Test Inference With Adapter
```bash
python ai-projects/chat-cli/src/chat_cli.py --provider lora --model data_out/lora_training/<job>/lora_adapter --once "Hello"
```
If this fails, the adapter is malformed or the model base doesn't match.

### Step 6 — Check Promotion Gate
`scripts/train_and_promote.py` promotes only when `combined_improvement` exceeds the configured threshold. If promotion doesn't fire:
- Check threshold in job YAML (`min_combined_improvement`)
- Lower threshold for experimentation; restore before merging

### Step 7 — Quick CPU-Friendly Smoke Test
```bash
python scripts/automated_training_pipeline.py --models tinyllama --quick
```
Uses TinyLlama to verify the pipeline end-to-end without GPU. Confirms dataset loading, LoRA attachment, and adapter output shape.

### Step 8 — Config Precedence Reminder
`YAML base` < `CLI flags` < `per-job YAML overrides` < `env vars`
When debugging config-not-applied issues, check in reverse order starting with env vars.

## Quality Checks
- [ ] Dry-run passes with no YAML or path errors
- [ ] Dataset validation reports zero errors for the failing category
- [ ] `adapter_config.json` + `adapter_model.safetensors` both present after run
- [ ] Inference smoke test (`--once "Hello"`) responds without exception
- [ ] Promotion threshold documented in job YAML, not hardcoded
- [ ] `data_out/` outputs only — no writes to `datasets/`
