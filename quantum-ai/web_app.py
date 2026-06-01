"""Compatibility wrapper for the quantum web app module.

The canonical implementation lives in:
  ai-projects/quantum-ml/web_app.py

This wrapper preserves legacy import paths used by tests and scripts and hardens
checkpoint loading to improve security and error handling.
"""

from __future__ import annotations

import importlib.util
import sys
import logging
import traceback
from pathlib import Path
from typing import Any, Dict, Optional

_CANONICAL = Path(__file__).resolve().parents[1] / "ai-projects" / "quantum-ml" / "web_app.py"

if not _CANONICAL.exists():
    raise FileNotFoundError(f"Canonical web app not found: {_CANONICAL}")

_spec = importlib.util.spec_from_file_location("_canonical_quantum_web_app", _CANONICAL)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Unable to load spec for {_CANONICAL}")

_mod = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _mod
_spec.loader.exec_module(_mod)


def _get_logger():
    """Return a logger instance from the canonical module if available, else a repo logger."""
    try:
        # prefer Flask app logger if present
        app = getattr(_mod, "app", None)
        if app is not None and hasattr(app, "logger"):
            return app.logger
    except Exception:
        pass
    return logging.getLogger("quantum-ai.web_app")


def _get_request_json() -> Dict[str, Any]:
    """Safely obtain JSON payload from the canonical module's request object.

    Returns an empty dict if request/json are unavailable or malformed.
    """
    try:
        req = getattr(_mod, "request", None)
        if req is None:
            return {}
        # request.get_json(silent=True) is safer than accessing .json directly
        if hasattr(req, "get_json"):
            return req.get_json(silent=True) or {}
        return getattr(req, "json", {}) or {}
    except Exception:
        return {}


def _is_within_directory(child: Path, parent: Path) -> bool:
    """Return True if child is inside parent directory.

    Uses pathlib.Path.relative_to when available; falls back to parent membership check.
    """
    try:
        child.resolve()
        parent_resolved = parent.resolve()
    except (OSError, RuntimeError):
        return False

    # Python 3.9+: is_relative_to
    if hasattr(child, "is_relative_to"):
        try:
            return child.is_relative_to(parent_resolved)
        except Exception:
            return False

    try:
        child.resolve().relative_to(parent_resolved)
        return True
    except Exception:
        return False


def _compat_load_checkpoint() -> Any:
    """Compatibility endpoint using the legacy quantum-ai checkpoints directory.

    Expected JSON payload: { "checkpoint_path": "relative/or/absolute/path/to/checkpoint" }

    Security:
    - Only allows checkpoint files contained in the repo's `quantum-ai/checkpoints` directory.
    - Performs strong path resolution and membership checks to avoid directory traversal.

    Error handling:
    - Returns concise error messages to callers and logs full tracebacks to the application logger.
    """
    logger = _get_logger()
    payload = _get_request_json()
    checkpoint_path = payload.get("checkpoint_path")

    if not checkpoint_path:
        return _mod.jsonify({"error": "No checkpoint path provided"}), 400

    try:
        requested_path = Path(checkpoint_path)
        checkpoint_dir = Path(__file__).resolve().parent / "checkpoints"

        # Normalize and resolve paths; fail if resolution errors occur
        try:
            resolved_path = requested_path.resolve()
            allowed_dir = checkpoint_dir.resolve()
        except (OSError, RuntimeError) as e:
            logger.debug("Path resolution failed: %s", e)
            return _mod.jsonify({"error": "Invalid checkpoint path"}), 400

        if not _is_within_directory(resolved_path, allowed_dir):
            return _mod.jsonify({"error": "Invalid checkpoint path: must be within checkpoints directory"}), 403

        if not resolved_path.exists() or not resolved_path.is_file():
            return _mod.jsonify({"error": "Checkpoint file not found"}), 404

        # Load numpy from canonical module if present to preserve behavior; otherwise import locally.
        np = getattr(_mod, "np", None)
        if np is None:
            try:
                import numpy as _np

                np = _np
            except Exception as e:
                logger.exception("NumPy is required to load checkpoints: %s", e)
                return _mod.jsonify({"error": "Server misconfiguration: NumPy not available"}), 500

        # Attempt safe load without pickles first; only allow pickles on explicit failure.
        allow_pickle = False
        load_error: Optional[Exception] = None
        try:
            checkpoint = np.load(str(resolved_path), allow_pickle=allow_pickle)
        except Exception as exc_no_pickle:
            load_error = exc_no_pickle
            logger.debug("Initial np.load without pickles failed: %s", exc_no_pickle)
            # Retry with allow_pickle=True as a fallback (some checkpoints use object arrays).
            try:
                checkpoint = np.load(str(resolved_path), allow_pickle=True)
                allow_pickle = True
                logger.warning("Loaded checkpoint with allow_pickle=True for %s", resolved_path)
            except Exception as exc_with_pickle:
                logger.exception("Failed to load checkpoint file: %s", exc_with_pickle)
                # Do not return raw exception text; provide a generic message.
                return _mod.jsonify({"error": "Failed to load checkpoint file"}), 500

        # np.load may return an NpzFile or ndarray; handle both.
        try:
            # Prefer dictionary-like access
            if hasattr(checkpoint, "files"):
                # .npz archive
                try:
                    data = {k: checkpoint[k] for k in checkpoint.files}
                except Exception as e_read:
                    # If initial load was without pickles, retry with allow_pickle=True
                    if not allow_pickle:
                        logger.debug("Reading checkpoint members failed (%s); retrying with allow_pickle=True", e_read)
                        try:
                            checkpoint = np.load(str(resolved_path), allow_pickle=True)
                            allow_pickle = True
                            data = {k: checkpoint[k] for k in checkpoint.files}
                        except Exception as e_retry:
                            logger.exception("Failed to read checkpoint after retry: %s", e_retry)
                            return _mod.jsonify({"error": "Unexpected checkpoint format"}), 500
                    else:
                        raise
            elif isinstance(checkpoint, np.ndarray) and checkpoint.dtype == object:
                # Legacy object arrays may contain a dict-like element
                data = checkpoint.tolist()
                if isinstance(data, list) and len(data) == 1 and isinstance(data[0], dict):
                    data = data[0]
            else:
                # If it's an ndarray with structured dtype, try to access fields
                data = dict(checkpoint)
        except Exception:
            # Best-effort: if checkpoint itself is a dict-like mapping
            try:
                data = dict(checkpoint)
            except Exception:
                logger.exception("Unexpected checkpoint structure for %s", resolved_path)
                return _mod.jsonify({"error": "Unexpected checkpoint format"}), 500

        # Validate required keys
        if not ("weights" in data and "epoch" in data):
            logger.debug("Checkpoint missing required keys: %s", list(getattr(data, "keys", lambda: [])()))
            return _mod.jsonify({"error": "Checkpoint missing required keys (weights, epoch)"}), 400

        weights = data["weights"]
        epoch_val = data["epoch"]
        try:
            epoch = int(epoch_val)
        except Exception:
            logger.debug("Invalid epoch value in checkpoint: %r", epoch_val)
            return _mod.jsonify({"error": "Invalid epoch value in checkpoint"}), 400

        # Config may be stored as an array or mapping; normalize to a plain dict when possible.
        config = data.get("config")
        if hasattr(config, "item"):
            try:
                config = config.item()
            except Exception:
                # leave as-is if it cannot be converted
                pass

        response = {
            "success": True,
            "weights_shape": (
                list(getattr(getattr(weights, "shape", None), "__iter__", lambda: [])())
                if hasattr(weights, "shape")
                else []
            ),
            "epoch": epoch,
            "config": config,
            "message": f"Checkpoint loaded from epoch {epoch}",
            "meta": {"loaded_with_allow_pickle": bool(allow_pickle)},
        }

        return _mod.jsonify(response)

    except Exception as exc:
        # Log full traceback for diagnostics but return a small error message to caller
        logger.exception("Unhandled error while loading checkpoint: %s", exc)
        return _mod.jsonify({"error": "Internal server error while loading checkpoint"}), 500


# Keep the route path and endpoint name stable while swapping the handler logic
# to use the legacy checkpoint root expected by callers of ai-projects/quantum-ml/web_app.py.
try:
    _mod.app.view_functions["load_checkpoint"] = _compat_load_checkpoint
except Exception:
    # If the canonical module doesn't expose `app` (e.g., during isolated testing),
    # fall back to exposing the function in this module's globals for direct import.
    pass

# Re-export public symbols for compatibility.
for _name, _value in list(_mod.__dict__.items()):
    if not _name.startswith("__"):
        globals()[_name] = _value

load_checkpoint = _compat_load_checkpoint
