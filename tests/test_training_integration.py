import asyncio
import subprocess
import sys
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch

import pytest

from mount.training_integration import TrainingIntegration


def make_config(tmp_path: Path):
    workspace = tmp_path / "workspace"
    phi = tmp_path / "phi"
    scripts = tmp_path / "scripts"
    data_out = tmp_path / "data_out"

    # create directories
    (workspace / "datasets" / "quantum").mkdir(parents=True, exist_ok=True)
    (workspace / "datasets" / "chat" ).mkdir(parents=True, exist_ok=True)
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

def test_list_datasets(tmp_path: Path):
    cfg = make_config(tmp_path)
    # create some dataset files/dirs
    workspace = Path(cfg["paths"]["workspace_root"])
    (workspace / "datasets" / "quantum" / "q1.csv").write_text("a,b,c")
    (workspace / "datasets" / "chat" / "chat1").mkdir()
    (workspace / "datasets" / "vision" / "vis1").mkdir()

    ti = TrainingIntegration(cfg)
    datasets = asyncio.run(ti.list_datasets())

    assert "q1" in datasets["quantum"]
    assert "chat1" in datasets["chat"]
    assert "vis1" in datasets["vision"]

def test_train_lora_invalid_dataset(tmp_path: Path):
    cfg = make_config(tmp_path)
    # no datasets created, so any dataset is invalid
    ti = TrainingIntegration(cfg)

    result = asyncio.run(ti.train_lora("nonexistent"))
    assert result["success"] is False
    assert result["error"] == "unknown_dataset"

def test_train_lora_reject_path_like(tmp_path: Path):
    cfg = make_config(tmp_path)
    # create a valid dataset name to ensure the check for path-like happens first
    workspace = Path(cfg["paths"]["workspace_root"])
    (workspace / "datasets" / "quantum" / "good.csv").write_text("data")

    ti = TrainingIntegration(cfg)
    # provide a path-like dataset
    result = asyncio.run(ti.train_lora("../etc/passwd"))
    assert result["success"] is False
    assert result["error"] == "invalid_dataset"

def test_train_lora_calls_subprocess(tmp_path: Path):
    cfg = make_config(tmp_path)
    workspace = Path(cfg["paths"]["workspace_root"])
    phi = Path(cfg["paths"]["phi_training"])

    # Create a dataset and training script/config
    (workspace / "datasets" / "quantum" / "dset.csv").write_text("1,2,3")
    train_script = phi / "scripts" / "train_lora.py"
    train_script.write_text("#!/usr/bin/env python\nprint('train')\n")
    config_file = phi / "lora" / "lora.yaml"
    config_file.write_text("dummy: true")

    ti = TrainingIntegration(cfg)

    mock_result = SimpleNamespace(returncode=0, stdout="ok", stderr="")

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        res = asyncio.run(ti.train_lora("dset", max_train_samples=10, max_eval_samples=2, epochs=3))

    assert res["success"] is True
    assert res["dataset"] == "dset"
    assert res["epochs"] == 3

    # verify subprocess called with expected command list
    assert mock_run.call_count == 1
    call_args = mock_run.call_args[0][0]
    assert call_args[0] == sys.executable
    assert str(train_script) in call_args
    assert "--dataset" in call_args
    assert "dset" in call_args

    # ensure cwd is phi path
    kwargs = mock_run.call_args[1]
    assert kwargs.get("cwd") == str(phi)
    assert "env" in kwargs

def test_train_lora_timeout_handling(tmp_path: Path):
    cfg = make_config(tmp_path)
    workspace = Path(cfg["paths"]["workspace_root"])
    phi = Path(cfg["paths"]["phi_training"])

    (workspace / "datasets" / "quantum" / "slow.csv").write_text("x")
    train_script = phi / "scripts" / "train_lora.py"
    train_script.write_text("print('slow')")
    config_file = phi / "lora" / "lora.yaml"
    config_file.write_text("dummy: true")

    ti = TrainingIntegration(cfg)

    def raise_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=1)

    with patch("subprocess.run", side_effect=raise_timeout):
        res = asyncio.run(ti.train_lora("slow"))

    assert res["success"] is False
    assert res["error"] == "training_timeout"
