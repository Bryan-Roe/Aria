"""Configuration validation for orchestrators.

Provides centralized validation of YAML configs before daemon startup.
Validates YAML syntax, required fields, script paths, schedule patterns, and dependencies.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    import yaml
except ImportError:
    raise SystemExit(
        "pyyaml required for config validation: pip install pyyaml"
    ) from None


@dataclass
class ValidationError:
    """Single validation error."""

    rule: str
    message: str
    severity: str = "error"  # error|warning
    # Path in config obj, e.g., "orchestrators[0].name"
    path: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of configuration validation."""

    config_path: Path
    valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)

    @property
    def has_critical_errors(self) -> bool:
        """Check if there are critical (non-warning) errors."""
        return any(e.severity == "error" for e in self.errors)

    def summary(self) -> str:
        """Return human-readable summary."""
        error_count = len(self.errors)
        warning_count = len(self.warnings)
        status = "✅ VALID" if self.valid else "❌ INVALID"
        msg = f"{status} | {error_count} errors, {warning_count} warnings"
        return msg

    def report(self, verbose: bool = False) -> str:
        """Generate detailed report."""
        lines = [
            f"\n{self.summary()}",
            f"Config: {self.config_path}",
        ]

        if verbose or self.errors:
            lines.append("\nErrors:")
            for err in self.errors:
                loc = f" [{err.path}]" if err.path else ""
                lines.append(f"  - {err.rule}:{loc} {err.message}")

        if verbose or self.warnings:
            lines.append("\nWarnings:")
            for warn in self.warnings:
                loc = f" [{warn.path}]" if warn.path else ""
                lines.append(f"  - {warn.rule}:{loc} {warn.message}")

        return "\n".join(lines)


class ConfigValidator:
    """Validates orchestrator YAML configurations."""

    # Cron schedule pattern (5 or 6 fields)
    CRON_PATTERN = re.compile(
        r"^(\*|[0-9]|1[0-9]|2[0-3]|[0-9]-[0-9]|[0-9],[0-9]|[*/0-9,-]+)\s+"  # min
        r"(\*|[0-9]|1[0-9]|2[0-3]|[0-9]-[0-9]|[0-9],[0-9]|[*/0-9,-]+)\s+"  # hour
        r"(\*|[0-9]|[12][0-9]|3[0-1]|[0-9]-[0-9]|[0-9],[0-9]|[*/0-9,-]+)\s+"  # day
        r"(\*|[0-9]|1[0-2]|[0-9]-[0-9]|[0-9],[0-9]|[*/0-9,-]+)\s+"  # month
        r"(\*|[0-7]|[0-9]-[0-9]|[0-9],[0-9]|[*/0-9,-]+)$"  # dow
    )

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = repo_root or Path(__file__).resolve().parents[1]

    def validate_file(self, config_path: Path) -> ValidationResult:
        """Validate a single YAML config file."""
        result = ValidationResult(config_path=config_path, valid=True)

        # 1. Check file exists
        if not config_path.exists():
            result.errors.append(
                ValidationError(
                    rule="file_exists",
                    message=f"Config file not found: {config_path}",
                    severity="error",
                )
            )
            result.valid = False
            return result

        # 2. Parse YAML
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            result.errors.append(
                ValidationError(
                    rule="yaml_syntax",
                    message=f"YAML parse error: {e}",
                    severity="error",
                )
            )
            result.valid = False
            return result
        except Exception as e:
            result.errors.append(
                ValidationError(
                    rule="file_read",
                    message=f"Failed to read file: {e}",
                    severity="error",
                )
            )
            result.valid = False
            return result

        # 3. Validate orchestrators if present
        orchestrators = config.get("orchestrators", [])
        if isinstance(orchestrators, list):
            self._validate_orchestrators(orchestrators, result)

        # 4. Validate workflows if present
        workflows = config.get("workflows", [])
        if isinstance(workflows, list):
            self._validate_workflows(workflows, result, orchestrators)

        result.valid = not result.has_critical_errors
        return result

    def _validate_orchestrators(
        self, orchestrators: List[Dict[str, Any]], result: ValidationResult
    ):
        """Validate orchestrator list."""
        defined_names: Set[str] = set()

        for idx, orch in enumerate(orchestrators):
            if not isinstance(orch, dict):
                result.errors.append(
                    ValidationError(
                        rule="orchestrator_type",
                        message=f"Orchestrator must be a dict, got {type(orch).__name__}",
                        path=f"orchestrators[{idx}]",
                        severity="error",
                    )
                )
                continue

            path_prefix = f"orchestrators[{idx}]"

            # Required fields
            name = orch.get("name")
            if not name:
                result.errors.append(
                    ValidationError(
                        rule="required_field",
                        message="Missing required field: name",
                        path=f"{path_prefix}.name",
                        severity="error",
                    )
                )
                continue

            if not isinstance(name, str):
                result.errors.append(
                    ValidationError(
                        rule="field_type",
                        message=f"name must be str, got {type(name).__name__}",
                        path=f"{path_prefix}.name",
                        severity="error",
                    )
                )
                continue

            defined_names.add(name)

            script = orch.get("script")
            if not script:
                result.errors.append(
                    ValidationError(
                        rule="required_field",
                        message="Missing required field: script",
                        path=f"{path_prefix}.script",
                        severity="error",
                    )
                )
                continue

            if not isinstance(script, str):
                result.errors.append(
                    ValidationError(
                        rule="field_type",
                        message=f"script must be str, got {type(script).__name__}",
                        path=f"{path_prefix}.script",
                        severity="error",
                    )
                )
                continue

            # Validate script path
            script_path = self.repo_root / script
            if not script_path.exists():
                result.errors.append(
                    ValidationError(
                        rule="script_path_exists",
                        message=f"Script not found: {script}",
                        path=f"{path_prefix}.script",
                        severity="error",
                    )
                )

            # Validate schedule pattern
            schedule = orch.get("schedule")
            if schedule:
                if not isinstance(schedule, str):
                    result.errors.append(
                        ValidationError(
                            rule="field_type",
                            message=f"schedule must be str, got {type(schedule).__name__}",
                            path=f"{path_prefix}.schedule",
                            severity="error",
                        )
                    )
                elif schedule != "continuous" and not self.CRON_PATTERN.match(schedule):
                    result.warnings.append(
                        ValidationError(
                            rule="schedule_pattern",
                            message=f"Invalid cron pattern (or use 'continuous'): {schedule}",
                            path=f"{path_prefix}.schedule",
                            severity="warning",
                        )
                    )

            # Validate timeout
            timeout = orch.get("timeout_minutes")
            if timeout is not None:
                if not isinstance(timeout, (int, float)):
                    result.errors.append(
                        ValidationError(
                            rule="field_type",
                            message=f"timeout_minutes must be number, got {type(timeout).__name__}",
                            path=f"{path_prefix}.timeout_minutes",
                            severity="error",
                        )
                    )
                elif timeout < 0:
                    result.warnings.append(
                        ValidationError(
                            rule="timeout_range",
                            message="timeout_minutes < 0 means no timeout",
                            path=f"{path_prefix}.timeout_minutes",
                            severity="warning",
                        )
                    )

            # Validate priority
            priority = orch.get("priority")
            if priority is not None and not isinstance(priority, int):
                result.errors.append(
                    ValidationError(
                        rule="field_type",
                        message=f"priority must be int, got {type(priority).__name__}",
                        path=f"{path_prefix}.priority",
                        severity="error",
                    )
                )

            # Dependencies will be checked in dependency validation

        # Check for dependency chain issues
        self._validate_dependencies(orchestrators, defined_names, result)

    def _validate_dependencies(
        self,
        orchestrators: List[Dict[str, Any]],
        defined_names: Set[str],
        result: ValidationResult,
    ):
        """Validate orchestrator dependencies (no circular refs, all exist)."""
        for idx, orch in enumerate(orchestrators):
            if not isinstance(orch, dict) or "name" not in orch:
                continue

            name = orch["name"]
            deps = orch.get("dependencies", [])

            if not isinstance(deps, list):
                result.errors.append(
                    ValidationError(
                        rule="field_type",
                        message=f"dependencies must be list, got {type(deps).__name__}",
                        path=f"orchestrators[{idx}].dependencies",
                        severity="error",
                    )
                )
                continue

            # Check all deps are defined
            for dep in deps:
                if dep not in defined_names:
                    result.errors.append(
                        ValidationError(
                            rule="dependency_undefined",
                            message=f"Dependency '{dep}' is not defined in orchestrators",
                            path=f"orchestrators[{idx}].dependencies",
                            severity="error",
                        )
                    )

            # Check for circular deps
            visited: Set[str] = set()
            if self._has_circular_dep(name, orchestrators, visited):
                result.errors.append(
                    ValidationError(
                        rule="circular_dependency",
                        message=f"Circular dependency detected involving {name}",
                        path=f"orchestrators[{idx}]",
                        severity="error",
                    )
                )

    def _has_circular_dep(
        self,
        orch_name: str,
        orchestrators: List[Dict[str, Any]],
        visited: Set[str],
        rec_stack: Optional[Set[str]] = None,
    ) -> bool:
        """Check if orchestrator has circular dependency."""
        if rec_stack is None:
            rec_stack = set()

        if orch_name in rec_stack:
            return True

        if orch_name in visited:
            return False

        visited.add(orch_name)
        rec_stack.add(orch_name)

        # Find orchestrator and check deps
        for orch in orchestrators:
            if orch.get("name") == orch_name:
                for dep in orch.get("dependencies", []):
                    if self._has_circular_dep(dep, orchestrators, visited, rec_stack):
                        return True
                break

        rec_stack.discard(orch_name)
        return False

    def _validate_workflows(
        self,
        workflows: List[Dict[str, Any]],
        result: ValidationResult,
        orchestrators: List[Dict[str, Any]],
    ):
        """Validate workflow list."""
        defined_orch_names = {
            o.get("name") for o in orchestrators if isinstance(o, dict) and "name" in o
        }

        for idx, wf in enumerate(workflows):
            if not isinstance(wf, dict):
                result.errors.append(
                    ValidationError(
                        rule="workflow_type",
                        message=f"Workflow must be a dict, got {type(wf).__name__}",
                        path=f"workflows[{idx}]",
                        severity="error",
                    )
                )
                continue

            path_prefix = f"workflows[{idx}]"

            # Required fields
            name = wf.get("name")
            if not name:
                result.errors.append(
                    ValidationError(
                        rule="required_field",
                        message="Missing required field: name",
                        path=f"{path_prefix}.name",
                        severity="error",
                    )
                )
                continue

            # Check orchestrators list
            orch_list = wf.get("orchestrators", [])
            if not isinstance(orch_list, list):
                result.errors.append(
                    ValidationError(
                        rule="field_type",
                        message=f"orchestrators must be list, got {type(orch_list).__name__}",
                        path=f"{path_prefix}.orchestrators",
                        severity="error",
                    )
                )
            else:
                for orch_ref in orch_list:
                    if orch_ref not in defined_orch_names:
                        result.errors.append(
                            ValidationError(
                                rule="orchestrator_reference",
                                message=f"Orchestrator '{orch_ref}' not defined",
                                path=f"{path_prefix}.orchestrators",
                                severity="error",
                            )
                        )

    def validate_master(self, config_path: Optional[Path] = None) -> ValidationResult:
        """Validate master_orchestrator.yaml specifically."""
        if config_path is None:
            config_path = self.repo_root / "config" / "master_orchestrator.yaml"
        return self.validate_file(config_path)

    def validate_autonomous_training(
        self, config_path: Optional[Path] = None
    ) -> ValidationResult:
        """Validate autonomous_training.yaml specifically."""
        if config_path is None:
            config_path = self.repo_root / "config" / "autonomous_training.yaml"
        return self.validate_file(config_path)


def validate_configs_before_daemon(
    repo_root: Optional[Path] = None, exit_on_error: bool = True, verbose: bool = False
) -> Tuple[bool, List[ValidationResult]]:
    """Validate all critical configs before starting daemon.

    Returns:
        (all_valid, [result1, result2, ...])
    """
    validator = ConfigValidator(repo_root)
    results = []

    # Key configs to validate
    configs_to_check = [
        (
            "master_orchestrator",
            (
                repo_root / "config" / "master_orchestrator.yaml"
                if repo_root
                else Path("config/master_orchestrator.yaml")
            ),
        ),
        (
            "autonomous_training",
            (
                repo_root / "config" / "autonomous_training.yaml"
                if repo_root
                else Path("config/autonomous_training.yaml")
            ),
        ),
    ]

    print("\n🔍 Validating orchestrator configurations...")
    for name, config_path in configs_to_check:
        result = validator.validate_file(config_path)
        results.append(result)
        print(result.report(verbose=verbose))

    all_valid = all(r.valid for r in results)

    if not all_valid and exit_on_error:
        print("\n❌ Configuration validation failed. Cannot start daemon.")
        sys.exit(1)

    if all_valid:
        print("\n✅ All configurations valid. Safe to start daemon.")

    return all_valid, results


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Validate orchestrator configurations")
    ap.add_argument("--config", help="Config file to validate")
    ap.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    ap.add_argument("--check-all", action="store_true", help="Check all known configs")
    args = ap.parse_args()

    validator = ConfigValidator()

    if args.check_all:
        _, results = validate_configs_before_daemon(
            verbose=args.verbose, exit_on_error=False
        )
        sys.exit(0 if all(r.valid for r in results) else 1)
    elif args.config:
        result = validator.validate_file(Path(args.config))
        print(result.report(verbose=args.verbose))
        sys.exit(0 if result.valid else 1)
    else:
        ap.print_help()
