# QAI – Copilot Instructions (Full Archive)

**Quick reference for AI agents** working in the Aria hybrid quantum‑AI/ML workspace. Focus on the essentials you need to be productive **today** while staying safe and cost‑aware.

---

## 1️⃣ Core Architecture

- **Projects (isolated venvs)**:
  - `ai-projects/quantum-ml/` – quantum‑ML pipelines, MCP server, web dashboard.
  - `ai-projects/chat-cli/` – multi‑provider chat CLI (Azure OpenAI, OpenAI, LoRA, local fallback).
  - `AI/microsoft_phi-silica-3.6_v1/` – Phi‑3.5 LoRA fine‑tuning.
- **Integration layer**: `function_app.py` (Azure Functions) exposing:
  - `/api/chat` – streaming chat.
  - `/api/chat-web` – web UI.
  - `/api/tts` – Azure Speech TTS (local fallback).
  - `/api/quantum/*` – quantum job submission/monitoring.
  - `/api/ai/status` – health & config summary.
- **Shared services** (`shared/`):
  - `chat_providers.py` – detection order **Azure OpenAI → OpenAI → LoRA → Local**.
  - `sql_engine.py` / `cosmos_client.py` – optional persistence (feature‑flagged).
  - `chat_memory.py` – embeddings + similarity search.
  - `telemetry.py` – Application Insights.

---

## 2️⃣ Data Conventions

- **Immutable source**: `datasets/` (read‑only).
- **Write‑only output**: `data_out/` – orchestrators write `status.json` and model artefacts.
- **Chat dataset schema** (`datasets/chat/<name>/`):

 ```json
 [{"messages": [{"role": "user|assistant", "content": "..."}]}]
 ```

- Validate with `python scripts/validate_datasets.py --category chat`.
- LoRA adapters are ready when both `adapter_config.json` **and** `adapter_model.safetensors` exist.

---

## 3️⃣ Core Workflows & Commands

| Goal | Command (repo root) | Notes |
|------|--------------------|-------|
| Dry‑run any orchestrator | `python scripts/autotrain.py --dry-run` (or quantum_autorun, evaluation_autorun) | Validate config only |
| Quick LoRA train & auto‑deploy | `python scripts/train_and_promote.py --quick --auto-promote` | Uses TinyLlama by default |
| Full multi‑model pipeline | `python scripts/automated_training_pipeline.py --quick` | Data → train → eval → ranking |
| Start Functions host | `func host start` | Serves all `/api/*` endpoints |
| Open web chat UI | Open `http://localhost:7071/api/chat-web` after host starts | - |
| Run unit tests | `python scripts/test_runner.py --unit` | - |
| Run full test suite with coverage | `python scripts/test_runner.py --all --coverage` | - |

---

## 4️⃣ Quantum‑AI Guardrails

- Simulate locally first: `python scripts/quantum_autorun.py --job local_simulator`.
- Real QPU jobs require `azure_confirm_cost: true` in `quantum_autorun.yaml` **and** a cost estimate via `estimate_quantum_cost`.
- MCP server entry point: `python ai-projects/quantum-ml/quantum_mcp_server.py` (tools: `create_quantum_circuit`, `simulate_quantum_circuit`, `submit_quantum_job`, `estimate_quantum_cost`).

---

## 5️⃣ Provider Detection & Health

- Detection order in `shared/chat_providers.py`: Azure OpenAI → OpenAI → LoRA → Local.
- Missing any Azure env var falls back to the next provider.
- Quick health check: `curl http://localhost:7071/api/ai/status | jq` (shows active provider, missing env vars, LoRA readiness, DB pool saturation, telemetry).

---

## 6️⃣ Safety & Cost Awareness

- **Dry‑run** all orchestrators before GPU/QPU usage.
- Limit QPU shots to ≤ 100 for first runs; increase only after a cost estimate.
- Monitor DB pool saturation via `/api/ai/status` (warning at 80 %).
- Cosmos DB is optional; enable with `QAI_ENABLE_COSMOS=true` and configure TTL for cheap cleanup.

---

## 7️⃣ Where to Look First

- `function_app.py` – HTTP routing and dynamic imports.
- `shared/chat_providers.py` – provider logic.
- Orchestrator scripts in `scripts/` (`autotrain.py`, `quantum_autorun.py`, `evaluation_autorun.py`).
- YAML job specs: `autotrain.yaml`, `quantum_autorun.yaml`, `evaluation_autorun.yaml`.
- Root `README.md` – high‑level overview.
- `scripts/README.md` – list of automation commands.

---

*Keep this file up‑to‑date. Add notes for any missing pieces.*

## Copilot Quickstart for QAI (condensed)

- Architecture in one breath: three independent projects — `ai-projects/quantum-ml/` (quantum ML + MCP server), `ai-projects/chat-cli/` (CLI chat), and `AI/microsoft_phi-silica-3.6_v1/` (LoRA fine-tuning) — unified by `function_app.py` (Azure Functions) and shared infra in `shared/`.
- Key endpoints (served by Functions): `/api/chat`, `/api/chat-web`, `/api/tts`, `/api/quantum/*`, `/api/ai/status`. Check runtime health at `/api/ai/status`.
- Provider detection order (see `shared/chat_providers.py:detect_provider()`): Azure OpenAI → OpenAI → LoRA → Local. Azure needs all 4 env vars: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`, `AZURE_OPENAI_API_VERSION`.
- Immutable data model: read-only `datasets/`; write-only `data_out/`. Orchestrators run from repo root and emit machine-readable status JSON under `data_out/<orchestrator>/status.json`.
- Orchestrators you'll use most (PowerShell):
  - Dry-run safety first: `python .\scripts\autotrain.py --dry-run`; `python .\scripts\quantum_autorun.py --dry-run`; `python .\scripts\evaluation_autorun.py --dry-run`.
  - Quick LoRA train+deploy: `python .\scripts\train_and_promote.py --quick --auto-promote`.
  - Ultrafast TinyLlama: `python .\scripts\automated_training_pipeline.py --models tinyllama --quick`.
- LoRA readiness: adapter must contain `adapter_config.json` and `adapter_model.safetensors`. Use CLI: `python .\talk-to-ai\src\chat_cli.py --provider lora --model <adapter_dir>`.
- Dataset convention (chat): `datasets/chat/<name>/{train.json,test.json}` with `[{"messages": [{"role": "user|assistant", "content": "..."}]}]`. Validate with `python .\scripts\validate_datasets.py --category chat`.
- Quantum guardrails: always simulate locally (Qiskit Aer) before cloud; real QPU runs require `azure_confirm_cost: true` in `quantum_autorun.yaml`. Use `python .\scripts\quantum_autorun.py --job azure_ionq_simulator` first.
- MCP server (quantum tools): `python .\quantum-ai\quantum_mcp_server.py`. Tools include `create_quantum_circuit`, `simulate_quantum_circuit`, `submit_quantum_job`, `estimate_quantum_cost` (see `ai-projects/quantum-ml/quantum_mcp_server.py`).
- Testing workflow: prefer `python .\scripts\test_runner.py --all` (fast) or VS Code Test Explorer (🧪). Pytest markers: `not slow and not azure` for local runs.
- Azure storage/dev: Azurite databases present at root; Functions host can run offline. Configure speech TTS via `AZURE_SPEECH_KEY`/`AZURE_SPEECH_REGION` or enable local fallback with `QAI_ENABLE_LOCAL_TTS=true`.
- Config precedence: YAML base < CLI flags < per-job YAML overrides < environment variables. Never hardcode secrets; use `local.settings.json` (dev) or Azure App Settings (prod).
- High-signal files to read first:
  - `function_app.py` — HTTP endpoints and dynamic imports.
  - `shared/chat_providers.py` — provider abstraction and detection logic.
  - `scripts/autotrain.py`, `scripts/quantum_autorun.py`, `scripts/evaluation_autorun.py` — orchestrators and status writing.
  - `autotrain.yaml`, `quantum_autorun.yaml`, `evaluation_autorun.yaml` — declarative job specs.
  - Health and observability: Application Insights integrates via `shared/telemetry.py`; optional Cosmos persistence via `shared/cosmos_client.py` (feature‑flagged). Failures are non-blocking; check `/api/ai/status` for env and pool saturation.

For full details and workflows, see the extended guide below (preserved). This quickstart is designed for immediate agent productivity and aligns with VS Code’s custom instructions guidance.

## 🚀 Getting Started (New Contributors)

### First-Time Setup (5 minutes)

```powershell
# 1. Clone and navigate to workspace
cd c:\Users\Bryan\OneDrive\AI

# 2. Verify Python 3.9+ installed
python --version

# 3. Run health check
python .\scripts\system_health_check.py

# 4. Test basic functionality (no API keys needed)
python .\talk-to-ai\src\chat_cli.py --provider local --once "Hello"

# 5. Run fast unit tests to verify setup
python .\scripts\test_runner.py --unit
```
