---
description: "Plan and execute quantum computing workflows — circuit design, simulation, Azure Quantum submission, and cost-aware QPU execution."
name: "Quantum Workflow"
argument-hint: "Circuit spec + backend target (example: circuit description + local-sim | azure-sim | ionq + cost limit)"
agent: qai-specialist
---

Handle the following quantum computing task with cost awareness and safety.

**Execution ladder (always follow this order):**
1. **Local simulation** (FREE): Qiskit Aer, PennyLane default.qubit
2. **Azure simulator** (FREE): `--job azure_ionq_simulator`
3. **Real QPU** (PAID): Only with `azure_confirm_cost: true` in YAML + cost estimate review

**Quick commands:**
```bash
# Validate config
python scripts/quantum_autorun.py --dry-run

# Run on simulator
python scripts/quantum_autorun.py --job azure_ionq_simulator

# MCP server (quantum tools)
python ai-projects/quantum-ml/quantum_mcp_server.py

# Interactive dashboard
cd ai-projects/quantum-ml && ./start_dashboard.sh
```

**MCP tools available:**
- `create_quantum_circuit`, `simulate_quantum_circuit`, `get_quantum_circuit_properties`
- `connect_azure_quantum`, `list_quantum_backends`, `submit_quantum_job`
- `estimate_quantum_cost`, `train_quantum_classifier`

**Safety limits:**
- Max qubits: 10 (local), 20 (Azure with approval)
- Max shots: 1,000 (default), 100,000 (with `high_shots=true`)
- Always validate circuit locally before cloud submission

**Key files:**
- MCP server: `ai-projects/quantum-ml/quantum_mcp_server.py`
- Classifier: `ai-projects/quantum-ml/src/quantum_classifier.py`
- Config: `quantum_autorun.yaml`, `ai-projects/quantum-ml/config/quantum_config.yaml`
