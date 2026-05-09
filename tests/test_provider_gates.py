from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "ai-projects" / "quantum-ml" / "scripts" / "test_provider_gates.py"
_spec = importlib.util.spec_from_file_location("test_provider_gates", SCRIPT_PATH)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Could not import {SCRIPT_PATH}")
gate_script = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate_script)


@pytest.mark.unit
def test_create_ghz_provider_native_variants():
    pytest.importorskip("qiskit")

    providers = ["standard", "quantinuum", "ionq", "rigetti"]
    for provider in providers:
        qc = gate_script.create_ghz_provider_native(4, provider=provider)

        assert qc is not None
        assert qc.num_qubits == 4
        assert qc.num_clbits == 4
        assert qc.count_ops().get("measure", 0) > 0

        if provider == "quantinuum":
            assert qc.count_ops().get("rzz", 0) >= 1
        if provider == "rigetti":
            assert qc.count_ops().get("cz", 0) >= 1
