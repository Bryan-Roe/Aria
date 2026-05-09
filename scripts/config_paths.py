"""Shared config path resolution helpers for orchestrators and CI scripts."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Canonical path first, legacy fallback second when present.
_CONFIG_CANDIDATES: Dict[str, Tuple[str, ...]] = {
    "master_orchestrator": (
        "config/master_orchestrator.yaml",
        "master_orchestrator.yaml",
    ),
    "quantum_autorun": (
        "config/quantum/quantum_autorun.yaml",
        "quantum_autorun.yaml",
    ),
    "evaluation_autorun": (
        "config/evaluation/evaluation_autorun.yaml",
        "evaluation_autorun.yaml",
    ),
    "autotrain": (
        "config/training/autotrain.yaml",
        "autotrain.yaml",
    ),
}


def known_config_keys() -> List[str]:
    """Return supported config keys in stable sorted order."""
    return sorted(_CONFIG_CANDIDATES.keys())


def get_config_candidates(repo_root: Path, key: str) -> List[Path]:
    """Return candidate config paths for a key, canonical-first."""
    if key not in _CONFIG_CANDIDATES:
        raise KeyError(f"Unknown config key: {key}")
    return [repo_root / rel for rel in _CONFIG_CANDIDATES[key]]


def canonical_config_path(repo_root: Path, key: str) -> Path:
    """Return canonical (preferred) config path for a key."""
    return get_config_candidates(repo_root, key)[0]


def resolve_existing_config_path(repo_root: Path, key: str) -> Optional[Path]:
    """Return first existing config path for key, or None if none exist."""
    candidates = get_config_candidates(repo_root, key)
    return next((path for path in candidates if path.exists()), None)


def resolve_config_path(repo_root: Path, key: str) -> Path:
    """Resolve config path for runtime use.

    Returns first existing candidate; if none exist, returns canonical path.
    """
    existing = resolve_existing_config_path(repo_root, key)
    if existing is not None:
        return existing
    return canonical_config_path(repo_root, key)
