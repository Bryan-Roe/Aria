# AI Workspace - Copilot Instructions

## Architecture Overview

This workspace contains **three independent AI/ML projects** with different purposes:

1. **quantum-ai/** - Hybrid quantum-classical ML using Azure Quantum + PennyLane + PyTorch
2. **talk-to-ai/** - Lightweight CLI chat with local fallback, OpenAI, and Azure OpenAI support
3. **AI/microsoft_phi-silica-3.6_v1/** - Fine-tuning workspace for Phi-3.6 models (LoRA + soft prompt)

Each project is self-contained with its own dependencies, configuration, and deployment infrastructure.

## Critical Developer Workflows

### Environment Setup & Dependencies

**PowerShell is the primary shell** - all commands should use PowerShell syntax (not bash).

#### For quantum-ai:
```powershell
cd quantum-ai
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Dependencies: `azure-quantum`, `qiskit`, `pennylane`, `torch`, `azure-identity`

#### For talk-to-ai:
```powershell
cd talk-to-ai
# Minimal deps - can run without venv
pip install -r requirements.txt  # Only: openai>=1.37.0, colorama
```

#### For fine-tuning projects:
Fine-tuning uses Azure AI Toolkit workspace configs. See `finetuning.workspace.config` and `*.yaml` files in `lora/` and `soft_prompt/` directories.

### Local Development with Azurite

The workspace root contains **Azurite database files** (`__azurite_db_*.json`, `__blobstorage__/`, `__queuestorage__/`). This indicates local Azure Storage emulator usage for development. When working with Azure Storage features, developers should:
- Use Azurite connection strings for local testing
- Expect blob/queue/table storage data in workspace root

### Running Projects

#### Quantum AI
```powershell
cd quantum-ai
# Run example classifier
python .\src\quantum_classifier.py

# Connect to Azure Quantum (requires config)
python .\src\azure_quantum_integration.py
```

Before running Azure Quantum code, update `config/quantum_config.yaml` with your Azure subscription details.

#### Talk-to-AI
```powershell
cd talk-to-ai
# Local mode (no API keys)
python .\src\chat_cli.py --provider local

# OpenAI mode
$env:OPENAI_API_KEY = "sk-..."
python .\src\chat_cli.py --provider openai

# Azure OpenAI mode
$env:AZURE_OPENAI_API_KEY = "..."
$env:AZURE_OPENAI_ENDPOINT = "https://....openai.azure.com/"
$env:AZURE_OPENAI_DEPLOYMENT = "gpt-4o-mini"
python .\src\chat_cli.py --provider azure
```

Interactive commands: `/new` (new conversation), `/save` (save to logs/), `/exit`

### Azure Deployment

#### Quantum Workspace Deployment
```powershell
cd quantum-ai\azure
# Login and set subscription
az login
az account set --subscription "<subscription-id>"

# Deploy Bicep template
az deployment group create `
  --resource-group rg-quantum-ai `
  --template-file quantum_workspace.bicep `
  --parameters quantum_workspace.parameters.json
```

See `quantum-ai/azure/DEPLOYMENT.md` for complete deployment guide including:
- Provider setup (IonQ, Quantinuum, Microsoft QC)
- Service principal authentication
- Cost management strategies

## Project-Specific Conventions

### Quantum AI Code Patterns

**Hybrid Classical-Quantum Architecture**: The pattern in `quantum_classifier.py` demonstrates the standard workflow:
1. Classical preprocessing (normalize to [0, 2π] for quantum encoding)
2. Quantum circuit execution (variational layers with RY/RZ rotations)
3. Classical postprocessing (linear layer + sigmoid)

```python
# Standard pattern for hybrid models
class HybridQuantumClassifier(nn.Module):
    def __init__(self, input_dim, quantum_classifier):
        super().__init__()
        self.classical_layers = nn.Sequential(...)  # Preprocessing
        self.quantum_weights = nn.Parameter(...)     # Quantum params
        self.output_layer = nn.Linear(...)           # Postprocessing
```

**Configuration-Driven Design**: All quantum parameters (n_qubits, n_layers, entanglement type, shots) come from `quantum_config.yaml`. Never hardcode these values.

**Entanglement Patterns**: Three supported modes in quantum circuits:
- `linear`: CNOT between adjacent qubits (i → i+1)
- `circular`: CNOT wrapping around (last → first)
- `full`: All-to-all CNOT connections

### Talk-to-AI Patterns

**Provider Auto-Detection**: `chat_providers.py` implements automatic provider selection based on environment variables:
1. Check Azure OpenAI vars (API_KEY + ENDPOINT + DEPLOYMENT)
2. Fall back to OpenAI (API_KEY + MODEL)
3. Fall back to local echo provider (no keys needed)

**Local Provider Philosophy**: The `LocalEchoProvider` is **intentionally simple** - it's for smoke tests and offline development, not production use. It rephrases user input to simulate responses.

**Conversation Persistence**: All chat sessions save to `talk-to-ai/logs/*.jsonl` in JSONL format (one message per line). Load with:
```python
messages = [json.loads(line) for line in open("logs/chat_*.jsonl")]
```

### Fine-Tuning Workspace

The `AI/microsoft_phi-silica-3.6_v1/` directory uses **Azure AI Toolkit conventions**:
- `lora/lora.yaml` - LoRA fine-tuning hyperparameters
- `soft_prompt/soft_prompt.yaml` - Soft prompt tuning config
- `infra/provision/finetuning.bicep` - Azure ML deployment templates

Key hyperparameters in `lora.yaml`:
- Training: 8000 samples, batch size 2, 1024 seq length
- Model: Phi-3.6-mini-instruct with LoRA dropout 0.1
- Optimization: AdamW (lr=0.0002, warmup=400 steps)

## Integration Points

### Azure Quantum Integration

The `azure_quantum_integration.py` module provides:
- **Workspace connection**: Uses `DefaultAzureCredential()` for auth (supports Azure CLI, service principal, managed identity)
- **Job submission**: `submit_circuit()` transpiles Qiskit circuits and submits to selected backend
- **Batch processing**: `QuantumJobManager` tracks multiple jobs by name

**Critical**: Always call `connect()` before `submit_circuit()` or `list_backends()`. Connection establishes the workspace and provider context.

### Chat Provider Abstraction

All providers implement `BaseChatProvider.complete(messages, stream)`:
- `messages`: List of `{"role": "system|user|assistant", "content": "..."}`
- `stream=True`: Returns generator yielding chunks
- `stream=False`: Returns complete response string

Add new providers by subclassing `BaseChatProvider` and implementing `complete()`.

## Testing & Validation

### Quantum Code Testing
```powershell
cd quantum-ai
pytest tests/  # If tests exist
# Or run examples to validate
python .\src\quantum_classifier.py
```

### Chat CLI Testing
```powershell
cd talk-to-ai
# Quick smoke test (no keys needed)
python .\src\chat_cli.py --provider local --once "Hello"
```

### Common Issues

**Azure Quantum Authentication**: If you see "Failed to connect to Azure Quantum", verify:
1. `az login` completed successfully
2. `quantum_config.yaml` has correct subscription_id and resource_group
3. Workspace exists: `az quantum workspace show -g rg-quantum-ai -n quantum-ai-workspace`

**Missing Quantum Providers**: Some providers require manual registration. Check `azure.list_backends()` output.

**Chat Streaming Issues**: If streaming doesn't work, verify SDK version: `pip list | grep openai` should show `openai>=1.37.0`.

## Cost Awareness

**Quantum Jobs** - Costs vary significantly by provider:
- Microsoft simulators: **Free**
- IonQ: ~$0.00003 per gate-shot
- Quantinuum: ~$0.00015 per circuit execution

**Best Practice**: Always test on `qiskit_aer` simulator locally before submitting to paid hardware.

## File Organization Patterns

- Configuration files use `.yaml` extension (quantum_config.yaml, lora.yaml)
- Logs/results go in project-specific directories (`quantum-ai/results/`, `talk-to-ai/logs/`)
- Infrastructure as Code uses Bicep (`.bicep` + `.parameters.json` pairs)
- Python modules use descriptive names: `*_integration.py`, `*_classifier.py`, `*_providers.py`

## Documentation Standards

Each project has comprehensive README.md with:
- Architecture diagrams (quantum-ai uses ASCII art)
- Quick start examples with exact commands
- Configuration templates
- Cost breakdowns
- Deployment guides

When modifying code, update README.md if:
- Adding new configuration options
- Changing CLI flags or commands
- Introducing new providers/backends
- Modifying cost implications
