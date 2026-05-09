<!-- Concise, practical instructions for AI agents working in this repo. Keep this file short — use the full archive (.github/copilot-instructions.full.md) for details. -->

# Aria — Copilot Quick Guide

*Last updated: November 29, 2025*

Short & actionable summary for AI agents editing Aria — an interactive AI character platform with autonomous learning, quantum ML integration, and multi-provider chat backends.

## Architecture

- **Interactive AI Character Platform** with 3D animated avatar, natural language movement commands, and real-time object interaction
- **Three isolated projects + Functions integration layer:**
  - `ai-projects/quantum-ml/` — MCP server, web dashboard, quantum ML pipelines (separate venv)
  - `ai-projects/chat-cli/` — chat CLI with multi-provider support (separate venv)
  - `AI/microsoft_phi-silica-3.6_v1/` — Phi-3.5 LoRA fine-tuning (separate venv)
  - `function_app.py` — Azure Functions integration exposing all APIs
- **Integration points:**
  - `function_app.py` dynamically imports from ai-projects/chat-cli/src and ai-projects/quantum-ml/src (adds to sys.path)
  - Shared infra in `shared/`: re-exports chat providers, DB engines, telemetry, Cosmos client
- **Web Interfaces:**
  - `apps/aria/` — Interactive Aria character interface with CSS animations, eye tracking, gestures
  - `apps/chat/` — Streaming chat UI with SSE support
- **API endpoints** (via `function_app.py`):
  - `/api/chat` — streaming chat SSE
  - `/api/chat-web` — web UI HTML
  - `/api/tts` — Azure Speech TTS (falls back to local if enabled)
  - `/api/quantum/*` — quantum job submission/monitoring
  - `/api/ai/status` — health check showing active provider, env vars, DB pool, Cosmos status
  - `/api/quantum-llm/status` — quantum-powered LLM backend info (backend, qubits, fallback, provider)
  - `/api/quantum-llm/chat` — non-streaming quantum-augmented LLM completion
  - `/api/quantum-llm/stream` — SSE streaming quantum-augmented LLM (same format as `/api/chat/stream`)
- **Aria Web API endpoints** (via `apps/aria/server.py` on port 8080):
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
cd apps/aria && python server.py                  # Start Aria web interface (port 8080)
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
python scripts/test_runner.py --unit --coverage # Unit tests + coverage
python scripts/test_runner.py --list-suites   # Show available suites
python scripts/test_runner.py --unit --watch  # Re-run on file changes
python ai-projects/chat-cli/src/chat_cli.py --provider local --once "Hello"  # Smoke test
python scripts/fast_validate.py              # Quick validation (datasets, scripts, venvs, configs, providers, deps)
python scripts/cleanup_artifacts.py          # Preview old artifact cleanup (dry-run)
python scripts/cleanup_artifacts.py --apply  # Actually delete old artifacts

# === ORCHESTRATORS (Manual Execution) ===
python scripts/autotrain.py --dry-run         # Validate training config (12 jobs)
python scripts/quantum_autorun.py --dry-run   # Validate quantum config
python scripts/evaluation_autorun.py --dry-run # Validate evaluation config

# === TRAINING PIPELINES ===
python scripts/automated_training_pipeline.py --quick  # Quick LoRA (TinyLlama)
python scripts/train_and_promote.py --quick --auto-promote  # Train + auto-deploy

# === MCP & TOOLS ===
python ai-projects/quantum-ml/quantum_mcp_server.py       # Start quantum MCP server

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
| Quantum LLM pipeline | `ai-projects/quantum-ml/src/quantum_llm/pipeline.py` |
| Quantum token sampler | `ai-projects/quantum-ml/src/quantum_llm/quantum_sampler.py` |
| Quantum embedding transformer | `ai-projects/quantum-ml/src/quantum_llm/quantum_embeddings.py` |
| Quantum provider router | `ai-projects/quantum-ml/src/quantum_llm/quantum_router.py` |
| Quantum LLM config | `ai-projects/quantum-ml/src/quantum_llm/config.py` |
| Chat provider logic | `ai-projects/chat-cli/src/chat_providers.py` (re-exported by `shared/chat_providers.py`) |
| Training orchestration | `scripts/autotrain.py` + root `autotrain.yaml` |
| Autonomous training behavior | `scripts/autonomous_training_orchestrator.py` + `config/autonomous_training.yaml` |
| Master orchestrator (schedules/coordination) | `scripts/master_orchestrator.py` + `config/master_orchestrator.yaml` |
| Aria automation | `scripts/aria_automation.py` (server + training + health monitoring) |
| Full repo automation | `scripts/repo_automation.py` (all components + backups + notifications) |
| Quantum jobs | `scripts/quantum_autorun.py` + root `quantum_autorun.yaml` |
| MCP server tools | `ai-projects/quantum-ml/quantum_mcp_server.py` |
| Shared DB/telemetry | `shared/sql_engine.py`, `shared/telemetry.py`, `shared/cosmos_client.py` |
| Aria character interface | `apps/aria/index.html`, `apps/aria/aria_controller.js`, `apps/aria/server.py` |
| Aria movement/gestures | `apps/aria/aria_controller.js` (command parsing & animation triggers) |
| Semantic memory/embeddings | `shared/chat_memory.py` (generate_embedding, fetch_similar, store) |
| Token management | `ai-projects/chat-cli/src/token_utils.py` (counting, pruning) |
| LLM tool generation | `ai-projects/llm-maker/src/tool_maker.py`, `tool_validator.py` |
| Website generation | `ai-projects/llm-maker/src/website_maker.py` |
| Cooking AI recipes | `ai-projects/cooking-ai/src/agents/recipe_agent.py` |
| Subscriptions/monetization | `shared/subscription_manager.py` + `setup_monetization.py` |
| DB logging (fault-tolerant) | `shared/db_logging.py` (SP wrappers) |
| Vision/expression AI | `scripts/vision_inference.py` (TinyConvNet) |
| Batch model evaluation | `scripts/batch_evaluator.py` + `config/evaluation/` |
| Monitoring dashboard | `apps/dashboard/` (hub, analytics, GPU monitor) |
| AGI reasoning | `ai-projects/chat-cli/src/agi_provider.py` |
| Test runner | `scripts/test_runner.py` (centralized suite orchestrator) |
| Request validation | `shared/request_validator.py` (JSON schema validation) |
| Artifact cleanup | `scripts/cleanup_artifacts.py` (data_out/ retention) |
| Model evaluation | `scripts/evaluate_model.py` (delegates or fallback metrics) |
| Fast validation | `scripts/fast_validate.py` (configs, providers, deps) |

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
- `agi-provider.instructions.md` — AGI reasoning system
- `aria-character.instructions.md` — Interactive character system
- `aria-web.instructions.md` — Aria web server module
- `autonomous-training.instructions.md` — Autonomous training orchestration
- `training-scripts.instructions.md` — Training script patterns
- `orchestrator-configs.instructions.md` — YAML orchestrator configs
- `dashboard.instructions.md` — Monitoring dashboard
- `tests.instructions.md` — Testing infrastructure
- `llm-maker.instructions.md` — Safe tool/website generation
- `cooking-ai.instructions.md` — Cooking AI recipe agent
- `chat-providers.instructions.md` — Multi-provider chat system
- `chat-memory.instructions.md` — Semantic memory & embeddings
- `subscription.instructions.md` — Subscription/monetization
- `db-logging.instructions.md` — Fault-tolerant DB logging
- `telemetry.instructions.md` — OpenTelemetry setup
- `token-utils.instructions.md` — Token counting & context pruning
- `evaluation.instructions.md` — Batch evaluation & analytics
- `vision-inference.instructions.md` — Vision AI & CNN models

These are automatically applied by VS Code based on file paths. Check attachment indicators to see which rules are active.

## Custom Coding Agents

Available agents in `.github/agents/`:

| Agent | Purpose |
|-------|---------|
| `ai.agent.md` | Primary autonomous agent — task decomposition, multi-step execution |
| `my-agent.agent.md` | QAI specialist — quantum-AI/ML development |
| `agi-reasoning.agent.md` | Chain-of-thought reasoning, self-reflection (CoT is internal, final answer only) |
| `visible-reasoning.agent.md` | Visible step-by-step reasoning, shows CoT trace to users |
| `aria-character.agent.md` | Interactive character commands, animations |
| `autonomous-trainer.agent.md` | LoRA training lifecycle, model promotion |
| `full-stack-debugger.agent.md` | Cross-stack issue diagnosis |
| `automated-code-fixer.agent.md` | Autonomous code improvements |
| `ai-architect.agent.md` | AI pipeline design, provider integration |
| `llm-maker.agent.md` | Safe tool/website generation |
| `chat-provider.agent.md` | Multi-provider chat, streaming, memory |
| `platform-ops.agent.md` | Subscriptions, monitoring, deployment |
| `vision-ai.agent.md` | Expression/emotion classification |
| `data-pipeline.agent.md` | Batch evaluation, dataset management |

**Mode equivalents now live in `.github/agents/`**:
- `AI_model_training.agent.md` — End-to-end LoRA training, evaluation, and model promotion
- `Aria_character_development.agent.md` — Interactive character commands, actions, world generation
- `Quantum_ML_development.agent.md` — Quantum circuits, simulation, Azure Quantum pipelines
- `Full_stack_debugging.agent.md` — Cross-stack diagnostic protocol
- `AI_chat_development.agent.md` — Multi-provider chat, streaming, memory, self-learning
- `Azure_function_codegen_and_deployment.agent.md` — Enterprise Azure Functions workflow with IaC
- `Azure_Static_Web_App.agent.md` — Static web app deployment patterns

**Prompts** (`.github/prompts/`):
- `agi.prompt.md` — Autonomous AGI reasoning with multi-step analysis and self-correction (chain-of-thought is internal, not exposed in output)
- `reason.prompt.md` — Visible step-by-step reasoning that exposes chain-of-thought, confidence scores, and self-reflection to the user (uses `visible-reasoning` agent)
- `debug.prompt.md` — Systematic diagnostic protocol
- `review.prompt.md` — Code review (correctness, security, performance)
- `aria-command.prompt.md` — Natural language → Aria actions
- `train.prompt.md` — Training execution with safety
- `quantum.prompt.md` — Cost-aware quantum workflows
- `chat.prompt.md` — Multi-provider chat with memory
- `generate-tool.prompt.md` — Safe Python tool generation
- `generate-website.prompt.md` — Complete website generation
- `evaluate.prompt.md` — Model evaluation & benchmarking
- `deploy.prompt.md` — Model/service deployment
- `optimize.prompt.md` — Performance analysis & optimization

**Usage**: Agents are invoked automatically based on context or explicitly selected in GitHub Copilot interfaces.

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
