import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from mount.training_integration import TrainingIntegration


def _make_config(tmp_path: Path):
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
    cfg = _make_config(tmp_path)
    phi = Path(cfg["paths"]["phi_training"])
    train_script = phi / "scripts" / "train_lora.py"
    train_script.write_text("print('train')")
    (phi / "lora" / "lora.yaml").write_text("dummy: true")

    ti = TrainingIntegration(cfg)
    mock_result = SimpleNamespace(returncode=0, stdout="ok", stderr="")

    with (
        patch.object(
            TrainingIntegration,
            "list_datasets",
            new=AsyncMock(return_value={"quantum": ["DatasetA", "dataset_b"]}),
        ),
        patch("subprocess.run", return_value=mock_result) as mock_run,
    ):
        result = asyncio.run(ti.train_lora("DATASET_B"))

    assert result["success"] is True
    assert result["dataset"] == "dataset_b"
    call_args = mock_run.call_args[0][0]
    assert call_args[0] == sys.executable
    assert str(train_script) in call_args
    assert "--dataset" in call_args
    assert "dataset_b" in call_args


def test_invalid_chars_rejected(tmp_path: Path):
    cfg = _make_config(tmp_path)
    phi = Path(cfg["paths"]["phi_training"])
    (phi / "scripts" / "train_lora.py").write_text("print('train')")
    (phi / "lora" / "lora.yaml").write_text("dummy: true")
    ti = TrainingIntegration(cfg)

    with (
        patch.object(
            TrainingIntegration,
            "list_datasets",
            new=AsyncMock(return_value={"quantum": ["DatasetA", "dataset_b"]}),
        ),
        patch("subprocess.run") as mock_run,
    ):
        result = asyncio.run(ti.train_lora("../secret"))

    assert result["success"] is False
    assert result["error"] == "invalid_dataset"
    assert mock_run.call_count == 0


def test_unknown_dataset_rejected(tmp_path: Path):
    cfg = _make_config(tmp_path)
    phi = Path(cfg["paths"]["phi_training"])
    (phi / "scripts" / "train_lora.py").write_text("print('train')")
    (phi / "lora" / "lora.yaml").write_text("dummy: true")
    ti = TrainingIntegration(cfg)

    with (
        patch.object(
            TrainingIntegration,
            "list_datasets",
            new=AsyncMock(return_value={"quantum": ["DatasetA", "dataset_b"]}),
        ),
        patch("subprocess.run") as mock_run,
    ):
        result = asyncio.run(ti.train_lora("missing_dataset"))

    assert result["success"] is False
    assert result["error"] == "unknown_dataset"
    assert mock_run.call_count == 0
