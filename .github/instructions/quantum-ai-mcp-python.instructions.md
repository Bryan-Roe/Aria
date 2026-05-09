---
name: "Quantum-AI-MCP-Python"
description: "Python-specific guidance for quantum-ai MCP server"
applyTo: "ai-projects/quantum-ml/quantum_mcp_server.py"
---
# Quantum AI MCP Server – Python file

## Cost Awareness
- **Azure simulators (ionq.simulator, quantinuum.sim.*) are FREE** – no cost confirmation needed
- **Real QPU hardware (ionq.qpu, quantinuum.qpu.*) is PAID** – requires `confirm_cost=true` parameter
- Always test on FREE simulators before using paid QPU

## MCP Tools & Safety
- Start MCP server: `python .\\quantum-ai\\quantum_mcp_server.py`.
- Available tools: `create_quantum_circuit`, `simulate_quantum_circuit`, `get_quantum_circuit_properties`, `connect_azure_quantum`, `list_quantum_backends`, `submit_quantum_job`, `estimate_quantum_cost`, `train_quantum_classifier`.
- Safety limits enforced: ≤10 local qubits, default ≤1000 shots, 60s timeout per call, CircuitCache (LRU + TTL) to avoid recomputation.
- Cost gate for Azure QPU: require `confirm_cost=true` (tool args) and set `azure_confirm_cost: true` in orchestrator YAML before real hardware.
- Prefer local simulator backends (Qiskit Aer) or FREE Azure simulators before paid hardware.
- Azure workspace configuration: `ai-projects/quantum-ml/config/quantum_config.yaml` (requires `az login`).
- Outputs & status: write to `data_out/quantum_autorun/` and use status JSON for machine-readable progress.
- Tests: `python .\\scripts\\test_runner.py --unit` and `pytest -m "not slow and not azure"`.
