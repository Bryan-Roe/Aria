"""Pytest suite for quantum-ai web_app checkpoint loader compatibility.

This test imports the compatibility wrapper by file path, creates a small
checkpoint file in the repository's quantum-ai/checkpoints directory, and
monkeypatches the internal canonical module reference to a fake object that
provides the expected interfaces (np, request, jsonify, app.logger).

The test verifies that the compatibility loader returns the expected JSON
structure when provided a valid checkpoint.
"""

import importlib.util
import logging
import sys
import types
from pathlib import Path

import numpy as np
from pytest import MonkeyPatch


def _load_wrapper():
    # Load the wrapper module by file path so tests don't rely on package imports.
    file = Path(__file__).resolve().parents[1] / "quantum-ai" / "web_app.py"
    spec = importlib.util.spec_from_file_location("quantum_ai_web_app_for_tests", str(file))
    if spec is None:
        raise RuntimeError(f"Could not create spec for {file}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    if spec.loader is None:
        raise RuntimeError(f"Spec loader is None for {file}")
    spec.loader.exec_module(mod)
    return mod


def test_compat_load_checkpoint_success(tmp_path: Path, monkeypatch: MonkeyPatch):
    repo_root = Path(__file__).resolve().parents[1]
    chk_dir = repo_root / "quantum-ai" / "checkpoints"
    chk_dir.mkdir(parents=True, exist_ok=True)

    # Create a small checkpoint file (.npz) with expected keys
    weights = np.zeros((2, 3))
    epoch = 7
    config = {"lr": 0.01}
    chk_file = chk_dir / "test_checkpoint.npz"

    np.savez(chk_file, weights=weights, epoch=epoch, config=np.array(config, dtype=object))

    mod = _load_wrapper()

    # Build a fake canonical module object that exposes the attributes the wrapper
    # expects: np, request.get_json(), jsonify, and app.logger
    class Req:
        def __init__(self, data):
            self._data = data

        def get_json(self, silent=True):
            return self._data

    fake = types.SimpleNamespace()
    fake.np = np
    fake.request = Req({"checkpoint_path": str(chk_file)})

    def jsonify(obj):
        # The wrapper expects jsonify to return a response-like object; for tests
        # returning the dict directly is convenient.
        return obj

    fake.jsonify = jsonify
    fake.app = types.SimpleNamespace(logger=logging.getLogger("test.quantum"))

    # Replace the canonical module reference inside the imported wrapper with our fake.
    monkeypatch.setattr(mod, "_mod", fake)

    result = mod._compat_load_checkpoint()

    # The fake jsonify returns the plain dict on success
    assert isinstance(result, dict)
    assert result.get("success") is True
    assert result.get("epoch") == epoch
    assert result.get("weights_shape") == [2, 3]
