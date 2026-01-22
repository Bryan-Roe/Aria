# CI/CD Testing Setup

This document describes the CI/CD testing infrastructure for the QAI repository.

## Overview

The repository uses **GitHub Actions** for continuous integration and testing. Multiple workflows handle different aspects of testing and validation.

## Workflows

### 1. Pytest CI (`pytest-ci.yml`)

**Primary testing workflow** - Runs comprehensive pytest suite on all commits.

**Triggers:**
- Push to `main`, `dev`, `feature/*` branches
- Pull requests to `main`, `dev`
- Manual workflow dispatch

**Jobs:**

#### Fast Tests (Always runs)
- **Duration:** ~5-10 minutes
- **Tests:** Unit tests only (`-m "not slow and not azure and not integration"`)
- **Runs on:** Every push
- **Purpose:** Quick feedback for developers

```bash
# Equivalent local command:
python -m pytest tests/ -m "not slow and not azure and not integration" -v
```

#### Full Test Suite (PRs and manual)
- **Duration:** ~15-20 minutes  
- **Tests:** All tests except slow/azure (`-m "not slow and not azure"`)
- **Coverage:** Generates coverage reports for `aria_web`, `shared`, `function_app`
- **Runs on:** Pull requests, manual dispatch

```bash
# Equivalent local command:
python -m pytest tests/ -m "not slow and not azure" --cov=aria_web --cov=shared --cov=function_app
```

#### Integration Tests (PRs and manual)
- **Duration:** ~10-15 minutes
- **Tests:** Integration tests (`-m "integration and not azure"`)
- **Runs on:** Pull requests, manual dispatch

#### Slow Tests (Scheduled only)
- **Duration:** ~20-30 minutes
- **Tests:** Long-running tests (`-m "slow and not azure"`)
- **Runs on:** Scheduled (nightly), manual dispatch

**Artifacts:**
- JUnit XML test results
- Coverage reports (uploaded to Codecov)
- Test duration reports

### 2. QAI CI Pipeline (`ci-pipeline.yml`)

**Legacy validation workflow** - Now integrated with pytest.

**Jobs:**
- Validation: Runs pytest + orchestrator validation
- Training: Dry-run training workflows (scheduled only)

### 3. Auto Validation (`auto-validation.yml`)

**Orchestrator validation** - Tests training/quantum configurations.

**Triggers:**
- Push to orchestrator files
- Daily schedule (5 AM UTC)

## Test Markers

Tests are organized using pytest markers. Use markers to control which tests run:

| Marker | Description | CI Usage |
|--------|-------------|----------|
| `unit` | Fast unit tests | Fast tests job |
| `integration` | Integration tests | Integration tests job |
| `slow` | Long-running tests (>5s) | Slow tests job (scheduled) |
| `azure` | Requires Azure credentials | Never run in CI |
| `e2e` | End-to-end browser tests | Manual only |
| `playwright` | Playwright browser tests | Manual only |
| `selenium` | Selenium browser tests | Manual only |

## Local Testing Commands

### Quick validation (before commit):
```bash
python scripts/ci_pytest_validate.py
```

### Fast tests (what CI runs on every commit):
```bash
python -m pytest tests/ -m "not slow and not azure and not integration"
```

### Full suite (what CI runs on PRs):
```bash
python -m pytest tests/ -m "not slow and not azure"
```

### With coverage:
```bash
python -m pytest tests/ --cov=aria_web --cov=shared --cov-report=html
```

### Specific test file:
```bash
python -m pytest tests/test_aria_web_comprehensive.py -v
```

### Watch mode (re-run on changes):
```bash
python -m pytest tests/ -f  # requires pytest-watch
```

## Configuration Files

### `pytest.ini`
Main pytest configuration:
- Test paths
- Markers
- Default options
- Timeout settings (5 minutes per test)

### `.github/workflows/pytest-ci.yml`
Primary CI workflow with multiple test jobs.

### `requirements.txt` & `dev-requirements.txt`
Dependencies for production and testing:
- `pytest>=7.4.0`
- `pytest-timeout>=2.1.0`
- `pytest-cov` (for coverage)
- `croniter>=1.3.0`

## CI Status Checks

The following checks must pass for PRs to be merged:

1. ✅ **Fast Tests** - Must pass (blocking)
2. ✅ **Full Test Suite** - Must pass (blocking)
3. ⚠️ **Integration Tests** - Can fail (non-blocking)

## Debugging CI Failures

### 1. Check Test Artifacts
Download test results from the Actions tab:
- `fast-test-results` - JUnit XML for fast tests
- `full-test-results` - JUnit XML + coverage for full suite
- `integration-test-results` - Integration test results

### 2. Reproduce Locally
```bash
# Run the exact same command as CI:
python -m pytest tests/ -m "not slow and not azure" -v --tb=short
```

### 3. Check Logs
Click on failed job → Expand failed step → View full logs

### 4. Run Validation Script
```bash
python scripts/ci_pytest_validate.py
```

## Performance

### Current Stats (as of setup):
- **Total tests:** 921 collected
- **Fast tests:** ~150 tests in ~2 minutes
- **Full suite:** 909 tests pass in ~2 minutes
- **Coverage:** aria_web, shared, function_app modules

### Optimization Tips:
1. Mark slow tests with `@pytest.mark.slow`
2. Use fixtures for expensive setup
3. Mock external services
4. Parallelize with `pytest-xdist` (future)

## Branch Protection Rules

Recommended settings for `main` branch:

```yaml
Required status checks:
  - Fast Tests
  - Full Test Suite
  - CI Status Check

Require branches to be up to date: ✅
Require pull request reviews: 1
Dismiss stale reviews: ✅
```

## Troubleshooting

### Import Errors in CI
**Problem:** Tests pass locally but fail in CI with import errors.

**Solution:**
1. Check `sys.path` modifications in test files
2. Verify all dependencies in `requirements.txt`
3. Ensure `PYTHONPATH` is set correctly

### Timeout Issues
**Problem:** Tests timeout in CI (default 5 minutes per test).

**Solution:**
1. Mark long tests with `@pytest.mark.slow`
2. Increase timeout in `pytest.ini` if needed
3. Optimize test fixtures

### Coverage Gaps
**Problem:** Coverage report missing modules.

**Solution:**
1. Add modules to `--cov=` flags in workflow
2. Check `.coveragerc` for exclusions
3. Verify imports in test files

## Manual Workflow Dispatch

You can manually trigger tests from GitHub:

1. Go to Actions tab
2. Select "Pytest CI" workflow
3. Click "Run workflow"
4. Choose test suite: `all`, `fast`, `unit`, `integration`, or `slow`

## Future Enhancements

- [ ] Parallel test execution with `pytest-xdist`
- [ ] Matrix testing (Python 3.10, 3.11, 3.12)
- [ ] Performance regression tracking
- [ ] Automatic issue creation for flaky tests
- [ ] Azure Quantum integration tests (with secrets)
- [ ] Playwright E2E tests in CI

## Support

For issues with CI/CD:
1. Check this documentation
2. Run `python scripts/ci_pytest_validate.py` locally
3. Review workflow logs in GitHub Actions
4. Check test artifacts for detailed reports
