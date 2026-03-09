<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
# Aria - Interactive AI Character Platform

<div align="center">

✨ **Meet Aria** ✨

*An intelligent, animated AI character with movement, gestures, and natural language interaction*

</div>

---

## 🎭 About Aria

Aria is an interactive AI character that combines:

- **3D Animated Avatar** - CSS-based character with smooth animations, eye tracking, and expressive gestures
- **Natural Language Movement** - Tell Aria to "move left", "wave", "dance", or "jump" using plain English
- **Multi-Provider AI Backend** - Powered by Azure OpenAI, OpenAI, or local models with LoRA fine-tuning
- **Real-time Object Interaction** - Add, pickup, drop, and throw objects on a virtual stage
- **Quantum ML Integration** - Experimental quantum-classical hybrid training

## 🚀 Quick Start

### 🤖 **NEW: Complete Repository Automation**

One command to automate the entire repository:

```bash
# Start everything (all components)
./scripts/start_repo_automation.sh full

# Or select specific components
./scripts/start_repo_automation.sh aria           # Aria character only
./scripts/start_repo_automation.sh training       # Training pipeline
./scripts/start_repo_automation.sh                # Interactive menu

# Check status
./scripts/start_repo_automation.sh status

# Stop all
./scripts/start_repo_automation.sh stop
```

**Automated Components:**

- ✅ **Aria Character** - Web server + continuous training
- ✅ **LoRA Training** - Automated fine-tuning pipelines
- ✅ **Quantum ML** - Quantum computing workflows
- ✅ **Evaluation** - Model evaluation system
- ✅ **Datasets** - Auto-discovery & downloads
- ✅ **Monitoring** - Health checks & alerts
- ✅ **Backups** - Daily automated backups

See [REPO_AUTOMATION_GUIDE.md](REPO_AUTOMATION_GUIDE.md) for full documentation.

### 🎭 Aria Character Only

If you only want Aria automation:

```bash
# Interactive menu
./scripts/start_aria.sh

# Direct start
./scripts/start_aria.sh full

# Background mode
./scripts/start_aria.sh full --background

# Check status
./scripts/start_aria.sh status
```

See [ARIA_AUTOMATION_GUIDE.md](ARIA_AUTOMATION_GUIDE.md) for details

📖 **Full Guide:** [ARIA_AUTOMATION_GUIDE.md](ARIA_AUTOMATION_GUIDE.md)  
📋 **Quick Ref:** [ARIA_QUICKREF.txt](ARIA_QUICKREF.txt)

---

### Chat with Aria (Web Interface)

```bash
# Start the Aria web server
cd aria_web
python server.py

# Open http://localhost:8000 in your browser
```

### Chat with Aria (CLI)

```bash
cd talk-to-ai
pip install -r requirements.txt
python src/chat_cli.py --provider local --once "Hello Aria!"
```

### Aria Character Demo

```bash
# Open the animated character page
# Navigate to: chat-web/aria.html
```

## 📁 Project Structure

This workspace is organized around Aria with supporting AI/ML infrastructure:

### 🎭 **aria_web/** - Aria Character Interface

The main Aria character controller with 3D animations and object interactions.

**Features:**

- 🎨 **3D Character Control** - Move Aria around the stage using waypoints
- 📦 **Object Management** - Add, pickup, drop, and throw objects
- 🔄 **Server Sync** - All client actions synchronized to Python backend
- 💬 **Chat Interface** - Send natural language commands
- 🌍 **World Generation** - LLM-powered themed environment creation

**Quick Start:**

```bash
cd aria_web
python server.py
# Open http://localhost:8000
```

**API Endpoints:**

- `GET /api/aria/state` - Get current stage state
- `POST /api/aria/command` - Send movement commands
- `POST /api/aria/object` - Manage objects
- `POST /api/aria/world` - Generate themed worlds

**Documentation:** [aria_web/README.md](aria_web/README.md)

---

### 💬 **talk-to-ai/** - Aria Chat CLI

Multi-provider chat CLI for interacting with Aria using natural language.

**Features:**

- 🤖 Provider auto-detection (Azure OpenAI → OpenAI → Local)
- 🎯 Aria movement command generation
- 💾 Conversation persistence (JSONL format)
- 🔌 Zero-dependency local mode for offline development
- ⚡ Streaming responses

**Quick Start:**

```powershell
cd talk-to-ai
pip install -r requirements.txt

# Local mode (no API keys required)
python .\src\chat_cli.py --provider local

# With OpenAI
$env:OPENAI_API_KEY = "sk-..."
python .\src\chat_cli.py --provider openai

# With Azure OpenAI
$env:AZURE_OPENAI_API_KEY = "..."
$env:AZURE_OPENAI_ENDPOINT = "https://....openai.azure.com/"
$env:AZURE_OPENAI_DEPLOYMENT = "gpt-4o-mini"
python .\src\chat_cli.py --provider azure
```

**Interactive Commands:** `/new`, `/save`, `/exit`

**Aria Movement Commands:** Try saying "Move Aria left", "Wave", "Dance", or "Jump"!

**Documentation:** See [talk-to-ai/README.md](talk-to-ai/README.md)

---

## 🛠️ Local dev adapter & telemetry (OTLP)

- Local development helper: `local_dev_adapter.py` is a tiny Flask-based adapter that
  lets you call a subset of the Azure Functions handlers (notably `/api/ai/status`) locally
  without running the full Functions host. It also includes a lightweight `azure.functions`
  shim so the `function_app` module can be imported in minimal containers or CI environments.

  Quick start:

  ```bash
  # Start the local adapter (serves /api/ai/status on port 7071)
  python local_dev_adapter.py
  # Open http://localhost:7071/api/ai/status
  ```

- OTLP exporter warnings during tests: you may see connection refused errors from
  OpenTelemetry's OTLP exporter (typically trying to reach localhost:4318). These are
  benign if you don't run an OTLP collector locally. To quiet them during tests you can
  either run a local collector (on port 4318) or disable OTLP exporting for the test run:

  ```bash
  # Prefer disabling tracing exporters for fast, local test runs
  export OTEL_TRACES_EXPORTER=none
  # or clear the OTLP endpoint
  export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=""
  pytest -q
  ```

  Note: `OTEL_TRACES_EXPORTER=none` is supported by many OpenTelemetry SDKs to disable
  remote exporting; alternatively clearing `APPLICATIONINSIGHTS_CONNECTION_STRING` will
  prevent the repo's Azure Monitor instrumentation from initializing.

  The local dev adapter is useful for quick health checks and debugging function handlers
  without the overhead of the Functions Core Tools host.

### 🧠 **AI/microsoft_phi-silica-3.6_v1/** - Aria Model Fine-Tuning

Fine-tuning workspace for training Aria's language understanding using LoRA and soft prompt techniques.

**Features:**

- 🎯 LoRA fine-tuning for Aria movement commands
- 📊 Aria-specific training datasets in `datasets/chat/aria_*`
- ☁️ Azure ML deployment infrastructure
- 🔧 Azure AI Toolkit integration

**Aria Training Datasets:**

- `datasets/chat/aria_movement/` - Movement command training data
- `datasets/chat/aria_expanded/` - Extended Aria interactions
- `datasets/chat/aria_simple/` - Basic Aria commands

**Quick Training:**

```bash
# Quick Aria movement training
python scripts/train_aria_direct.py

# Validate Aria dataset
python scripts/test_aria_dataset.py --validate-only
```

**Documentation:** See [docs/aria/](docs/aria/) for comprehensive Aria training guides

---

### ⚛️ **quantum-ai/** - Quantum ML Platform (Experimental)

Hybrid quantum-classical ML for advanced Aria capabilities.

**Features:**

- 🎨 Interactive Web Dashboard for training visualization
- ⚛️ Quantum circuit creation and simulation
- ☁️ Azure Quantum integration (IonQ, Quantinuum)
- 🤖 MCP server with 8 quantum tools

**Quick Start:**

```bash
cd quantum-ai
./start_dashboard.sh
# Open http://localhost:5000
```

**Documentation:** [quantum-ai/README.md](quantum-ai/README.md)

---

## 🔧 Development Environment

### Prerequisites

- **Python:** 3.9+
- **PowerShell:** Primary shell for all commands
- **Azure CLI:** For Azure Quantum and Azure ML deployments
- **Git:** Version control

### Common Commands

#### Environment Setup

```powershell
# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

#### Azure Login

```powershell
az login
az account set --subscription "<subscription-id>"
```

### Local Development Tools

**Azurite (Azure Storage Emulator):**
The workspace root contains Azurite database files for local Azure Storage development:

- `__azurite_db_*.json`
- `__blobstorage__/`
- `__queuestorage__/`

These are used for local testing of Azure Functions and Storage features.

### Remote TTS (chat-web)

To enable server-side TTS (used by the web UI at /api/chat-web -> /api/tts) add your Azure Speech credentials to your local env or Functions settings.

- Add AZURE_SPEECH_KEY and AZURE_SPEECH_REGION to your environment or into `local.settings.json` when running the Functions host locally.
- See `local.settings.json.example` and `.env.example` in the repo root for templates you can copy and fill in.

### Optional local TTS fallback (no Azure keys)

If you prefer not to configure Azure Speech for local development, the Functions app can optionally synthesize audio locally using pyttsx3 (offline) or gTTS (Google TTS) when Azure credentials are not provided.

To enable local fallback:

1. Set QAI_ENABLE_LOCAL_TTS=true in your `local.settings.json` or `.env` (the example files include this key).
2. Install the extra packages into your Functions environment:

```powershell
# From repo root
pip install -r requirements.txt
```

3. Restart the Functions host. When you call `/api/tts` the server will try Azure first, then pyttsx3, then gTTS.

Note: pyttsx3 is generally best on Windows (uses SAPI), gTTS uses Google Translate's TTS API and will produce MP3 output if used. The `/api/tts` endpoint returns audio_base64 and the format field (mp3 or wav). The client will use the returned format to play the audio.

---

## 🚀 Deployment

### Quantum AI Deployment

  --parameters quantum_workspace.parameters.json

See `quantum-ai/azure/DEPLOYMENT.md` for complete deployment guide.

---

- **Microsoft Simulators:** Free
- **IonQ:** ~$0.00003 per gate-shot
- **Quantinuum:** ~$0.00015 per circuit execution

**Best Practice:** Always test on `qiskit_aer` simulator locally before submitting to paid hardware.

### Azure OpenAI

- Costs vary by model and token usage
- Use local provider for development/testing

---

### Quantum AI MCP Server

The `quantum-ai/quantum_mcp_server.py` exposes 8 quantum computing tools via Model Context Protocol:

**Circuit Tools:**

- `create_quantum_circuit` - Build circuits (bell, ghz, entanglement, random, custom)
- `simulate_quantum_circuit` - Local simulation (Qiskit Aer, up to 100k shots)
- `get_quantum_circuit_properties` - Analyze depth, gates, topology

**Azure Quantum Tools:**

- `connect_azure_quantum` - Authenticate to workspace
- `list_quantum_backends` - Enumerate hardware/simulators
- `submit_quantum_job` - Execute on real quantum computers
- `estimate_quantum_cost` - Calculate costs before running

**ML Tools:**

- `train_quantum_classifier` - Train hybrid models (iris, wine, breast_cancer, synthetic datasets)

**VS Code Integration:**
Add to `.vscode/mcp.json` (if supported by your VS Code version):

```json
{
  "quantum-ai": {
    "type": "stdio",
    "command": "python",
    "args": ["c:\\Users\\Bryan\\OneDrive\\AI\\quantum-ai\\quantum_mcp_server.py"]
  }
}
```

### Chat Provider Abstraction

All chat providers implement `BaseChatProvider.complete(messages, stream)`:

```python
messages = [{"role": "user", "content": "Hello"}]
response = provider.complete(messages, stream=True)
```

Add new providers by subclassing `BaseChatProvider`.

---

## 🧪 Quick Testing

### Aria Web Interface

```powershell
cd aria_web
python server.py
# Open http://localhost:8000
```

### Aria Chat CLI

```powershell
cd talk-to-ai
python .\src\chat_cli.py --provider local --once "Move Aria left"
```

### Aria Character Animation

```powershell
# Open chat-web/aria.html in your browser
# Click on Aria to see walking animation
# Press 'W' to wave, 'R' to raise arms
```

---

## 📝 File Organization

```
├── aria_web/               # 🎭 Main Aria character controller
│   ├── server.py           # Python backend API
│   ├── aria_controller.js  # Frontend character logic
│   └── index.html          # Interactive stage UI
├── chat-web/               # 💬 Web chat interface
│   ├── aria.html           # Animated Aria character page
│   └── index.html          # Chat with Aria web UI
├── datasets/chat/          # 📊 Aria training datasets
│   ├── aria_movement/      # Movement command training
│   ├── aria_expanded/      # Extended interactions
│   └── aria_simple/        # Basic commands
├── docs/aria/              # 📖 Aria documentation
│   ├── ARIA_MOVEMENT_COMPLETE.md
│   ├── ARIA_MOVEMENT_TRAINING.md
│   └── ARIA_VISUAL_SYSTEM.md
├── scripts/                # 🔧 Aria training & utility scripts
│   ├── train_aria_direct.py
│   ├── automate_aria_movement.py
│   └── test_aria_dataset.py
├── talk-to-ai/             # Chat CLI for Aria
├── quantum-ai/             # Quantum ML platform
├── AI/                     # Model fine-tuning workspace
├── config/                 # Configuration files
├── shared/                 # Shared Python modules
├── tests/                  # Test suites
└── data_out/               # Generated outputs (git-ignored)
```

---

## 📚 Documentation

### Aria Documentation

- **[docs/aria/](docs/aria/)** - Complete Aria system documentation
  - [ARIA_MOVEMENT_COMPLETE.md](docs/aria/ARIA_MOVEMENT_COMPLETE.md) - Implementation guide
  - [ARIA_MOVEMENT_TRAINING.md](docs/aria/ARIA_MOVEMENT_TRAINING.md) - Training reference
  - [ARIA_VISUAL_SYSTEM.md](docs/aria/ARIA_VISUAL_SYSTEM.md) - Visual system design
- **[aria_web/README.md](aria_web/README.md)** - Web interface and API docs
- **[aria_web/TESTING.md](aria_web/TESTING.md)** - Testing guide

### Supporting Documentation

- **[docs/README.md](docs/README.md)** - Documentation index
- **[docs/training/](docs/training/)** - LoRA and training guides
- **[docs/quantum/](docs/quantum/)** - Quantum computing documentation
- **[docs/database/](docs/database/)** - SQL and database setup

---

## ⚠️ Common Issues

### Aria Not Moving

If Aria commands aren't working:

1. Ensure the aria_web server is running: `python aria_web/server.py`
2. Check browser console for JavaScript errors
3. Verify API responses: `curl http://localhost:8000/api/aria/state`

### Azure Quantum Authentication

If you see "Failed to connect to Azure Quantum":

1. Run `az login`
2. Verify `quantum_config.yaml` has correct subscription_id and resource_group
3. Check workspace exists: `az quantum workspace show -g rg-quantum-ai -n quantum-ai-workspace`

### Chat Streaming Issues

Verify SDK version: `pip list | findstr openai` should show `openai>=1.37.0`

---

## 🔧 Recent Enhancements

**November 2025 Updates:**

- **🎭 Aria Character System**: Complete 3D animated character with movement, gestures, and object interaction
- **📊 Aria Training Pipeline**: Movement command datasets and training automation
- **🌍 LLM World Generation**: Dynamic themed environment creation via `/api/aria/world`
- **🎯 Movement Command Parser**: Natural language to `[aria:action:direction]` tag conversion
- **✨ Visual Enhancements**: Eye tracking, breathing animations, and character expressions

📖 **Aria Documentation:**

- [ARIA_MOVEMENT_COMPLETE.md](docs/aria/ARIA_MOVEMENT_COMPLETE.md) - Full implementation guide
- [ARIA_MOVEMENT_TRAINING.md](docs/aria/ARIA_MOVEMENT_TRAINING.md) - Training reference
- [aria_web/TESTING.md](aria_web/TESTING.md) - Testing strategies

---

## 🤝 Contributing

When modifying code, update project README.md if:

- Adding new configuration options
- Changing CLI flags or commands
- Introducing new providers/backends
- Modifying cost implications

---

## 📄 License

See individual project directories for license information.

---

## 🧪 Testing

This workspace has comprehensive test coverage across multiple automated test suites fully integrated with VS Code's native Testing UI.

### Quick Start

1. **Open Test Explorer:** Click the beaker icon (🧪) in the Activity Bar or press `Ctrl+Shift+T`
2. **Run Tests:** Click the ▶️ play button next to any test, suite, or file
3. **Debug Tests:** Set breakpoints, then right-click test → "Debug Test"
4. **View Results:** Click any test to see output, assertions, and stack traces

### Test Suites

- **Unit Tests (Fast):** 40 tests (~0.5 seconds) ✅
- **Integration Tests:** 30 tests (external services)
- **All Fast Tests:** 70 tests (~10 seconds) - fast tests (unit + integration)
- **Complete Test Suite:** 84+ tests with coverage support

### Test Orchestrator (Recommended)

```powershell
# Run all fast tests
python .\scripts\test_runner.py --all

# Run unit tests only
python .\scripts\test_runner.py --unit

# Run with coverage report
python .\scripts\test_runner.py --all --coverage

# List available test suites
python .\scripts\test_runner.py --list-suites
```

### Documentation

- **Quick Reference:** See `VSCODE_TESTING_QUICKREF.md` for keyboard shortcuts and common tasks
- **Full Guide:** See `VSCODE_TESTING_GUIDE.md` for comprehensive documentation
- **Setup Details:** See `VSCODE_TESTING_COMPLETE.md` for configuration details

### Direct Pytest Commands

```powershell
# Run all fast tests
python -m pytest -m "not slow and not azure" tests/

# Run with coverage
python -m pytest tests/ --cov=scripts --cov=shared --cov-report=html

# Run specific test file
python -m pytest tests/test_autotrain_unit.py -v
```

---

## 🔍 Quick Navigation

| Component | Path | Purpose |
|-----------|------|---------|
| **Aria Web** | `aria_web/` | 🎭 Main character controller |
| **Aria Character** | `chat-web/aria.html` | ✨ Animated avatar demo |
| **Chat with Aria** | `talk-to-ai/` | 💬 CLI chat interface |
| **Aria Training** | `datasets/chat/aria_*` | 📊 Training datasets |
| **Aria Docs** | `docs/aria/` | 📖 Documentation |
| **Quantum ML** | `quantum-ai/` | ⚛️ Experimental quantum features |
| **Fine-tuning** | `AI/` | 🧠 LoRA model training |

---

**Last Updated:** November 29, 2025

## 🚀 CI/CD Pipeline

Automated continuous integration with **5/10 steps passing**:

### Critical Steps (All Passing ✅)

- ✅ Orchestrator Validations (autotrain, quantum_autorun, evaluation_autorun)
- ✅ Unit Tests (40/40 passing in 0.5s)
- ✅ Deployment Artifact Preparation

### Run CI Pipeline

```powershell
# Full CI pipeline
python .\scripts\ci_orchestrator.py --ci-pipeline

# Validate all orchestrators
python .\scripts\ci_orchestrator.py --validate-all

# Individual validations
python .\scripts\autotrain.py --dry-run
python .\scripts\quantum_autorun.py --dry-run
python .\scripts\evaluation_autorun.py --dry-run
```

**CI Results:** See `data_out/ci_orchestrator/ci_results.json` for detailed step-by-step results.

---

## TinyLlama Ultrafast LoRA Quick Start 🚀

The workspace now includes an ultrafast LoRA config for **TinyLlama-1.1B-Chat**, enabling rapid iteration (≈10–15s per synthetic run on CPU).

### Quick Commands (PowerShell)

```powershell
# Generate synthetic data + ultrafast TinyLlama training (evaluation & ranking)
python .\scripts\automated_training_pipeline.py --models tinyllama --quick

# Larger synthetic set (300 samples) ranked by diversity alias (distinct_diversity)
python .\scripts\automated_training_pipeline.py --models tinyllama --samples 300 --ranking-metric distinct_diversity

# Data generation only (no training) – inspect dataset quality
python .\scripts\automated_training_pipeline.py --models tinyllama --quick --generate-only

# Direct auto data + single TinyLlama run (bypass wrapper)
python .\scripts\auto_data_train.py --model tinyllama --quick

# Emit Azure ML job spec (no submission)
python .\scripts\automated_training_pipeline.py --models tinyllama --quick --azure-ml-spec --generate-only
```

### Ranking Metrics Cheat Sheet

| Metric | Meaning | Direction | Notes |
|--------|---------|-----------|-------|
| perplexity_improvement | Relative reduction (pre vs post) | Higher better | Default |
| post_perplexity | Final perplexity | Lower better | Stored negative internally for sorting |
| diversity_avg | Avg of Distinct-1 & Distinct-2 | Higher better | Requires sample generation |
| distinct_diversity | Alias of diversity_avg | Higher better | Use interchangeably |
| combined_improvement | 70% perplexity_improvement + 30% diversity_avg | Higher better | Balanced quality + diversity |

Use `--ranking-metric distinct_diversity` when you want variety-focused exploration; fallback behavior automatically reverts to post perplexity if a metric is unavailable.

### Inspect Status History

All parallel LoRA runs append to `data_out/parallel_training/status.json` with a `runs[]` array and optional `job_ranking[]`. TinyLlama entries appear with names like `tinyllama_ultra_<timestamp>`.

### Azure ML Validation & Optional Submission

After emitting a spec (`--azure-ml-spec`), validate locally:

```powershell
python .\scripts\azureml_ci_validate.py            # Validate latest job_*.yaml
python .\scripts\azureml_ci_validate.py --submit   # Validate + submit
```

Graceful skip occurs automatically if the Azure CLI is not installed.

### Cleanup Behavior

Passing `--cleanup` to training wrappers prunes `checkpoint*` artifacts while preserving `lora_adapter/`, `tokenizer/`, and `metrics.jsonl`. The status history will record `"cleanup": "completed"` when successful.

---

## LoRA Provider Usage for Aria

Train and use fine-tuned Aria models using LoRA adapters:

### CLI Example

```powershell
# Chat with a trained Aria adapter
python ./talk-to-ai/src/chat_cli.py --provider lora --model data_out/aria_models/aria_direct

# Or use the default adapter location
python ./talk-to-ai/src/chat_cli.py --provider lora --model data_out/lora_training/lora_adapter
```

### Web App

- Select "LoRA" in the provider dropdown.
- Enter the adapter path (e.g., `data_out/aria_models/aria_direct`) if prompted.
- The backend will load your trained Aria model for chat.

**Requirements:**

- `peft`, `transformers`, and `torch` must be installed in your environment.
- The adapter directory must contain `adapter_config.json` and `adapter_model.safetensors`.

**Troubleshooting:**

- If you see errors about missing `peft`, run:

```powershell
pip install peft transformers torch
```

- If the model fails to load, check that your adapter path is correct and contains the required files.

---
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
# Aria — Interactive AI Character Platform

<div align="center">

[![CI Pipeline](https://github.com/Bryan-Roe/Aria/actions/workflows/ci-pipeline.yml/badge.svg)](https://github.com/Bryan-Roe/Aria/actions/workflows/ci-pipeline.yml)
=======
# Aria - Interactive AI Character Platform

<div align="center">

✨ **Meet Aria** ✨

*An intelligent, animated AI character with movement, gestures, and natural language interaction*

[![CI Pipeline](https://github.com/Bryan-Roe/Aria/actions/workflows/ci-pipeline.yml/badge.svg)](https://github.com/Bryan-Roe/Aria/actions/workflows/ci-pipeline.yml)
[![PR Checks](https://github.com/Bryan-Roe/Aria/actions/workflows/pr-checks.yml/badge.svg)](https://github.com/Bryan-Roe/Aria/actions/workflows/pr-checks.yml)
[![Auto Validation](https://github.com/Bryan-Roe/Aria/actions/workflows/auto-validation.yml/badge.svg)](https://github.com/Bryan-Roe/Aria/actions/workflows/auto-validation.yml)
>>>>>>> origin/sync/github-sync-20260307-085533
[![Code Quality](https://github.com/Bryan-Roe/Aria/actions/workflows/code-quality.yml/badge.svg)](https://github.com/Bryan-Roe/Aria/actions/workflows/code-quality.yml)
[![CodeQL](https://github.com/Bryan-Roe/Aria/actions/workflows/codeql.yml/badge.svg)](https://github.com/Bryan-Roe/Aria/actions/workflows/codeql.yml)
[![E2E Tests](https://github.com/Bryan-Roe/Aria/actions/workflows/e2e-tests.yml/badge.svg)](https://github.com/Bryan-Roe/Aria/actions/workflows/e2e-tests.yml)

<<<<<<< main
**An intelligent, animated AI character with movement, gestures, and natural language interaction.**

[Live Demo](https://bryan-roe.github.io/Aria) · [Aria Web UI](aria_web/) · [Quick Start](#-quick-start)

=======
>>>>>>> origin/sync/github-sync-20260307-085533
</div>

---

<<<<<<< main
## What is Aria?

Aria is a full-stack interactive AI character platform. She lives on a virtual 3D stage, responds to natural language commands ("wave", "pick up the ball", "dance"), speaks via text-to-speech, and is powered by a multi-provider AI backend that supports Azure OpenAI, OpenAI, LM Studio, local models, and LoRA fine-tuned adapters.

The project is organized around four core areas:

| Area | Folder | Description |
|------|--------|-------------|
| **Character interface** | `aria_web/` | Animated 3D character stage with object interaction |
| **Chat / AI backends** | `talk-to-ai/` | Multi-provider CLI and streaming chat API |
| **Quantum ML** | `quantum-ai/` | Hybrid quantum-classical training (experimental) |
| **Model fine-tuning** | `AI/` | LoRA fine-tuning for Aria's language understanding |

Supporting infrastructure lives in `shared/`, `scripts/`, `config/`, and `function_app.py` (Azure Functions API layer).

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Git

### 1 — Run the Aria character web UI

```bash
cd aria_web
pip install -r ../requirements.txt   # only needed once
python server.py
# Open http://localhost:8080
```

Type commands in the chat box: `move left`, `wave`, `jump`, `pick up the ball`, `dance`.

### 2 — Chat via CLI (no UI required)

```bash
# Local mode — no API keys required
python talk-to-ai/src/chat_cli.py --provider local --once "Hello Aria!"

# OpenAI
OPENAI_API_KEY=sk-... python talk-to-ai/src/chat_cli.py --provider openai

# Azure OpenAI (requires all four env vars — see Configuration below)
python talk-to-ai/src/chat_cli.py --provider azure
```

Interactive session commands: `/new`, `/save`, `/exit`.

### 3 — Start the Azure Functions API host

```bash
func host start
# Endpoints: /api/chat, /api/chat-web, /api/tts, /api/quantum/*, /api/ai/status
curl http://localhost:7071/api/ai/status | python -m json.tool   # health check
```

---

## 🏗️ Project Structure

```
aria_web/           Animated character stage (HTML/CSS/JS + Python API server)
chat-web/           Browser-based streaming chat UI
talk-to-ai/         Multi-provider chat CLI
quantum-ai/         Quantum ML platform (circuits, MCP server, Azure Quantum)
llm-maker/          Autonomous tool-creation system
cooking-ai/         Cooking-focused AI assistant
AI/                 LoRA fine-tuning workspace (Phi / TinyLlama)
shared/             Shared Python modules (providers, DB, telemetry, Cosmos)
scripts/            Orchestration, training, evaluation, and utility scripts
config/             YAML configs for orchestrators
datasets/           Read-only training datasets
data_out/           All generated outputs (git-ignored)
function_app.py     Azure Functions entry point (all /api/* endpoints)
```

---

## 🎭 Aria Character

The Aria character runs at `http://localhost:8080` (or the [GitHub Pages demo](https://bryan-roe.github.io/Aria)).

**Natural language commands (examples):**

| Command | Effect |
|---------|--------|
| `move left` / `move right` | Walk to stage edge |
| `wave` / `dance` / `jump` | Trigger gesture |
| `pick up the ball` | Pick up a nearby object |
| `throw the ball` | Throw held object with physics |
| `say hello` | Aria speaks the text aloud via TTS |

The auto-execute system parses complex multi-step requests ("walk to the table and pick up the apple") into a structured sequence of 8 core actions: `move`, `say`, `pickup`, `drop`, `throw`, `gesture`, `look`, `wait`.

**Aria web server API (port 8080):**

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/aria/state` | Current stage state (position, objects, expressions) |
| `POST` | `/api/aria/command` | Process a natural language command |
| `POST` | `/api/aria/execute` | Auto-execute an action sequence |
| `POST` | `/api/aria/object` | Add / update / remove an object |
| `POST` | `/api/aria/world` | Generate a themed world via LLM |

---

## 💬 Chat Providers

Provider auto-detection order:

```
LM Studio → Azure OpenAI → OpenAI → Local (zero-dependency echo)
```

Pass `--provider` to override: `local`, `openai`, `azure`, `lora`, `quantum`, `agi`.

**Azure OpenAI** — all four variables required:

```
AZURE_OPENAI_API_KEY
AZURE_OPENAI_ENDPOINT
AZURE_OPENAI_DEPLOYMENT
AZURE_OPENAI_API_VERSION
```

**LoRA adapter** — adapter directory must contain:

```
adapter_config.json
adapter_model.safetensors
```

```bash
python talk-to-ai/src/chat_cli.py --provider lora --model data_out/lora_training/lora_adapter
```

All providers implement `BaseChatProvider.complete(messages, stream)`. Add a new provider by subclassing `BaseChatProvider` in `shared/chat_providers.py`.

---

## ⚛️ Quantum ML (Experimental)

Local Qiskit Aer simulation is free and unlimited. Azure simulator backends are also free. Real QPU hardware is billed per gate-shot — always simulate first.

**Workflow:** Test locally → Validate on Azure simulator → Run on QPU (set `azure_confirm_cost: true` in YAML first)

```bash
# Validate config without running anything
python scripts/quantum_autorun.py --dry-run

# Interactive training dashboard
cd quantum-ai && ./start_dashboard.sh   # http://localhost:5000

# Start the MCP server (8 quantum tools)
python quantum-ai/quantum_mcp_server.py
```

**MCP tools:** `create_quantum_circuit`, `simulate_quantum_circuit`, `get_quantum_circuit_properties`, `connect_azure_quantum`, `list_quantum_backends`, `submit_quantum_job`, `estimate_quantum_cost`, `train_quantum_classifier`.

---

## 🧠 LoRA Fine-Tuning

Train a small model on Aria-specific datasets using LoRA adapters.

```bash
# Quick training run (TinyLlama, CPU-friendly, ~10–15 s)
python scripts/automated_training_pipeline.py --models tinyllama --quick

# Full train → evaluate → auto-promote best checkpoint
python scripts/train_and_promote.py --quick --auto-promote

# Validate configs without running
python scripts/autotrain.py --dry-run
```

Training datasets are in `datasets/chat/aria_movement/`, `aria_expanded/`, and `aria_simple/` (read-only).
Outputs are written to `data_out/lora_training/`.

---

## 🤖 Autonomous Training

A background orchestrator continuously discovers datasets, trains, and evaluates models on a 30-minute cycle.

```bash
# Start the autonomous loop (runs indefinitely)
nohup python scripts/autonomous_training_orchestrator.py > data_out/autonomous_training.log 2>&1 &

# Check live status
cat data_out/autonomous_training_status.json | python -m json.tool
tail -f data_out/autonomous_training.log
```

---

## 🔧 LLM Tool Maker

An autonomous system where an LLM generates, validates, and sandboxes Python tools at runtime.

```bash
cd llm-maker
python examples/quick_start.py        # create a tool from a description
python llm_maker_mcp_server.py        # expose tools via MCP
```

Security: no dangerous imports, no filesystem or network access, no `eval`/`exec`, sandboxed execution with resource limits.

---

## 🧪 Testing

```bash
# Fast unit tests (~0.5 s, no external services)
python scripts/test_runner.py --unit

# All fast tests (unit + integration, ~10 s)
python scripts/test_runner.py --all

# With coverage report
python scripts/test_runner.py --all --coverage

# Direct pytest
pytest -m "not slow and not azure" tests/
```

VS Code users: open the Test Explorer (🧪 beaker icon) for interactive test running and debugging.

---

## 🌐 Live Demo

**[https://bryan-roe.github.io/Aria](https://bryan-roe.github.io/Aria)**

The demo runs in mock mode with simulated API responses — no API keys needed. For full AI capabilities, run the project locally.

---

## 🔒 Configuration & Secrets

Copy the example files to get started:

```bash
cp .env.example .env
cp local.settings.json.example local.settings.json
# Fill in API keys as needed
```

Never commit secrets. All keys belong in environment variables or `local.settings.json` (development only).

**Optional services** (feature-flagged — safe to leave unset):

| Service | How to enable |
|---------|---------------|
| SQL persistence | `QAI_DB_CONN` env var (SQLite, PostgreSQL, or Azure SQL) |
| Cosmos DB | `QAI_ENABLE_COSMOS=true` + `COSMOS_ENDPOINT`, `COSMOS_KEY`, `COSMOS_DATABASE`, `COSMOS_CONTAINER` |
| Application Insights | `APPLICATIONINSIGHTS_CONNECTION_STRING` |
| Azure Speech TTS | `AZURE_SPEECH_KEY` + `AZURE_SPEECH_REGION` |
| Local TTS fallback | `QAI_ENABLE_LOCAL_TTS=true` (uses pyttsx3 or gTTS when Azure credentials are absent) |
=======
## 🎭 About Aria

Aria is an interactive AI character that combines:

- **3D Animated Avatar** - CSS-based character with smooth animations, eye tracking, and expressive gestures
- **Natural Language Movement** - Tell Aria to "move left", "wave", "dance", or "jump" using plain English
- **Multi-Provider AI Backend** - Powered by Azure OpenAI, OpenAI, or local models with LoRA fine-tuning
- **Real-time Object Interaction** - Add, pickup, drop, and throw objects on a virtual stage
- **Quantum ML Integration** - Experimental quantum-classical hybrid training
- **⚛️ Quantum-Enhanced Passive LLM Training** - Background training with quantum computing optimization
  (can also fine-tune a real HuggingFace model using `--base-model` when `transformers` is installed)
- **🆕 LLM Tool Maker** - Autonomous tool creation system where LLMs create, validate, and execute Python tools
- **💰 Revenue Stream System** - Complete subscription and monetization platform achieving $2,235/month MRR

## 💰 Revenue Stream

Aria includes a comprehensive monetization system with **$2,235/month MRR** (111.8% of $2,000 target):

### Quick Access
- **[View Pricing](pricing.html)** - Three-tier subscription model (Free, Pro $49/mo, Enterprise $199/mo)
- **[Try Aria Character](web/aria_web/index.html)** - Interactive character interface with integrated navigation
- **[Admin Dashboard](admin_dashboard.html)** - Revenue analytics and subscriber management
- **[Monetization Hub](monetization-index.html)** - Complete overview of all monetization features

### Features
- ✅ **3-Tier Subscription System** - Free, Pro ($49/mo), Enterprise ($199/mo)
- ✅ **Usage Tracking** - 5 resource types monitored (chat, quantum, training, API, websites)
- ✅ **REST API Endpoints** - 5 subscription management APIs
- ✅ **Beautiful UI Pages** - 7 professional pages covering entire user journey
- ✅ **Stripe-Ready** - Payment integration structure in place
- ✅ **Revenue Analytics** - Real-time MRR/ARR tracking

See [MONETIZATION_GUIDE.md](MONETIZATION_GUIDE.md) for complete documentation.

## 🌐 Live Demo (GitHub Pages)

**Try Aria online without installing anything:**

👉 **[https://bryan-roe.github.io/Aria](https://bryan-roe.github.io/Aria)** 👈

The live demo includes:
- ✨ **Aria Character** - Interactive 3D character with animations
- 💬 **AI Chat Interface** - Chat with Aria (demo mode with simulated responses)
- 📊 **Training Dashboard** - View training metrics and progress
- ⚛️ **Quantum ML** - Quantum computing interface

**Note:** The GitHub Pages demo runs in **demo mode** with mock API responses. For full AI capabilities, quantum computing, and real-time training, run the project locally following the Quick Start guide below.

## 🚀 Quick Start

### 📊 Automation Status

The badges at the top of this README map to these automated checks:

- **CI Pipeline** ([`.github/workflows/ci-pipeline.yml`](.github/workflows/ci-pipeline.yml)): Core validation, test execution, and scheduled training/deploy workflow.
- **PR Checks** ([`.github/workflows/pr-checks.yml`](.github/workflows/pr-checks.yml)): Pull request guardrails (workflow YAML validation, repo health validation, size checks, and auto-labeling).
- **Auto Validation** ([`.github/workflows/auto-validation.yml`](.github/workflows/auto-validation.yml)): Dry-run validation of orchestrator and automation configuration.
- **Code Quality** ([`.github/workflows/code-quality.yml`](.github/workflows/code-quality.yml)): Static quality checks and lint-style enforcement.
- **CodeQL** ([`.github/workflows/codeql.yml`](.github/workflows/codeql.yml)): Security/code scanning for vulnerabilities and risky patterns.
- **E2E Tests** ([`.github/workflows/e2e-tests.yml`](.github/workflows/e2e-tests.yml)): Browser-level end-to-end coverage for Aria web flows.

### 🤖 **NEW: Complete Repository Automation**

One command to automate the entire repository:

```bash
# Start everything (all components)
./scripts/start_repo_automation.sh full

# Or select specific components
./scripts/start_repo_automation.sh aria           # Aria character only
./scripts/start_repo_automation.sh training       # Training pipeline
./scripts/start_repo_automation.sh                # Interactive menu

# Check status
./scripts/start_repo_automation.sh status

# Stop all
./scripts/start_repo_automation.sh stop
```

**Automated Components:**

- ✅ **Aria Character** - Web server + continuous training
- ✅ **LoRA Training** - Automated fine-tuning pipelines
- ✅ **Quantum ML** - Quantum computing workflows
- ✅ **Evaluation** - Model evaluation system
- ✅ **Datasets** - Auto-discovery & downloads
- ✅ **Monitoring** - Health checks & alerts
- ✅ **Backups** - Daily automated backups

See [REPO_AUTOMATION_GUIDE.md](REPO_AUTOMATION_GUIDE.md) for full documentation.

### 🔧 QAI Workspace Verification

For developers working on the **Quantum AI (QAI) workspace**, a helper script exercises
all of the critical components (chat providers, quantum classifier, quantum
provider, Azure Functions imports) and will report success/failure. It is useful
for sanity-checking a fresh checkout or after installing new dependencies.

```bash
# run the standalone verifier
python tests/test-qai.py

# or run via the test runner (also installs quantum dependencies automatically)
python scripts/test_runner.py --suite quantum
```

The verifier will auto-install missing modules such as `torch` and
`pennylane` during pytest collection thanks to the updated `tests/conftest.py`.

---

### 🎭 Aria Character Only

If you only want Aria automation:

```bash
# Interactive menu
./scripts/start_aria.sh

# Direct start
./scripts/start_aria.sh full

# Background mode
./scripts/start_aria.sh full --background

# Check status
./scripts/start_aria.sh status
```

See [ARIA_AUTOMATION_GUIDE.md](ARIA_AUTOMATION_GUIDE.md) for details

📖 **Full Guide:** [ARIA_AUTOMATION_GUIDE.md](ARIA_AUTOMATION_GUIDE.md)  
📋 **Quick Ref:** [ARIA_QUICKREF.txt](ARIA_QUICKREF.txt)

---

### Chat with Aria (Web Interface)

```bash
# Start the Aria web server
cd web/aria_web
python server.py

# Open http://localhost:8000 in your browser
```

### Chat with Aria (CLI)

```bash
cd tools/talk-to-ai

# create and use a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

pip install -r requirements.txt
python src/chat_cli.py --provider local --once "Hello Aria!"
```

### Aria Character Demo

```bash
# Open the animated character page
# Navigate to: web/chat-web/aria.html
```

## 📁 Project Structure

This workspace is organized around Aria with supporting AI/ML infrastructure:

### 🎭 **web/aria_web/** - Aria Character Interface

The main Aria character controller with 3D animations and object interactions.

**Features:**

- 🎨 **3D Character Control** - Move Aria around the stage using waypoints
- 📦 **Object Management** - Add, pickup, drop, and throw objects
- 🔄 **Server Sync** - All client actions synchronized to Python backend
- 💬 **Chat Interface** - Send natural language commands
- 🌍 **World Generation** - LLM-powered themed environment creation

**Quick Start:**

```bash
cd web/aria_web
python server.py
# Open http://localhost:8000
```

**API Endpoints:**

- `GET /api/aria/state` - Get current stage state
- `POST /api/aria/command` - Send movement commands
- `POST /api/aria/object` - Manage objects
- `POST /api/aria/world` - Generate themed worlds

**Documentation:** [web/aria_web/README.md](web/aria_web/README.md)

---

### 💬 **tools/talk-to-ai/** - Aria Chat CLI

Multi-provider chat CLI for interacting with Aria using natural language.

**Features:**

- 🤖 Provider auto-detection (Azure OpenAI → OpenAI → Local)
- 🎯 Aria movement command generation
- 💾 Conversation persistence (JSONL format)
- 🔌 Zero-dependency local mode for offline development
- ⚡ Streaming responses

**Quick Start:**

```powershell
cd tools/talk-to-ai
pip install -r requirements.txt

# Local mode (no API keys required)
python .\src\chat_cli.py --provider local

# With OpenAI
$env:OPENAI_API_KEY = "sk-..."
python .\src\chat_cli.py --provider openai

# With Azure OpenAI
$env:AZURE_OPENAI_API_KEY = "..."
$env:AZURE_OPENAI_ENDPOINT = "https://....openai.azure.com/"
$env:AZURE_OPENAI_DEPLOYMENT = "gpt-4o-mini"
python .\src\chat_cli.py --provider azure
```

**Interactive Commands:** `/new`, `/save`, `/exit`

**Aria Movement Commands:** Try saying "Move Aria left", "Wave", "Dance", or "Jump"!

**Documentation:** See [tools/talk-to-ai/README.md](tools/talk-to-ai/README.md)

---

## 🛠️ Local dev adapter & telemetry (OTLP)

- Local development helper: `local_dev_adapter.py` is a tiny Flask-based adapter that
  lets you call a subset of the Azure Functions handlers (notably `/api/ai/status`) locally
  without running the full Functions host. It also includes a lightweight `azure.functions`
  shim so the `function_app` module can be imported in minimal containers or CI environments.

  Quick start:

  ```bash
  # Start the local adapter (serves /api/ai/status on port 7071)
  python local_dev_adapter.py
  # Open http://localhost:7071/api/ai/status
  ```

- OTLP exporter warnings during tests: you may see connection refused errors from
  OpenTelemetry's OTLP exporter (typically trying to reach localhost:4318). These are
  benign if you don't run an OTLP collector locally. To quiet them during tests you can
  either run a local collector (on port 4318) or disable OTLP exporting for the test run:

  ```bash
  # Prefer disabling tracing exporters for fast, local test runs
  export OTEL_TRACES_EXPORTER=none
  # or clear the OTLP endpoint
  export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=""
  pytest -q
  ```

  Note: `OTEL_TRACES_EXPORTER=none` is supported by many OpenTelemetry SDKs to disable
  remote exporting; alternatively clearing `APPLICATIONINSIGHTS_CONNECTION_STRING` will
  prevent the repo's Azure Monitor instrumentation from initializing.

  The local dev adapter is useful for quick health checks and debugging function handlers
  without the overhead of the Functions Core Tools host.

### 🧠 **AI/microsoft_phi-silica-3.6_v1/** - Aria Model Fine-Tuning

Fine-tuning workspace for training Aria's language understanding using LoRA and soft prompt techniques.

**Features:**

- 🎯 LoRA fine-tuning for Aria movement commands
- 📊 Aria-specific training datasets in `datasets/chat/aria_*`
- ☁️ Azure ML deployment infrastructure
- 🔧 Azure AI Toolkit integration

**Aria Training Datasets:**

- `datasets/chat/aria_movement/` - Movement command training data
- `datasets/chat/aria_expanded/` - Extended Aria interactions
- `datasets/chat/aria_simple/` - Basic Aria commands
- `datasets/chat/github_actions/` - GitHub Actions & CI/CD workflows training data

**Quick Training:**

```bash
# Quick Aria movement training
python scripts/train_aria_direct.py

# Validate Aria dataset
python scripts/test_aria_dataset.py --validate-only
```

**Documentation:** See [docs/aria/](docs/aria/) for comprehensive Aria training guides

---

### ⚛️ **quantum/** - Quantum ML Platform (Experimental)

Hybrid quantum-classical ML for advanced Aria capabilities.

**Features:**

- 🎨 Interactive Web Dashboard for training visualization
- ⚛️ Quantum circuit creation and simulation
- ☁️ Azure Quantum integration (IonQ, Quantinuum)
- 🤖 MCP server with 8 quantum tools
- **⚡ NEW: Quantum-Enhanced Passive LLM Training**

**Quick Start:**

```bash
cd quantum-ai
./start_dashboard.sh
# Open http://localhost:5000
```

**Quantum LLM Training:**

```bash
# Active training
python scripts/quantum_llm_trainer.py --dataset datasets/chat/aria_chat --quantum-backend local

# Passive mode (continuous background training)
python scripts/quantum_llm_trainer.py --passive --interval 3600

# Integrated with autonomous orchestrator
python scripts/autonomous_training_orchestrator.py
```

**Documentation:** 
- [quantum/README.md](quantum/README.md)
- **[QUANTUM_LLM_TRAINING.md](QUANTUM_LLM_TRAINING.md)** ⚡ NEW

---

### 🔧 **tools/llm-maker/** - LLM Tool Maker (NEW!)

Autonomous tool creation system where LLMs can create, validate, and execute Python tools in a sandboxed environment.

**Features:**

- 🤖 AI-powered tool generation from natural language descriptions
- 🔒 Multi-layer security validation (code analysis, sandboxing, resource limits)
- 📦 Tool registry for storage and management
- ⚡ Safe execution environment with timeout and memory limits
- 🔌 MCP server integration for seamless tool discovery and execution

**Quick Start:**

```bash
cd llm-maker

# Create a tool
python examples/quick_start.py

# Or use the MCP server
python llm_maker_mcp_server.py
```

**Example: Creating a Tool**

```python
from llm_maker import ToolMaker, ToolRegistry

maker = ToolMaker()
registry = ToolRegistry()

# Create a Fibonacci calculator
tool = maker.create_tool(
    name="calculate_fibonacci",
    description="Calculate the nth Fibonacci number",
    parameters={"n": "int"},
    return_type="int"
)

# Register and use it
tool_id = registry.register(tool)
```

**Security Features:**

- No dangerous imports (os, sys, subprocess, etc.)
- No file system or network access
- No code execution (eval, exec, compile)
- Sandboxed execution with resource limits
- Static code analysis before execution

**Documentation:** [tools/llm-maker/README.md](tools/llm-maker/README.md)

---

## 🔧 Development Environment

### Prerequisites

- **Python:** 3.9+
- **PowerShell:** Primary shell for all commands
- **Azure CLI:** For Azure Quantum and Azure ML deployments
- **Git:** Version control

### Common Commands

#### Environment Setup

```powershell
# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Install development tooling (lint/format/type/pre-commit)
pip install -r dev-requirements.txt
```

#### Quality & Validation

```powershell
# Fast repo health validation
python .\scripts\fast_validate.py --fail-on-errors

# Unit tests
python .\scripts\test_runner.py --unit

# Run local pre-commit hooks
pre-commit run --all-files
```

#### VS Code Tasks

This repo includes preconfigured tasks in `.vscode/tasks.json` for common flows:

- `func: host start`
- `validate: fast`
- `test: unit`
- `Run: AutoTrain (dry-run)` / `Run: AutoTrain (all)`
- `Run: Quantum AutoRun (dry-run)` / `Run: Quantum AutoRun (all)`
- `Run: Evaluation AutoRun (dry-run)`

#### Azure Login

```powershell
az login
az account set --subscription "<subscription-id>"
```

### Local Development Tools

**Azurite (Azure Storage Emulator):**
The workspace root contains Azurite database files for local Azure Storage development:

- `__azurite_db_*.json`
- `__blobstorage__/`
- `__queuestorage__/`

These are used for local testing of Azure Functions and Storage features.

### Remote TTS (chat-web)

To enable server-side TTS (used by the web UI at /api/chat-web -> /api/tts) add your Azure Speech credentials to your local env or Functions settings.

- Add AZURE_SPEECH_KEY and AZURE_SPEECH_REGION to your environment or into `local.settings.json` when running the Functions host locally.
- See `local.settings.json.example` and `.env.example` in the repo root for templates you can copy and fill in.

### Optional local TTS fallback (no Azure keys)

If you prefer not to configure Azure Speech for local development, the Functions app can optionally synthesize audio locally using pyttsx3 (offline) or gTTS (Google TTS) when Azure credentials are not provided.

To enable local fallback:

1. Set QAI_ENABLE_LOCAL_TTS=true in your `local.settings.json` or `.env` (the example files include this key).
2. Install the extra packages into your Functions environment:

```powershell
# From repo root
pip install -r requirements.txt
```

3. Restart the Functions host. When you call `/api/tts` the server will try Azure first, then pyttsx3, then gTTS.

Note: pyttsx3 is generally best on Windows (uses SAPI), gTTS uses Google Translate's TTS API and will produce MP3 output if used. The `/api/tts` endpoint returns audio_base64 and the format field (mp3 or wav). The client will use the returned format to play the audio.

---

## 🚀 Deployment

### Quantum AI Deployment

  --parameters quantum_workspace.parameters.json

See `quantum/azure/DEPLOYMENT.md` for complete deployment guide.

---

- **Microsoft Simulators:** Free
- **IonQ:** ~$0.00003 per gate-shot
- **Quantinuum:** ~$0.00015 per circuit execution

**Best Practice:** Always test on `qiskit_aer` simulator locally before submitting to paid hardware.

### Azure OpenAI

- Costs vary by model and token usage
- Use local provider for development/testing

---

### Quantum AI MCP Server

The `quantum/quantum_mcp_server.py` exposes 8 quantum computing tools via Model Context Protocol:

**Circuit Tools:**

- `create_quantum_circuit` - Build circuits (bell, ghz, entanglement, random, custom)
- `simulate_quantum_circuit` - Local simulation (Qiskit Aer, up to 100k shots)
- `get_quantum_circuit_properties` - Analyze depth, gates, topology

**Azure Quantum Tools:**

- `connect_azure_quantum` - Authenticate to workspace
- `list_quantum_backends` - Enumerate hardware/simulators
- `submit_quantum_job` - Execute on real quantum computers
- `estimate_quantum_cost` - Calculate costs before running

**ML Tools:**

- `train_quantum_classifier` - Train hybrid models (iris, wine, breast_cancer, synthetic datasets)

**VS Code Integration:**
Add to `.vscode/mcp.json` (if supported by your VS Code version):

```json
{
  "quantum-ai": {
    "type": "stdio",
    "command": "python",
    "args": ["c:\\Users\\Bryan\\OneDrive\\AI\\quantum-ai\\quantum_mcp_server.py"]
  }
}
```

### Chat Provider Abstraction

All chat providers implement `BaseChatProvider.complete(messages, stream)`:

```python
messages = [{"role": "user", "content": "Hello"}]
response = provider.complete(messages, stream=True)
```

Add new providers by subclassing `BaseChatProvider`.

---

## 🧪 Quick Testing

### Aria Web Interface

```powershell
cd web/aria_web
python server.py
# Open http://localhost:8000
```

### Aria Chat CLI

```powershell
cd tools/talk-to-ai
python .\src\chat_cli.py --provider local --once "Move Aria left"
```

### Aria Character Animation

```powershell
# Open web/chat-web/aria.html in your browser
# Click on Aria to see walking animation
# Press 'W' to wave, 'R' to raise arms
```

---

## 📝 File Organization

```
├── web/aria_web/               # 🎭 Main Aria character controller
│   ├── server.py           # Python backend API
│   ├── aria_controller.js  # Frontend character logic
│   └── index.html          # Interactive stage UI
├── web/chat-web/               # 💬 Web chat interface
│   ├── aria.html           # Animated Aria character page
│   └── index.html          # Chat with Aria web UI
├── datasets/chat/          # 📊 Aria training datasets
│   ├── aria_movement/      # Movement command training
│   ├── aria_expanded/      # Extended interactions
│   └── aria_simple/        # Basic commands
├── docs/aria/              # 📖 Aria documentation
│   ├── ARIA_MOVEMENT_COMPLETE.md
│   ├── ARIA_MOVEMENT_TRAINING.md
│   └── ARIA_VISUAL_SYSTEM.md
├── scripts/                # 🔧 Aria training & utility scripts
│   ├── train_aria_direct.py
│   ├── automate_aria_movement.py
│   └── test_aria_dataset.py
├── tools/talk-to-ai/             # Chat CLI for Aria
├── quantum/             # Quantum ML platform
├── tools/llm-maker/              # 🔧 LLM Tool Maker (autonomous tool creation)
├── AI/                     # Model fine-tuning workspace
├── config/                 # Configuration files
├── shared/                 # Shared Python modules
├── tests/                  # Test suites
└── data_out/               # Generated outputs (git-ignored)
```
>>>>>>> origin/sync/github-sync-20260307-085533

---

## 📚 Documentation

<<<<<<< main
| Document | Purpose |
|----------|---------|
| [aria_web/README.md](aria_web/README.md) | Character stage API reference |
| [quantum-ai/README.md](quantum-ai/README.md) | Quantum ML platform guide |
| [talk-to-ai/README.md](talk-to-ai/README.md) | Chat CLI reference |
| [llm-maker/README.md](llm-maker/README.md) | Tool maker guide |
| [docs/aria/](docs/aria/) | Aria movement & training documentation |
| [MONETIZATION_GUIDE.md](MONETIZATION_GUIDE.md) | Subscription and revenue system |
| [REPO_AUTOMATION_GUIDE.md](REPO_AUTOMATION_GUIDE.md) | Full repository automation reference |
| [QUANTUM_LLM_TRAINING.md](QUANTUM_LLM_TRAINING.md) | Quantum-LLM concurrent training |
=======
### Aria Documentation

- **[docs/aria/](docs/aria/)** - Complete Aria system documentation
  - [ARIA_MOVEMENT_COMPLETE.md](docs/aria/ARIA_MOVEMENT_COMPLETE.md) - Implementation guide
  - [ARIA_MOVEMENT_TRAINING.md](docs/aria/ARIA_MOVEMENT_TRAINING.md) - Training reference
  - [ARIA_VISUAL_SYSTEM.md](docs/aria/ARIA_VISUAL_SYSTEM.md) - Visual system design
- **[web/aria_web/README.md](web/aria_web/README.md)** - Web interface and API docs
- **[web/aria_web/TESTING.md](web/aria_web/TESTING.md)** - Testing guide

### Supporting Documentation

- **[docs/README.md](docs/README.md)** - Documentation index
- **[docs/training/](docs/training/)** - LoRA and training guides
- **[docs/quantum/](docs/quantum/)** - Quantum computing documentation
- **[docs/database/](docs/database/)** - SQL and database setup

---

## ⚠️ Common Issues

### Aria Not Moving

If Aria commands aren't working:

1. Ensure the web/aria_web server is running: `python web/aria_web/server.py`
2. Check browser console for JavaScript errors
3. Verify API responses: `curl http://localhost:8000/api/aria/state`

### Azure Quantum Authentication

If you see "Failed to connect to Azure Quantum":

1. Run `az login`
2. Verify `quantum_config.yaml` has correct subscription_id and resource_group
3. Check workspace exists: `az quantum workspace show -g rg-quantum-ai -n quantum-ai-workspace`

### Chat Streaming Issues

Verify SDK version: `pip list | findstr openai` should show `openai>=1.37.0`

---

## 🔧 Recent Enhancements

**November 2025 Updates:**

- **🎭 Aria Character System**: Complete 3D animated character with movement, gestures, and object interaction
- **📊 Aria Training Pipeline**: Movement command datasets and training automation
- **🌍 LLM World Generation**: Dynamic themed environment creation via `/api/aria/world`
- **🎯 Movement Command Parser**: Natural language to `[aria:action:direction]` tag conversion
- **✨ Visual Enhancements**: Eye tracking, breathing animations, and character expressions

📖 **Aria Documentation:**

- [ARIA_MOVEMENT_COMPLETE.md](docs/aria/ARIA_MOVEMENT_COMPLETE.md) - Full implementation guide
- [ARIA_MOVEMENT_TRAINING.md](docs/aria/ARIA_MOVEMENT_TRAINING.md) - Training reference
- [web/aria_web/TESTING.md](web/aria_web/TESTING.md) - Testing strategies
>>>>>>> origin/sync/github-sync-20260307-085533

---

## 🤝 Contributing

<<<<<<< main
- Update `README.md` when adding configuration options, changing CLI flags, introducing new providers, or modifying cost behaviour.
- All output files go under `data_out/` (git-ignored). Never modify files under `datasets/`.
- Always run `--dry-run` on orchestrators before executing GPU or QPU workloads.
=======
When modifying code, update project README.md if:

- Adding new configuration options
- Changing CLI flags or commands
- Introducing new providers/backends
- Modifying cost implications
>>>>>>> origin/sync/github-sync-20260307-085533

---

## 📄 License

See individual project directories for license information.
<<<<<<< main
=======

---

## 🧪 Testing

This workspace has comprehensive test coverage across multiple automated test suites fully integrated with VS Code's native Testing UI.

### Quick Start

1. **Open Test Explorer:** Click the beaker icon (🧪) in the Activity Bar or press `Ctrl+Shift+T`
2. **Run Tests:** Click the ▶️ play button next to any test, suite, or file
3. **Debug Tests:** Set breakpoints, then right-click test → "Debug Test"
4. **View Results:** Click any test to see output, assertions, and stack traces

### Test Suites

- **Unit Tests (Fast):** 40 tests (~0.5 seconds) ✅
- **Integration Tests:** 30 tests (external services)
- **All Fast Tests:** 70 tests (~10 seconds) - fast tests (unit + integration)
- **Complete Test Suite:** 84+ tests with coverage support

### Test Orchestrator (Recommended)

```powershell
# One-command repo health automation (fast validate + unit tests)
bash ./scripts/auto_health.sh

# Validation only (no tests)
bash ./scripts/auto_health.sh --validate-only

# Run all fast tests
python .\scripts\test_runner.py --all

# Run unit tests only
python .\scripts\test_runner.py --unit

# Run with coverage report
python .\scripts\test_runner.py --all --coverage

# List available test suites
python .\scripts\test_runner.py --list-suites
```

### Documentation

- **Quick Reference:** See `VSCODE_TESTING_QUICKREF.md` for keyboard shortcuts and common tasks
- **Full Guide:** See `VSCODE_TESTING_GUIDE.md` for comprehensive documentation
- **Setup Details:** See `VSCODE_TESTING_COMPLETE.md` for configuration details

### Direct Pytest Commands

```powershell
# Run all fast tests
python -m pytest -m "not slow and not azure" tests/

# Run with coverage
python -m pytest tests/ --cov=scripts --cov=shared --cov-report=html

# Run specific test file
python -m pytest tests/test_autotrain_unit.py -v
```

---

## 🔍 Quick Navigation

| Component | Path | Purpose |
|-----------|------|---------|
| **Aria Web** | `web/aria_web/` | 🎭 Main character controller |
| **Aria Character** | `web/chat-web/aria.html` | ✨ Animated avatar demo |
| **Chat with Aria** | `tools/talk-to-ai/` | 💬 CLI chat interface |
| **Aria Training** | `datasets/chat/aria_*` | 📊 Training datasets |
| **Aria Docs** | `docs/aria/` | 📖 Documentation |
| **Quantum ML** | `quantum/` | ⚛️ Experimental quantum features |
| **Fine-tuning** | `AI/` | 🧠 LoRA model training |

---

**Last Updated:** November 29, 2025

## 🚀 CI/CD Pipeline

Automated continuous integration with **5/10 steps passing**:

### Critical Steps (All Passing ✅)

- ✅ Orchestrator Validations (autotrain, quantum_autorun, evaluation_autorun)
- ✅ Unit Tests (40/40 passing in 0.5s)
- ✅ Deployment Artifact Preparation

### Run CI Pipeline

```powershell
# Full CI pipeline
python .\scripts\ci_orchestrator.py --ci-pipeline

# Validate all orchestrators
python .\scripts\ci_orchestrator.py --validate-all

# Individual validations
python .\scripts\autotrain.py --dry-run
python .\scripts\quantum_autorun.py --dry-run
python .\scripts\evaluation_autorun.py --dry-run
```

**CI Results:** See `data_out/ci_orchestrator/ci_results.json` for detailed step-by-step results.

---

## TinyLlama Ultrafast LoRA Quick Start 🚀

The workspace now includes an ultrafast LoRA config for **TinyLlama-1.1B-Chat**, enabling rapid iteration (≈10–15s per synthetic run on CPU).

### Quick Commands (PowerShell)

```powershell
# Generate synthetic data + ultrafast TinyLlama training (evaluation & ranking)
python .\scripts\automated_training_pipeline.py --models tinyllama --quick

# Larger synthetic set (300 samples) ranked by diversity alias (distinct_diversity)
python .\scripts\automated_training_pipeline.py --models tinyllama --samples 300 --ranking-metric distinct_diversity

# Data generation only (no training) – inspect dataset quality
python .\scripts\automated_training_pipeline.py --models tinyllama --quick --generate-only

# Direct auto data + single TinyLlama run (bypass wrapper)
python .\scripts\auto_data_train.py --model tinyllama --quick

# Emit Azure ML job spec (no submission)
python .\scripts\automated_training_pipeline.py --models tinyllama --quick --azure-ml-spec --generate-only
```

### Ranking Metrics Cheat Sheet

| Metric | Meaning | Direction | Notes |
|--------|---------|-----------|-------|
| perplexity_improvement | Relative reduction (pre vs post) | Higher better | Default |
| post_perplexity | Final perplexity | Lower better | Stored negative internally for sorting |
| diversity_avg | Avg of Distinct-1 & Distinct-2 | Higher better | Requires sample generation |
| distinct_diversity | Alias of diversity_avg | Higher better | Use interchangeably |
| combined_improvement | 70% perplexity_improvement + 30% diversity_avg | Higher better | Balanced quality + diversity |

Use `--ranking-metric distinct_diversity` when you want variety-focused exploration; fallback behavior automatically reverts to post perplexity if a metric is unavailable.

### Inspect Status History

All parallel LoRA runs append to `data_out/parallel_training/status.json` with a `runs[]` array and optional `job_ranking[]`. TinyLlama entries appear with names like `tinyllama_ultra_<timestamp>`.

### Azure ML Validation & Optional Submission

After emitting a spec (`--azure-ml-spec`), validate locally:

```powershell
python .\scripts\azureml_ci_validate.py            # Validate latest job_*.yaml
python .\scripts\azureml_ci_validate.py --submit   # Validate + submit
```

Graceful skip occurs automatically if the Azure CLI is not installed.

### Cleanup Behavior

Passing `--cleanup` to training wrappers prunes `checkpoint*` artifacts while preserving `lora_adapter/`, `tokenizer/`, and `metrics.jsonl`. The status history will record `"cleanup": "completed"` when successful.

---

## LoRA Provider Usage for Aria

Train and use fine-tuned Aria models using LoRA adapters:

### CLI Example

```powershell
# Chat with a trained Aria adapter
python ./tools/talk-to-ai/src/chat_cli.py --provider lora --model data_out/aria_models/aria_direct

# Or use the default adapter location
python ./tools/talk-to-ai/src/chat_cli.py --provider lora --model data_out/lora_training/lora_adapter
```

### Web App

- Select "LoRA" in the provider dropdown.
- Enter the adapter path (e.g., `data_out/aria_models/aria_direct`) if prompted.
- The backend will load your trained Aria model for chat.

**Requirements:**

- `peft`, `transformers`, and `torch` must be installed in your environment.
- The adapter directory must contain `adapter_config.json` and `adapter_model.safetensors`.

**Troubleshooting:**

- If you see errors about missing `peft`, run:

```powershell
pip install peft transformers torch
```

- If the model fails to load, check that your adapter path is correct and contains the required files.

---
>>>>>>> origin/sync/github-sync-20260307-085533
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
