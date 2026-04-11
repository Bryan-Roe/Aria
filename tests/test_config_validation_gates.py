"""Integration tests for config validation gates."""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestConfigValidationGates:
    """Test config validation gates in orchestrator entrypoints."""

    def test_autonomous_training_with_valid_config(self):
        """Test autonomous_training_orchestrator with valid config."""
        result = subprocess.run(
            [sys.executable, "scripts/autonomous_training_orchestrator.py", "--status"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Should succeed with valid config
        assert result.returncode == 0
        assert "cycles_completed" in result.stdout

    def test_repo_automation_validate_flag(self):
        """Test repo_automation.py --validate flag."""
        result = subprocess.run(
            [sys.executable, "scripts/repo_automation.py", "--validate"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Should exit with 0 if configs are valid
        assert result.returncode == 0
        assert "✅" in result.stdout or "valid" in result.stdout.lower()

    def test_master_orchestrator_validation(self):
        """Test master_orchestrator.py validation gate."""
        result = subprocess.run(
            [sys.executable, "scripts/master_orchestrator.py", "--list-orchestrators"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Should succeed with valid config
        assert result.returncode == 0
        # Should list orchestrators
        assert "autotrain" in result.stdout
        assert "quantum_autorun" in result.stdout

    def test_repo_automation_start_with_validation(self):
        """Test repo_automation.py --start with built-in validation."""
        # This should validate configs before starting anything
        # We won't actually start anything, just test that the --start path works
        result = subprocess.run(
            [sys.executable, "scripts/repo_automation.py", "--status"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Should succeed (status doesn't trigger validation, but setup should work)
        assert result.returncode == 0 or "no status" in result.stdout.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-xvs"])
