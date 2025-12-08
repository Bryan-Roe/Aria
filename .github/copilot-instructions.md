<!-- Concise, practical instructions for AI agents working in this repo. Keep this file short — use the full archive (.github/copilot-instructions.full.md) for details. -->

# Aria — Copilot Quick Guide

*Last updated: November 29, 2025*

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
nohup python scripts/autonomous_training_orchestrator.py > data_out/autonomous_training.log 2>&1 &

# Trigger immediate cycle (skip 30-min wait)
pkill -USR1 -f autonomous_training

# Full repo automation (Aria + training + quantum + monitoring)
python scripts/repo_automation.py --start
python scripts/repo_automation.py --status
./scripts/start_repo_automation.sh full          # Bash wrapper with menu
./scripts/start_repo_automation.sh stop          # Stop all components

# Aria character automation (server + continuous training)
python scripts/aria_automation.py --mode full
python scripts/aria_automation.py --status

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
python scripts/autotrain.py --dry-run         # Validate training config (12 jobs)
python scripts/quantum_autorun.py --dry-run   # Validate quantum config
python scripts/evaluation_autorun.py --dry-run # Validate evaluation config

# === TRAINING PIPELINES ===
python scripts/automated_training_pipeline.py --quick  # Quick LoRA (TinyLlama)
python scripts/train_and_promote.py --quick --auto-promote  # Train + auto-deploy

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

## Critical Patterns

**Autonomous/self-managing systems:**
- `scripts/autonomous_training_orchestrator.py` — Continuous learning with 30-min cycles (infinite by default)
  - Self-discovers datasets (scans `datasets/quantum`, `datasets/chat`, `datasets/massive_quantum`)
  - Self-optimizes: Adaptive epochs `[25, 50, 100, 200]` based on performance history
  - Self-heals: Graceful error handling, continues on failure, logs to `data_out/autonomous_training.log`
  - State: `data_out/autonomous_training_status.json` (cycles_completed, best_accuracy, dataset_inventory)
  - Config: `config/autonomous_training.yaml` (cycle_interval_minutes, epochs_progression, min_datasets)
  - Trigger: Time-based (30min) OR signal-based (`pkill -USR1 -f autonomous_training`)
- `scripts/repo_automation.py` — Full repo automation (all components: Aria + training + quantum + datasets)
- `scripts/aria_automation.py` — Aria-specific automation (server on port 8080 + continuous training)
- `scripts/master_orchestrator.py` — Coordinates all sub-orchestrators with schedules/dependencies
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
- All in `scripts/` with matching root YAMLs (e.g., `autotrain.yaml`, `quantum_autorun.yaml`)
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
| Training orchestration | `scripts/autotrain.py` + root `autotrain.yaml` |
| Autonomous training behavior | `scripts/autonomous_training_orchestrator.py` + `config/autonomous_training.yaml` |
| Master orchestrator (schedules/coordination) | `scripts/master_orchestrator.py` + `config/master_orchestrator.yaml` |
| Aria automation | `scripts/aria_automation.py` (server + training + health monitoring) |
| Full repo automation | `scripts/repo_automation.py` (all components + backups + notifications) |
| Quantum jobs | `scripts/quantum_autorun.py` + root `quantum_autorun.yaml` |
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
