import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_autotrain_dry_run_smoke(tmp_path):
    """Smoke test: the autotrain script should validate the default config in dry-run mode."""
    script = REPO_ROOT / "scripts" / "autotrain.py"
    cfg = REPO_ROOT / "config" / "training" / "autotrain.yaml"
    assert script.exists(), "autotrain.py missing"
    assert cfg.exists(), "autotrain.yaml missing"

    # Run dry-run for the named job
    proc = subprocess.run(
        ["python", str(script), "--config", str(cfg), "--job", "phi35_mixed_chat", "--dry-run"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr

    # The script prints a JSON block per job result; verify at least one JSON-looking structure
    stdout = proc.stdout.strip()
    assert "phi35_mixed_chat" in stdout

    # Status file should be created
    status_path = REPO_ROOT / "data_out" / "autotrain" / "status.json"
    assert status_path.exists(), "status.json not created"
    data = json.loads(status_path.read_text(encoding="utf-8"))
    assert isinstance(data, dict) and "jobs" in data
    assert any(j.get("name") == "phi35_mixed_chat" for j in data.get("jobs", []))
