# AI Workspace

A comprehensive workspace for quantum computing, AI fine-tuning, and chat applications.

## 📁 Project Structure

This workspace contains **three independent AI/ML projects**:

### 1. **quantum-ai/** - Quantum Machine Learning Platform 🆕

Hybrid quantum-classical ML using Azure Quantum + PennyLane + PyTorch with **Interactive Web Dashboard** and MCP Server support.

#### ✨ NEW: Web Training Dashboard

Train and visualize quantum AI models with a beautiful interactive UI:

```bash
cd quantum-ai
./start_dashboard.sh
# Open http://localhost:5000
```

**Features:**

- 🎨 **Interactive Web Dashboard** - Real-time training visualization with live charts
- ⚛️ Quantum circuit creation and simulation (Bell, GHZ, entanglement states)
- ☁️ Azure Quantum integration (IonQ, Quantinuum, Microsoft QC)
- 🧠 Hybrid quantum-classical neural networks
- 🤖 Model Context Protocol (MCP) server with 8 quantum tools
- 📊 Live loss/accuracy metrics and session management
- 🎛️ Interactive hyperparameter tuning (qubits, layers, learning rate)
- 📚 Training history browser with saved results

**Quick Start (Web Dashboard):**

```bash
cd quantum-ai
./start_dashboard.sh
# Open browser to http://localhost:5000
# Select dataset, configure parameters, click "Start Training"
# Watch real-time charts update as model trains!
```

**Quick Start (CLI):**

```bash
cd quantum-ai
source venv/bin/activate
pip install -r requirements.txt

# Run example classifier
python src/quantum_classifier.py

# Run MCP server
python quantum_mcp_server.py
```

**Documentation:**

- 🎨 **[Web Dashboard Guide](quantum-ai/WEB_DASHBOARD_README.md)** - Interactive training UI (NEW!)
- 📖 [Main README](quantum-ai/README.md) - Full project documentation
- 🤖 [MCP Server Guide](quantum-ai/MCP_SERVER_README.md) - AI agent integration

---

### 2. **talk-to-ai/** - Lightweight CLI Chat Application

Multi-provider chat CLI with local fallback, OpenAI, and Azure OpenAI support.

**Features:**

- Provider auto-detection (Azure OpenAI → OpenAI → Local)
- Streaming responses
- Conversation persistence (JSONL format)
- Zero-dependency local mode for offline development
- Minimal footprint (2 dependencies)

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

**Documentation:** See `talk-to-ai/README.md`

---

### 3. **AI/microsoft_phi-silica-3.6_v1/** - Phi-3.6 Fine-Tuning Workspace

Fine-tuning workspace for Microsoft Phi-3.6 models using LoRA and soft prompt techniques.

**Features:**

- LoRA fine-tuning (low-rank adaptation)
- Soft prompt tuning
- Azure ML deployment infrastructure
- Azure AI Toolkit integration

**Configuration:**

- **LoRA:** `AI/microsoft_phi-silica-3.6_v1/lora/lora.yaml`
- **Soft Prompt:** `AI/microsoft_phi-silica-3.6_v1/soft_prompt/soft_prompt.yaml`
- **Infrastructure:** `AI/microsoft_phi-silica-3.6_v1/lora/infra/provision/finetuning.bicep`

**Key Hyperparameters (LoRA):**

- Training: 8000 samples, batch size 2, seq length 1024
- Model: Phi-3.6-mini-instruct
- Optimizer: AdamW (lr=0.0002, warmup=400 steps)
- LoRA: dropout=0.1

**Note:** This project uses Azure AI Toolkit workspace configurations.

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

### Quantum Code

```powershell
cd quantum-ai
python .\src\quantum_classifier.py
```

### Chat CLI

```powershell
cd talk-to-ai
python .\src\chat_cli.py --provider local --once "Hello"
```

---

## 📝 File Organization

```
├── config/                 # Configuration files
│   ├── training/           # LoRA training configs (autotrain.yaml, etc.)
│   ├── quantum/            # Quantum job configs (quantum_autorun.yaml)
│   ├── evaluation/         # Evaluation configs (evaluation_autorun.yaml)
│   ├── autogen/            # Auto-generated configs (gitignored)
│   └── master_orchestrator.yaml
├── docs/                   # All documentation
│   ├── guides/             # Feature guides and summaries
│   ├── quickref/           # Quick reference cards
│   ├── training/           # Training documentation
│   ├── quantum/            # Quantum computing docs
│   ├── database/           # Database setup guides
│   ├── deployment/         # Azure deployment docs
│   └── aria/               # ARIA system docs
├── scripts/                # All orchestrator and utility scripts
├── shared/                 # Shared Python modules
├── tests/                  # Test suites
├── quantum-ai/             # Quantum ML platform
├── talk-to-ai/             # Chat CLI application
├── chat-web/               # Web chat interface
├── datasets/               # Training datasets (read-only)
└── data_out/               # Generated outputs (git-ignored)
```

---

## 📚 Documentation

All documentation has been organized into the `docs/` directory:

- **[docs/README.md](docs/README.md)** - Documentation index and navigation
- **[docs/quickref/](docs/quickref/)** - Quick reference cards
- **[docs/training/](docs/training/)** - LoRA and training guides
- **[docs/quantum/](docs/quantum/)** - Quantum computing documentation
- **[docs/database/](docs/database/)** - SQL and database setup
- **[docs/deployment/](docs/deployment/)** - Azure deployment guides

### Project-Specific Documentation

- **quantum-ai/README.md** - Architecture, quick start, deployment
- **quantum-ai/MCP_SERVER_README.md** - MCP server usage
- **talk-to-ai/README.md** - Chat CLI usage
- **.github/copilot-instructions.md** - Development conventions

---

## ⚠️ Common Issues

### Azure Quantum Authentication

If you see "Failed to connect to Azure Quantum":

1. Run `az login`
2. Verify `quantum_config.yaml` has correct subscription_id and resource_group
3. Check workspace exists: `az quantum workspace show -g rg-quantum-ai -n quantum-ai-workspace`

### Missing Quantum Providers

Some providers require manual registration. Check `list_backends()` output.

### Chat Streaming Issues

Verify SDK version: `pip list | findstr openai` should show `openai>=1.37.0`

---

## 🔧 Recent Enhancements

**November 2025 Updates:**

- **Quantum Status Integration**: `/api/ai/status` endpoint now includes quantum environment diagnostics
- **Qiskit 1.x Upgrade Path**: Scripted migration tool with backup/revert capabilities
- **Telemetry & Cosmos DB**: Production observability with Application Insights and Cosmos persistence
- **Enhanced Testing**: Unit test coverage for quantum environment validation

📖 **Documentation:**

- [Enhancements Summary](docs/guides/ENHANCEMENTS_SUMMARY.md) - Overview of all recent improvements
- [Telemetry & Cosmos Enablement Guide](docs/database/TELEMETRY_COSMOS_ENABLEMENT.md) - Step-by-step setup for observability
- [Quantum AutoRun README](docs/quantum/QUANTUM_AUTORUN_README.md) - Orchestrated quantum training automation
- [AutoTrain README](docs/training/AUTOTRAIN_README.md) - LoRA training orchestration

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

This workspace has comprehensive test coverage with **68 automated tests** fully integrated with VS Code's native Testing UI.

### Quick Start

1. **Open Test Explorer:** Click the beaker icon (🧪) in the Activity Bar or press `Ctrl+Shift+T`
2. **Run Tests:** Click the ▶️ play button next to any test, suite, or file
3. **Debug Tests:** Set breakpoints, then right-click test → "Debug Test"
4. **View Results:** Click any test to see output, assertions, and stack traces

### Test Suites

- **Unit Tests (Fast):** 40 tests (~0.5 seconds) ✅
- **Integration Tests:** 30 tests (external services) - 29 passing
- **All Fast Tests:** 83 tests (~10 seconds) - all passing ✅
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

| Project | Path | Purpose |
|---------|------|---------|
| Quantum AI | `quantum-ai/` | Quantum ML + MCP Server |
| Chat CLI | `talk-to-ai/` | Multi-provider chat |
| Fine-tuning | `AI/microsoft_phi-silica-3.6_v1/` | Phi-3.6 model tuning |

---

**Last Updated:** November 25, 2025

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

## LoRA Provider Usage

Interact with your fine-tuned LoRA model using the CLI or web app:

### CLI Example

```powershell
python .\src\chat_cli.py --provider lora --model ..\..\data_out\lora_training\lora_adapter
```

### Web App

- Select "LoRA" in the provider dropdown.
- Enter the adapter path (e.g., `data_out/lora_training/lora_adapter`) if prompted.
- The backend will load your LoRA model for chat.

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
