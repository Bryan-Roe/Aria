import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def write_jsonl(path: Path, items):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it) + "\n")


def test_evaluate_local_model_smoke(tmp_path: Path):
    dataset = tmp_path / "local_ds.jsonl"
    data = [
        {"input": "Hello world", "expected": "echo: Hello world"},
        {"input": "Goodbye", "expected": "echo: Goodbye"},
    ]
    write_jsonl(dataset, data)

    out_dir = tmp_path / "out_local"
    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "evaluate_local_model.py"),
            "--dataset",
            str(dataset),
            "--max-samples",
            "10",
            "--metric",
            "accuracy",
            "--metric",
            "determinism",
            "--output-format",
            "json",
            "--save-dir",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, proc.stderr
    results_file = out_dir / "results.json"
    assert results_file.exists()
    data = json.loads(results_file.read_text(encoding="utf-8"))
    assert "summary" in data
    assert data["summary"]["accuracy"] == 1.0


def test_evaluate_quantum_model_smoke(tmp_path: Path):
    # small dataset with labels
    ds = tmp_path / "ds.jsonl"
    write_jsonl(ds, [{"label": "1"}, {"label": "0"}, {"label": "1"}])

    # model file with predictions aligned with dataset
    model = tmp_path / "qm.json"
    model.write_text(json.dumps({"predictions": ["1", "0", "1"]}), encoding="utf-8")

    out_dir = tmp_path / "out_qm"
    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "evaluate_quantum_model.py"),
            "--dataset",
            str(ds),
            "--model",
            str(model),
            "--metric",
            "accuracy",
            "--save-dir",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, proc.stderr
    res = json.loads((out_dir / "results.json").read_text(encoding="utf-8"))
    assert res.get("summary", {}).get("accuracy") == 1.0


def test_evaluation_autorun_dry_run_uses_config(tmp_path: Path):
    # Use the provided repo config path for evaluation_autorun
    script = REPO_ROOT / "scripts" / "evaluation_autorun.py"
    cfg = REPO_ROOT / "config" / "evaluation" / "evaluation_autorun.yaml"
    assert script.exists()
    assert cfg.exists()

    proc = subprocess.run(
        [
            sys.executable,
            str(script),
            "--config",
            str(cfg),
            "--dry-run",
        ],
        capture_output=True,
        text=True,
    )

    # dry-run should exit 0 and print JSON blocks / validated info
    assert proc.returncode == 0, proc.stderr
    assert "Job" in proc.stdout or "validated" in proc.stdout
