import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from mount.training_integration import TrainingIntegration


def make_config(tmp_path: Path):
    workspace = tmp_path / "workspace"
    phi = tmp_path / "phi"
    scripts = tmp_path / "scripts"
    data_out = tmp_path / "data_out"

    (workspace / "datasets" / "quantum").mkdir(parents=True, exist_ok=True)
    (workspace / "datasets" / "chat").mkdir(parents=True, exist_ok=True)
    (workspace / "datasets" / "vision").mkdir(parents=True, exist_ok=True)
    (phi / "scripts").mkdir(parents=True, exist_ok=True)
    (phi / "lora").mkdir(parents=True, exist_ok=True)
    scripts.mkdir(parents=True, exist_ok=True)
    data_out.mkdir(parents=True, exist_ok=True)

    return {
        "paths": {
            "workspace_root": str(workspace),
            "phi_training": str(phi),
            "scripts": str(scripts),
            "data_out": str(data_out),
        },
        "training": {"enabled": True},
    }


def test_valid_dataset_runs_subprocess(tmp_path: Path):
    cfg = make_config(tmp_path)
    phi = Path(cfg["paths"]["phi_training"])
    train_script = phi / "scripts" / "train_lora.py"
    config_file = phi / "lora" / "lora.yaml"
    train_script.write_text("#!/usr/bin/env python\nprint('train')\n")
    config_file.write_text("dummy: true\n")

    ti = TrainingIntegration(cfg)
    ti.list_datasets = AsyncMock(return_value={"cat": ["DatasetA", "dataset_b"]})
    mock_result = SimpleNamespace(returncode=0, stdout="ok", stderr="")

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        result = asyncio.run(ti.train_lora("DATASET_B"))

    assert result["success"] is True
    assert result["dataset"] == "dataset_b"
    assert mock_run.call_count == 1
    call_args = mock_run.call_args[0][0]
    assert isinstance(call_args, list)
    assert call_args[0] == sys.executable
    assert str(train_script) in call_args
    assert "--dataset" in call_args
    assert call_args[call_args.index("--dataset") + 1] == "dataset_b"


def test_invalid_chars_rejected(tmp_path: Path):
    cfg = make_config(tmp_path)
    ti = TrainingIntegration(cfg)
    ti.list_datasets = AsyncMock(return_value={"cat": ["DatasetA", "dataset_b"]})

    with patch("subprocess.run") as mock_run:
        result = asyncio.run(ti.train_lora("../secret"))

    assert result["success"] is False
    assert result["error"] == "invalid_dataset"
    assert "disallowed characters" in result["message"]
    mock_run.assert_not_called()


def test_unknown_dataset_rejected(tmp_path: Path):
    cfg = make_config(tmp_path)
    ti = TrainingIntegration(cfg)
    ti.list_datasets = AsyncMock(return_value={"cat": ["DatasetA", "dataset_b"]})

    with patch("subprocess.run") as mock_run:
        result = asyncio.run(ti.train_lora("missing_dataset"))

    assert result["success"] is False
    assert result["error"] == "unknown_dataset"
    assert "Dataset not found" in result["message"]
    mock_run.assert_not_called()
