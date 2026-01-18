# Test Execution Guide

## Quick Start

### Run All Tests
```bash
cd /workspaces/AI
python scripts/test_runner.py --all
```

### Run Only Unit Tests (Fast)
```bash
python scripts/test_runner.py --unit
```

### Run Specific Test File
```bash
pytest tests/test_master_orchestrator.py -v
```

## Test Suite Organization

### New Test Files (Created January 17, 2026)

#### 1. Infrastructure Tests
```bash
# Master orchestrator tests
pytest tests/test_master_orchestrator.py -v

# Repository automation tests
pytest tests/test_repo_automation.py -v

# Status dashboard and monitoring
pytest tests/test_status_dashboard.py -v

# Resource monitoring
pytest tests/test_resource_monitor.py -v
```

#### 2. Feature Tests
```bash
# Chat provider tests
pytest tests/test_chat_providers.py -v

# Training analytics
pytest tests/test_training_analytics.py -v

# System integration
pytest tests/test_system_integration.py -v
```

#### 3. Existing Test Suites
```bash
# Aria character tests
pytest tests/test_aria_*.py -v

# Training and LoRA tests
pytest tests/test_*train*.py -v

# Quantum ML tests
pytest tests/test_quantum*.py -v
```

## Detailed Test Descriptions

### test_master_orchestrator.py (14 tests)
Tests for master orchestration system

```bash
pytest tests/test_master_orchestrator.py::TestMasterOrchestratorConfig -v
pytest tests/test_master_orchestrator.py::TestMasterOrchestratorDependencies -v
pytest tests/test_master_orchestrator.py::TestMasterOrchestratorScheduling -v
pytest tests/test_master_orchestrator.py::TestMasterOrchestratorStatusManagement -v
pytest tests/test_master_orchestrator.py::TestMasterOrchestratorErrorHandling -v
pytest tests/test_master_orchestrator.py::TestMasterOrchestratorIntegration -v
```

**What it tests**:
- ✅ YAML config loading
- ✅ Required field validation
- ✅ Circular dependency detection
- ✅ Valid dependency chains
- ✅ Cron schedule parsing
- ✅ Priority ordering
- ✅ Status JSON management
- ✅ Retry logic
- ✅ Timeout handling
- ✅ Orchestrator chaining

### test_repo_automation.py (19 tests)
Tests for repository automation

```bash
pytest tests/test_repo_automation.py::TestRepoAutomationConfig -v
pytest tests/test_repo_automation.py::TestRepoAutomationBackup -v
pytest tests/test_repo_automation.py::TestRepoAutomationHealthCheck -v
pytest tests/test_repo_automation.py::TestRepoAutomationMonitoring -v
```

**What it tests**:
- ✅ Repo structure validation
- ✅ Backup creation and manifests
- ✅ Incremental backup logic
- ✅ Component health checks
- ✅ Database pool saturation
- ✅ Storage space monitoring
- ✅ Rollback state tracking
- ✅ Status file updates
- ✅ Metrics collection
- ✅ Log aggregation

### test_status_dashboard.py (17 tests)
Tests for status dashboard and metrics

```bash
pytest tests/test_status_dashboard.py::TestStatusDashboard -v
pytest tests/test_status_dashboard.py::TestOrchestrationMetrics -v
pytest tests/test_status_dashboard.py::TestAlertManagement -v
```

**What it tests**:
- ✅ Status aggregation
- ✅ Metrics calculation
- ✅ Duration tracking
- ✅ Success rate analysis
- ✅ Trend detection
- ✅ Threshold monitoring
- ✅ Alert generation
- ✅ Alert deduplication
- ✅ Data formatting
- ✅ Health endpoints

### test_resource_monitor.py (22 tests)
Tests for resource monitoring

```bash
pytest tests/test_resource_monitor.py::TestCPUMonitoring -v
pytest tests/test_resource_monitor.py::TestMemoryMonitoring -v
pytest tests/test_resource_monitor.py::TestGPUMonitoring -v
pytest tests/test_resource_monitor.py::TestProcessMonitoring -v
```

**What it tests**:
- ✅ CPU usage sampling
- ✅ Memory tracking
- ✅ Disk space monitoring
- ✅ GPU memory and utilization
- ✅ Network I/O
- ✅ Process resource usage
- ✅ Metrics collection
- ✅ Historical tracking
- ✅ Anomaly detection
- ✅ Alert generation

### test_chat_providers.py (22 tests)
Tests for chat provider system

```bash
pytest tests/test_chat_providers.py::TestProviderDetection -v
pytest tests/test_chat_providers.py::TestChatCompletion -v
pytest tests/test_chat_providers.py::TestStreamingResponses -v
pytest tests/test_chat_providers.py::TestLoRAAdapters -v
```

**What it tests**:
- ✅ Provider detection chain
- ✅ LMStudio/Azure/OpenAI detection
- ✅ Chat completions
- ✅ Multi-turn conversations
- ✅ SSE stream parsing
- ✅ Token counting
- ✅ Error recovery
- ✅ Fallback chains
- ✅ LoRA adapter loading
- ✅ Rate limit handling

### test_training_analytics.py (23 tests)
Tests for training analytics

```bash
pytest tests/test_training_analytics.py::TestTrainingAnalytics -v
pytest tests/test_training_analytics.py::TestPerformanceTrends -v
pytest tests/test_training_analytics.py::TestAnomalyDetection -v
```

**What it tests**:
- ✅ Accuracy tracking
- ✅ Convergence detection
- ✅ Overfitting detection
- ✅ Improvement rate calculation
- ✅ Momentum calculation
- ✅ Plateau detection
- ✅ Loss spike detection
- ✅ NaN detection
- ✅ Gradient explosion detection
- ✅ Report generation

### test_system_integration.py (27 tests)
Tests for system integration

```bash
pytest tests/test_system_integration.py::TestRepoStructureIntegrity -v
pytest tests/test_system_integration.py::TestConfigurationValidation -v
pytest tests/test_system_integration.py::TestCrossComponentIntegration -v
```

**What it tests**:
- ✅ Directory structure
- ✅ File presence
- ✅ Configuration parsing
- ✅ Python syntax
- ✅ YAML/JSON validation
- ✅ Dependency integrity
- ✅ Documentation presence
- ✅ Git setup
- ✅ Module imports
- ✅ Cross-component integration

## Running Tests with Options

### Verbose Output
```bash
pytest tests/test_master_orchestrator.py -v
# Shows each test as it runs
```

### Show Print Statements
```bash
pytest tests/test_master_orchestrator.py -s
# Displays any print() output from tests
```

### Stop on First Failure
```bash
pytest tests/test_master_orchestrator.py -x
# Stops at first failure instead of continuing
```

### Run Specific Test
```bash
pytest tests/test_master_orchestrator.py::TestMasterOrchestratorConfig::test_load_master_config_from_yaml -v
```

### With Coverage Report
```bash
pytest tests/ --cov=. --cov-report=html
# Generates HTML coverage report in htmlcov/
```

### Test Markers
```bash
# Run slow tests
pytest tests/ -m slow

# Run only fast tests
pytest tests/ -m "not slow"

# Run Azure tests
pytest tests/ -m azure
```

## Test Results Interpretation

### Passing Test Output
```
tests/test_master_orchestrator.py::TestMasterOrchestratorConfig::test_load_master_config_from_yaml PASSED
```

### Failed Test Output
```
tests/test_master_orchestrator.py::TestMasterOrchestratorConfig::test_load_master_config_from_yaml FAILED
AssertionError: assert None is not None
  E   where None = config
```

**How to debug**:
1. Read the assertion error
2. Look at the test source code
3. Check the files being tested
4. Run with `-s` to see print output
5. Run with `--pdb` to debug interactively

## Common Issues & Solutions

### Issue: "No tests collected"
```bash
# Solution: Check file and test naming
# - Files must be named test_*.py
# - Classes must start with Test
# - Methods must start with test_
```

### Issue: "ModuleNotFoundError"
```bash
# Solution: Ensure you're in repo root
cd /workspaces/AI
python scripts/test_runner.py --all
```

### Issue: "Timeout during test execution"
```bash
# Solution: Run specific test file or use smaller set
pytest tests/test_master_orchestrator.py -v
# Don't run entire suite if time-limited
```

### Issue: "Port already in use"
```bash
# Solution: Check for running services
lsof -i :8080  # Check Aria web
lsof -i :7071  # Check Azure Functions
# Kill with: kill -9 <PID>
```

## Performance Optimization

### Run Tests in Parallel
```bash
pytest tests/ -n auto
# Requires: pip install pytest-xdist
```

### Run Only Modified Tests
```bash
pytest tests/ --lf
# Runs only tests that failed last time
```

### Run Tests by Keyword
```bash
pytest tests/ -k "orchestrator"
# Runs only tests with "orchestrator" in name
```

## Integration with Development

### Run Tests on Save (Watch Mode)
```bash
# Using pytest-watch (pip install pytest-watch)
ptw tests/

# Or manually in loop
while true; do pytest tests/ -q; sleep 2; done
```

### Run Before Commit
```bash
# Add to .git/hooks/pre-commit
#!/bin/bash
pytest tests/ -q || exit 1
```

### GitHub Actions Configuration
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r dev-requirements.txt
      - run: python scripts/test_runner.py --all
```

## Test Coverage Reports

### Generate Coverage Report
```bash
pytest tests/ --cov=. --cov-report=html
# Open in browser: open htmlcov/index.html
```

### View Coverage in Terminal
```bash
pytest tests/ --cov=. --cov-report=term-missing
```

### Coverage Thresholds
```bash
# Fail if coverage below threshold
pytest tests/ --cov=. --cov-fail-under=80
```

## Troubleshooting

### Debug a Specific Test
```bash
# Enter debugger on failure
pytest tests/test_master_orchestrator.py::TestMasterOrchestratorConfig::test_load_master_config_from_yaml --pdb

# Set breakpoint in test
import pdb; pdb.set_trace()
```

### Check Test Collection
```bash
# See what tests would be collected
pytest tests/ --collect-only

# Filter to specific tests
pytest tests/ --collect-only -k "orchestrator"
```

### Validate Test Environment
```bash
# Check Python version
python --version

# Check pytest version
pytest --version

# Check installed dependencies
pip list | grep pytest
```

## Best Practices

1. **Run full suite before commits**: `python scripts/test_runner.py --all`
2. **Add tests for new features**: Create tests in appropriate file
3. **Keep tests independent**: No test should depend on another
4. **Use descriptive names**: `test_config_loads_required_fields` not `test_1`
5. **Include docstrings**: Document what each test validates
6. **Handle errors gracefully**: Catch expected exceptions
7. **Mock external calls**: Don't hit real APIs during tests
8. **Use fixtures**: Share setup code between tests

## Next Steps

1. ✅ Run `python scripts/test_runner.py --unit` to verify unit tests
2. ✅ Run `python scripts/test_runner.py --all` for complete test suite
3. ✅ Generate coverage report: `pytest tests/ --cov --cov-report=html`
4. ✅ Check test documentation in each test file
5. ✅ Add more tests as needed for new features

---

**Document Version**: 1.0
**Last Updated**: January 17, 2026
**Test Files**: 61+
**Test Methods**: 600+
