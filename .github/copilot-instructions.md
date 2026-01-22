<!-- Concise, practical instructions for AI agents working in this repo. Keep this file short — use the full archive (.github/copilot-instructions.full.md) for details. -->

# Aria — Copilot Quick Guide

*Last updated: January 21, 2026*

Short & actionable summary for AI agents editing Aria — an interactive AI character platform with autonomous learning, quantum ML integration, and multi-provider chat backends.

## Critical Architectural Patterns

**Multi-Layered Component Isolation (3 Independent Projects + Azure Functions):**
This repo packages three completely isolated Python projects (each with separate venvs):
1. **quantum-ai/** — Quantum ML pipelines, MCP server, Azure Quantum integration (Python 3.9+)
2. **talk-to-ai/** — Multi-provider chat CLI, chat memory, provider detection (Python 3.10+)
3. **AI/microsoft_phi-silica-3.6_v1/** — LoRA fine-tuning trainer for Phi/Qwen models (Python 3.10+)

Then **function_app.py** (Azure Functions) dynamically imports from all three via sys.path manipulation to expose unified REST APIs. This design allows independent venv management, dependency isolation, and zero shared state between training/chat/quantum workloads.

**Provider Detection Chain** (in `shared/chat_providers.py`, re-exported by `function_app.py`):
```python
# Precedence order (first match wins):
1. LMStudio (if LMSTUDIO_BASE_URL set) → fastest, local-only
2. Azure OpenAI (needs all 4: AZURE_OPENAI_API_KEY + ENDPOINT + DEPLOYMENT + API_VERSION)
3. OpenAI (OPENAI_API_KEY)
4. LoRA adapter (explicit --provider lora + adapter path)
5. Local echo fallback (zero dependencies, deterministic)
```

**Orchestrator-Driven Workflows** (State-Machine Pattern):
All heavy lifting flows through YAML-driven orchestrators that write status.json to `data_out/<name>/`:
- `autotrain.py` — LoRA training jobs (sequential, per-job logging)
- `quantum_autorun.py` — Quantum ML evaluation
- `autonomous_training_orchestrator.py` — Continuous 30-min learning cycles (infinite or limited)
- `master_orchestrator.py` — Coordinates all sub-orchestrators with cron schedules & dependencies

Each maintains a single source of truth: `data_out/<orchestrator>/status.json` with job counts, success/failure rates, timestamps.

## Architecture

- **Interactive AI Character Platform** with 3D animated avatar, natural language movement commands, and real-time object interaction
- **Three isolated projects + Functions integration layer:**
  - `quantum-ai/` — MCP server, web dashboard, quantum ML pipelines (Python 3.9+, separate venv)
  - `talk-to-ai/` — chat CLI with multi-provider support (Python 3.10+, separate venv)
  - `AI/microsoft_phi-silica-3.6_v1/` — Phi-3.5 LoRA fine-tuning (Python 3.10+, separate venv)
  - `function_app.py` — Azure Functions integration exposing unified APIs
  - `scripts/` — Orchestrators (training, quantum, evaluation) + automation/monitoring suites
- **Integration points:**
  - `function_app.py` dynamically imports from talk-to-ai/src and quantum-ai/src (sys.path manipulation)
  - Shared infra in `shared/`: re-exports chat providers, DB engines, telemetry, Cosmos client
  - `scripts/automation/` — Full repo automation (aria_automation.py, repo_automation.py, master_orchestrator.py)
- **Web Interfaces:**
  - `aria_web/server.py` (port 8080) — Interactive Aria character (CSS animations, eye tracking, gestures)
  - `chat-web/` — Streaming chat UI (pure HTML/JS, SSE backend via function_app.py)
  - `aria_web/auto-execute.html` — LLM-powered action sequence planner (plan vs execute modes)
- **Function App API endpoints** (via `function_app.py`):
  - `/api/chat` — streaming chat SSE
  - `/api/ai/status` — comprehensive health check (provider detection, env vars, DB pool, GPU status, venv status)
  - `/api/quantum/*` — quantum job submission/monitoring
  - `/api/tts` — Azure Speech TTS (falls back to local if enabled)
- **Aria Web Server endpoints** (via `aria_web/server.py`):
  - `GET /api/aria/state` — current stage state (position, objects, expressions)
  - `POST /api/aria/command` — process natural language commands (LLM + rule-based fallback)
  - `POST /api/aria/execute` — auto-execute action sequences (plan or execute mode)
  - `POST /api/aria/object` — manage objects (add, update, remove)
  - `POST /api/aria/world` — LLM-powered themed world generation

## Key Features

**Interactive Character System (aria_web/):**
- 3D CSS-animated character with smooth transitions and physics-based movement
- Natural language command processing ("move left", "wave", "dance", "jump", "pickup ball")
- **Auto-Execute System**: LLM-powered action parser converts natural language to structured sequences
  - 8 core actions: move, say, pickup, drop, throw, gesture, look, wait
  - Plan mode (preview) and execute mode (run sequences) in auto-execute.html
  - Dual fallback: LLM-powered when available, fast rule-based parsing when offline
- Object interaction system (add, pickup, drop, throw with trajectory physics)
- **World Generation**: LLM-powered themed environment creation
- Eye tracking (follows mouse cursor)
- Gesture system (wave, dance, jump, idle animations)
- Real-time speech synthesis via Azure TTS or local fallback (QAI_ENABLE_LOCAL_TTS)
- Server-synchronized state management (position, objects, expressions stored in stage_state dict)

**Autonomous Learning (autonomous_training_orchestrator.py):**
- Self-discovering dataset collection (scans datasets/, auto-downloads from sklearn/openml/huggingface)
- Adaptive epoch selection (25→50→100→200 progression based on performance history)
- Automatic model promotion when accuracy > threshold (default 0.90)
- Performance degradation detection (alerts if accuracy drops >5%)
- Continuous 30-min learning cycles (infinite by default, configurable in autonomous_training.yaml)
- Graceful error recovery with state persistence to data_out/autonomous_training_status.json

**Multi-Provider Chat (shared/chat_providers.py):**
- Azure OpenAI, OpenAI, LMStudio, local models via detection chain
- LoRA adapter support for fine-tuned models (explicit --provider lora)
- Automatic provider fallback chain (LMStudio → Azure OpenAI → OpenAI → local)
- SSE-based streaming responses via function_app.py
- Provider detection logic: explicit flag > env var detection > fallback

## Quick Commands (from repo root)

```bash
# === AUTONOMOUS SYSTEMS (Self-Managing) ===
# Start autonomous training (continuous 30-min cycles)
nohup python scripts/training/autonomous_training_orchestrator.py > data_out/autonomous_training.log 2>&1 &

# Trigger immediate cycle (skip 30-min wait)
pkill -USR1 -f autonomodashboard + Aria character + continuous training
python scripts/monitoring/auto_ops_dashboard.py --watch &  # Background monitor
./scripts/start_repo_automation.sh full                    # Start all components
./scripts/start_repo_automation.sh status                  # Check status
./scripts/start_repo_automation.sh stop                    # Stop gracefully

# Aria character automation (server on 8000 + continuous training)
./scripts/start_aria.sh full                # Interactive setup
python scripts/automation/aria_automation.py --mode full   # Direct start
python scripts/automation/aria_automation.py --status      # Status checkning)
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
python scripts/monitoring/auto_ops_dashboard.py # CLI orchestrator dashboard
python scripts/monitoring/auto_ops_dashboard.py --watch # Live monitoring
python scripts/monitoring/vscode_quickstart.py  # VS Code monitoring suite (interactive menu)
python scripts/monitoring/vscode_quickstart.py --full # Start dashboard + alerts
python scripts/monitoring/vs_code_server.py     # Web dashboard (http://localhost:8765)
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

**GPU Detection & Configuration:**
- Training scripts auto-detect CUDA via PyTorch
- Force GPU: Set `device: cuda` in YAML configs (autotrain.yaml, autonomous_training.yaml)
- Check availability: `python -c "import torch; print(torch.cuda.is_available())"`
- Monitor usage: `watch -n 1 nvidia-smi`

**GPU Training Configs:**
- `config/training/autotrain.yaml` — All jobs configured with `device: cuda`
- `config/autonomous_training.yaml` — `device: cuda`, `max_cpu_cores: 0`, `max_gpu_memory_gb: 0` (use all)
- Batch size tuning: Reduce max_train_samples/max_eval_samples if CUDA OOM errors occur

**Progressive Training Workflow:**
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
 for AI Agents

**Autonomous/Self-Managing Orchestrators:**

1. **Autonomous Training** (`scripts/training/autonomous_training_orchestrator.py`):
   - Continuous learning with 30-min cycles (config: `config/autonomous_training.yaml`)
   - Self-discovers datasets: scans `datasets/{quantum,chat,massive_quantum}`, auto-downloads from sklearn/openml/huggingface
   - Adaptive epochs: `[25, 50, 100, 200]` progression based on performance history
   - State machine: discovery → collection → training → analysis → optimization → deployment
   - Triggers: Time-based (30min interval) OR signal-based (`pkill -USR1 -f autonomous_training`)
   - Status file: `data_out/autonomous_training_status.json` (source of truth)
   - Error recovery: Graceful degradation, continues on failure, logged to `data_out/autonomous_training.log`

2. **Training Orchestrator** (`scripts/training/autotrain.py`):
   - Sequential LoRA fine-tuning jobs from YAML config (`config/training/autotrain.yaml`)
   - Per-job logging: `data_out/autotrain/<job_name>/<timestamp>/stdout.log`
   - Two runners: `hf` (full Hugging Face stack) or `local` (streamlined)
   - Status: `data_out/autotrain/status.json` (machine-readable job summary)
   - Supports `--dry-run` for validation before GPU execution

3. **Master Orchestrator** (`scripts/automation/master_orchestrator.py`):
   - Coordinates all sub-orchestrators (autotrain, quantum_autorun, evaluation_autorun, aria_automation)
   - Config: `config/master_orchestrator.yaml` (cron schedules, priorities, dependencies, retry logic)
   - Enforces orchestrator ordering: autotrain → quantum_autorun → evaluation_autorun

4. **Aria Automation** (`scripts/automation/aria_automation.py`):
   - Manages aria_web server (port 8080) + continuous training integration
   - Server startup, health monitoring, graceful shutdown
   - Integrated with master orchestrator via config

**Monitoring & Observability:**
- `scripts/monitoring/auto_ops_dashboard.py` — Real-time orchestrator status dashboard
  - Flags: `--watch` (live), `--problems` (errors only), `--compact` (brief), `--export` (JSON)
  - Reads from all orchestrator status.json files
- `scripts/monitoring/vs_code_server.py` — Flask web dashboard for VS Code Simple Browser (port 8765)
  - Live HTML dashboard with auto-refresh, status cards, alert highlighting
  - VS Code integration: Open http://localhost:8765 in Simple Browser
- `scripts/monitoring/vscode_quickstart.py` — Interactive launcher for VS Code monitoring suite
  - Flags: `--server` (dashboard), `--alerts` (alert monitor), `--cli` (CLI dashboard), `--full` (all components)
  - Checks dependencies (flask, flask-cors), starts services, opens browser
- `scripts/monitoring/vs_code_alert_monitor.py` — Background alert monitor (VS Code notifications)
  - Scans status.json files for failures, sends VS Code notifications
  - Runs as background service alongside dashboard server
- `scripts/status_dashboard.py` — Legacy unified status view (supports --watch, --export)
- `scripts/resource_monitor.py` — CPU/memory/disk/GPU snapshot with threshold alerts

**Data Conventions:**
- `datasets/` is **read-only** — never modify existing datasets
- All outputs go to `data_out/<orchestrator>/` with `status.json` as source of truth
- Chat datasets format: `[{"messages": [{"role": "user|assistant", "content": "..."}]}]`
- LoRA adapters: both `adapter_config.json` + `adapter_model.safetensors` required
- Quantum circuit results: stored in `data_out/<job>/circuits/` with JSON metadata

**Config Precedence** (for YAML orchestrators):
`YAML base defaults` < `CLI --flags` < `per-job YAML overrides` < `environment variables`

**Database Patterns:**
- SQL pooling: Monitored via `/api/ai/status` (warns at ≥80% saturation)
- Cosmos DB (feature-flagged): Enable via `QAI_ENABLE_COSMOS=true`
- Chat memory: Embeddings stored + retrieval via `shared/chat_memory.py` (optional)

## Where to Edit

| Component | File(s) | Purpose |
|-----------|---------|---------|
| Web APIs | [function_app.py](function_app.py) | Add/modify REST endpoints (chat, quantum, TTS, status) |
| Aria Character Server | [aria_web/server.py](aria_web/server.py) | Endpoints for character state, commands, object interaction |
| Chat Providers | [shared/chat_providers.py](shared/chat_providers.py) | Multi-provider chat logic (detection chain, streaming) |
| LoRA Training | [scripts/training/autotrain.py](scripts/training/autotrain.py) + [config/training/autotrain.yaml](config/training/autotrain.yaml) | Training job orchestration |
| Autonomous Training | [scripts/training/autonomous_training_orchestrator.py](scripts/training/autonomous_training_orchestrator.py) + [config/autonomous_training.yaml](config/autonomous_training.yaml) | Continuous learning cycles, dataset discovery |
| Master Orchestration | [scripts/automation/master_orchestrator.py](scripts/automation/master_orchestrator.py) + [config/master_orchestrator.yaml](config/master_orchestrator.yaml) | Cron scheduling, orchestrator coordination |
| Aria Automation | [scripts/automation/aria_automation.py](scripts/automation/aria_automation.py) | Server lifecycle, health monitoring |
| Full Repo Automation | [scripts/automation/repo_automation.py](scripts/automation/repo_automation.py) | All components + backups + notifications |
| Quantum Jobs | [scripts/evaluation/quantum_autorun.py](scripts/evaluation/quantum_autorun.py) + quantum_autorun.yaml | Quantum circuit submission/monitoring |
| MCP Server | [quantum-ai/quantum_mcp_server.py](quantum-ai/quantum_mcp_server.py) | Quantum ML tools for Model Context Protocol |
| Shared DB/Telemetry | [shared/sql_engine.py](shared/sql_engine.py), [shared/telemetry.py](shared/telemetry.py), [shared/cosmos_client.py](shared/cosmos_client.py) | Database pooling, tracing, Cosmos integration |
| Character UI/Gestures | [aria_web/index.html](aria_web/index.html), [aria_web/aria_controller.js](aria_web/aria_controller.js) | CSS animations, command parsing, gesture triggers |
| Auto-Execute Planner | [aria_web/auto-execute.html](aria_web/auto-execute.html) | LLM-powered action sequence planning/execution |

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
- **Fast validation:** `python scripts/fast_validate.py` (instant, no imports) — quick cross-component check
- **Watch mode:** `python scripts/test_runner.py --watch` (auto-reruns on file change)
- **Chat dataset validation:** `python scripts/validate_datasets.py --category chat`

## Optional Services

**SQL Persistence** (feature-flagged):
- Enable: `QAI_DB_CONN` env var (SQLite, PostgreSQL, Azure SQL)
- Pool size: `QAI_SQL_POOL_SIZE` (default: 10)
- Health: Check `/api/ai/status` for pool saturation (warns ≥80%)

**Cosmos DB** (feature-flagged):
- Enable: `QAI_ENABLE_COSMOS=true`
- Config: `COSMOS_ENDPOINT`, `COSMOS_KEY`, `COSMOS_DATABASE`, `COSMOS_CONTAINER`
- Partition key: `/session_id`, enable TTL for cost savings

**Local TTS Fallback**:
- Enable: `QAI_ENABLE_LOCAL_TTS=true` (no Azure Speech required)
- Falls back automatically if Azure Speech unavailable

**Application Insights** (optional):
- Enable: `APPLICATIONINSIGHTS_CONNECTION_STRING` env var
- Non-blocking, g** (`function_app.py`):
- Local dev: `func host start` (runs on port 7071)
- Deploy: `func azure functionapp publish <app-name>`
- Verify: `curl http://localhost:7071/api/ai/status | jq`
- Key endpoints: `/api/chat`, `/api/quantum/*`, `/api/ai/status`, `/api/tts`

**Aria Web Server** (`aria_web/server.py`):
- Local: `cd aria_web && python server.py` (port 8080)
- Production: Deploy behind nginx/Apache with WSGI (gunicorn/uvicorn)
- Systemd service: Use `config/aria_automation.service` template
- Auto-Execute UI: Access at `http://localhost:8080/auto-execute.html`

**Chat Web UI** (`chat-web/`):
- Pure HTML/JS, deploy to Azure Static Web Apps or any CDN
- No build step required, serves static assets
- Uses SSE from function_app.py for streaming responses

**Container Deployment:**
- Dev container config at `.devcontainer/devcontainer.json`
- For production: M assets

**Container deployment:**
- Dev container config at `.devcontainer/devcontainer.json`
- For production containers, consider multi-stage Docker builds with separate venvs

## Common Workflows & Troubleshooting

**Rapid Development Workflow:**
```bash
# Step 1: Validate entire repo in seconds (no imports)
python scripts/fast_validate.py

# Step 2: Run unit tests (30-60s)
python scripts/test_runner.py --unit

# Step 3: Check system health (shows active provider, DB pool, GPU status)
curl http://localhost:7071/api/ai/status | jq

# Step 4: Manual provider testing
python talk-to-ai/src/chat_cli.py --provider local --once "test"
python talk-to-ai/src/chat_cli.py --provider azure --once "test"  # requires Azure creds
```

**Training Debugging:**
```bash
# Validate orchestrator config without execution
python scripts/training/autotrain.py --dry-run

# Check GPU availability
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"

# Monitor active training in real-time
tail -f data_out/autotrain/job_*.log

# Watch autonomous training progress
watch -n 5 'cat data_out/autonomous_training_status.json | python -m json.tool'

# Check disk space (training writes large checkpoints)
df -h /workspaces
```

**Provider Issues:**
```bash
# Check which provider is active
curl http://localhost:7071/api/ai/status | jq '.provider'

# Debug LoRA adapter loading
python talk-to-ai/src/chat_cli.py --provider lora --adapter-path deployed_models/best_model --once "test"

# Test each provider explicitly
python talk-to-ai/src/chat_cli.py --provider lmstudio --once "test"  # LMStudio local
python talk-to-ai/src/chat_cli.py --provider azure --once "test"     # Azure OpenAI
```

**Database Issues:**
```bash
# Monitor SQL pool saturation (warns at ≥80%)
curl http://localhost:7071/api/ai/status | jq '.database'

# Verify Cosmos DB (if enabled)
curl http://localhost:7071/api/ai/status | jq '.cosmos'

# Check environment variable setup
python -c "import os; print(os.environ.get('QAI_DB_CONN', 'Not set'))"
```

**Common Error Patterns:**
| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: chat_providers` | Incorrect sys.path in function_app.py | Verify talk-to-ai/src is in sys.path |
| `CUDA out of memory` | Batch size too large | Reduce max_train_samples or use device: cpu in YAML |
| `Provider detection failed` | Missing env vars | Run `/api/ai/status` and verify env vars in local.settings.json |
| `Dataset not found` | Missing category subdirectory | Verify datasets/{chat,quantum,vision} exist |
| `LoRA adapter invalid` | Missing adapter files | Check both adapter_config.json + adapter_model.safetensors present |
| `Port 8080 already in use` | Aria server still running | Kill: `pkill -f aria_web` or `lsof -ti:8080 \| xargs kill` |

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
 First**
   - Read this file (`.github/copilot-instructions.md`) for essential patterns
   - Check for relevant `.github/instructions/*.instructions.md` files based on file paths you're editing
   - Verify `.github/agents/my-agent.agent.md` for QAI-specific patterns (quantum, training, orchestration)

2. **Safety-First Approach**
   - Always `--dry-run` orchestrators before GPU/QPU execution (autotrain.py, quantum_autorun.py)
   - Never modify files in `datasets/` (read-only)
   - Check `/api/ai/status` before making provider-dependent changes
   - Verify test suite passes: `python scripts/test_runner.py --unit`
   - Monitor resource usage: GPU/CPU status visible in `/api/ai/status`, Cosmos pool saturation warnings

3. **Follow Established Patterns**
   - Provider detection chain: explicit flag → LMStudio → Azure OpenAI → OpenAI → fallback
   - Config precedence: YAML base < CLI flags < per-job YAML < env vars
   - Status files: Always write to `data_out/<orchestrator>/status.json`
   - Autonomous systems: Use signal-based triggers (`pkill -USR1`) for immediate execution

4. **Debugging & Issue Detection**
   - Chat provider issues: Check `/api/ai/status` for active provider + env var presence
   - Training failures: Review orchestrator logs in `data_out/<name>/job_*.log`
   - LoRA adapter problems: Verify both `adapter_config.json` + `adapter_model.safetensors` exist
   - Provider detection failures: Test with `talk-to-ai/src/chat_cli.py --provider local --once "test"`
   - Database connection issues: Check SQL pool saturation via `/api/ai/status`

5. **Before Committing**
   - Run `python scripts/fast_validate.py` (instant cross-component validation)
   - Run `python scripts/test_runner.py --unit` (unit tests only)
   - If modifying orchestrators: test with `--dry-run` first
   - If changing providers: verify chain still works with `/api/ai/status`
   - Check disk space for training outputs: `df -h | grep /workspaces`
   - Verify no hardcoded secrets (use `local.settings.json` or env vars)real QPU
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

Full/verbose guidance and advanced examples are preserved at `.github/copilot-instructions.full.md`. 

**Quick Reference**: For 1-2 minute rapid lookups, see `.github/copilot-cheatsheet.md` (commands, patterns, safety checklist, troubleshooting).

Ask me to expand any area or add examples for a specific change.
