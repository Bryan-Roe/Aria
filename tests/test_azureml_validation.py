import importlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
AML_DIR = REPO_ROOT / ".azureml"


def test_azureml_validation_skip(monkeypatch, tmp_path):
    # Create a dummy spec so script attempts validation
    AML_DIR.mkdir(exist_ok=True)
    spec = AML_DIR / "job_dummy.yaml"
    spec.write_text("command: echo test\n", encoding="utf-8")
    mod = importlib.import_module("scripts.azureml_ci_validate")

    # Force az_available to False to simulate missing CLI
    monkeypatch.setattr(mod, "az_available", lambda: False)

    # validate() should skip gracefully and return True
    assert mod.validate(spec) is True
