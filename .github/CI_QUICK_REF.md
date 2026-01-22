# CI/CD Quick Reference

## Before Pushing Code

```bash
# 1. Run fast validation
python scripts/ci_pytest_validate.py

# 2. Run fast tests (what CI runs on every commit)
python -m pytest tests/ -m "not slow and not azure and not integration" -v

# 3. (Optional) Run full suite if making significant changes
python -m pytest tests/ -m "not slow and not azure" -v
```

## Common Test Commands

```bash
# All tests (909 passing)
python -m pytest tests/

# Fast tests only (~150 tests, 2 min)
python -m pytest tests/ -m "not slow and not azure and not integration"

# With coverage
python -m pytest tests/ --cov=aria_web --cov=shared

# Single test file
python -m pytest tests/test_aria_web_comprehensive.py -v

# Specific test
python -m pytest tests/test_aria_web_comprehensive.py::TestAriaStateEndpoint::test_state_returns_valid_dict -v

# Show slowest tests
python -m pytest tests/ --durations=10
```

## CI Workflow Triggers

| Event | Fast Tests | Full Suite | Integration | Slow Tests |
|-------|------------|------------|-------------|------------|
| Push to main/dev | ✅ | ❌ | ❌ | ❌ |
| Pull Request | ✅ | ✅ | ✅ | ❌ |
| Schedule (nightly) | ✅ | ✅ | ✅ | ✅ |
| Manual dispatch | ✅ | ✅ | ✅ | Optional |

## Test Markers

```python
@pytest.mark.unit          # Fast unit test (always run)
@pytest.mark.integration   # Integration test (PR/manual)
@pytest.mark.slow          # Long test (scheduled/manual)
@pytest.mark.azure         # Requires Azure (never in CI)
@pytest.mark.e2e           # Browser test (manual only)
```

## Status Check Requirements

**Must pass for merge:**
- ✅ Fast Tests
- ✅ Full Test Suite
- ✅ CI Status Check

**Optional:**
- ⚠️ Integration Tests (can fail)

## Debugging Failed CI

1. **Download artifacts:**
   - Actions → Failed run → Artifacts → Download test results

2. **Reproduce locally:**
   ```bash
   python -m pytest tests/ -m "not slow and not azure" -v --tb=short
   ```

3. **Check specific failure:**
   ```bash
   python -m pytest tests/test_file.py::test_name -vv
   ```

## Key Files

- `.github/workflows/pytest-ci.yml` - Main CI workflow
- `pytest.ini` - Pytest configuration
- `requirements.txt` - Production dependencies  
- `dev-requirements.txt` - Testing dependencies
- `scripts/ci_pytest_validate.py` - Pre-commit validation

## CI Performance

- **Fast tests:** ~2 minutes, ~150 tests
- **Full suite:** ~5 minutes, 909 tests
- **Integration:** ~5 minutes, varies
- **Slow tests:** ~30 minutes, scheduled only

## Manual Workflow Run

GitHub → Actions → Pytest CI → Run workflow → Choose test suite

## Coverage Report

Coverage uploaded to Codecov on PRs:
- `aria_web/` - Aria character server
- `shared/` - Shared utilities
- `function_app.py` - Azure Functions

## Quick Fixes

**Import error in CI:**
```bash
# Check dependencies
pip install -r requirements.txt -r dev-requirements.txt
```

**Test timeout:**
```python
@pytest.mark.timeout(60)  # Increase timeout
def test_slow_function():
    ...
```

**Flaky test:**
```python
@pytest.mark.flaky(reruns=3)  # Retry on failure
def test_sometimes_fails():
    ...
```
