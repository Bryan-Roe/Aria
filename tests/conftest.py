"""Pytest configuration for QAI test suite.

This conftest ensures that the scripts package is importable during tests.
"""
import sys
from pathlib import Path

# Add project root to Python path for importing scripts
REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# === ensure test dependencies ===
# When the virtual environment isn't activated properly, imports can fail
# during collection. To make the repo "just work" for QAI developers we
# attempt to install a handful of common test libraries on-the-fly.
import pkgutil
import subprocess

REQUIRED_MODULES = [
    "yaml",     # PyYAML for YAML parsing tests
    "flask",    # web app security/integration tests
    "requests", # HTTP clients used by integration tests
    "PIL",      # pillow Image for vision tests
    # the QAI workspace tests need torch and pennylane; installing here
    "torch",    # PyTorch for model-based tests
    "pennylane",# PennyLane quantum ML framework
]

for mod in REQUIRED_MODULES:
    try:
        if pkgutil.find_loader(mod) is None:  # type: ignore[attr-defined]
            print(f"[conftest] installing missing module {mod}")
            subprocess.run([sys.executable, "-m", "pip", "install", mod], check=True)
    except Exception as exc:  # pragma: no cover
        print(f"[conftest] failed to install {mod}: {exc}")
