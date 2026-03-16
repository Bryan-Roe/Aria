"""Unit tests for shared config path resolver helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.config_paths import (
    canonical_config_path,
    get_config_candidates,
    known_config_keys,
    resolve_config_path,
    resolve_existing_config_path,
)


@pytest.mark.unit
def test_known_keys_include_orchestrators() -> None:
    keys = set(known_config_keys())
    assert {"master_orchestrator", "quantum_autorun", "evaluation_autorun"}.issubset(keys)


@pytest.mark.unit
def test_get_candidates_canonical_first(tmp_path: Path) -> None:
    candidates = get_config_candidates(tmp_path, "quantum_autorun")
    assert len(candidates) >= 2
    assert candidates[0] == tmp_path / "config" / "quantum" / "quantum_autorun.yaml"
    assert candidates[1] == tmp_path / "quantum_autorun.yaml"


@pytest.mark.unit
def test_resolve_existing_prefers_canonical_over_legacy(tmp_path: Path) -> None:
    canonical = tmp_path / "config" / "quantum" / "quantum_autorun.yaml"
    legacy = tmp_path / "quantum_autorun.yaml"

    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_text("jobs: []\n", encoding="utf-8")
    legacy.write_text("jobs: [legacy]\n", encoding="utf-8")

    resolved = resolve_existing_config_path(tmp_path, "quantum_autorun")
    assert resolved == canonical


@pytest.mark.unit
def test_resolve_config_uses_legacy_when_canonical_missing(tmp_path: Path) -> None:
    legacy = tmp_path / "master_orchestrator.yaml"
    legacy.write_text("version: 1\n", encoding="utf-8")

    resolved = resolve_config_path(tmp_path, "master_orchestrator")
    assert resolved == legacy


@pytest.mark.unit
def test_resolve_config_returns_canonical_when_none_exist(tmp_path: Path) -> None:
    resolved = resolve_config_path(tmp_path, "evaluation_autorun")
    assert resolved == canonical_config_path(tmp_path, "evaluation_autorun")


@pytest.mark.unit
def test_unknown_key_raises(tmp_path: Path) -> None:
    with pytest.raises(KeyError):
        get_config_candidates(tmp_path, "not_a_real_config")
