from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

_CANONICAL_PATHS = {
    "workspace_root": ".",
    "quantum_ai": "ai-projects/quantum-ml",
    "talk_to_ai": "ai-projects/chat-cli",
    "phi_training": "ai-projects/lora-training/microsoft_phi-silica-3.6_v1",
    "datasets": "datasets",
    "data_out": "data_out",
    "scripts": "scripts",
}

_LEGACY_DEFAULTS = {
    "quantum_ai": {"../quantum-ai", "quantum-ai"},
    "talk_to_ai": {"../talk-to-ai", "talk-to-ai"},
    "phi_training": {
        "../AI/microsoft_phi-silica-3.6_v1",
        "AI/microsoft_phi-silica-3.6_v1",
    },
}


def _normalize_path_text(value: str) -> str:
    return value.replace("\\", "/").rstrip("/")


def _resolve_path(value: str, *, base_dir: Path) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def _path_base_dir(value: str, *, config_dir: Path, workspace_root: Path) -> Path:
    if value.startswith(("./", "../")):
        return config_dir
    return workspace_root


def _resolve_repo_path(
    configured_value: Any,
    *,
    key: str,
    repo_root: Path,
    config_dir: Path,
    workspace_root: Path,
) -> Path:
    canonical = (repo_root / _CANONICAL_PATHS[key]).resolve()
    if isinstance(configured_value, str) and configured_value.strip():
        configured_text = configured_value.strip()
        normalized = _normalize_path_text(configured_text)
        if normalized in _LEGACY_DEFAULTS.get(key, set()):
            return canonical
        return _resolve_path(
            configured_text,
            base_dir=_path_base_dir(
                configured_text,
                config_dir=config_dir,
                workspace_root=workspace_root,
            ),
        )
    return canonical


def _resolve_workspace_root(configured_value: Any, *, config_dir: Path, repo_root: Path) -> Path:
    if isinstance(configured_value, str) and configured_value.strip():
        return _resolve_path(configured_value.strip(), base_dir=config_dir)
    return repo_root.resolve()


def _resolve_optional_path(
    configured_value: Any,
    *,
    config_dir: Path,
    workspace_root: Path,
    default: Optional[Path] = None,
) -> Optional[str]:
    if isinstance(configured_value, str) and configured_value.strip():
        configured_text = configured_value.strip()
        candidate = _resolve_path(
            configured_text,
            base_dir=_path_base_dir(
                configured_text,
                config_dir=config_dir,
                workspace_root=workspace_root,
            ),
        )
        return str(candidate)
    if default is None:
        return None
    return str(default.resolve())


def resolve_qai_config(raw_config: Dict[str, Any], config_path: Path) -> Dict[str, Any]:
    config = deepcopy(raw_config)
    config_dir = config_path.resolve().parent
    repo_root = config_dir.parent

    paths = dict(config.get("paths") or {})
    config["paths"] = paths
    workspace_root = _resolve_workspace_root(
        paths.get("workspace_root"),
        config_dir=config_dir,
        repo_root=repo_root,
    )
    paths["workspace_root"] = str(workspace_root)
    for key in _CANONICAL_PATHS:
        if key == "workspace_root":
            continue
        paths[key] = str(
            _resolve_repo_path(
                paths.get(key),
                key=key,
                repo_root=repo_root,
                config_dir=config_dir,
                workspace_root=workspace_root,
            )
        )

    quantum = config.get("quantum")
    if isinstance(quantum, dict):
        quantum["config_file"] = _resolve_optional_path(
            quantum.get("config_file"),
            config_dir=config_dir,
            workspace_root=workspace_root,
            default=repo_root / "ai-projects" / "quantum-ml" / "config" / "quantum_config.yaml",
        )
        quantum["results_dir"] = _resolve_optional_path(
            quantum.get("results_dir"),
            config_dir=config_dir,
            workspace_root=workspace_root,
            default=repo_root / "ai-projects" / "quantum-ml" / "results",
        )

    chat = config.get("chat")
    if isinstance(chat, dict):
        providers = chat.get("providers")
        if isinstance(providers, dict):
            lora = providers.get("lora")
            if isinstance(lora, dict):
                lora["adapter_path"] = _resolve_optional_path(
                    lora.get("adapter_path"),
                    config_dir=config_dir,
                    workspace_root=workspace_root,
                    default=repo_root / "data_out" / "lora_training" / "lora_adapter",
                )

    training = config.get("training")
    if isinstance(training, dict):
        training["output_dir"] = _resolve_optional_path(
            training.get("output_dir"),
            config_dir=config_dir,
            workspace_root=workspace_root,
            default=repo_root / "data_out",
        )
        orchestrators = training.get("orchestrators")
        if isinstance(orchestrators, dict):
            autotrain = orchestrators.get("autotrain")
            if isinstance(autotrain, dict):
                autotrain["config_file"] = _resolve_optional_path(
                    autotrain.get("config_file"),
                    config_dir=config_dir,
                    workspace_root=workspace_root,
                    default=repo_root / "config" / "training" / "autotrain.yaml",
                )
                autotrain["status_file"] = _resolve_optional_path(
                    autotrain.get("status_file"),
                    config_dir=config_dir,
                    workspace_root=workspace_root,
                    default=repo_root / "data_out" / "autotrain" / "status.json",
                )
            quantum_autorun = orchestrators.get("quantum_autorun")
            if isinstance(quantum_autorun, dict):
                quantum_autorun["config_file"] = _resolve_optional_path(
                    quantum_autorun.get("config_file"),
                    config_dir=config_dir,
                    workspace_root=workspace_root,
                    default=repo_root / "config" / "quantum" / "quantum_autorun.yaml",
                )
                quantum_autorun["status_file"] = _resolve_optional_path(
                    quantum_autorun.get("status_file"),
                    config_dir=config_dir,
                    workspace_root=workspace_root,
                    default=repo_root / "data_out" / "quantum_autorun" / "status.json",
                )

    return config


def load_qai_config(config_path: Path) -> Dict[str, Any]:
    with config_path.open(encoding="utf-8") as f:
        raw_config = yaml.safe_load(f) or {}
    return resolve_qai_config(raw_config, config_path)
