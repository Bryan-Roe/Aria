# QAI – Copilot Instructions (Concise)

Project-specific essentials for AI agents (target: fast, safe, cost-aware contributions).

## 1. Domains & Boundaries
`quantum-ai/` (hybrid quantum ML + MCP) | `talk-to-ai/` (multi-provider chat) | `AI/microsoft_phi-silica-3.6_v1/` (LoRA + soft prompt). Each has its own venv. Root `function_app.py` (Azure Functions) injects their `src` paths. All orchestrators in `scripts/` MUST run from repo root.

## 2. Orchestrated Workflow
Configs: `autotrain.yaml`, `quantum_autorun.yaml`. Precedence: YAML < CLI flags < per‑job overrides. Always run `--dry-run` first; consume `data_out/<orchestrator>/status.json` (never parse stdout). Example:
```json
{"jobs":[{"name":"phi36_mixed_chat","status":"validated"}],"errors":[],"timestamp":"..."}
```
Dataset immutability: only read `datasets/`; write under `data_out/`.

## 3. Providers & Env Vars
Auto-detect order: Azure OpenAI → OpenAI → LoRA (if adapter dir has `adapter_model.safetensors`) → Local. Azure requires ALL: `AZURE_OPENAI_API_KEY|ENDPOINT|DEPLOYMENT|API_VERSION` or fallback. Health: `/api/ai/status` shows `active_provider`.

## 4. Quantum vs MCP
Training script (`train_custom_dataset.py`) = long-running; MCP server (`quantum-ai/quantum_mcp_server.py`) = 8 short ops (≤10 qubits, ≤1k shots, 60s). Paid backends need `azure_confirm_cost: true`. Approx costs: IonQ ~$0.00003/gate-shot; Quantinuum ~$0.00015/circuit. Always prove locally on `qiskit_aer` first.

## 5. Testing & Validation
Run `pytest tests/` (root). Skip slow: `pytest -m "not slow"`. Dataset checks: `scripts/validate_datasets.py`; quantum result charts: `quantum-ai/scripts/visualize_hardware_results.py`.

## 6. Extensibility
Chat provider: subclass `BaseChatProvider` then update `detect_provider()`. Quantum job/backend: add YAML entry, dry-run, Bell test, then hardware with cost flag. New Function endpoint: extend `/api/ai/status` (additive only).

## 7. Diagnostics
status.json: `jobs[].status` (`validated|succeeded|failed|missing`). LoRA ready when `adapter_config.json` & `adapter_model.safetensors` exist. Azure fallback usually due to missing one of 4 env vars. Quantum auth: `az login` + matching `quantum_config.yaml`.

## 8. Safety & Secrets
No secrets committed. Use env vars or local `local.settings.json` (dev only). Dry-run before paid runs. Initial QPU shots ≤100. LoRA smoke: `--max-train-samples 64 --epochs 1`.

## 9. Key Commands
```powershell
python .\scripts\autotrain.py --dry-run
python .\scripts\quantum_autorun.py --dry-run
python .\scripts\auto_bootstrap.py --dry-run  # one-shot env + orchestrator validation
python .\scripts\train_and_evaluate.py --all-variants --dry-run  # validate hyperparam jobs + eval mapping
python .\talk-to-ai\src\chat_cli.py --provider local --once "Test"
func host start
python .\quantum-ai\quantum_mcp_server.py
```

## 10. References
See project READMEs + root `README.md`; recover verbose guidance via git history. Cosmos DB modeling: `TELEMETRY_COSMOS_ENABLEMENT.md`.

Last updated: 2025-11-22
