# QAI workspace – Copilot instructions

This repo contains three independent projects; treat them as separate apps with their own deps and configs:
- `quantum-ai/` – Hybrid quantum–classical ML with Azure Quantum + Qiskit/PennyLane, includes an MCP server
- `talk-to-ai/` – Minimal CLI chat with local fallback, OpenAI, and Azure OpenAI
- `AI/microsoft_phi-silica-3.6_v1/` – Phi‑3.6 LoRA/soft‑prompt fine‑tuning (Azure AI Toolkit–style configs)

Conventions you must follow:
- Windows PowerShell is the default shell; use PS syntax and paths under `c:\Users\Bryan\OneDrive\AI`.
- Config is YAML first; don’t hardcode model/back‑end settings—read `quantum-ai/config/quantum_config.yaml` and the LoRA YAMLs.
- Logs/results live under project folders (e.g., `talk-to-ai/logs/`, `quantum-ai/results/`). Azurite files at repo root indicate local Azure Storage use.

Quantum AI fast path:
- Setup: `cd quantum-ai`; create venv; `pip install -r requirements.txt`; for MCP: `pip install -r mcp-requirements.txt`.
- Local run: `python .\src\quantum_classifier.py`.
- MCP server: `python .\quantum_mcp_server.py` (tools: create/simulate/analyze circuits; connect/list/submit/estimate Azure; train hybrid classifier).
- Typical flow: create_circuit → simulate locally → optionally submit to Azure (circuit cache is session‑scoped).
- VS Code MCP snippet:
  { "quantum-ai": { "type": "stdio", "command": "python", "args": ["c:\\Users\\Bryan\\OneDrive\\AI\\quantum-ai\\quantum_mcp_server.py"] } }

Azure Quantum integration (quantum-ai/src/azure_quantum_integration.py):
- Uses DefaultAzureCredential; always call `connect()` before `list_backends()` or `submit_circuit()`.
- Edit `quantum-ai/config/quantum_config.yaml` with subscription/workspace. Full guide: `quantum-ai/azure/DEPLOYMENT.md`.
- Cost: simulators free; IonQ ~3e‑5 per gate‑shot; Quantinuum ~1.5e‑4 per circuit—validate on Qiskit Aer first.

Circuit/model patterns (enforced by code):
- Entanglement modes: `linear`, `circular`, `full` (CNOT topology).
- Hybrid models: classical preprocess → variational RY/RZ layers → classical postprocess; parameters come from YAML.

Talk‑to‑AI fast path:
- Auto‑detects provider: Azure OpenAI → OpenAI → Local. One‑shot local: `python .\talk-to-ai\src\chat_cli.py --provider local --once "Hello"`.
- Azure OpenAI env: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT` (plus `AZURE_OPENAI_API_VERSION`).
- OpenAI env: `OPENAI_API_KEY` (optional `OPENAI_MODEL`). Logs are JSONL in `talk-to-ai/logs/`.

Phi‑3.6 fine‑tuning fast path:
- Install `AI/microsoft_phi-silica-3.6_v1/requirements.txt`; configs in `lora/lora.yaml` and `soft_prompt/soft_prompt.yaml`.
- Dry‑run/validate: `python .\AI\microsoft_phi-silica-3.6_v1\scripts\train_lora.py --dry-run --dataset .\AI\microsoft_phi-silica-3.6_v1\data --config .\AI\microsoft_phi-silica-3.6_v1\lora\lora.yaml`.
- Train small: set `HF_MODEL_ID` if needed; use manifests or local JSONL; metrics go to `save_dir` and can optionally emit to Azure Monitor/App Insights.

Datasets (repo‑wide):
- One‑shot setup: `python .\scripts\quick_setup_datasets.py`. Ready‑to‑use CSVs under `datasets/quantum/`; chat JSONL under `datasets/chat/`.
- Use with quantum‑ai custom trainer `train_custom_dataset.py` or Phi scripts’ `--dataset`/manifests.

Troubleshooting quick hits:
- Azure Quantum: `az login`; verify `quantum_config.yaml`; workspace exists (`quantum-ai/azure/DEPLOYMENT.md`). Always `connect()` before actions.
- Chat streaming: requires `openai>=1.37.0` per `talk-to-ai/requirements.txt`.
- Large qubit counts can exhaust memory—reduce `n_qubits`/layers or shots in YAML.

Additive changes checklist:
- Update the relevant README when adding providers/backends/config keys or changing CLI flags.
- Keep commands PowerShell‑friendly; store data under `datasets/` and results under project `results/`.
