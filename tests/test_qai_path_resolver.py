from __future__ import annotations

from pathlib import Path

import pytest

from mount.path_resolver import resolve_qai_config


@pytest.mark.unit
def test_resolve_qai_config_maps_legacy_defaults_to_repo_layout(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    config_path = repo_root / "mount" / "config.yaml"
    (repo_root / "mount").mkdir(parents=True, exist_ok=True)
    (repo_root / "ai-projects" / "chat-cli").mkdir(parents=True, exist_ok=True)
    (repo_root / "ai-projects" / "quantum-ml" / "config").mkdir(parents=True, exist_ok=True)
    (repo_root / "ai-projects" / "lora-training" / "microsoft_phi-silica-3.6_v1").mkdir(parents=True, exist_ok=True)
    (repo_root / "datasets").mkdir()
    (repo_root / "data_out").mkdir()
    (repo_root / "scripts").mkdir()

    raw_config = {
        "paths": {
            "workspace_root": "..",
            "quantum_ai": "../quantum-ai",
            "talk_to_ai": "../talk-to-ai",
            "phi_training": "../AI/microsoft_phi-silica-3.6_v1",
            "datasets": "../datasets",
            "data_out": "../data_out",
            "scripts": "../scripts",
        },
        "quantum": {
            "config_file": "../ai-projects/quantum-ml/config/quantum_config.yaml",
            "results_dir": "../ai-projects/quantum-ml/results",
        },
        "chat": {
            "providers": {
                "lora": {
                    "adapter_path": "../data_out/lora_training/lora_adapter",
                }
            }
        },
        "training": {
            "output_dir": "../data_out",
            "orchestrators": {
                "autotrain": {
                    "config_file": "../config/training/autotrain.yaml",
                    "status_file": "../data_out/autotrain/status.json",
                },
                "quantum_autorun": {
                    "config_file": "../config/quantum/quantum_autorun.yaml",
                    "status_file": "../data_out/quantum_autorun/status.json",
                },
            },
        },
    }

    resolved = resolve_qai_config(raw_config, config_path)

    assert resolved["paths"]["workspace_root"] == str(repo_root)
    assert resolved["paths"]["quantum_ai"] == str(repo_root / "ai-projects" / "quantum-ml")
    assert resolved["paths"]["talk_to_ai"] == str(repo_root / "ai-projects" / "chat-cli")
    assert resolved["paths"]["phi_training"] == str(
        repo_root / "ai-projects" / "lora-training" / "microsoft_phi-silica-3.6_v1"
    )
    assert resolved["quantum"]["config_file"] == str(
        repo_root / "ai-projects" / "quantum-ml" / "config" / "quantum_config.yaml"
    )
    assert resolved["chat"]["providers"]["lora"]["adapter_path"] == str(
        repo_root / "data_out" / "lora_training" / "lora_adapter"
    )


@pytest.mark.unit
def test_resolve_qai_config_preserves_existing_custom_paths(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    config_path = repo_root / "mount" / "config.yaml"
    custom_quantum = tmp_path / "custom-quantum"
    custom_chat = tmp_path / "custom-chat"
    custom_phi = tmp_path / "custom-phi"
    custom_output = tmp_path / "custom-output"

    (repo_root / "mount").mkdir(parents=True, exist_ok=True)
    custom_quantum.mkdir()
    custom_chat.mkdir()
    custom_phi.mkdir()
    custom_output.mkdir()

    raw_config = {
        "paths": {
            "workspace_root": "..",
            "quantum_ai": str(custom_quantum),
            "talk_to_ai": str(custom_chat),
            "phi_training": str(custom_phi),
            "data_out": str(custom_output),
        }
    }

    resolved = resolve_qai_config(raw_config, config_path)

    assert resolved["paths"]["quantum_ai"] == str(custom_quantum)
    assert resolved["paths"]["talk_to_ai"] == str(custom_chat)
    assert resolved["paths"]["phi_training"] == str(custom_phi)
    assert resolved["paths"]["data_out"] == str(custom_output)


@pytest.mark.unit
def test_resolve_qai_config_uses_custom_workspace_for_relative_overrides(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    config_path = repo_root / "mount" / "config.yaml"
    custom_workspace = tmp_path / "custom-workspace"

    (repo_root / "mount").mkdir(parents=True, exist_ok=True)
    (custom_workspace / "ai-projects" / "quantum-ml").mkdir(parents=True, exist_ok=True)
    (custom_workspace / "config" / "training").mkdir(parents=True, exist_ok=True)

    raw_config = {
        "paths": {
            "workspace_root": str(custom_workspace),
            "quantum_ai": "ai-projects/quantum-ml",
        },
        "training": {
            "orchestrators": {
                "autotrain": {
                    "config_file": "config/training/autotrain.yaml",
                }
            }
        },
    }

    resolved = resolve_qai_config(raw_config, config_path)

    assert resolved["paths"]["workspace_root"] == str(custom_workspace)
    assert resolved["paths"]["quantum_ai"] == str(custom_workspace / "ai-projects" / "quantum-ml")
    assert resolved["training"]["orchestrators"]["autotrain"]["config_file"] == str(
        custom_workspace / "config" / "training" / "autotrain.yaml"
    )


@pytest.mark.unit
def test_resolve_qai_config_preserves_missing_custom_paths(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    config_path = repo_root / "mount" / "config.yaml"
    missing_chat = tmp_path / "custom-workspace" / "chat-cli"
    missing_adapter = tmp_path / "custom-workspace" / "adapter"

    (repo_root / "mount").mkdir(parents=True, exist_ok=True)

    raw_config = {
        "paths": {
            "workspace_root": "..",
            "talk_to_ai": str(missing_chat),
        },
        "chat": {
            "providers": {
                "lora": {
                    "adapter_path": str(missing_adapter),
                }
            }
        },
    }

    resolved = resolve_qai_config(raw_config, config_path)

    assert resolved["paths"]["talk_to_ai"] == str(missing_chat)
    assert resolved["chat"]["providers"]["lora"]["adapter_path"] == str(missing_adapter)
