from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
AML_DIR = REPO_ROOT / ".azureml"


def test_job_yaml_schema_basic():
    if not AML_DIR.exists():
        pytest.skip("No .azureml directory present")
    specs = sorted(AML_DIR.glob("job_*.yaml"))
    if not specs:
        pytest.skip("No job specs to validate")
    latest = specs[-1]
    with latest.open("r", encoding="utf-8") as f:
        # Ignore potential leading $schema: line by safe_load which handles it
        data = yaml.safe_load(f)
    # Basic required fields
    for key in ["command", "code", "experiment_name", "compute", "environment"]:
        assert key in data, f"Missing key in job spec: {key}"
    env = data["environment"]
    for key in ["image", "conda_file", "name"]:
        assert key in env, f"Environment missing {key}"
    assert (
        data.get("resources", {}).get("instance_count") == 1
    ), "Instance count should be 1"
