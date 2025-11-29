<!-- Concise, practical instructions for AI agents working in this repo. Keep this file short — use the full archive (.github/copilot-instructions.full.md) for details. -->

# QAI — Copilot Quick Guide

Short & actionable summary for AI agents editing Aria.

## Architecture

- **Three isolated projects + Functions integration layer:**
  - `quantum-ai/` — MCP server, web dashboard, quantum ML pipelines (separate venv)
  - `talk-to-ai/` — chat CLI with multi-provider support (separate venv)
  - `AI/microsoft_phi-silica-3.6_v1/` — Phi-3.5 LoRA fine-tuning (separate venv)
  - `function_app.py` — Azure Functions integration exposing all APIs
- **Integration points:**
  - `function_app.py` dynamically imports from talk-to-ai/src and quantum-ai/src (adds to sys.path)
  - Shared infra in `shared/`: re-exports chat providers, DB engines, telemetry, Cosmos client
- **API endpoints** (via `function_app.py`):
  - `/api/chat` — streaming chat SSE
  - `/api/chat-web` — web UI HTML
  - `/api/tts` — Azure Speech TTS (falls back to local if enabled)
  - `/api/quantum/*` — quantum job submission/monitoring
  - `/api/ai/status` — health check showing active provider, env vars, DB pool, Cosmos status

## Quick Commands (from repo root)

```bash
# Start Functions host (serves all APIs)
func host start

# Health check
curl http://localhost:7071/api/ai/status | jq

# Smoke test chat (no keys needed)
python talk-to-ai/src/chat_cli.py --provider local --once "Hello"

# Run tests
python scripts/test_runner.py --unit           # Fast unit tests
python scripts/test_runner.py --all            # All tests
python scripts/test_runner.py --coverage       # With coverage

# Dry-run orchestrators (validates config)
python scripts/autotrain.py --dry-run
python scripts/quantum_autorun.py --dry-run
python scripts/evaluation_autorun.py --dry-run

# Quick LoRA pipeline (TinyLlama by default)
python scripts/automated_training_pipeline.py --quick

# Train and auto-deploy best model
python scripts/train_and_promote.py --quick --auto-promote

# Start MCP server (quantum tools)
python quantum-ai/quantum_mcp_server.py
```

## Critical Patterns

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

## Where to Edit

| Change | File(s) |
|--------|---------|
| Add/modify API endpoint | `function_app.py` |
| Chat provider logic | `talk-to-ai/src/chat_providers.py` (re-exported by `shared/chat_providers.py`) |
| Training orchestration | `scripts/autotrain.py` + root `autotrain.yaml` |
| Quantum jobs | `scripts/quantum_autorun.py` + root `quantum_autorun.yaml` |
| MCP server tools | `quantum-ai/quantum_mcp_server.py` |
| Shared DB/telemetry | `shared/sql_engine.py`, `shared/telemetry.py`, `shared/cosmos_client.py` |

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
