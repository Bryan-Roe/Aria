---
name: "Quantum-AI-workspace"
description: "Slim instructions for quantum-ai/"
applyTo: "quantum-ai/**"
---
# Quantum AI – workspace-specific guidance

- Prefer local simulation first (Qiskit Aer) before Azure hardware.
  - Validate with: `python .\\scripts\\quantum_autorun.py --dry-run`
  - Then: `python .\\scripts\\quantum_autorun.py --job azure_ionq_simulator`
- Real QPU runs require an explicit cost gate: set `azure_confirm_cost: true` in `quantum_autorun.yaml` and start with ≤100 shots.
- MCP server tools (run: `python .\\quantum-ai\\quantum_mcp_server.py`):
  - `create_quantum_circuit`, `simulate_quantum_circuit`, `get_quantum_circuit_properties`
  - `connect_azure_quantum`, `list_quantum_backends`, `submit_quantum_job`, `estimate_quantum_cost`
  - `train_quantum_classifier`
- Interactive Web Dashboard: `quantum-ai/start_dashboard.sh` → http://localhost:5000
- Azure workspace config: `quantum-ai/config/quantum_config.yaml` (requires `az login`).
- Data immutability: read-only `datasets/`; write-only outputs in `data_out/quantum_autorun/<job>/...`.
- Unit tests: `python .\\scripts\\test_runner.py --unit` or `pytest -m "not slow and not azure"` for fast local validation.
- Safety limits: ≤10 qubits local; default ≤1000 shots; MCP server has CircuitCache (LRU + TTL) to avoid re-computation.
- Key files: `quantum-ai/quantum_mcp_server.py`, `quantum-ai/src/quantum_classifier.py`, `QUANTUM_AUTORUN_README.md`, `quantum-ai/HARDWARE_TEST_RESULTS.md`.
- Observability: Application Insights via `shared/telemetry.py`; failures are non-blocking and surfaced in `/api/ai/status`.
