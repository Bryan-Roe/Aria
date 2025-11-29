# Quantum AutoRun: Azure Hardware Examples

Complete examples for using Quantum AutoRun with Azure Quantum hardware.

## Prerequisites Checklist

- [ ] Azure account with active subscription
- [ ] Azure Quantum workspace created and configured
- [ ] Azure CLI installed: `az --version`
- [ ] Authenticated: `az login`
- [ ] Config updated: `quantum-ai/config/quantum_config.yaml`
- [ ] Python environment with quantum-ai dependencies

## Example 1: Free Azure Simulator (No Costs)

This example uses IonQ's cloud simulator which is free to use.

### Config (`quantum_autorun.yaml`)

```yaml
jobs:
  - name: azure_free_test
    mode: azure_hardware
    azure_backend: ionq.simulator  # FREE
    azure_shots: 100
    n_qubits: 3
    enabled: true
    extra_args:
      - --circuit-file
      - quantum-ai/results/bell_state.qasm
```

### Commands

```powershell
# Validate without executing
python .\scripts\quantum_autorun.py --job azure_free_test --dry-run

# Run on Azure simulator (free)
python .\scripts\quantum_autorun.py --job azure_free_test

# Check results
cat data_out\quantum_autorun\azure_free_test\<timestamp>\stdout.log
```

## Example 2: Paid Hardware with Safety Checks

This example targets real quantum hardware (IonQ QPU) with cost safety enabled.

### Hardware Config

```yaml
jobs:
  - name: ionq_hardware_run
    mode: azure_hardware
    azure_backend: ionq.qpu  # PAID: Real quantum hardware
    azure_shots: 50          # Keep low to minimize cost
    n_qubits: 3
    azure_confirm_cost: true  # REQUIRED for paid hardware
    enabled: false            # Keep disabled until ready
    extra_args:
      - --circuit-file
      - quantum-ai/results/optimized_circuit.qasm
```

### Safety Validation

```powershell
# This will FAIL validation (cost not confirmed)
# azure_confirm_cost: false

# This will PASS validation
# azure_confirm_cost: true

# Dry-run to verify (no submission)
python .\scripts\quantum_autorun.py --job ionq_hardware_run --dry-run

# Enable in config and run (charges will apply)
python .\scripts\quantum_autorun.py --job ionq_hardware_run
```

### Cost Estimation

- IonQ QPU: ~$0.00003 per gate-shot
- 50 shots × 10 gates = ~$0.015
- Always test on simulator first!

## Example 3: Multi-Backend Comparison

Compare results across simulators and hardware.

### Config

```yaml
jobs:
  # Local simulator (baseline)
  - name: compare_local
    mode: train_custom_dataset
    preset: heart
    n_qubits: 3
    epochs: 1
    enabled: true

  # Azure IonQ simulator
  - name: compare_ionq_sim
    mode: azure_hardware
    azure_backend: ionq.simulator
    azure_shots: 100
    n_qubits: 3
    enabled: true

  # Azure Rigetti simulator
  - name: compare_rigetti_sim
    mode: azure_hardware
    azure_backend: rigetti.sim.qvm
    azure_shots: 100
    n_qubits: 3
    enabled: true

  # IonQ hardware (disabled by default)
  - name: compare_ionq_hardware
    mode: azure_hardware
    azure_backend: ionq.qpu
    azure_shots: 50
    n_qubits: 3
    azure_confirm_cost: true
    enabled: false
```

### Batch Execution

```powershell
# Run all enabled jobs sequentially
python .\scripts\quantum_autorun.py

# Check aggregated status
cat data_out\quantum_autorun\status.json

# Compare results programmatically
python .\scripts\analyze_quantum_results.py
```

## Example 4: Circuit File Integration

### Create Circuit

```python
# quantum-ai/create_test_circuit.py
from qiskit import QuantumCircuit

def create_bell_state():
    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])
    return qc

if __name__ == "__main__":
    circuit = create_bell_state()
    circuit.qasm(filename="results/bell_state.qasm")
    print("Circuit saved to results/bell_state.qasm")
```

### Submit to Azure

```yaml
jobs:
  - name: bell_state_ionq
    mode: azure_hardware
    azure_backend: ionq.simulator
    azure_shots: 1000
    enabled: true
    extra_args:
      - --circuit-file
      - quantum-ai/results/bell_state.qasm
```

## Troubleshooting

### Error: "Not connected to Azure Quantum"

```powershell
# Check Azure login
az account show

# Re-login if needed
az login

# Verify workspace exists
az quantum workspace show --name quantum-ai-workspace --resource-group rg-quantum-ai
```

### Error: "COST SAFETY: azure_confirm_cost must be true"

This is expected! Set `azure_confirm_cost: true` in your config to acknowledge hardware costs.

### Error: "Backend not found"

```powershell
# List available backends
az quantum workspace show --name quantum-ai-workspace --resource-group rg-quantum-ai

# Common backend names:
# - ionq.simulator (free)
# - ionq.qpu (paid)
# - rigetti.sim.qvm (free)
# - quantinuum.sim.h1-1sc (free)
```

## Best Practices

1. **Always test locally first**: Use `mode: train_custom_dataset` to validate circuits
2. **Use simulators for development**: Azure simulators are free and catch errors
3. **Keep shots low initially**: Start with 50-100 shots, increase only if needed
4. **Enable dry-run by default**: Add `--dry-run` to all commands during development
5. **Monitor costs**: Check Azure Portal → Cost Management regularly
6. **Version control circuits**: Keep QASM files in git for reproducibility
7. **Document experiments**: Use descriptive job names and maintain a results log

## Cost Management Scripts

### Check Recent Azure Costs

```powershell
# Last 7 days of Quantum costs
az consumption usage list --start-date (Get-Date).AddDays(-7).ToString("yyyy-MM-dd") | ConvertFrom-Json | Where-Object { $_.instanceName -like "*quantum*" }
```

### Set Budget Alert

```powershell
# Create budget alert for quantum workspace
az consumption budget create --amount 50 --category cost --time-grain monthly --resource-group rg-quantum-ai --budget-name quantum-monthly-budget
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Quantum Tests

on: [push]

jobs:
  quantum-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run quantum autorun dry-run
        run: |
          python scripts/quantum_autorun.py --dry-run
      
      - name: Run simulator tests only
        run: |
          python scripts/quantum_autorun.py --job azure_ionq_simulator
```

## Advanced: Programmatic Job Submission

```python
# scripts/submit_quantum_batch.py
import subprocess
import json
from pathlib import Path

jobs = ["azure_sim_1", "azure_sim_2", "azure_sim_3"]

results = []
for job in jobs:
    cmd = ["python", "scripts/quantum_autorun.py", "--job", job]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    results.append({
        "job": job,
        "status": "success" if proc.returncode == 0 else "failed",
        "output": proc.stdout
    })

# Save batch results
with open("data_out/batch_results.json", "w") as f:
    json.dump(results, f, indent=2)
```

## Support

- Azure Quantum Docs: <https://learn.microsoft.com/azure/quantum/>
- IonQ Provider: <https://learn.microsoft.com/azure/quantum/provider-ionq>
- Rigetti Provider: <https://learn.microsoft.com/azure/quantum/provider-rigetti>
- Cost Calculator: <https://azure.microsoft.com/pricing/details/quantum/>
