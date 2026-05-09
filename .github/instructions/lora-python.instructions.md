---
name: "LoRA-Python"
description: "Python-specific guidance for ai-projects/lora-training/microsoft_phi-silica-3.6_v1/"
applyTo: "ai-projects/lora-training/microsoft_phi-silica-3.6_v1/scripts/**/*.py"
---
# LoRA Fine-Tuning – Python files

- Validate configs early:
  - `python .\\scripts\\autotrain.py --dry-run`
  - Quick pipeline (train → evaluate → deploy best): `python .\\scripts\\train_and_promote.py --quick --auto-promote`
- Ultrafast TinyLlama (CPU-friendly): `python .\\scripts\\automated_training_pipeline.py --models tinyllama --quick`
- Config & datasets:
  - LoRA config: `ai-projects/lora-training/microsoft_phi-silica-3.6_v1/lora/lora.yaml`
  - Dataset convention (chat): `datasets/chat/<name>/{train.json,test.json}` with `messages[]` entries.
  - Validate datasets: `python .\\scripts\\validate_datasets.py --category chat`
- LoRA readiness: adapter dir requires `adapter_config.json` and `adapter_model.safetensors` (`data_out/lora_training/<job>/lora_adapter/`).
- Ranking metrics: `perplexity_improvement`, `diversity_avg` (`distinct_diversity`), `combined_improvement`.
- Use in CLI: `python .\\talk-to-ai\\src\\chat_cli.py --provider lora --model <adapter_dir>`
- Config precedence: base YAML < CLI flags < per-job YAML overrides < env vars.
- Data immutability: read-only `datasets/`; write-only outputs under `data_out/`.
- Tests & CI: `python .\\scripts\\test_runner.py --all` and VS Code Test Explorer (🧪) for debugging.
