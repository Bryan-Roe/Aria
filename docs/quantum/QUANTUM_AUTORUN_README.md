# Quantum AutoRun

A lightweight orchestrator to automate quantum training runs using
`ai-projects/quantum-ml/train_custom_dataset.py` (local simulators) and
`ai-projects/quantum-ml/deploy_to_azure_quantum.py` (Azure Quantum hardware).
It mirrors the AutoTrain pattern used for LoRA fine-tuning and supports both
free local execution and cloud hardware submission.

## What it does

- Reads jobs from `quantum_autorun.yaml`
- Builds commands for local simulator training OR Azure Quantum hardware submission
- Supports dry-run validation without execution
- Writes per-job run directories and aggregated status JSON
- **Cost safety**: Requires explicit confirmation (`azure_confirm_cost: true`) for paid hardware

## Files

- `scripts/evaluation/quantum_autorun.py` – the orchestrator
- `quantum_autorun.yaml` – declarative job definitions
- Outputs under `data_out/quantum_autorun/`
  - `<job>/<timestamp>/stdout.log`
  - `<job>/last_run.json`
  - `status.json` with a summary of the last invocation

## Quick start (PowerShell)

```powershell
# Validate the default jobs without executing
python .\scripts\quantum_autorun.py --dry-run

# Run a single job
python .\scripts\quantum_autorun.py --job heart_quick

# List configured jobs (JSON)
python .\scripts\quantum_autorun.py --list
```

You can also use VS Code tasks:

- Run: Quantum AutoRun (dry-run)
- Run: Quantum AutoRun (all)

## Config format (quantum_autorun.yaml)

### Local simulator job (FREE)

```yaml
version: 1
jobs:
  - name: heart_quick
    mode: train_custom_dataset          # Local simulator
    preset: heart                       # or use: csv: datasets/quantum/heart_disease.csv
    n_qubits: 4
    epochs: 1
    batch_size: 16
    learning_rate: 0.001
    test_size: 0.2
    enabled: true
```

### Azure Quantum hardware job

```yaml
  - name: azure_ionq_simulator
    mode: azure_hardware                # Azure Quantum submission
    azure_backend: ionq.simulator       # FREE: IonQ cloud simulator
    azure_shots: 100
    n_qubits: 3
    enabled: true

  - name: azure_ionq_qpu
    mode: azure_hardware
    azure_backend: ionq.qpu             # PAID: Real quantum hardware
    azure_shots: 100
    n_qubits: 3
    azure_confirm_cost: true            # REQUIRED for paid hardware
    enabled: false
    extra_args:
      - --circuit-file
      - ai-projects/quantum-ml/results/circuit.qasm
```

Notes:

- **Local mode** (`train_custom_dataset`): Choose either `preset` or `csv` (not both). If neither is provided, the script falls back to a small demo dataset.
- **Azure mode** (`azure_hardware`): Requires Azure credentials (`az login`) and a configured quantum workspace.
- **Cost safety**: Jobs targeting paid hardware (e.g., `ionq.qpu`, `rigetti.qpu`) MUST set `azure_confirm_cost: true` or validation will fail.
- Supported presets: `heart`, `ionosphere`, `sonar`, `banknote`.
- Supported Azure backends (examples): `ionq.simulator` (free), `ionq.qpu` (paid), `rigetti.sim.qvm` (free), `quantinuum.sim.h1-1sc` (free).

## Status endpoint integration

The `/api/ai/status` Azure Function now includes a `quantum_autorun` field when
`data_out/quantum_autorun/status.json` exists. This makes it easy to check the
last validation/execution results from the web UI or via curl.

## Azure Quantum setup

### Prerequisites

1. **Azure account** with an active subscription
2. **Azure Quantum workspace** created (see [Azure Quantum quickstart](https://learn.microsoft.com/azure/quantum/))
3. **Azure CLI** installed and authenticated: `az login`
4. **Config file** updated: `ai-projects/quantum-ml/config/quantum_config.yaml` with your workspace details

### Quick Azure setup

```powershell
# Login to Azure
az login

# Create resource group (if needed)
az group create --name rg-quantum-ai --location eastus

# Create quantum workspace (via Portal or Bicep)
# See: ai-projects/quantum-ml/azure/DEPLOYMENT.md

# Update ai-projects/quantum-ml/config/quantum_config.yaml with your:
# - subscription_id
# - resource_group
# - workspace_name
# - location
```

### Testing Azure connection

```powershell
# Dry-run an Azure simulator job (validates config, no execution)
python .\scripts\quantum_autorun.py --job azure_ionq_simulator --dry-run

# Run Azure simulator job (FREE - no QPU costs)
python .\scripts\quantum_autorun.py --job azure_ionq_simulator
```

### Cost management

- **Always test on simulators first** (`*.simulator` backends are free)
- Set `azure_confirm_cost: true` explicitly for paid hardware jobs
- Check Azure Quantum pricing: ~$0.00003/gate-shot (IonQ), varies by provider
- Monitor costs in Azure Portal → Cost Management
- Dry-run validates cost confirmation before submission

## Future extensions

- ~~Azure Quantum submission support~~ ✅ **DONE**
- Parse `results/custom_training_summary.json` after real (non-dry) runs and enrich `status.json`
- Batch experiment grids (varying `n_qubits`, `epochs`, and circuit depth)
- Automatic artifact collation (pull key metrics from Azure job results)
- Cost estimation API integration (show estimated cost during dry-run)
