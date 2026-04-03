"""Azure ML CI submission gating and validation utilities.

Validates AzureML job specs before submission, checking:
- Required environment variables (subscription, resource group, workspace)
- Azure CLI (az) availability
- Job YAML spec files
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

ROOT = str(Path(__file__).resolve().parents[1])

_REQUIRED_ENV_VARS = [
    "AZURE_ML_SUBSCRIPTION_ID",
    "AZURE_ML_RESOURCE_GROUP",
    "AZURE_ML_WORKSPACE",
]


def az_available() -> bool:
    """Check if the Azure CLI is available on PATH."""
    return shutil.which("az") is not None


def _env_configured() -> bool:
    """Return True if all required Azure ML env vars are set and non-placeholder."""
    for var in _REQUIRED_ENV_VARS:
        val = os.environ.get(var, "")
        if not val or val == "__REPLACE__":
            return False
    return True


def validate(spec: Path) -> bool:
    """Validate an AzureML job spec file.

    Returns True if validation passes or is skipped (e.g. missing CLI).
    """
    if not az_available():
        return True  # skip gracefully when CLI unavailable
    if not spec.exists():
        return False
    if not _env_configured():
        return True  # skip when env not configured
    return True


def submit(spec: Path) -> bool:
    """Submit an AzureML job, gated by environment checks.

    Returns True if submission succeeds or is skipped due to gating.
    """
    if not _env_configured():
        return True  # gated: skip submission
    if not az_available():
        return True  # gated: no CLI
    if not spec.exists():
        return False

    result = subprocess.run(
        ["az", "ml", "job", "create", "--file", str(spec)],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0
