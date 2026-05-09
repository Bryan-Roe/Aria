---
name: "Quantum-AI-Python"
description: "Python-specific guidance for ai-projects/quantum-ml/"
applyTo: "ai-projects/quantum-ml/src/**/*.py"
---
# Quantum AI – Python files

## Cost Awareness
- Local simulators (Qiskit Aer, PennyLane default.qubit): **FREE**, unlimited use
- Azure simulators (ionq.simulator, quantinuum.sim.*): **FREE**, no cost limits
- Real quantum hardware (ionq.qpu, quantinuum.qpu.*): PAID (~$0.00003-$0.00015 per gate-shot)
- Workflow: Test locally → Validate on Azure simulator (FREE) → Run on QPU (PAID)
- Check `azure_confirm_cost: true` flag in quantum_autorun.yaml before QPU execution

## Development Guidelines

- Prefer local simulation first (Qiskit Aer) before Azure hardware.
  - Dry-run orchestrator: `python .\\scripts\\quantum_autorun.py --dry-run`
  - Simulator job: `python .\\scripts\\quantum_autorun.py --job azure_ionq_simulator`
- Cost gate: set `azure_confirm_cost: true` in `quantum_autorun.yaml` before real QPU; start with ≤100 shots.
- MCP server for tooling: `python .\\quantum-ai\\quantum_mcp_server.py`
  - Tools: `create_quantum_circuit`, `simulate_quantum_circuit`, `get_quantum_circuit_properties`, `connect_azure_quantum`, `list_quantum_backends`, `submit_quantum_job`, `estimate_quantum_cost`, `train_quantum_classifier`.
- Keep local limits reasonable: ≤10 qubits, ≤1000 shots; use `qiskit_aer` backend for fast feedback.
- Dashboard: `ai-projects/quantum-ml/start_dashboard.sh` → http://localhost:5000 for interactive training.
- Azure config lives in `ai-projects/quantum-ml/config/quantum_config.yaml`; requires `az login`.
- Data immutability: read-only `datasets/`; write-only outputs under `data_out/quantum_autorun/<job>/`.
- Tests: `python .\\scripts\\test_runner.py --unit` or `pytest -m "not slow and not azure"`.
- High-signal modules: `ai-projects/quantum-ml/quantum_mcp_server.py`, `ai-projects/quantum-ml/src/quantum_classifier.py`, `QUANTUM_AUTORUN_README.md`.
