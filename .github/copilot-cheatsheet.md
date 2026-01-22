<!-- AI Agent Rapid Reference - 1-2 minute read -->

# Aria Repository — Quick Cheat Sheet

**3 Core Projects:** `quantum-ai/` (Python 3.9) + `talk-to-ai/` (3.10) + `AI/microsoft_phi-silica-3.6_v1/` (3.10) → unified via `function_app.py` (Azure Functions)

## Quick Commands

```bash
# === SETUP ===
pip install -r requirements.txt && pip install -r dev-requirements.txt
cd quantum-ai && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && deactivate
cd talk-to-ai && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && deactivate
cd AI/microsoft_phi-silica-3.6_v1 && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && deactivate

# === VALIDATE & TEST (Run FIRST) ===
python scripts/fast_validate.py              # Instant cross-component check
python scripts/test_runner.py --unit         # Unit tests only (~30s)
curl http://localhost:7071/api/ai/status | jq # Health check (requires func running)

# === DEVELOPMENT ===
func host start                               # Azure Functions (port 7071)
cd aria_web && python server.py               # Aria character (port 8080)
python talk-to-ai/src/chat_cli.py --provider local --once "test"  # Chat test

# === ORCHESTRATORS (Always --dry-run first!) ===
python scripts/training/autotrain.py --dry-run          # Validate config
python scripts/training/autotrain.py                    # Run training jobs
python scripts/evaluation/quantum_autorun.py --dry-run   # Validate quantum
python scripts/automation/master_orchestrator.py         # Coordinate all

# === MONITORING ===
python scripts/monitoring/vscode_quickstart.py           # Interactive menu
python scripts/monitoring/vscode_quickstart.py --full    # Dashboard + alerts
python scripts/monitoring/auto_ops_dashboard.py --watch  # Live CLI status
curl http://localhost:7071/api/ai/status | jq          # Status snapshot

# === AUTOMATION ===
./scripts/start_repo_automation.sh full                  # Start everything
./scripts/start_repo_automation.sh status                # Check status
./scripts/start_repo_automation.sh stop                  # Stop all
```

## Key Files & Patterns

| File | Purpose |
|------|---------|
| `function_app.py` | Azure Functions API gateway (sys.path magic to import all projects) |
| `shared/chat_providers.py` | Provider detection: LMStudio → Azure OpenAI → OpenAI → fallback |
| `aria_web/server.py` | Character server (port 8080, REST endpoints) |
| `config/training/autotrain.yaml` | LoRA training jobs (12 jobs, GPU enabled) |
| `config/autonomous_training.yaml` | Continuous 30-min learning cycles (adaptive epochs) |
| `config/master_orchestrator.yaml` | Cron schedules + orchestrator dependencies |
| `data_out/<name>/status.json` | Source of truth for all orchestrators |

## Critical Patterns

**Provider Chain** (explicit flag > LMStudio > Azure > OpenAI > local):
```python
from shared.chat_providers import detect_provider
provider = detect_provider()  # Returns active provider
```

**YAML Config Precedence**: Base defaults < CLI flags < per-job YAML < env vars

**Data Immutability**: `datasets/` is **read-only**, all outputs → `data_out/`

**Orchestrator Status**: Always write `data_out/<orchestrator>/status.json` (machine-readable)

**LoRA Adapters**: Must have BOTH `adapter_config.json` + `adapter_model.safetensors`

## Safety Checklist

- [ ] `--dry-run` orchestrators before GPU execution
- [ ] Quantum: simulate locally first → `azure_ionq_simulator` → real QPU
- [ ] QPU jobs: require `azure_confirm_cost: true` in YAML
- [ ] Check `/api/ai/status` before making provider changes
- [ ] No hardcoded secrets (use `local.settings.json` or env vars)
- [ ] Monitor DB pool via `/api/ai/status` (warns ≥80%)

## Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: chat_providers` | Check `function_app.py` sys.path has `talk-to-ai/src` |
| CUDA OOM | Reduce `max_train_samples` in YAML or set `device: cpu` |
| Provider detection failed | Run `/api/ai/status`, verify env vars in `local.settings.json` |
| Port 8080 in use | `pkill -f aria_web` or `lsof -ti:8080 \| xargs kill` |
| Port 7071 in use | `lsof -ti:7071 \| xargs kill` |
| Adapter not found | Verify both `adapter_config.json` + `adapter_model.safetensors` exist |

## Environment Variables (Essential)

```bash
# Chat Providers (in local.settings.json)
AZURE_OPENAI_API_KEY=xxx
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_DEPLOYMENT=model-name
OPENAI_API_KEY=xxx (fallback)
LMSTUDIO_BASE_URL=http://localhost:1234 (local)

# Optional Features
QAI_ENABLE_LOCAL_TTS=true              # No Azure Speech required
QAI_DB_CONN=sqlite:///data.db          # SQL persistence
QAI_ENABLE_COSMOS=true                 # Cosmos DB
APPLICATIONINSIGHTS_CONNECTION_STRING  # Application Insights
```

## Component Entry Points

- **Chat**: `python talk-to-ai/src/chat_cli.py --provider <name>`
- **Quantum**: `python quantum-ai/quantum_mcp_server.py` (MCP)
- **Training**: `python scripts/training/autotrain.py`
- **Aria**: `cd aria_web && python server.py`
- **APIs**: `func host start` (all endpoints on port 7071)

## Monitoring Endpoints

```bash
# Status & Health
curl http://localhost:7071/api/ai/status | jq           # Comprehensive health
http://localhost:8080/api/aria/state                     # Character state
http://localhost:8765                                    # Web dashboard (VS Code)

# Real-time Logs
tail -f data_out/autonomous_training.log
tail -f data_out/autotrain/job_*.log
watch -n 5 'cat data_out/autonomous_training_status.json | python -m json.tool'
```

## Before Committing

1. `python scripts/fast_validate.py` (instant)
2. `python scripts/test_runner.py --unit` (30s)
3. If orchestrators changed: `--dry-run` them
4. If providers changed: test with `/api/ai/status`
5. Check no hardcoded secrets
6. Update relevant `.github/instructions/*.md` if major changes

---

**Full Guide**: `.github/copilot-instructions.md` | **File-Specific Rules**: `.github/instructions/` | **Agent Expertise**: `.github/agents/my-agent.agent.md`
