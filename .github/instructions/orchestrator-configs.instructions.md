---
name: "Orchestrator-Configs"
description: "Guidance for YAML orchestrator configuration files"
applyTo: "config/**/*.yaml"
---
# Orchestrator Configs — YAML Guidance

- All orchestrators in `scripts/` have matching YAML configs.
- Config precedence: `YAML base` < `CLI flags` < `per-job YAML` < `env vars`.
- Always validate with `--dry-run` after editing any config.

## Key Config Files

| Config | Orchestrator | Validates With |
|--------|-------------|----------------|
| `autotrain.yaml` | `scripts/autotrain.py` | `python scripts/autotrain.py --dry-run` |
| `quantum_autorun.yaml` | `scripts/quantum_autorun.py` | `python scripts/quantum_autorun.py --dry-run` |
| `config/autonomous_training.yaml` | `scripts/autonomous_training_orchestrator.py` | Check status JSON |
| `config/master_orchestrator.yaml` | `scripts/master_orchestrator.py` | `python scripts/master_orchestrator.py --dry-run` |

## Autonomous Training Config Keys
- `cycle_interval_minutes` — Time between cycles (default 30)
- `epochs_progression` — Adaptive epoch list `[25, 50, 100, 200]`
- `min_datasets` — Minimum datasets before training starts
- `auto_deploy` — Enable automatic model promotion
- `deploy_threshold` — Accuracy threshold for auto-deploy (default 0.90)

## Master Orchestrator Config Keys
- Cron schedules for sub-orchestrators
- Priority ordering and dependency chains
- Retry logic and timeout configuration
- Workflow definitions (e.g., `daily_full_pipeline`)

## Quantum Config Keys
- `azure_confirm_cost: true` — Required for real QPU jobs
- `max_qubits` — Safety limit (10 local, 20 Azure)
- `max_shots` — Shot count limit (1000 default)
- Backend selection: simulator vs QPU

## Safety
- Never set `azure_confirm_cost: true` without reviewing cost estimate
- Keep `max_qubits` ≤ 20 for Azure, ≤ 10 for local
- Validate YAML syntax: `python -c "import yaml; yaml.safe_load(open('config_file.yaml'))"`
