# QAI workspace – Copilot instructions

This repo contains three independent projects; treat them as separate apps with their own deps and configs:
- `quantum-ai/` – Hybrid quantum–classical ML with Azure Quantum + Qiskit/PennyLane, includes an MCP server
- `talk-to-ai/` – Minimal CLI chat with local fallback, OpenAI, and Azure OpenAI
- `AI/microsoft_phi-silica-3.6_v1/` – Phi‑3.6 LoRA/soft‑prompt fine‑tuning (Azure AI Toolkit–style configs)

## Dev Container & Cross-Platform Support

**Environment:** Alpine Linux dev container (3.20) with bash as default shell
- **Windows host conventions:** Original docs use PowerShell syntax (`.\path\`, `$env:VAR`)
- **Linux container commands:** Use bash syntax (`./path/`, `export VAR=value`)
- Commands in this file are **Linux/bash-first** for container compatibility
- When editing code, maintain PowerShell examples in per-project READMEs for Windows users

## 🆓 Free Tier Quick Start (No Cloud Costs)

All projects work **100% locally** without any paid services:

```bash
# 1. Quantum AI - Local simulation (NO Azure required)
cd quantum-ai
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python src/quantum_classifier.py          # Free: Qiskit Aer simulator

# 2. Chat - Local mode (NO API keys required)
cd ../talk-to-ai
pip install -r requirements.txt
python src/chat_cli.py --provider local --once "Test"  # Zero cost, offline-capable

# 3. Datasets - All free, open-source
cd ..
python scripts/quick_setup_datasets.py    # Dolly 15k, UCI datasets (all free)
```

**💡 Free alternatives to paid services:**
- Quantum hardware → Use `qiskit_aer` or `lightning.qubit` simulators (unlimited, free)
- OpenAI/Azure OpenAI → Use `--provider local` mode (rule-based, no keys needed)
- GPU training → Use `--max-train-samples 64` for CPU-friendly tests
- Azure Storage → Local Azurite emulator (already configured at repo root)

## Core conventions

**Configuration philosophy:**
- **YAML-first**: Never hardcode models/backends—read `quantum-ai/config/quantum_config.yaml`, `lora/lora.yaml`, `soft_prompt/soft_prompt.yaml`.
- **Config structure**: `azure.*` for infra, `quantum.*` for circuits/backends, `ml.*` for training hyperparams.
- **Config loading pattern**: All quantum modules use relative paths from script location:
  ```python
  current_dir = Path(__file__).parent
  config_path = current_dir.parent / "config" / "quantum_config.yaml"
  with open(config_path) as f:
      config = yaml.safe_load(f)
  ```
- **Logs/results**: Always write to project-local dirs (`talk-to-ai/logs/*.jsonl`, `quantum-ai/results/*.json`, `AI/microsoft_phi-silica-3.6_v1/data_out/`).

**Azure Functions integration:**
- Repo root contains Azure Functions app (`function_app.py`) that serves chat web UI and REST API
- Provider abstraction: All chat providers inherit `BaseChatProvider` and implement `complete(messages, stream)` method
- Functions import talk-to-ai modules dynamically: `sys.path.insert(0, "talk-to-ai/src")`
- Local dev: Azurite emulator files at root (`__azurite_db_*.json`, `__blobstorage__/`, `__queuestorage__/`)
- Config: `local.settings.json` sets `AzureWebJobsStorage: UseDevelopmentStorage=true`
- **Status endpoint** (`/api/ai/status`):
  - Returns comprehensive JSON with provider info, ML dependencies, LoRA adapter readiness, AutoTrain status, and Quantum AutoRun status.
  - **Azure Quantum context**: Includes workspace details from `quantum-ai/config/quantum_config.yaml`, direct portal link, and array of Azure jobs with IDs/backends/results.
  - Portal links: `quantum_azure.workspace_portal_url` for workspace, `portal_job_url_template` for deep-linking to specific jobs.

**Dataset integration:**
- `datasets/dataset_index.json`: Metadata registry for all datasets (quantum CSVs, chat JSONL, sizes, licenses)
- Structure: `datasets/{quantum,chat,vision,raw,processed}/` 
- Quantum training: `train_custom_dataset.py` loads from `datasets/quantum/*.csv` via pandas
- LLM training: Scripts accept `--dataset path/to/jsonl` or manifest files
- Quick setup: `scripts/quick_setup_datasets.py` downloads UCI + Dolly 15k (~500MB, auto-validates)

## Quantum AI (`quantum-ai/`)

**Setup & execution:**
```bash
cd quantum-ai
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt          # Core: qiskit, pennylane, pytorch
pip install -r mcp-requirements.txt      # For MCP server: mcp>=0.9.0
python src/quantum_classifier.py         # Local simulation demo
python train_custom_dataset.py           # Train on datasets/quantum/*.csv
```

**Quantum AutoRun orchestrator** (`scripts/quantum_autorun.py`):
- **YAML-driven automation**: Define jobs in `quantum_autorun.yaml` with presets, hyperparams, and Azure backends.
- **Two modes**:
  - `train_custom_dataset`: Local simulator training (FREE, default)
  - `azure_hardware`: Submit to Azure Quantum (simulators FREE, QPU paid)
- **Safety**: Azure QPU jobs require `azure_confirm_cost: true` to prevent accidental charges.
- **Status tracking**: Generates `data_out/quantum_autorun/status.json` with per-job results, aggregates, and Azure metadata.
- **Usage**:
  ```powershell
  python .\scripts\quantum_autorun.py --dry-run              # Validate all enabled jobs
  python .\scripts\quantum_autorun.py --job heart_quick      # Run specific job
  python .\scripts\quantum_autorun.py --list                 # List configured jobs
  ```
- **VS Code tasks**: "Run: Quantum AutoRun (dry-run)" and "Run: Quantum AutoRun (all)".
- **Azure enrichment**: Successful Azure runs parse results and attach `azure_job_id`, `azure_counts`, `azure_success` to status meta.

**MCP server** (Model Context Protocol for AI agents):
- Run: `python quantum_mcp_server.py` (exposes 8 quantum tools via stdio).
- Tools: `create_quantum_circuit`, `simulate_quantum_circuit`, `train_quantum_classifier`, `connect_azure_quantum`, `submit_quantum_job`, `list_quantum_backends`, `estimate_quantum_cost`, `get_quantum_circuit_properties`.
- Circuit cache: Session-scoped LRU with TTL (100 circuits, 3600s); cleared on server restart.
- Architecture: ProcessPoolExecutor (2 workers) for CPU-bound quantum ops, ThreadPoolExecutor (4 workers) for I/O
- VS Code MCP config (`.vscode/mcp.json`):
  ```json
  { "quantum-ai": { "type": "stdio", "command": "python", "args": ["c:\\Users\\Bryan\\OneDrive\\AI\\quantum-ai\\quantum_mcp_server.py"] } }
  ```

**Azure Quantum integration** (`src/azure_quantum_integration.py`):
- **⚠️ OPTIONAL** - All quantum features work locally without Azure. Only use Azure for real quantum hardware access.
- Auth: `DefaultAzureCredential` (requires `az login` or env vars). Always call `connect()` before `list_backends()`/`submit_circuit()`.
- Config: Edit `quantum_config.yaml` → `azure.subscription_id`, `azure.resource_group`, `azure.workspace_name`.
- Deployment: Bicep templates in `azure/` (see `azure/DEPLOYMENT.md`). Create workspace via Portal or `az deployment group create`.
- **Free tier:** Microsoft Quantum simulators, `qiskit_aer`, `lightning.qubit` (unlimited local use).
- **Paid tier:** IonQ ~$0.00003/gate-shot, Quantinuum ~$0.00015/circuit.
- **Critical pattern:** ALWAYS test locally (`simulator.backend: qiskit_aer`) - never submit to paid hardware without validation.

**Circuit & model patterns** (enforced by YAML + code):
- Entanglement modes: `linear` (chain), `circular` (ring), `full` (all-to-all CNOT).
- Variational circuits: RY/RZ rotation layers → entangling CNOTs → measurement.
- Hybrid architecture: Classical preprocessing → quantum variational layer → classical output NN.
- Dataset integration: `train_custom_dataset.py` expects CSV with features + labels. Use PCA to reduce to `n_qubits` features, StandardScaler normalization.

**Hardware validation** (as of Nov 2025):
- ✅ Rigetti `rigetti.sim.qvm`: Production-ready, 1% accuracy vs hardware.
- ⚠️ Quantinuum H-series simulators: Known Azure bug (avoid until fixed). See `PROVIDER_COMPARISON_RESULTS.md`.
- Test flow: Bell state → GHZ → variational circuit. Results in `results/*.json`. Visualize with `scripts/visualize_hardware_results.py`.

## Talk-to-AI (`talk-to-ai/`)

**🆓 FREE DEFAULT: Local provider works offline with zero deps/keys**

**Provider auto-detection** (priority order):
1. Azure OpenAI: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`, `AZURE_OPENAI_API_VERSION`.
2. OpenAI: `OPENAI_API_KEY` (optional `OPENAI_MODEL`).
3. **Local fallback (FREE):** Zero deps, offline-capable (rule-based responses).

**Usage:**
```powershell
cd talk-to-ai
pip install -r requirements.txt  # openai>=1.37.0 (only for cloud providers)

# 🆓 FREE: One-shot local (no keys, works offline)
python .\src\chat_cli.py --provider local --once "Hello"

# 🆓 FREE: Interactive local mode
python .\src\chat_cli.py --provider local

# 💰 PAID: Interactive Azure OpenAI
$env:AZURE_OPENAI_API_KEY = "..."; $env:AZURE_OPENAI_ENDPOINT = "https://....openai.azure.com/"; $env:AZURE_OPENAI_DEPLOYMENT = "gpt-4o-mini"
python .\src\chat_cli.py --provider azure

# Interactive commands: /new (reset), /save (write to logs/), /exit
```

**Persistence:**
- Conversations saved as JSONL in `logs/chat_<timestamp>.jsonl`.
- Format: `{"role": "user|assistant", "content": "...", "timestamp": "..."}`

## Phi-3.6 Fine-Tuning (`AI/microsoft_phi-silica-3.6_v1/`)

**💰 Note:** Full training requires GPU. Use CPU-friendly test mode for experimentation.

**Config structure:**
- LoRA: `lora/lora.yaml` (rank, dropout, target modules, training hyperparams).
- Soft prompt: `soft_prompt/soft_prompt.yaml` (prompt tuning params).
- Key settings in `lora.yaml`:
  - `finetune_train_nsamples: 8000`, `finetune_train_batch_size: 2`, `finetune_train_seqlen: 1024`.
  - Optimizer: `learning_rate: 0.0002`, `adam_beta1: 0.9`, `adam_beta2: 0.95`, `num_warmup_steps: 400`.
  - LoRA: `lora_dropout: 0.1`, `model: Phi-3.6-mini-instruct`.

**Execution:**
```powershell
cd AI\microsoft_phi-silica-3.6_v1
pip install -r requirements.txt

# 🆓 CPU-friendly test (no GPU required, 64 samples) - STREAMING MODE (default, handles large datasets)
python .\scripts\train_lora.py --dataset ..\..\datasets\chat\dolly --config .\lora\lora.yaml --max-train-samples 64 --max-eval-samples 16 --epochs 1

# 🆓 CPU-friendly test - NON-STREAMING MODE (faster for small datasets)
python .\scripts\train_lora.py --dataset ..\..\datasets\chat\dolly --config .\lora\lora.yaml --max-train-samples 64 --max-eval-samples 16 --epochs 1 --no-stream

# Dry-run (validate config, no training)
python .\scripts\train_lora.py --dry-run --dataset .\data --config .\lora\lora.yaml

# 💰 Full training (GPU required - use Colab free tier or Kaggle notebooks for free GPU access)
python .\scripts\train_lora.py --dataset ..\..\datasets\chat\dolly --config .\lora\lora.yaml
```

**VS Code quick tasks:**
- "Run: LoRA quick (streaming)" – smoke test with streaming dataset (default, memory-efficient)
- "Run: LoRA quick (non-stream)" – smoke test with non-streaming dataset (faster for small data)

**Free GPU alternatives:**
- Google Colab (free tier: ~12 hours GPU/day)
- Kaggle Notebooks (free tier: ~30 hours GPU/week)
- GitHub Codespaces (free tier: 120 core-hours/month)

**Dataset format:**
- JSONL with Phi-3 chat template: `{"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}`
- Scripts support manifests (pointers to JSONL files) or direct JSONL dirs.
- Metrics → `save_dir` (local) or Azure Monitor/App Insights (if configured).

## Datasets (`datasets/`)

**🆓 All datasets are free and open-source**

**Quick setup:**
```powershell
python .\scripts\quick_setup_datasets.py  # Downloads quantum CSVs + Dolly 15k (~500 MB, 5 min)
```

**Structure:**
- `datasets/quantum/`: UCI ML datasets (heart_disease, ionosphere, sonar, banknote) as CSV.
- `datasets/chat/`: LLM fine-tuning (dolly, openassistant, alpaca) as JSONL.
- `datasets/raw/`: Original downloads (cache).
- `datasets/processed/`: Cleaned/transformed data.
- `datasets/dataset_index.json`: Metadata inventory.

**Manual downloads:**
```powershell
python .\scripts\download_datasets.py --category quantum                        # All quantum CSVs
python .\scripts\download_datasets.py --category chat --dataset dolly           # Dolly 15k (CC BY-SA, commercial OK)
python .\scripts\download_datasets.py --category chat --dataset openassistant   # OASST (Apache 2.0, larger)
python .\scripts\validate_datasets.py --verbose                                  # Validate integrity
```

**License awareness:**
- ✅ Commercial: Dolly (CC BY-SA 3.0), OpenAssistant (Apache 2.0), UCI datasets (attribution).
- ⚠️ Non-commercial: Alpaca (CC BY-NC 4.0).

**Integration:**
- Quantum: `train_custom_dataset.py` loads from `datasets/quantum/*.csv` with pandas.
- Phi-3.6: `--dataset ../../datasets/chat/dolly` (path to JSONL dir or manifest).

## Online IDE Compatibility

**GitHub Codespaces / VS Code Online:**
- All projects work in browser-based environments
- Free tier: 120 core-hours/month (60 hours on 2-core machine)
- Set up: `git clone` → run setup commands above
- Storage: Use free tier's 15GB for datasets

**Google Colab (for GPU tasks):**
```python
# Clone repo in Colab
!git clone https://github.com/<your-repo>/QAI.git
%cd QAI/AI/microsoft_phi-silica-3.6_v1
!pip install -r requirements.txt
# Run training with Colab's free GPU
!python scripts/train_lora.py --dataset ../../datasets/chat/dolly --config lora/lora.yaml --max-train-samples 256
```

**Kaggle Notebooks:**
- Free tier: 30 GPU hours/week
- Add datasets as Kaggle datasets (no download needed)
- Enable GPU in notebook settings

## Troubleshooting

**Azure Quantum connection fails:**
1. Verify: `az login` and `az account show` (correct subscription).
2. Check `quantum_config.yaml`: subscription_id, resource_group, workspace_name match Portal.
3. Confirm workspace exists: `az quantum workspace show -g rg-quantum-ai -n quantum-ai-workspace` or Portal.
4. Code pattern: Must call `azure_integration.connect()` before any `list_backends()`/`submit_circuit()` calls.

**Chat streaming not working:**
- Verify `openai>=1.37.0`: `pip list | findstr openai`.
- Check provider config: `--provider azure` requires all 4 env vars (`*_KEY`, `*_ENDPOINT`, `*_DEPLOYMENT`, `*_API_VERSION`).

**Out of memory (quantum):**
- Reduce `n_qubits` (4→3), `n_layers` (2→1), or `shots` (1024→128) in `quantum_config.yaml`.
- Use `simulator.backend: lightning.qubit` (faster than `qiskit_aer` for >10 qubits).

**JSONL validation errors:**
- Run `python .\scripts\validate_datasets.py --category chat --verbose` for details.
- Common fixes: Remove trailing blank lines, ensure valid JSON per line, verify `messages` array exists.

**LoRA training crashes:**
- **Streaming dataset errors**: Fixed in `train_lora.py` with auto-computed `max_steps` and FilteringDataCollator. Use `--no-stream` flag if issues persist.
- CPU: Use `--max-train-samples 64 --max-eval-samples 16 --epochs 1` for quick tests.
- GPU OOM: Reduce `finetune_train_batch_size` (2→1) or `finetune_train_seqlen` (1024→512) in `lora.yaml`.
- **No GPU?** Use Google Colab free tier (12 hours/day GPU) or Kaggle (30 hours/week GPU).
- **VS Code tasks**: Use "Run: LoRA quick (streaming)" or "Run: LoRA quick (non-stream)" for one-click smoke tests.

**Cost optimization:**
- Quantum: Default to `qiskit_aer` or `lightning.qubit` simulators (free, unlimited).
- Chat: Use `--provider local` for testing (no API costs).
- Training: Start with `--max-train-samples 64` on CPU before scaling to GPU.
- Azure: Only provision resources when you need paid hardware/services.

## Contribution checklist

When adding features or changing APIs:
1. Update the relevant project README (`quantum-ai/README.md`, etc.).
2. Document new config keys in YAML comments and this file.
3. Add CLI flags to help text (`--help` output).
4. For backends/providers: Update cost estimates (this file + `DEPLOYMENT.md`).
5. For datasets: Update `AI_DATASETS_CATALOG.md` and `dataset_index.json`.
6. Keep commands PowerShell-friendly (backticks, not semicolons; `.\path\`, not `./path/`).
