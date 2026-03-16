"""Token utilities re-export module for shared infrastructure.

This module re-exports token utilities from the canonical source at
talk-to-ai/src/token_utils.py to avoid code duplication while
maintaining backward compatibility for imports from shared/.

Usage:
    from shared.token_utils import prune_messages, count_messages_tokens
    # or after adding shared/ to sys.path:
    from token_utils import prune_messages
"""
from __future__ import annotations

import sys
import importlib.util
from pathlib import Path

# Load canonical token utils from current chat-cli location, with legacy fallback.
_repo_root = Path(__file__).resolve().parent.parent
_canonical_candidates = [
    _repo_root / "ai-projects" / "chat-cli" / "src" / "token_utils.py",
    _repo_root / "talk-to-ai" / "src" / "token_utils.py",
]

_canonical_path = next((p for p in _canonical_candidates if p.exists()), None)
if _canonical_path is None:
    raise FileNotFoundError("token_utils canonical file not found in known locations")

_spec = importlib.util.spec_from_file_location("_canonical_token_utils", _canonical_path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Unable to load canonical token utils: {_canonical_path}")

_canonical_module = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _canonical_module
_spec.loader.exec_module(_canonical_module)

# Re-export all public symbols from canonical token_utils
RoleMessage = _canonical_module.RoleMessage
MODEL_CONTEXT_DEFAULTS = _canonical_module.MODEL_CONTEXT_DEFAULTS
PruneStats = _canonical_module.PruneStats
count_messages_tokens = _canonical_module.count_messages_tokens
prune_messages = _canonical_module.prune_messages

__all__ = [
    "RoleMessage",
    "MODEL_CONTEXT_DEFAULTS",
    "PruneStats",
    "count_messages_tokens",
    "prune_messages",
]
