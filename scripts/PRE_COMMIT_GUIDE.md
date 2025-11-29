# Pre-Commit Validation Script for QAI

## Purpose

Automated checks to run before committing code changes, ensuring code quality, test coverage, and documentation consistency.

## Quick Usage

```powershell
# Run all checks
python .\scripts\pre_commit_check.py

# Run specific checks
python .\scripts\pre_commit_check.py --checks tests,lint

# Skip specific checks
python .\scripts\pre_commit_check.py --skip docs
```

## Checks Performed

### 1. Unit Tests (`tests`)
- Runs pytest on all test files
- Requires: All tests passing
- Fails if: Any test fails or coverage below threshold

### 2. Type Checking (`types`)
- Validates Python type hints (if mypy installed)
- Checks: `function_app.py`, `shared/`, `scripts/`
- Fails if: Type errors found

### 3. Linting (`lint`)
- Code style and potential bugs
- Uses: ruff (if available), fallback to pycodestyle
- Warns on: Long lines, unused imports, complexity

### 4. Documentation (`docs`)
- README.md up-to-date
- All new scripts have docstrings
- CHANGELOG updated (if exists)

### 5. Security (`security`)
- No hardcoded secrets (API keys, passwords)
- Requirements.txt has no known vulnerabilities
- `.env` not committed

### 6. Git Hygiene (`git`)
- No large files (>10MB)
- No `__pycache__` or venv in staging
- Branch name follows convention

## Installation

```powershell
# Optional: Install code quality tools
pip install ruff mypy pytest-cov

# Make script executable (if on Linux/Mac)
chmod +x scripts/pre_commit_check.py
```

## CI/CD Integration

This script can be integrated into GitHub Actions:

```yaml
name: Pre-Commit Checks
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pip install ruff mypy pytest-cov
      - run: python scripts/pre_commit_check.py
```

## Configuration

Create `.pre-commit-config.yaml` to customize:

```yaml
checks:
  tests:
    enabled: true
    coverage_threshold: 80
  
  lint:
    enabled: true
    max_line_length: 120
    ignore:
      - E501  # line too long (handled by formatter)
  
  security:
    enabled: true
    exclude_patterns:
      - test_*.py  # Test files may have dummy secrets
  
  docs:
    enabled: true
    require_changelog: false  # Set true if using CHANGELOG.md
```

## Exit Codes

- `0`: All checks passed
- `1`: One or more checks failed
- `2`: Configuration error or missing dependencies

## Example Output

```
═══════════════════════════════════════════════════════════════
QAI PRE-COMMIT VALIDATION
═══════════════════════════════════════════════════════════════

[1/6] Running unit tests...
  ✓ 45 tests passed in 2.3s
  ✓ Coverage: 87% (threshold: 80%)

[2/6] Type checking...
  ✓ No type errors found

[3/6] Linting code...
  ⚠ Warning: 3 files exceed line length limit
  ✓ No critical issues

[4/6] Checking documentation...
  ✓ All public functions have docstrings
  ✓ README.md is up-to-date

[5/6] Security scan...
  ✓ No hardcoded secrets detected
  ✓ No vulnerable dependencies

[6/6] Git hygiene...
  ✓ No large files in staging
  ✓ No unwanted files (.pyc, venv)

═══════════════════════════════════════════════════════════════
RESULT: All checks passed ✓
═══════════════════════════════════════════════════════════════
```

## Troubleshooting

### "pytest not found"
```powershell
pip install pytest pytest-asyncio
```

### "ruff not found"
```powershell
pip install ruff
# Or skip linting:
python .\scripts\pre_commit_check.py --skip lint
```

### "Tests failing locally but pass in CI"
- Check Python version matches CI (3.11)
- Ensure all dependencies installed: `pip install -r requirements.txt`
- Check for environment-specific issues (paths, temp files)

### "Type checking too strict"
- Configure mypy with `mypy.ini`:
```ini
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = False
ignore_missing_imports = True
```

## Best Practices

1. **Run before every commit**: Catches issues early
2. **Fix warnings incrementally**: Don't ignore linter output
3. **Keep tests fast**: Pre-commit checks should run in <30s
4. **Update thresholds**: Increase coverage requirements over time
5. **Document exceptions**: If skipping a check, explain why

## See Also

- [Testing Guide](../tests/README.md)
- [Contributing Guidelines](../CONTRIBUTING.md)
- [Code Style Guide](../STYLE_GUIDE.md)
