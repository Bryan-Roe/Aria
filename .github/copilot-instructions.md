<!-- Concise, practical instructions for AI agents working in this repo. Keep this file short — use the full archive (.github/copilot-instructions.full.md) for details. -->

# Aria — Copilot Quick Guide

*Last updated: January 17, 2026*

Short & actionable summary for AI agents editing Aria — an interactive AI character platform with autonomous learning, quantum ML integration, and multi-provider chat backends.

## Architecture

- **Interactive AI Character Platform** with 3D animated avatar, natural language movement commands, and real-time object interaction
- **Three isolated projects + Functions integration layer:**
  - `quantum-ai/` — MCP server, web dashboard, quantum ML pipelines (separate venv)
  - `talk-to-ai/` — chat CLI with multi-provider support (separate venv)
  - `AI/microsoft_phi-silica-3.6_v1/` — Phi-3.5 LoRA fine-tuning (separate venv)
  - `function_app.py` — Azure Functions integration exposing all APIs
- **Integration points:**
  - `function_app.py` dynamically imports from talk-to-ai/src and quantum-ai/src (adds to sys.path)
  - Shared infra in `shared/`: re-exports chat providers, DB engines, telemetry, Cosmos client
- **Web Interfaces:**
  - `aria_web/` — Interactive Aria character interface with CSS animations, eye tracking, gestures
  - `chat-web/` — Streaming chat UI with SSE support
- **API endpoints** (via `function_app.py`):
  - `/api/chat` — streaming chat SSE
  - `/api/chat-web` — web UI HTML
  - `/api/tts` — Azure Speech TTS (falls back to local if enabled)
  - `/api/quantum/*` — quantum job submission/monitoring
  - `/api/ai/status` — health check showing active provider, env vars, DB pool, Cosmos status
- **Aria Web API endpoints** (via `aria_web/server.py` on port 8080):
  - `GET /api/aria/state` — current stage state (position, objects, expressions)
  - `POST /api/aria/command` — process natural language commands
  - `POST /api/aria/execute` — auto-execute action sequences (plan or execute mode)
  - `POST /api/aria/object` — manage objects (add, update, remove)
  - `POST /api/aria/world` — LLM-powered themed world generation

## Key Features

**Interactive Character System:**
- 3D CSS-animated character with smooth transitions and physics-based movement
- Natural language command processing ("move left", "wave at me", "dance", "jump", "pickup ball")
- **Auto-Execute System**: LLM-powered action parser converts natural language to structured action sequences
  - 8 core actions: move, say, pickup, drop, throw, gesture, look, wait
  - Plan mode (preview actions) and execute mode (run sequences)
  - Dual-mode parsing: LLM-powered + rule-based fallback
- Object interaction system (add, pickup, drop, throw with trajectory physics)
- **World Generation**: LLM-powered themed environment creation
- Eye tracking and attention system (follows mouse cursor)
- Emotion/gesture system (wave, dance, jump, idle animations)
- Real-time speech synthesis via Azure TTS or local fallback
- Server-synchronized state management (character position, objects, expressions)

**Autonomous Learning:**
- Self-discovering dataset collection from multiple sources
- Adaptive epoch selection based on performance history
- Automatic model promotion when accuracy thresholds met
- Performance degradation detection and alerting
- Continuous 30-minute training cycles with graceful error recovery

**Multi-Provider Chat:**
- Azure OpenAI, OpenAI, LMStudio, local models
- LoRA adapter support for fine-tuned models
- Automatic provider fallback chain
- SSE-based streaming responses

## Quick Commands (from repo root)

```bash
# === AUTONOMOUS SYSTEMS (Self-Managing) ===
# Start autonomous training (continuous 30-min cycles)
nohup python scripts/training/autonomous_training_orchestrator.py > data_out/autonomous_training.log 2>&1 &

# Trigger immediate cycle (skip 30-min wait)
pkill -USR1 -f autonomous_training

# Full repo automation (Aria + training + quantum + monitoring)
python scripts/automation/repo_automation.py --start
python scripts/automation/repo_automation.py --status
./scripts/start_repo_automation.sh full          # Bash wrapper with menu
./scripts/start_repo_automation.sh stop          # Stop all components

# Aria character automation (server + continuous training)
python scripts/automation/aria_automation.py --mode full
python scripts/automation/aria_automation.py --status

# === ARIA CHARACTER WEB UI ===
cd aria_web && python server.py                  # Start Aria web interface (port 8080)
# Access at: http://localhost:8080
# Auto-Execute UI: http://localhost:8080/auto-execute.html
# Commands: "move left", "wave", "dance", "jump", "pickup ball", "throw"
# Complex: "Walk to the table and pick up the apple", "Say hello and wave"

# === AZURE FUNCTIONS & APIs ===
func host start                                # Start Functions host (serves all APIs)
curl http://localhost:7071/api/ai/status | jq # Health check

# === TESTING & VALIDATION ===
python scripts/test_runner.py --unit          # Fast unit tests
python scripts/test_runner.py --all           # All tests
python talk-to-ai/src/chat_cli.py --provider local --once "Hello"  # Smoke test
python scripts/fast_validate.py              # Quick validation across all components

# === ORCHESTRATORS (Manual Execution) ===
python scripts/training/autotrain.py --dry-run         # Validate training config (12 jobs)
python scripts/evaluation/quantum_autorun.py --dry-run   # Validate quantum config
python scripts/evaluation/evaluation_autorun.py --dry-run # Validate evaluation config

# === TRAINING PIPELINES ===
python scripts/automated_training_pipeline.py --quick  # Quick LoRA (TinyLlama)
python scripts/training/train_and_promote.py --quick --auto-promote  # Train + auto-deploy

# === MCP & TOOLS ===
python quantum-ai/quantum_mcp_server.py       # Start quantum MCP server

# === MONITORING & DIAGNOSTICS ===
curl http://localhost:7071/api/ai/status | jq # Comprehensive health check
python scripts/status_dashboard.py            # Unified orchestrator status
python scripts/status_dashboard.py --watch    # Auto-refresh every 10s
python scripts/resource_monitor.py --snapshot # CPU/memory/disk/GPU snapshot
python scripts/system_health_check.py         # Full system health report
python scripts/training_analytics.py          # Performance trends & insights
tail -f data_out/autonomous_training.log      # Live autonomous training logs
watch -n 5 'cat data_out/autonomous_training_status.json | python -m json.tool' # Live status
```

## Development Environment Setup

**Dev Container (Recommended):**
- Based on `mcr.microsoft.com/devcontainers/python:2-3.14-trixie`
- Pre-configured with Python 3.14 and Windows AI Studio extension
- Opens automatically in VS Code with Docker installed

**Quick setup:**
```bash
# 1. Clone and open in VS Code (dev container auto-starts)
# 2. Install core dependencies
pip install -r requirements.txt
pip install -r dev-requirements.txt

# 3. Setup project-specific venvs (isolated environments)
cd quantum-ai && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && deactivate
cd talk-to-ai && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && deactivate
cd AI/microsoft_phi-silica-3.6_v1 && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && deactivate

# 4. Configure environment (copy and edit)
cp local.settings.json.example local.settings.json
# Edit local.settings.json with your API keys (Azure OpenAI, Speech, etc.)

# 5. Validate setup
python scripts/fast_validate.py  # Quick validation (instant)
python scripts/test_runner.py --unit  # Run unit tests (~30s)
```

**Environment variables** (in `local.settings.json` for dev):
- `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT` — Azure OpenAI provider
- `OPENAI_API_KEY` — OpenAI provider fallback
- `LMSTUDIO_BASE_URL` — LMStudio local provider
- `QAI_ENABLE_LOCAL_TTS=true` — Enable local TTS fallback (no Azure Speech needed)
- `QAI_DB_CONN` — Optional SQL persistence (SQLite/PostgreSQL/Azure SQL)
- `QAI_ENABLE_COSMOS=true` — Enable Cosmos DB integration

## GPU Training Support

**GPU detection and configuration:**
- Training scripts auto-detect CUDA availability via PyTorch
- Force GPU: Set `device: cuda` in YAML configs
- Check availability: `python -c "import torch; print(torch.cuda.is_available())"`
- Monitor usage: `watch -n 1 nvidia-smi`

**Progressive training workflow:**
```bash
# Phase 1: Quick test (5-15 min, 1 job)
python scripts/training/progressive_training.py --phase quick

# Phase 2: Standard (30-60 min, 2 baseline models)
python scripts/training/progressive_training.py --phase standard

# Phase 3: Full (2-8 hours, all 12 jobs)
python scripts/training/progressive_training.py --phase full

# All phases with auto-deployment
python scripts/training/progressive_training.py --all --auto-promote
```

**GPU training configs:**
- `config/training/autotrain.yaml` — All 12 jobs configured for `device: cuda`
- `config/autonomous_training.yaml` — `device: cuda`, `max_cpu_cores: 0`, `max_gpu_memory_gb: 0` (use all)

## Critical Patterns

**Autonomous/self-managing systems:**
- `scripts/training/autonomous_training_orchestrator.py` — Continuous learning with 30-min cycles (infinite by default)
  - Self-discovers datasets (scans `datasets/quantum`, `datasets/chat`, `datasets/massive_quantum`)
  - Self-optimizes: Adaptive epochs `[25, 50, 100, 200]` based on performance history
  - Self-heals: Graceful error handling, continues on failure, logs to `data_out/autonomous_training.log`
  - State: `data_out/autonomous_training_status.json` (cycles_completed, best_accuracy, dataset_inventory)
  - Config: `config/autonomous_training.yaml` (cycle_interval_minutes, epochs_progression, min_datasets)
  - Trigger: Time-based (30min) OR signal-based (`pkill -USR1 -f autonomous_training`)
- `scripts/automation/repo_automation.py` — Full repo automation (all components: Aria + training + quantum + datasets)
- `scripts/automation/aria_automation.py` — Aria-specific automation (server on port 8080 + continuous training)
- `scripts/automation/master_orchestrator.py` — Coordinates all sub-orchestrators with schedules/dependencies
  - Config: `config/master_orchestrator.yaml` (cron schedules, priorities, retry logic, timeouts)

**Data conventions:**
- `datasets/` is **read-only** — never modify existing datasets
- All outputs go to `data_out/<orchestrator>/` with `status.json` as source of truth
- Chat datasets: `[{"messages": [{"role": "user|assistant", "content": "..."}]}]`
- LoRA adapters need both `adapter_config.json` + `adapter_model.safetensors`

**Provider detection chain** (in `shared/chat_providers.py`):
1. Explicit choice (--provider flag)
2. LMStudio (if `LMSTUDIO_BASE_URL` configured)
3. Azure OpenAI (needs all 4: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`, `AZURE_OPENAI_API_VERSION`)
4. OpenAI (needs `OPENAI_API_KEY`)
5. LoRA (explicit --provider lora with adapter path)
6. Local fallback (zero-dependency echo)

**Config precedence:**
`YAML base` < `CLI flags` < `per-job YAML` < `env vars`

**YAML orchestrators:**
- Scripts in `scripts/`, configs in both root and `config/` subdirectories (e.g., `config/training/autotrain.yaml`, `quantum_autorun.yaml`)
- Write `data_out/<name>/status.json` with machine-readable job status
- Support `--dry-run` to validate before execution

**Autonomous training implementation patterns:**
```python
# State machine: discovery → collection → training → analysis → optimization → deployment
async def run_single_cycle(cycle_number):
    await discover_datasets()           # Scan datasets/, catalog by category
    await download_new_datasets()       # Download if below min_datasets threshold
    epochs = await select_optimal_epochs()  # Adaptive: increase if accuracy < 0.70 or plateau
    results = await train_cycle(epochs) # Distributed training with multiprocessing
    await analyze_performance(results)  # Track metrics, detect degradation
    await optimization_cycle()          # Hyperparameter tuning (if enabled)
    await deployment_cycle()            # Auto-deploy if accuracy > 0.90 (if enabled)
```

**Process management:**
- Autonomous systems run via `nohup` in background, logs to `data_out/*.log`
- Check status: `ps aux | grep -E "(autonomous|aria)" | grep -v grep`
- Manual trigger: `pkill -USR1 -f autonomous_training` forces immediate cycle
- Graceful shutdown: `pkill -TERM -f autonomous_training`

**Performance monitoring & observability:**
- **Health endpoint**: `GET /api/ai/status` — Comprehensive system diagnostics
  - Active provider detection (azure|openai|local|lora)
  - Environment variable presence (Azure OpenAI, OpenAI, Cosmos, SQL)
  - ML library availability (torch, transformers, peft) — in-process & venv
  - SQL pool metrics with saturation alerts (warns at ≥80%)
  - Cosmos DB health check (lazy connection)
  - Quantum environment status (qiskit, pennylane, Azure Quantum backends)
  - LoRA adapter readiness (adapter_config.json, tokenizer)
- **Status files**: All orchestrators write `data_out/<name>/status.json`
  - Schema: `{total_jobs, succeeded, failed, running, last_updated, avg_duration}`
  - Autonomous training: `{cycles_completed, best_accuracy, performance_history[], dataset_inventory}`
- **Monitoring scripts**:
  - `scripts/status_dashboard.py` — Unified view of all orchestrators (supports --watch, --export)
  - `scripts/resource_monitor.py` — CPU/memory/disk/GPU with threshold alerts
  - `scripts/system_health_check.py` — Comprehensive health report (venvs, Azure Functions, datasets)
  - `scripts/training_analytics.py` — Performance trends, improvement rates, plateau detection
- **Performance degradation alerts**: Auto-detect >5% accuracy drops between cycles
- **Metrics tracked**: mean_accuracy, median_accuracy, max_accuracy, successful_count, exceptional_models
- **Notification config**: `config/notification_config.yaml` (email/SMTP/local alerts)

## Where to Edit

| Change | File(s) |
|--------|---------|
| Add/modify API endpoint | `function_app.py` |
| Chat provider logic | `talk-to-ai/src/chat_providers.py` (re-exported by `shared/chat_providers.py`) |
| Training orchestration | `scripts/training/autotrain.py` + `config/training/autotrain.yaml` |
| Autonomous training behavior | `scripts/training/autonomous_training_orchestrator.py` + `config/autonomous_training.yaml` |
| Master orchestrator (schedules/coordination) | `scripts/automation/master_orchestrator.py` + `config/master_orchestrator.yaml` |
| Aria automation | `scripts/automation/aria_automation.py` (server + training + health monitoring) |
| Full repo automation | `scripts/automation/repo_automation.py` (all components + backups + notifications) |
| Quantum jobs | `scripts/evaluation/quantum_autorun.py` + `quantum_autorun.yaml` (root) or `config/quantum/quantum_autorun.yaml` |
| MCP server tools | `quantum-ai/quantum_mcp_server.py` |
| Shared DB/telemetry | `shared/sql_engine.py`, `shared/telemetry.py`, `shared/cosmos_client.py` |
| Aria character interface | `aria_web/index.html`, `aria_web/aria_controller.js`, `aria_web/server.py` |
| Aria movement/gestures | `aria_web/aria_controller.js` (command parsing & animation triggers) |

## Safety Rules

- Always `--dry-run` orchestrators before GPU/QPU execution
- Quantum: simulate locally first, then use `azure_ionq_simulator`, only then real QPU
- Real QPU jobs require `azure_confirm_cost: true` in YAML + cost estimate review
- Never hardcode secrets — use `local.settings.json` (dev) or Azure App Settings (prod)
- Monitor DB pool via `/api/ai/status` (warns at ≥80% saturation)

## Testing & Validation

- **Unit tests:** `pytest tests/ -m "not slow and not azure"` or `python scripts/test_runner.py --unit`
- **Integration tests:** `python scripts/test_runner.py --integration`
- **All tests:** `python scripts/test_runner.py --all`
- **VS Code Test Explorer:** Use 🧪 icon for interactive test running
- **Markers:** `@pytest.mark.slow`, `@pytest.mark.azure`, `@pytest.mark.integration`
- **Chat dataset validation:** `python scripts/validate_datasets.py --category chat`

## Optional Services

**SQL persistence** (optional):
- Enable via `QAI_DB_CONN` env var (SQLite, PostgreSQL, Azure SQL)
- Pool size: `QAI_SQL_POOL_SIZE` (default: 10)
- Health: Check `/api/ai/status` for pool saturation (warns ≥80%)

**Cosmos DB** (optional, feature-flagged):
- Enable: `QAI_ENABLE_COSMOS=true`
- Config: `COSMOS_ENDPOINT`, `COSMOS_KEY`, `COSMOS_DATABASE`, `COSMOS_CONTAINER`
- Partition key: `/session_id`, enable TTL for cost savings

**Telemetry** (optional):
- Application Insights via `APPLICATIONINSIGHTS_CONNECTION_STRING`
- Non-blocking, gracefully degrades if unavailable

## Deployment Patterns

**Azure Functions (function_app.py):**
- Local dev: `func host start` (runs on port 7071)
- Deploy: `func azure functionapp publish <app-name>`
- Verify: `curl http://localhost:7071/api/ai/status | jq`

**Aria Web Server (aria_web/server.py):**
- Local: `cd aria_web && python server.py` (port 8080)
- Production: Deploy behind nginx/Apache with WSGI (gunicorn/uvicorn)
- Systemd service: Use `config/aria_automation.service` template

**Static Web Apps:**
- `chat-web/` — Pure HTML/JS, deploy to Azure Static Web Apps or any CDN
- No build step required, serves static assets

**Container deployment:**
- Dev container config at `.devcontainer/devcontainer.json`
- For production containers, consider multi-stage Docker builds with separate venvs

## Common Workflows & Troubleshooting

**Rapid validation workflow:**
```bash
# Step 1: Fast validation (instant, no imports)
python scripts/fast_validate.py

# Step 2: Unit tests (30-60s)
python scripts/test_runner.py --unit

# Step 3: Integration tests (if needed, 2-5 min)
python scripts/test_runner.py --integration

# Step 4: Check system health
curl http://localhost:7071/api/ai/status | jq
```

**Provider troubleshooting:**
```bash
# Check provider detection
curl http://localhost:7071/api/ai/status | jq '.provider'

# Test chat CLI with explicit provider
python talk-to-ai/src/chat_cli.py --provider local --once "test"
python talk-to-ai/src/chat_cli.py --provider azure --once "test"  # Needs Azure creds

# Debug LoRA adapter loading
python talk-to-ai/src/chat_cli.py --provider lora --adapter-path deployed_models/best_model --once "test"
```

**Training troubleshooting:**
```bash
# Validate config without execution
python scripts/training/autotrain.py --dry-run

# Check for GPU availability
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# Monitor active training
tail -f data_out/autotrain/job_*.log
watch -n 5 'cat data_out/autonomous_training_status.json | python -m json.tool'

# Check disk space (training writes large checkpoints)
df -h | grep -E '(Filesystem|/workspaces)'
```

**Database connection issues:**
```bash
# Check SQL pool status
curl http://localhost:7071/api/ai/status | jq '.database'

# Verify connection string format
python -c "import os; print(os.environ.get('QAI_DB_CONN', 'Not set'))"

# Test Cosmos DB (if enabled)
curl http://localhost:7071/api/ai/status | jq '.cosmos'
```

**Common error patterns:**
- `ModuleNotFoundError` → Ensure correct venv activated or `sys.path` adjusted in `function_app.py`
- `CUDA out of memory` → Reduce batch size in YAML configs or use `device: cpu`
- `Provider detection failed` → Check `/api/ai/status` and verify env vars in `local.settings.json`
- `Dataset not found` → Verify `datasets/` subdirectories exist (`chat/`, `quantum/`, `vision/`)
- `LoRA adapter invalid` → Must have both `adapter_config.json` + `adapter_model.safetensors`

## Modular Instructions

This repo uses component-specific instruction files in `.github/instructions/`:
- `functions.instructions.md` — Azure Functions API endpoints
- `shared-python.instructions.md` — Shared infrastructure patterns
- `quantum-ai*.instructions.md` — Quantum ML workflows
- `talk-to-ai*.instructions.md` — Chat CLI patterns
- `lora*.instructions.md` — LoRA fine-tuning patterns
- `chat-web.instructions.md` — Frontend SSE integration

These are automatically applied by VS Code based on file paths. Check attachment indicators to see which rules are active.

## Custom Coding Agents

**QAI Specialist Agent** (`.github/agents/my-agent.agent.md`):
- Expert in quantum-AI/ML hybrid development, training orchestration, and Azure Functions integration
- Understands provider detection chain, orchestrator-driven workflows, and quantum cost awareness
- Enforces safety protocols: dry-runs before execution, cost warnings for QPU, dataset immutability
- Quick commands: orchestrator validation, LoRA training, chat CLI testing, MCP server operations
- Access via GitHub Copilot agent selection or direct reference

**Chat Modes** (`.github/chatmodes/`):
- `Azure_function_codegen_and_deployment.chatmode.md` — Enterprise Azure Functions workflow with IaC
- `Azure_Static_Web_App.chatmode.md` — Static web app deployment patterns

**Usage**: These agents are invoked automatically based on context or can be explicitly selected in GitHub Copilot interfaces.

## Coding Agent Best Practices

**For AI Coding Agents working in this repository:**

1. **Always Check Context**
   - Read `.github/copilot-instructions.md` (this file) first
   - Check for relevant `.github/instructions/*.instructions.md` files based on file paths
   - Reference `.github/agents/my-agent.agent.md` for QAI-specific patterns

2. **Safety-First Approach**
   - `--dry-run` all orchestrators before GPU/QPU execution
   - Never modify files in `datasets/` (read-only)
   - Check `/api/ai/status` before making provider-dependent changes
   - Verify test suite passes: `python scripts/test_runner.py --unit`

3. **Follow Established Patterns**
   - Provider detection chain: Azure OpenAI → OpenAI → LMStudio → Local
   - Config precedence: `YAML base` < `CLI flags` < `per-job YAML` < `env vars`
   - Status files: Always write to `data_out/<orchestrator>/status.json`
   - Autonomous systems: Use signal-based triggers (`pkill -USR1`) for immediate execution

4. **Testing & Validation**
   - Run unit tests before committing: `python scripts/test_runner.py --unit`
   - Use `scripts/fast_validate.py` for quick cross-component validation
   - Check health endpoint: `curl http://localhost:7071/api/ai/status | jq`
   - Monitor logs: `tail -f data_out/autonomous_training.log`

5. **Documentation Updates**
   - Update this file when adding major features or changing workflows
   - Keep component-specific instructions in `.github/instructions/` in sync
   - Update PR checklist if adding new safety requirements
   - Document new orchestrators in "Where to Edit" table

6. **Cost & Resource Awareness**
   - Quantum: Simulate locally first, then Azure simulator, only then real QPU
   - Monitor DB pool saturation via `/api/ai/status` (warns at ≥80%)
   - Check GPU/CPU usage: `python scripts/resource_monitor.py --snapshot`
   - Review training analytics: `python scripts/training_analytics.py`

## PR Checklist for AI Agents & Reviewers

Before submitting or approving PRs, verify:

- [ ] **Dry-run orchestrators**: If modifying YAML configs or orchestrators, run `--dry-run` to validate changes before committing
- [ ] **Provider detection intact**: Changes to `shared/chat_providers.py` or `function_app.py` don't break detection chain (test with `/api/ai/status`)
- [ ] **Dataset immutability**: No modifications to `datasets/` — all outputs written to `data_out/`
- [ ] **Status.json compliance**: Orchestrator changes maintain status JSON writes to `data_out/<orchestrator>/status.json`
- [ ] **Test suite passes**: Run `python scripts/test_runner.py --unit` (or `--all` for integration tests)
- [ ] **No hardcoded secrets**: All API keys/connection strings use env vars or `local.settings.json`
- [ ] **Quantum cost gates**: QPU jobs include `azure_confirm_cost: true` in YAML configs
- [ ] **LoRA adapter validity**: If modifying training scripts, verify output includes both `adapter_config.json` + `adapter_model.safetensors`
- [ ] **Documentation sync**: Update relevant READMEs/instruction files if changing core workflows or adding features

Full/verbose guidance and advanced examples are preserved at `.github/copilot-instructions.full.md`. Ask me to expand any area or add examples for a specific change.
