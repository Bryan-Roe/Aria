# VS Code Testing Guide

## Overview
This workspace is configured for seamless test execution using VS Code's native Testing UI. All tests are discoverable, debuggable, and organized by test type.

## Quick Start

### 1. Open Test Explorer
- Click the beaker icon (🧪) in the Activity Bar (left sidebar)
- Or press `Ctrl+Shift+T` to open the Testing view
- All tests will be automatically discovered from the `tests/` directory

### 2. Run Tests
**Via Test Explorer:**
- Click the play button (▶️) next to any test, suite, or file
- Right-click for more options (Run, Debug, Run with Coverage)
- Use the refresh button (🔄) to rediscover tests

**Via Command Palette (`Ctrl+Shift+P`):**
- `Python: Run All Tests`
- `Python: Debug All Tests`
- `Python: Run Failed Tests`
- `Python: Run Current Test File`

**Via Keyboard Shortcuts:**
- `Ctrl+; Ctrl+A` - Run all tests
- `Ctrl+; Ctrl+F` - Run failed tests
- `Ctrl+; Ctrl+L` - Run last test run
- `Ctrl+; Ctrl+D` - Debug last test run

### 3. View Results
- ✅ Green checkmark = Test passed
- ❌ Red X = Test failed
- ⏭️ Gray skip icon = Test skipped
- 🔄 Spinner = Test running
- Click any test to see output, assertions, and stack traces

## Test Organization

### Test Discovery Patterns
Tests are discovered using these patterns:
- **Files**: `test_*.py` in `tests/`, `cooking-ai/tests/`, `ai-projects/quantum-ml/tests/`
- **Classes**: `Test*`
- **Functions**: `test_*`

### Test Markers (Filters)
Tests can be filtered using pytest markers:
- `unit` - Fast unit tests (< 1 second each)
- `integration` - Integration tests requiring external services
- `slow` - Long-running tests (> 5 seconds)
- `azure` - Tests requiring Azure Quantum credentials

**Run specific markers:**
```bash
# Via terminal
python -m pytest -m "unit"
python -m pytest -m "not slow and not azure"

# Via Test Explorer: Use test profiles (see below)
```

## Test Profiles

Test profiles are pre-configured test run configurations accessible via the Test Explorer:

| Profile | Description | Command |
|---------|-------------|---------|
| **Unit Tests (Fast)** | Quick unit tests only | `-m "not slow and not azure" tests/test_*_unit.py` |
| **Integration Tests** | External service integration | `-m "integration" tests/` |
| **All Fast Tests** | All tests except slow/azure | `-m "not slow and not azure" tests/` |
| **Quantum Tests** | Quantum-specific test files | `tests/test_quantum*.py tests/test_validate_qiskit*.py` |
| **All Tests** | Everything except azure | `-m "not azure" tests/` |
| **All with Coverage** | Full suite with coverage report | `--cov=. --cov-report=html tests/` |

## Debugging Tests

### Debug a Single Test
1. Set breakpoints in test file or source code
2. Right-click test in Test Explorer
3. Select "Debug Test"
4. Use Debug toolbar (Step Over, Step Into, Continue, Stop)

### Debug Test Configuration
Tests use the root workspace Python interpreter with these settings:
- Working directory: `${workspaceFolder}`
- Arguments: `-v --tb=short --no-header --color=yes`
- Environment: Inherits from terminal environment

### Common Debug Scenarios
**Test fails only in Test Explorer:**
- Check working directory (should be workspace root)
- Verify environment variables are set
- Check if test requires specific fixtures

**Test passes but debugging doesn't work:**
- Ensure `pytest` and `pytest-cov` are installed: `pip install pytest pytest-cov`
- Reload window: `Ctrl+Shift+P` → "Developer: Reload Window"

## Test Output & Logs

### Test Output Window
- Click any test to see its output
- Output includes: stdout, stderr, assertion errors, stack traces
- Use "Show Output" to see full pytest execution logs

### Coverage Reports
After running tests with coverage:
1. Open `htmlcov/index.html` in browser for interactive report
2. Check terminal output for summary statistics
3. View inline coverage indicators in source files

### Test Results Export
Test results are automatically exported to:
- `data_out/test_runner/results.json` - Machine-readable format
- `data_out/test_runner/results.md` - Human-readable summary

## CI/CD Integration

### GitHub Actions
Tests run automatically on push/PR via `.github/workflows/ci-pipeline.yml`:
```yaml
- name: Run unit tests
  run: python scripts/test_runner.py --unit --coverage

- name: Run integration tests
  run: python scripts/test_runner.py --integration
```

### Pre-commit Hooks
Fast unit tests run before each commit:
```bash
# Install hooks (one-time)
git config core.hooksPath .githooks

# Tests run automatically on git commit
# Bypass if needed: git commit --no-verify
```

## Troubleshooting

### Tests Not Discovered
**Symptom:** Test Explorer shows "No tests found"
**Solutions:**
1. Check Python interpreter: `Ctrl+Shift+P` → "Python: Select Interpreter"
2. Refresh tests: Click refresh button (🔄) in Test Explorer
3. Check pytest installation: Open terminal → `python -m pytest --version`
4. Verify test paths in `pytest.ini`: `testpaths = tests`
5. Reload window: `Ctrl+Shift+P` → "Developer: Reload Window"

### Import Errors in Tests
**Symptom:** `ModuleNotFoundError` when running tests
**Solutions:**
1. Ensure workspace root is in PYTHONPATH (automatic with `python.testing.cwd`)
2. Check virtual environment activation
3. Install missing dependencies: `pip install -r requirements.txt`

### Tests Pass in Terminal, Fail in Test Explorer
**Symptom:** `pytest` command works, but Test Explorer fails
**Solutions:**
1. Check working directory: Should be `${workspaceFolder}` in settings.json
2. Verify environment variables are exported
3. Compare pytest args between terminal and `python.testing.pytestArgs`

### Slow Test Discovery
**Symptom:** Test Explorer takes long to refresh
**Solutions:**
1. Exclude large directories in `pytest.ini`: `norecursedirs = venv data_out`
2. Reduce test paths: Focus on specific directories
3. Disable auto-discovery on save: Set `python.testing.autoTestDiscoverOnSaveEnabled: false`

## Advanced Usage

### Run Tests in Watch Mode
Use the test runner script for continuous testing:
```bash
python scripts/test_runner.py --unit --integration --watch
```
Tests re-run automatically when files change.

### Custom Test Arguments
Temporarily override pytest args:
1. Open settings: `Ctrl+,`
2. Search "pytest args"
3. Add arguments to `python.testing.pytestArgs` array

### Multi-root Workspaces
For quantum-ai and cooking-ai subprojects:
- Each has its own `venv` and `tests/` directory
- Tests are discovered from all roots via `pytest.ini` testpaths
- Use full paths when debugging cross-project tests

## Best Practices

1. **Name tests clearly**: `test_<component>_<behavior>_<expected>`
2. **Keep unit tests fast**: < 1 second each
3. **Use markers**: Tag slow/integration tests appropriately
4. **Run fast tests frequently**: Use "Unit Tests (Fast)" profile
5. **Debug failing tests**: Right-click → "Debug Test" instead of print statements
6. **Check coverage**: Run with coverage periodically to find untested code
7. **Fix failing tests immediately**: Don't let test debt accumulate

## Configuration Files

### `.vscode/settings.json`
```json
{
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["-v", "--tb=short", "--no-header", "--color=yes"],
  "python.testing.cwd": "${workspaceFolder}",
  "python.testing.autoTestDiscoverOnSaveEnabled": true
}
```

### `pytest.ini`
```ini
[pytest]
testpaths = tests cooking-ai/tests ai-projects/quantum-ml/tests
python_files = test_*.py
addopts = -v --tb=short --no-header --color=yes
markers =
    unit: fast unit tests
    integration: integration tests
    slow: slow-running tests
    azure: tests requiring Azure credentials
```

## Resources

- **pytest Documentation**: https://docs.pytest.org/
- **VS Code Python Testing**: https://code.visualstudio.com/docs/python/testing
- **Test Runner Script**: `scripts/test_runner.py` - Advanced orchestration
- **CI Pipeline**: `.github/workflows/ci-pipeline.yml` - Automated testing

## Support

For issues or questions:
1. Check this guide's Troubleshooting section
2. Review test output in Test Explorer
3. Run tests manually: `python -m pytest tests/ -v`
4. Check pytest logs: `python -m pytest tests/ -v --log-cli-level=DEBUG`
