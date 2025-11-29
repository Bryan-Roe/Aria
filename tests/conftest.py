"""Pytest configuration for QAI test suite.

This conftest ensures that the scripts package is importable during tests.
"""
import sys
from pathlib import Path

# Add project root to Python path for importing scripts
REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
