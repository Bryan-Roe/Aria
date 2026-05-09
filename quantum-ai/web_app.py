"""Compatibility wrapper for the quantum web app module.

The canonical implementation lives in:
  ai-projects/quantum-ml/web_app.py

This wrapper preserves legacy import paths used by tests and scripts.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_CANONICAL = (
    Path(__file__).resolve().parents[1] / "ai-projects" / "quantum-ml" / "web_app.py"
)

if not _CANONICAL.exists():
    raise FileNotFoundError(f"Canonical web app not found: {_CANONICAL}")

_spec = importlib.util.spec_from_file_location("_canonical_quantum_web_app", _CANONICAL)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Unable to load spec for {_CANONICAL}")

_mod = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _mod
_spec.loader.exec_module(_mod)


def _compat_load_checkpoint():
    """Compatibility endpoint using the legacy quantum-ai checkpoints directory."""
    payload = _mod.request.json or {}
    checkpoint_path = payload.get("checkpoint_path")

    if not checkpoint_path:
        return _mod.jsonify({"error": "No checkpoint path provided"}), 400

    try:
        requested_path = Path(checkpoint_path)
        checkpoint_dir = Path(__file__).resolve().parent / "checkpoints"

        try:
            resolved_path = requested_path.resolve()
            allowed_dir = checkpoint_dir.resolve()
        except (OSError, RuntimeError):
            return _mod.jsonify({"error": "Invalid checkpoint path"}), 400

        if hasattr(resolved_path, "is_relative_to"):
            if not resolved_path.is_relative_to(allowed_dir):
                return (
                    _mod.jsonify(
                        {
                            "error": "Invalid checkpoint path: must be within checkpoints directory"
                        }
                    ),
                    403,
                )
        else:
            try:
                resolved_path.relative_to(allowed_dir)
            except ValueError:
                return (
                    _mod.jsonify(
                        {
                            "error": "Invalid checkpoint path: must be within checkpoints directory"
                        }
                    ),
                    403,
                )

        if not resolved_path.exists():
            return _mod.jsonify({"error": "Checkpoint file not found"}), 404

        checkpoint = _mod.np.load(str(resolved_path), allow_pickle=True)
        weights = checkpoint["weights"]
        epoch = int(checkpoint["epoch"])
        config = (
            checkpoint["config"].item()
            if isinstance(checkpoint["config"], _mod.np.ndarray)
            else checkpoint["config"]
        )

        return _mod.jsonify(
            {
                "success": True,
                "weights_shape": list(weights.shape),
                "epoch": epoch,
                "config": config,
                "message": f"Checkpoint loaded from epoch {epoch}",
            }
        )
    except Exception as exc:
        return _mod.jsonify({"error": str(exc)}), 500


# Keep the route path and endpoint name stable while swapping the handler logic
# to use the legacy checkpoint root expected by callers of ai-projects/quantum-ml/web_app.py.
_mod.app.view_functions["load_checkpoint"] = _compat_load_checkpoint

# Re-export public symbols for compatibility.
for _name, _value in _mod.__dict__.items():
    if not _name.startswith("__"):
        globals()[_name] = _value

load_checkpoint = _compat_load_checkpoint
