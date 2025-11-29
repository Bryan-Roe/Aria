---
name: "LoRA-Fine-Tuning-workspace"
description: "Slim instructions for AI/microsoft_phi-silica-3.6_v1/"
applyTo: "AI/microsoft_phi-silica-3.6_v1/**"
---
# LoRA Fine-Tuning – workspace-specific guidance

- Start with dry-runs to validate config:
  - `python .\\scripts\\autotrain.py --dry-run`
  - Quick pipeline (train → evaluate → deploy best): `python .\\scripts\\train_and_promote.py --quick --auto-promote`
- Ultrafast TinyLlama (CPU-friendly): `python .\\scripts\\automated_training_pipeline.py --models tinyllama --quick`
- Configs & datasets:
  - LoRA config: `AI/microsoft_phi-silica-3.6_v1/lora/lora.yaml`
  - Dataset convention (chat): `datasets/chat/<name>/{train.json,test.json}` with `messages[]` entries.
  - Validate datasets: `python .\\scripts\\validate_datasets.py --category chat`
- LoRA readiness: adapter directory must contain BOTH `adapter_config.json` and `adapter_model.safetensors` (e.g., under `data_out/lora_training/<job>/lora_adapter/`).
- Ranking metrics used by automation: `perplexity_improvement`, `diversity_avg` (aka `distinct_diversity`), and `combined_improvement`.
- Post-training usage (Chat CLI): `python .\\talk-to-ai\\src\\chat_cli.py --provider lora --model <adapter_dir>`
- Config precedence: base YAML < CLI flags < per-job YAML overrides < environment variables.
- Data immutability: read-only `datasets/`; write-only outputs in `data_out/` (autotrain, lora_training, evaluation_autorun, parallel_training).
- Tests & CI: prefer `python .\\scripts\\test_runner.py --all` for fast validation; use VS Code Test Explorer (🧪) for debugging.
