# Aria — Copilot Instructions

Aria is an **interactive AI character platform** with autonomous learning, quantum ML integration, and multi-provider LLM chat backends. It features a 3D CSS-animated avatar, natural language command processing, continuous training orchestration, and Azure Functions-based APIs.

---

## Testing

```bash
# Run all tests
python3 -m pytest tests/ -q --tb=short

# Run a single test file
pytest tests/test_setup_env_check.py -v

# Run a single test function
pytest tests/test_setup_env_check.py::test_check_ai_token_health_valid_status -v

# Run by marker (unit, slow, azure, integration, e2e, selenium, playwright, pyppeteer)
pytest tests/ -m "not slow and not azure" -v

# Stop at first failure
pytest tests/ -x -v
```

Install dependencies into `.venv` first:
```bash
pip install -r requirements.txt        # or: python3 run_automation.py (sets up .venv automatically)
```

## Dev Environment

### DevContainer
Opens in Python 3.12 (Debian Bookworm). On create, a `.venv` is auto-created and `requirements.txt` is installed — no manual setup needed.

```bash
# If setting up outside the devcontainer:
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

`PYTHONUNBUFFERED=1` is set by default (stdout/stderr are unbuffered).

### Pre-commit hooks
```bash
git config core.hooksPath .githooks   # activate hooks from worktree
```
Before each commit, runs `python scripts/test_runner.py --unit --verbose 0`. Bypass only in emergencies: `git commit --no-verify`.

### VS Code / pytest
pytest is pre-configured: discovers `*test*.py`, runs with `-v --tb=short --no-header --color=yes`, auto-runs on save. Extra paths (`ai-projects/llm-maker/src`, `aria_web`, `tests/`, `ai-projects/quantum-ml/src`) are added to the Python analysis path.

---

## Automation

```bash
# Full automation: env validation → dep check → tests → fast-validate
python3 run_automation.py

# Continuous background daemon (default: every 60 min)
python3 run_continuous_automation.py --interval 60

# Environment/dependency check only
python3 scripts/setup_env_check.py
```

## Aria Character Web Server

```bash
cd apps/aria && python server.py           # Starts on port 8080 (or $ARIA_PORT)
# http://localhost:8080
# http://localhost:8080/auto-execute.html  (LLM action sequencer)
```

## Orchestrators (when present)

All orchestrators support `--dry-run` to validate without executing:
```bash
python scripts/autotrain.py --dry-run
python scripts/quantum_autorun.py --dry-run
python scripts/evaluation_autorun.py --dry-run
```

```bash
python scripts/fast_validate.py           # Cross-component quick check
python scripts/test_runner.py --unit      # Centralized test runner
python scripts/status_dashboard.py --watch  # Live orchestrator status
```

---

## Architecture

```
function_app.py (Azure Functions entry point)
  └── /api/chat, /api/tts, /api/quantum/*, /api/ai/status
        ├── ai-projects/chat-cli/src/       (multi-provider chat, AGI, memory)
        ├── ai-projects/quantum-ml/src/     (MCP server, Qiskit, Azure Quantum)
        └── shared/                         (chat_providers, db_logging, telemetry, cosmos_client)

apps/aria/server.py  (port 8080)
  └── /api/aria/command, /api/aria/execute, /api/aria/state, /api/aria/world

apps/dashboard/serve.py  (port 8000)
  └── Training/orchestrator monitoring UI

scripts/*_orchestrator.py  →  data_out/<name>/status.json  (machine-readable state)
```

**Each `ai-projects/*` subdirectory has its own isolated virtualenv.** Do not cross-import between them directly — all shared infra goes through `shared/`.

### Chat provider detection chain (`shared/chat_providers.py`)

```
explicit --provider flag → LMStudio → Azure OpenAI → OpenAI → LoRA adapter → local echo fallback
```

Required env vars per provider:
- LMStudio: `LMSTUDIO_BASE_URL`, `LMSTUDIO_MODEL`
- Azure OpenAI: `AZURE_OPENAI_API_KEY` + `AZURE_OPENAI_ENDPOINT` + `AZURE_OPENAI_DEPLOYMENT` + `AZURE_OPENAI_API_VERSION`
- OpenAI: `OPENAI_API_KEY`

### Configuration precedence

`YAML base` < `CLI flags` < `per-job YAML` < `environment variables`

Local dev config lives in `local.settings.json` (Azure Functions format, never commit secrets).

---

## Key Conventions

### Test organization

- Test files: `test_*.py` in `tests/`
- Load scripts under test via `importlib.util.spec_from_file_location` (not imports) — this is the established pattern for testing standalone scripts
- Use `monkeypatch` for dependency injection; pytest markers for categorization

```python
# Standard pattern for testing a script file
def _load_module():
    spec = importlib.util.spec_from_file_location("module_name", Path(__file__).parent.parent / "scripts" / "module.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
```

### Orchestrator outputs

- All outputs go to `data_out/<orchestrator>/` — **never write outputs to source directories**
- `datasets/` is **read-only** — never modify existing datasets
- Each orchestrator writes `data_out/<orchestrator>/status.json`:
  ```json
  { "total_jobs": N, "succeeded": N, "failed": N, "running": N, "last_updated": "ISO8601", "avg_duration": seconds }
  ```

### Hook scripts (`.github/hooks/scripts/`)

Hooks receive context via environment variables and must exit 0 on success:
```python
COPILOT_HOOK_EVENT    # or hook_event_name / HOOK_EVENT_NAME
COPILOT_HOOK_PAYLOAD  # JSON string
transcript_path       # path to JSONL transcript
```

### Aria character actions

8 core actions in the auto-execute system: `move`, `say`, `pickup`, `drop`, `throw`, `gesture`, `look`, `wait`. Command parsing uses LLM-powered parser with rule-based frozenset keyword fallback (pre-compiled at module level for O(1) lookup).

### Performance patterns

- Pre-compile regex at module scope (not in loops): `_RE_PATTERN = re.compile(r'...')`
- Use `frozenset` for keyword membership tests
- Autonomous training cycles: state machine `discovery → training → analysis → optimization → deployment`; signal-based immediate trigger via `pkill -USR1 -f autonomous_training`

---

## Safety Rules

- Always `--dry-run` orchestrators before GPU/QPU execution
- Quantum jobs: simulate locally → `azure_ionq_simulator` → real QPU only with `azure_confirm_cost: true` in YAML
- Never hardcode secrets — use `local.settings.json` (dev) or Azure App Settings (prod)
- Check `/api/ai/status` for DB pool saturation (warns at ≥80%)

---

## Where to Edit

| Change | File |
|--------|------|
| Azure Functions API endpoints | `function_app.py` |
| Chat provider logic | `ai-projects/chat-cli/src/chat_providers.py` (re-exported by `shared/chat_providers.py`) |
| Aria character interface | `apps/aria/index.html`, `apps/aria/aria_controller.js`, `apps/aria/server.py` |
| Training orchestration | `scripts/autotrain.py` + `autotrain.yaml` |
| Autonomous training behavior | `scripts/autonomous_training_orchestrator.py` + `config/autonomous_training.yaml` |
| Quantum jobs | `scripts/quantum_autorun.py` + `quantum_autorun.yaml` |
| Shared DB/telemetry | `shared/sql_engine.py`, `shared/telemetry.py`, `shared/cosmos_client.py` |
| Monitoring dashboard | `apps/dashboard/` |
| Environment validation | `scripts/setup_env_check.py` |

---

## `ai-projects/` Sub-projects

Each sub-project has its **own isolated virtualenv** and `requirements.txt`. Never share venvs across sub-projects.

| Sub-project | Entry point | Purpose |
|-------------|-------------|---------|
| `chat-cli/src/chat_cli.py` | `--provider <name> --once "msg"` | Multi-provider chat CLI with AGI + memory |
| `chat-cli/src/chat_providers.py` | imported by `shared/` | Provider detection chain (re-exported by `shared/chat_providers.py`) |
| `chat-cli/src/agi_provider.py` | — | Chain-of-thought reasoning layer |
| `chat-cli/src/token_utils.py` | — | Token counting and context-window pruning |
| `chat-cli/src/quantum_provider.py` | — | Quantum-backed response provider |
| `quantum-ml/src/` | `quantum_mcp_server.py` | MCP server, Qiskit circuits, Azure Quantum integration |
| `lora-training/microsoft_phi-silica-3.6_v1/` | `scripts/train_lora.py` | Phi-3.x LoRA fine-tuning (local + AzureML) |
| `llm-maker/src/` | `tool_maker.py`, `website_maker.py` | Safe tool/website generation from prompts |
| `cooking-ai/src/` | `agents/`, `main.py` | Recipe generation agent with provider/utils pattern |
| `lmstudio-mcp/` | — | LMStudio MCP server bridge |
| `writer-reviewer-workflow/` | — | Document review agent workflow |

### Smoke-testing sub-projects

```bash
# Chat CLI smoke test
python ai-projects/chat-cli/src/chat_cli.py --provider local --once "Hello"

# LoRA training dry-run (validates config without downloading models)
cd ai-projects/lora-training/microsoft_phi-silica-3.6_v1
python scripts/train_lora.py --dry-run --dataset ./data --config ./lora/lora.yaml
```

---

## LoRA Fine-Tuning (`ai-projects/lora-training/microsoft_phi-silica-3.6_v1/`)

### Dataset format

All training data must be JSONL with a `messages` array:
```json
{"messages": [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello!"}]}
```

CSV files (`prompt,response` or `input,output` columns) can be converted:
```bash
python scripts/prepare_dataset.py --input <data> --output-dir ./data --train-ratio 0.99
```

### Training configs (`lora/`)

Multiple speed presets available: `lora.yaml`, `lora_fast.yaml`, `lora_ultrafast.yaml`, `lora_tinyllama_ultrafast.yaml`, `lora_qwen_ultrafast.yaml`. Key fields:
- `save_dir`: output path (default: `data_out/lora_training`)
- `epochs`, `learning_rate`, `gradient_accumulation_steps`
- `early_stopping_patience` / `early_stopping_threshold`

Valid LoRA adapter output requires **both**: `adapter_config.json` + `adapter_model.safetensors`

### AzureML deployment (`azureml/`)

```bash
# Submit training job to AzureML
az ml job create -f azureml/job-lora-train.yml --set compute=azureml:gpu-cluster

# Hyperparameter sweep
az ml job create -f azureml/job-lora-sweep.yml
```

The AzureML job YAMLs expect datasets at `azureml://datastores/workspaceblobstore/paths/qai/datasets/...`. Override at submission time with `--set inputs.train_manifest.path=...`.

---

## Quantum ML (`ai-projects/quantum-ml/`)

### Pipeline

1. **Local simulation** — run circuits with Qiskit's `AerSimulator` (zero cost)
2. **Azure IonQ Simulator** — `azure_ionq_simulator` backend (low cost)
3. **Real QPU** — only with `azure_confirm_cost: true` in YAML + cost review

```bash
python scripts/quantum_autorun.py --dry-run    # Validate without running
python ai-projects/quantum-ml/quantum_mcp_server.py  # Start MCP server
```

### Key source files (`src/`)

| File | Purpose |
|------|---------|
| `quantum_circuit_optimizer.py` | Circuit compilation and gate reduction |
| `hybrid_qnn.py` | Quantum-classical hybrid neural net |
| `quantum_classifier.py` / `_enhanced.py` | QML classification models |
| `quantum_llm_*.py` | Quantum-augmented LLM pipelines |
| `azure_quantum_integration.py` | Azure Quantum job submission |
| `azure_ml_integration.py` | AzureML experiment tracking |
| `dataset_loader.py` | Quantum dataset loading + streaming |

Results land in `quantum-ai/results/` and `data_out/quantum/`.

---

## Shared Infrastructure (`shared/`)

`shared/` re-exports from `ai-projects/chat-cli/src/` for use by `function_app.py` and `apps/`. All modules degrade gracefully when optional services are unavailable.

| Module | Purpose | Enable via |
|--------|---------|------------|
| `chat_providers.py` | Provider detection chain + streaming | `LMSTUDIO_BASE_URL` / `AZURE_OPENAI_*` / `OPENAI_API_KEY` |
| `sql_engine.py` | SQLAlchemy pool with saturation alerts | `QAI_DB_CONN` (SQLite/Postgres/Azure SQL) |
| `cosmos_client.py` | Cosmos DB lazy connection | `QAI_ENABLE_COSMOS=true` + `COSMOS_*` vars |
| `telemetry.py` | OpenTelemetry → App Insights | `APPLICATIONINSIGHTS_CONNECTION_STRING` |
| `db_logging.py` | Fault-tolerant DB logging (SP wrappers) | `QAI_DB_CONN` |
| `chat_memory.py` | Semantic memory with embeddings | — |
| `request_validator.py` | JSON schema validation for API inputs | — |
| `subscription_manager.py` | Monetization / Stripe webhooks | `STRIPE_*` vars |
| `evaluation_utils.py` | Shared metrics for batch evaluation | — |
| `token_utils.py` | Token counting + context pruning | — |

All optional services fail silently — check `/api/ai/status` for live health.

---

## Azure Deployment

### Azure Functions (primary API layer)

```bash
func host start                            # Local dev server (port 7071)
curl http://localhost:7071/api/ai/status | jq  # Health check
```

`function_app.py` adds `ai-projects/chat-cli/src` and `ai-projects/quantum-ml/src` to `sys.path` at startup. All `shared/` modules must be importable from the Functions host.

### AzureML (training jobs)

Defined in `ai-projects/lora-training/microsoft_phi-silica-3.6_v1/azureml/`. Uses curated GPU environment `AzureML-pytorch-2.4-ubuntu22.04-py310-cuda12` by default.

### Azure Quantum (QPU jobs)

CI/CD via `ai-projects/quantum-ml/src/Untitled-1.yml` (GitHub Actions — triggers on push to `main`, runs `azure/quantum_master_orchestration.ps1` on `windows-latest`).

---

## `generated_tools/` and `llm-maker`

`ai-projects/llm-maker/src/` generates validated Python tools and websites from prompts:
- `tool_maker.py` → validated tool → `generated_tools/`
- `website_maker.py` → complete website bundle
- `tool_validator.py` — sandboxed execution check before saving
- `tool_registry.py` — registry of available generated tools

All generated tools are written to `generated_tools/data_out/`. Never commit untested generated output.

---

## apps/chat/ — Chat Web UI

- Pure HTML/CSS/JS frontend (no build step needed), served at `/api/chat-web` via Azure Functions
- Streaming uses Fetch API `ReadableStream` (**not** EventSource/SSE) — `POST /api/chat/stream`
- Non-streaming fallback: `POST /api/chat`
- Request body: `{ messages, temperature, max_tokens, stream: true }`
- Chunks are plain text decoded incrementally; markdown rendered post-stream with `marked.js` + `hljs`
- Abort support via `AbortController`
- Other API calls: `GET /api/ai/status` (provider detection), `POST /api/quantum/classify`, `POST /api/vision/infer`, `POST /api/image/generate`
- UI controls: temperature slider (0–1), max_tokens, system prompt, quantum mode toggle, vision image upload
- Conversation history + settings persisted in `localStorage`

---

## apps/store/ — Product Storefront

- Pure static HTML/CSS/JS — no backend required; open `apps/store/index.html` directly
- "TechDrop" electronics retail storefront (demo/example app)
- Pages: `index.html` (hero + featured), `products.html` (filter/sort/search), `product.html` (detail + related), `about.html`, `contact.html`
- Product data in `js/products.js` as `const PRODUCTS = [...]` array with fields: `id, name, price, category, image, description, featured, features[]`
- Shared platform nav bar (links to Aria/Chat/Dashboard/Store) in `js/components.js`
- Filtering: category dropdown, price range, live search, sort by price/alpha

---

## Component-specific instructions

Detailed per-component guidance lives in `.github/instructions/*.instructions.md` (applied automatically by VS Code based on file paths). Custom agents are in `.github/agents/`.
