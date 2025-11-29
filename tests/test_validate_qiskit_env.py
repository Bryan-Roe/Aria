import importlib.util
import pathlib

# Dynamically load the validation script so tests do not depend on package layout
SCRIPT_PATH = pathlib.Path(__file__).resolve().parent.parent / "quantum-ai" / "scripts" / "validate_qiskit_env.py"
_spec = importlib.util.spec_from_file_location("validate_qiskit_env", SCRIPT_PATH)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)  # type: ignore


def test_pre_1x_environment_no_conflict():
    versions = {
        "qiskit": "0.46.0",
        "qiskit_aer": "0.12.2",
        "qiskit_machine_learning": "0.6.1",
    }
    meta = mod.detect_conflict(versions)
    assert meta["conflict"] is False
    assert "Pre-1.0" in meta["recommendation"]


def test_mixed_environment_conflict():
    versions = {
        "qiskit": "1.0.2",
        "qiskit_aer": "0.12.2",
        "qiskit_machine_learning": "0.6.1",
    }
    meta = mod.detect_conflict(versions)
    assert meta["conflict"] is True
    assert "mixes Qiskit >=1.x" in meta["recommendation"]


def test_error_import_conflict():
    versions = {
        "qiskit": "1.0.2",
        "qiskit_aer": "error: ImportError simulated",
    }
    meta = mod.detect_conflict(versions)
    assert meta["conflict"] is True
    assert "failed to import" in meta["recommendation"].lower()
