# AI Workspace

A comprehensive workspace for quantum computing, AI fine-tuning, and chat applications.

## 📁 Project Structure

This workspace contains **three independent AI/ML projects**:

### 1. **quantum-ai/** - Quantum Machine Learning Platform 🆕

Hybrid quantum-classical ML using Azure Quantum + PennyLane + PyTorch with **Interactive Web Dashboard** and MCP Server support.

**✨ NEW: Web Training Dashboard**

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

---

## 🚀 Deployment

### Quantum AI Deployment

```powershell
cd quantum-ai\azure
az deployment group create `
  --resource-group rg-quantum-ai `
  --template-file quantum_workspace.bicep `
  --parameters quantum_workspace.parameters.json
```

See `quantum-ai/azure/DEPLOYMENT.md` for complete deployment guide.

---

## 📊 Cost Awareness

### Quantum Jobs

- **Microsoft Simulators:** Free
- **IonQ:** ~$0.00003 per gate-shot
- **Quantinuum:** ~$0.00015 per circuit execution

**Best Practice:** Always test on `qiskit_aer` simulator locally before submitting to paid hardware.

### Azure OpenAI

- Costs vary by model and token usage
- Use local provider for development/testing

---

## 🔗 Integration Points

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

## 🧪 Testing

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

- **Configuration:** YAML files (`quantum_config.yaml`, `lora.yaml`)
- **Logs/Results:** Project-specific directories
- **Infrastructure:** Bicep templates (`.bicep` + `.parameters.json`)
- **Python Modules:** Descriptive names (`*_integration.py`, `*_classifier.py`)

---

## 📚 Documentation

Each project has comprehensive documentation:

- **quantum-ai/README.md** - Architecture, quick start, deployment
- **quantum-ai/MCP_SERVER_README.md** - MCP server usage
- **quantum-ai/azure/DEPLOYMENT.md** - Azure deployment guide
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

## 🔍 Quick Navigation

| Project | Path | Purpose |
|---------|------|---------|
| Quantum AI | `quantum-ai/` | Quantum ML + MCP Server |
| Chat CLI | `talk-to-ai/` | Multi-provider chat |
| Fine-tuning | `AI/microsoft_phi-silica-3.6_v1/` | Phi-3.6 model tuning |

---

**Last Updated:** October 31, 2025

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
