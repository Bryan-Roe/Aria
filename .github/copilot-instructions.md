<!-- Concise, actionable instructions for AI agents working in this repo. -->

# Aria — Copilot Quick Guide
*Last updated: January 29, 2026*

## Core Architecture

**Unified Monorepo with Isolated Components:**
- **src/chat/** — Core chat providers (multi-provider detection: LMStudio, Azure OpenAI, OpenAI, LoRA, local fallback). Source of truth for provider logic; re-exported via `shared/chat_providers.py`.
- **quantum-ai/** (Python 3.9+, separate venv) — Quantum ML pipelines, PennyLane circuits, MCP server, web dashboards. Fully isolated with own requirements.
- **AI/microsoft_phi-silica-3.6_v1/** (Python 3.10+, separate venv) — LoRA fine-tuning for Phi-3.5/Qwen models. Training scripts in `scripts/train_lora.py`.
- **function_app.py** — Azure Functions REST API hub that imports from `src/chat`, `quantum-ai/src`, and `shared/` via dynamic sys.path (lines 14-19, 88-93).

**Web Surfaces & Integration Points:**
- **src/web/aria/aria_web/server.py** (port 8080) — Interactive 3D character with movement, object interaction, auto-execute planner. Falls back gracefully to rule-based logic if LLM unavailable (see lines 37-46 for provider detection try/catch pattern).
- **src/web/chat/chat-web/** — Pure static HTML/JS SSE client consuming `/api/chat` streaming responses from function_app.py.
- **function_app.py** — Primary REST API hub: `/api/chat`, `/api/ai/status`, `/api/quantum/*`, `/api/tts`. Entry point for all HTTP interactions.
- **shared/** — Shared infrastructure: `chat_providers.py` (re-exports from `src/chat`), `sql_engine.py`, `cosmos_client.py`, `telemetry.py`, `chat_memory.py`.

**Development Environments:**
- **Dev Container**: `.devcontainer/devcontainer.json` provides Python 3.14 + Windows AI Studio extension
- **VS Code Tasks**: 40+ preconfigured tasks in `.vscode/tasks.json` for training, testing, monitoring, orchestration
- **Startup Scripts**: `scripts/start_aria.sh`, `scripts/start_aria_full.sh` for one-command environment setup

## Critical Patterns

**Chat Provider Detection Chain** (in `src/chat/chat_providers.py`, re-exported by `shared/chat_providers.py`):
```
Priority order (first match wins):
1. Explicit --provider flag (e.g., --provider azure)
2. LMStudio (if LMSTUDIO_BASE_URL env set) → fastest local-only option
3. Azure OpenAI (requires all 4: AZURE_OPENAI_API_KEY + ENDPOINT + DEPLOYMENT + API_VERSION)
4. OpenAI (OPENAI_API_KEY only)
5. LoRA adapter (--provider lora + adapter dir with adapter_config.json + adapter_model.safetensors)
6. Local echo fallback (deterministic, zero dependencies)
```
This chain is consumed by function_app.py (line 21), src/web/aria/aria_web/server.py (line 41), and all web integrations.

**Orchestrator-Driven Workflows** (YAML-based state machines):
All heavy operations (training, quantum, evaluation) write status.json to `data_out/<orchestrator>/` as source of truth:
- `scripts/training/autotrain.py` — Sequential LoRA fine-tuning jobs from `config/training/autotrain.yaml`
  - Outputs: per-job logs in `data_out/autotrain/<job>/<timestamp>/stdout.log`, summary in `data_out/autotrain/status.json`
  - Example: `python scripts/training/autotrain.py --dry-run` validates YAML without execution
- `scripts/training/autonomous_training_orchestrator.py` — Continuous 30-min learning cycles with dataset auto-discovery
- `scripts/evaluation/quantum_autorun.py` — Quantum circuit submission and monitoring (requires Azure Quantum config)
- `scripts/automation/master_orchestrator.py` — Coordinates all sub-orchestrators with cron schedules and dependencies

**Data Conventions:**
- `datasets/` is **read-only** (never modify; add new data to `data_out/` instead)
- LoRA adapters must include both `adapter_config.json` AND `adapter_model.safetensors`
- Chat datasets: JSON format `[{"messages": [{"role": "user|assistant", "content": "..."}]}]`
- Config precedence: YAML defaults < CLI flags < per-job YAML overrides < environment variables

## Environment & Setup

**Dependency Installation:**
```bash
# Core dependencies (shared across all projects)
pip install -r requirements.txt -r dev-requirements.txt

# Each isolated project needs its own venv
cd quantum-ai && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && deactivate
cd AI/http_chat/talk-to-ai && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && deactivate
cd AI/microsoft_phi-silica-3.6_v1 && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && deactivate
```

**Local Configuration:**
```bash
cp local.settings.json.example local.settings.json  # Then edit with your API keys
```
Essential env vars for local.settings.json:
- `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`, `AZURE_OPENAI_API_VERSION` (Azure provider)
- `OPENAI_API_KEY` (OpenAI fallback)
- `LMSTUDIO_BASE_URL` (LMStudio local provider, e.g., `http://localhost:1234/v1`)
- `QAI_ENABLE_LOCAL_TTS=true` (pyttsx3 fallback if Azure Speech unavailable)
- `QAI_DB_CONN` (optional SQL persistence; e.g., `sqlite:///data_out/qai.db`)
- `QAI_ENABLE_COSMOS=true` + `COSMOS_ENDPOINT`, `COSMOS_KEY` (optional Cosmos persistence)

## Go-To Commands (from repo root)

**Validation & Testing:**
- `python scripts/fast_validate.py` — Instant repo-wide validation (no imports, checks syntax/structure)
- `python scripts/test_runner.py --unit` — Unit tests only (~1-2 min)
- `python scripts/test_runner.py --all` — All tests including integration (~5-10 min)
- `python scripts/test_runner.py --watch` — Auto-rerun on file change

**API & Functions:**
- `func host start` — Start Azure Functions host (port 7071), then check health: `curl http://localhost:7071/api/ai/status | jq`
- `curl http://localhost:7071/api/ai/status | jq` — Comprehensive health check (shows active provider, env vars, DB pool saturation, GPU/CUDA status)

**Character & Chat:**
- `bash scripts/start_aria_full.sh` — One-command startup (Aria server + Functions + monitoring)
- `bash scripts/start_aria.sh` — Interactive menu for selective startup
- `cd src/web/aria/aria_web && python server.py` — Start Aria web UI (port 8080), access at http://localhost:8080
- `python src/chat/chat_cli.py --provider local --once "Hello"` — Quick chat CLI smoke test
- `python src/chat/chat_cli.py --provider azure --once "test"` — Test Azure OpenAI provider

**Orchestrators (always --dry-run first):**
- `python scripts/training/autotrain.py --dry-run` — Validate training config without GPU execution
- `python scripts/training/autotrain.py` — Run all configured LoRA jobs sequentially
- `python scripts/evaluation/quantum_autorun.py --dry-run` — Validate quantum config
- `python scripts/automation/master_orchestrator.py --status` — Check orchestrator status

**Monitoring & Diagnostics:**
- `python scripts/monitoring/auto_ops_dashboard.py` — Real-time orchestrator status
- `python scripts/monitoring/auto_ops_dashboard.py --watch` — Auto-refresh every 10s
- `python scripts/monitoring/vs_code_server.py` — Start web dashboard (port 8765) for VS Code
- `tail -f data_out/autotrain/job_*.log` — Watch active training job logs
- `python scripts/resource_monitor.py --snapshot` — CPU/memory/disk/GPU snapshot

## Development Conventions

**Component Isolation:**
- Each project (quantum-ai/, AI/microsoft_phi-silica-3.6_v1/) is completely isolated
- Never import across project boundaries directly; always go through function_app.py's sys.path handling (lines 14-19) or shared/ re-exports
- If adding new cross-project imports, update sys.path in function_app.py, src/web/aria/aria_web/server.py, and mount/app.py

**Provider Detection & Fallback:**
- Always preserve the detection chain; never assume a specific provider is available
- Implement graceful degradation: try LLM first, fall back to rule-based logic (see src/web/aria/aria_web/server.py line 41-46 pattern)
- Use `detect_provider()` from shared/chat_providers.py to check availability before calling; test with `/api/ai/status`

**Status Files & Observability:**
- All orchestrators MUST write to `data_out/<name>/status.json` (e.g., `data_out/autotrain/status.json`)
- Use this as the single source of truth for job counts, success/failure rates, last run timestamp
- Monitoring tools (`auto_ops_dashboard.py`, `vs_code_server.py`) parse these files, so format consistency is critical

**Config & Environment:**
- Config precedence: YAML base defaults < CLI `--flags` < per-job YAML overrides < `env vars`
- Example: `autotrain.yaml` sets `epochs: 1`, but `python autotrain.py --job phi35_mixed_chat --epochs 3` overrides it
- Never hardcode API keys; always use `local.settings.json` (dev) or Azure App Settings (prod)

**Data Conventions:**
- `datasets/` is read-only; any generated data goes to `data_out/`
- Chat datasets follow format: `[{"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}]`
- LoRA checkpoints must include BOTH `adapter_config.json` AND `adapter_model.safetensors` to be deployable
- Quantum circuit results stored in `data_out/<job>/circuits/` with JSON metadata

## Safety & Deployment

**Before Running Expensive Operations:**
- Always `--dry-run` orchestrators first: `python scripts/training/autotrain.py --dry-run`
- For quantum: set `azure_confirm_cost: true` in YAML ONLY after reviewing cost estimate in Azure Portal
- Quantum jobs: simulate locally first (`backend: qiskit_aer`), then test on `azure_ionq_simulator`, THEN real QPU

**Secrets & Security:**
- Never hardcode API keys, connection strings, or credentials in code
- Use `local.settings.json` for development, Azure App Settings for production
- Check `/api/ai/status` to verify env vars are loaded correctly
- Watch DB pool saturation via `/api/ai/status` (warns at ≥80%); adjust `QAI_SQL_POOL_SIZE` if needed

**Monitoring Health:**
- `/api/ai/status` is your first diagnostic tool: shows active provider, SQL pool saturation, Cosmos status, GPU availability
- If provider detection fails, compare env vars shown in `/api/ai/status` against your local.settings.json
- Training logs: `tail -f data_out/autotrain/job_*/stdout.log` shows real-time progress
- Orchestrator status: `python scripts/monitoring/auto_ops_dashboard.py --watch` shows job counts and failure rates

## Editing Hotspots

| File | Purpose |
|------|---------|
| [function_app.py](function_app.py) | REST API endpoints & Azure Functions integration |
| [src/web/aria/aria_web/server.py](src/web/aria/aria_web/server.py) | Aria character server, endpoints, LLM fallback patterns |
| [shared/chat_providers.py](shared/chat_providers.py) | Multi-provider detection chain re-export |
| [scripts/training/autotrain.py](scripts/training/autotrain.py) | LoRA training orchestrator |
| [config/training/autotrain.yaml](config/training/autotrain.yaml) | Training job configuration |
| [scripts/training/autonomous_training_orchestrator.py](scripts/training/autonomous_training_orchestrator.py) | Continuous learning cycles |
| [scripts/automation/master_orchestrator.py](scripts/automation/master_orchestrator.py) | Cron scheduling & orchestrator coordination |
| [scripts/monitoring/auto_ops_dashboard.py](scripts/monitoring/auto_ops_dashboard.py) | Real-time status monitoring |

## Testing & Validation

- **Unit tests:** `pytest tests/ -m "not slow and not azure"` or `python scripts/test_runner.py --unit`
- **Integration tests:** `python scripts/test_runner.py --integration`
- **All tests:** `python scripts/test_runner.py --all`
- **VS Code Test Explorer:** Use 🧪 icon for interactive test running
- **Markers:** `@pytest.mark.slow`, `@pytest.mark.azure`, `@pytest.mark.integration`
- **Fast validation:** `python scripts/fast_validate.py` (instant, no imports)
- **Watch mode:** `python scripts/test_runner.py --watch` (auto-reruns on file change)

## Common Troubleshooting

| Issue | Diagnosis | Solution |
|-------|-----------|----------|
| Provider detection fails | Check `/api/ai/status` shows which env vars are missing | Verify all 4 Azure vars set, or OPENAI_API_KEY, or LMSTUDIO_BASE_URL |
| CUDA out of memory | `tail -f data_out/autotrain/job_*.log` shows OOM | Reduce `max_train_samples` in YAML or use `device: cpu` |
| LoRA adapter not found | `--provider lora` fails | Verify `adapter_config.json` + `adapter_model.safetensors` both exist in adapter dir |
| Training not starting | Check orchestrator dry-run | `python scripts/training/autotrain.py --dry-run` reveals config errors |
| Aria web UI not responding | Check server logs | `cd src/web/aria/aria_web && python server.py`, verify port 8080 is free |
| DB pool saturation | `/api/ai/status` shows `saturation_alert: true` | Increase `QAI_SQL_POOL_SIZE` environment variable |

## Modular Instructions

This repo uses component-specific instruction files in `.github/instructions/`:
- `functions.instructions.md` — Azure Functions API endpoints
- `shared-python.instructions.md` — Shared infrastructure patterns
- `quantum-ai*.instructions.md` — Quantum ML workflows
- `lora*.instructions.md` — LoRA fine-tuning patterns
- `chat-web.instructions.md` — Frontend SSE integration

These are automatically applied by VS Code based on file paths.

## AI Agent Best Practices

**Before making changes:**
1. Read this file and relevant `.github/instructions/*.instructions.md` files based on file paths
2. Run `python scripts/fast_validate.py` to check repo state
3. Check `/api/ai/status` if modifying provider or API code
4. For orchestrator changes: start with `--dry-run` to validate YAML

**Key principles:**
- Never modify `datasets/` (read-only)
- Always write orchestrator status to `data_out/<name>/status.json`
- Preserve provider detection chain; test with `/api/ai/status`
- Config precedence: YAML base < CLI flags < per-job YAML < env vars
- Use signal-based triggers for immediate orchestrator execution: `pkill -USR1 -f <orchestrator_name>`

**Before committing:**
- Run tests: `python scripts/test_runner.py --unit`
- Validate orchestrators: `--dry-run` each one you modified
- Check secrets: no hardcoded API keys, use env vars
- Verify no disk space issues: `df -h /workspaces`
- If modifying training: ensure output has both `adapter_config.json` + `adapter_model.safetensors`
