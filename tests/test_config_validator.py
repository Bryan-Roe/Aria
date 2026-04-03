"""Tests for ConfigValidator validation logic."""

import sys
import tempfile
from pathlib import Path

import pytest

# Add shared to path for direct module imports
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "shared"))

from config_validator import ValidationError  # noqa: E402
from config_validator import ConfigValidator, ValidationResult


class TestConfigValidator:
    """Test ConfigValidator class."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return ConfigValidator(REPO_ROOT)

    def test_valid_master_orchestrator(self, validator):
        """Test validation of master_orchestrator.yaml."""
        result = validator.validate_master()
        assert (
            result.valid
        ), f"Master config should be valid: {result.report(verbose=True)}"
        assert not result.errors

    def test_valid_autonomous_training(self, validator):
        """Test validation of autonomous_training.yaml."""
        result = validator.validate_autonomous_training()
        assert (
            result.valid
        ), f"Autonomous training config should be valid: {result.report(verbose=True)}"
        assert not result.errors

    def test_missing_file(self, validator):
        """Test validation of missing file."""
        result = validator.validate_file(Path("/nonexistent/config.yaml"))
        assert not result.valid
        assert any(e.rule == "file_exists" for e in result.errors)

    def test_invalid_yaml_syntax(self, validator):
        """Test validation of invalid YAML syntax."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: [yaml: syntax: here")
            f.flush()
            temp_path = Path(f.name)

        try:
            result = validator.validate_file(temp_path)
            assert not result.valid
            assert any(e.rule == "yaml_syntax" for e in result.errors)
        finally:
            temp_path.unlink()

    def test_missing_required_field_name(self, validator):
        """Test validation detects missing name field."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("orchestrators:\n  - script: test.py\n    enabled: true\n")
            f.flush()
            temp_path = Path(f.name)

        try:
            result = validator.validate_file(temp_path)
            assert not result.valid
            assert any(
                e.rule == "required_field" and "name" in e.message
                for e in result.errors
            )
        finally:
            temp_path.unlink()

    def test_missing_required_field_script(self, validator):
        """Test validation detects missing script field."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("orchestrators:\n  - name: test\n    enabled: true\n")
            f.flush()
            temp_path = Path(f.name)

        try:
            result = validator.validate_file(temp_path)
            assert not result.valid
            assert any(
                e.rule == "required_field" and "script" in e.message
                for e in result.errors
            )
        finally:
            temp_path.unlink()

    def test_script_not_found(self, validator):
        """Test validation detects non-existent script."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(
                "orchestrators:\n  - name: test\n    script: /nonexistent/test.py\n    enabled: true\n"
            )
            f.flush()
            temp_path = Path(f.name)

        try:
            result = validator.validate_file(temp_path)
            assert not result.valid
            assert any(e.rule == "script_path_exists" for e in result.errors)
        finally:
            temp_path.unlink()

    def test_invalid_cron_pattern(self, validator):
        """Test validation detects invalid cron pattern."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(
                "orchestrators:\n  - name: test\n    script: scripts/autotrain.py\n    enabled: true\n    schedule: invalid_cron\n"
            )
            f.flush()
            temp_path = Path(f.name)

        try:
            result = validator.validate_file(temp_path)
            # Should have a warning but pass (cron is optional)
            assert any(e.rule == "schedule_pattern" for e in result.warnings)
        finally:
            temp_path.unlink()

    def test_valid_cron_pattern(self, validator):
        """Test validation accepts valid cron pattern."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(
                "orchestrators:\n  - name: test\n    script: scripts/autotrain.py\n    enabled: true\n    schedule: '0 2 * * *'\n"
            )
            f.flush()
            temp_path = Path(f.name)

        try:
            result = validator.validate_file(temp_path)
            assert result.valid
            assert not any(e.rule == "schedule_pattern" for e in result.warnings)
        finally:
            temp_path.unlink()

    def test_continuous_schedule(self, validator):
        """Test validation accepts 'continuous' as schedule."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(
                "orchestrators:\n  - name: test\n    script: scripts/autotrain.py\n    enabled: true\n    schedule: continuous\n"
            )
            f.flush()
            temp_path = Path(f.name)

        try:
            result = validator.validate_file(temp_path)
            assert result.valid
            # No warning about schedule pattern
            assert not any(e.rule == "schedule_pattern" for e in result.warnings)
        finally:
            temp_path.unlink()

    def test_undefined_dependency(self, validator):
        """Test validation detects undefined dependencies."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(
                """orchestrators:
  - name: test1
    script: scripts/autotrain.py
    enabled: true
    dependencies: [undefined_orch]
"""
            )
            f.flush()
            temp_path = Path(f.name)

        try:
            result = validator.validate_file(temp_path)
            assert not result.valid
            assert any(e.rule == "dependency_undefined" for e in result.errors)
        finally:
            temp_path.unlink()

    def test_circular_dependency(self, validator):
        """Test validation detects circular dependencies."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(
                """orchestrators:
  - name: test1
    script: scripts/autotrain.py
    enabled: true
    dependencies: [test2]
  - name: test2
    script: scripts/quantum_autorun.py
    enabled: true
    dependencies: [test1]
"""
            )
            f.flush()
            temp_path = Path(f.name)

        try:
            result = validator.validate_file(temp_path)
            assert not result.valid
            assert any(e.rule == "circular_dependency" for e in result.errors)
        finally:
            temp_path.unlink()

    def test_workflow_references_undefined_orchestrator(self, validator):
        """Test validation detects undefined orchestrator references in workflows."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(
                """orchestrators:
  - name: test1
    script: scripts/autotrain.py
    enabled: true

workflows:
  - name: wf1
    enabled: true
    orchestrators: [test1, undefined_orch]
"""
            )
            f.flush()
            temp_path = Path(f.name)

        try:
            result = validator.validate_file(temp_path)
            assert not result.valid
            assert any(e.rule == "orchestrator_reference" for e in result.errors)
        finally:
            temp_path.unlink()

    def test_invalid_priority_type(self, validator):
        """Test validation detects invalid priority type."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(
                """orchestrators:
  - name: test1
    script: scripts/autotrain.py
    enabled: true
    priority: "not_a_number"
"""
            )
            f.flush()
            temp_path = Path(f.name)

        try:
            result = validator.validate_file(temp_path)
            assert not result.valid
            assert any(
                e.rule == "field_type" and "priority" in e.message
                for e in result.errors
            )
        finally:
            temp_path.unlink()

    def test_validation_result_summary(self):
        """Test ValidationResult.summary() method."""
        result = ValidationResult(config_path=Path("test.yaml"), valid=True)
        assert "✅ VALID" in result.summary()

        result.errors.append(ValidationError(rule="test", message="test error"))
        result.valid = False
        assert "❌ INVALID" in result.summary()
        assert "1 errors" in result.summary()


class TestConfigValidatorIntegration:
    """Integration tests for config validation."""

    def test_pre_flight_validation_function(self):
        """Test validate_configs_before_daemon function."""
        from config_validator import validate_configs_before_daemon

        # Should not exit (exit_on_error=False)
        all_valid, results = validate_configs_before_daemon(
            repo_root=REPO_ROOT, exit_on_error=False, verbose=False
        )

        assert len(results) >= 2  # At least master + autonomous_training
        # Current configs should be valid
        assert all(r.valid for r in results)

    def test_config_validator_specific_file(self, capsys):
        """Test ConfigValidator on specific file."""
        validator = ConfigValidator(REPO_ROOT)

        # Validate master orchestrator
        result = validator.validate_master()
        assert result.valid

        # Check report output
        report = result.report(verbose=False)
        assert "✅ VALID" in report or "Config:" in report


if __name__ == "__main__":
    pytest.main([__file__, "-xvs"])
