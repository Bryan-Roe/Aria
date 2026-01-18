# GitHub Actions Workflows

This directory contains CI/CD workflows for the QAI repository.

## Workflows Overview

### 1. Auto Validation (`auto-validation.yml`)
**Trigger**: Push to main, schedule (daily at 5 AM UTC), manual
**Purpose**: Validates orchestrator configurations (autotrain, quantum_autorun)
**Status**: ✅ Active

**Jobs**:
- `dry-run`: Runs auto_bootstrap.py to validate all orchestrator configs
- Uploads status artifacts from autotrain and quantum_autorun

**Requirements**:
- ✅ Python 3.11
- ✅ requirements.txt + pyyaml
- ✅ scripts/orchestrators/auto_bootstrap.py exists

---

### 2. CI Pipeline (`ci-pipeline.yml`)
**Trigger**: Push to main/dev, PRs to main, schedule (daily at 2 AM UTC)
**Purpose**: Continuous integration with validation, testing, and training
**Status**: ✅ Active

**Jobs**:
1. `validate`: Run CI validation and unit/integration tests
2. `train`: Run training workflow (scheduled builds only)

**Requirements**:
- ✅ Python 3.11
- ✅ scripts/orchestrators/ci_orchestrator.py
- ✅ scripts/test_runner.py
- ✅ scripts/training/autotrain.py

---

### 3. Aria Tests (`aria-tests.yml`)
**Trigger**: Push/PR to main/develop (aria_web/** changes), manual
**Purpose**: End-to-end testing of Aria web interface
**Status**: ✅ Active (Fixed port 8080)

**Jobs**:
1. `unit-integration-tests`: Python 3.10, 3.11, 3.12 matrix tests
2. `playwright-e2e`: Playwright browser tests
3. `pyppeteer-e2e`: Pyppeteer browser tests
4. `containerized-chrome-e2e`: Selenium Chrome tests
5. `test-summary`: Aggregate test results

**Server Configuration**:
- Port: 8080 (fixed from 8000)
- Host: 0.0.0.0 (via ARIA_HOST env var)
- URL: http://localhost:8080

**Requirements**:
- ✅ aria_web/server.py
- ✅ tests/test_aria_server.py
- ✅ tests/test_object_api_integration.py
- ✅ tests/test_ui_playwright.py
- ✅ tests/test_ui_pyppeteer.py
- ✅ tests/test_ui_selenium.py

---

### 4. E2E Tests (`e2e-tests.yml`)
**Trigger**: Push/PR to main
**Purpose**: Simplified E2E testing with multiple browser engines
**Status**: ✅ Active (Fixed port 8080)

**Jobs**:
1. `integration`: Unit & integration tests
2. `e2e_playwright`: Playwright E2E tests
3. `containerized_chrome`: Pyppeteer in container

**Server Configuration**:
- Port: 8080
- Host: 0.0.0.0 (via ARIA_HOST env var)

**Requirements**:
- ✅ Python 3.11
- ✅ Same test files as aria-tests.yml

---

### 5. Aria Pages (`aria-pages.yml`)
**Trigger**: Push to main (aria_web/** changes)
**Purpose**: Deploy Aria web interface to GitHub Pages
**Status**: ⚠️ Requires GitHub Pages setup

**Requirements**:
- GitHub Pages enabled in repository settings
- aria_web/ static files

---

### 6. Quantum Orchestration (`quantum-orchestration.yml`)
**Trigger**: Push to main, manual
**Purpose**: Run quantum training orchestration via PowerShell
**Status**: ⚠️ Windows-only, requires Azure credentials

**Requirements**:
- ⚠️ quantum-ai/azure/quantum_master_orchestration.ps1 (check if exists)
- Azure credentials secret
- Windows runner

---

### 7. AzureML Train (`azureml-train.yml`)
**Trigger**: Manual (workflow_dispatch)
**Purpose**: Submit LoRA training jobs to Azure ML
**Status**: ⚠️ Requires Azure ML workspace

**Requirements**:
- Azure credentials secret (AZURE_CREDENTIALS)
- Azure ML workspace configured
- Job YAML: AI/microsoft_phi-silica-3.6_v1/azureml/job-lora-train.yml

---

## Configuration Notes

### Environment Variables
All workflows support:
- `PYTHONPATH`: Set to `${{ github.workspace }}`
- `ARIA_HOST`: Set to `0.0.0.0` for server binding
- `ARIA_PORT`: Default 8080 (configurable)

### Secrets Required
Optional (for Azure workflows):
- `AZURE_CREDENTIALS`: Service principal JSON for azure/login
- Contains: clientId, clientSecret, subscriptionId, tenantId

### Port Configuration
**IMPORTANT**: Aria server runs on port **8080**, not 8000.
- Server code: `aria_web/server.py` (uses `ARIA_PORT` env var, default 8080)
- All workflows updated to use port 8080
- Health check: `curl http://localhost:8080/api/aria/state`

## Testing Workflows Locally

### Validate Auto Bootstrap
```bash
python scripts/orchestrators/auto_bootstrap.py
```

### Run CI Orchestrator
```bash
python scripts/orchestrators/ci_orchestrator.py --validate-all
python scripts/test_runner.py --unit
python scripts/test_runner.py --integration
```

### Test Aria Server
```bash
cd aria_web
export ARIA_HOST=0.0.0.0
export ARIA_PORT=8080
python server.py &
sleep 3
curl http://localhost:8080/api/aria/state
pytest ../tests/test_aria_server.py -v
```

### Validate Training Config
```bash
python scripts/training/autotrain.py --dry-run
python scripts/evaluation/quantum_autorun.py --dry-run
```

## Troubleshooting

### Port Conflicts
If you see "Address already in use" errors:
```bash
# Find process using port 8080
lsof -i :8080
# Or on Linux
netstat -tulpn | grep 8080

# Set different port
export ARIA_PORT=8081
```

### Missing Dependencies
```bash
# Install all dependencies
pip install -r requirements.txt
pip install pytest pytest-timeout pytest-cov playwright pyppeteer selenium

# Install Playwright browsers
playwright install chromium
```

### Server Not Starting
Check logs:
```bash
# In workflow
cat /tmp/aria_server.log

# Local testing
python aria_web/server.py
```

### Test Failures
Run with verbose output:
```bash
pytest tests/test_aria_server.py -vv --tb=long
```

## Workflow Status Dashboard

Check workflow runs:
- https://github.com/YOUR_USERNAME/AI/actions

View specific workflow:
- Auto Validation: `.github/workflows/auto-validation.yml`
- CI Pipeline: `.github/workflows/ci-pipeline.yml`
- Aria Tests: `.github/workflows/aria-tests.yml`

## Recent Changes

**2026-01-17**:
- ✅ Fixed port mismatch: Changed 8000 → 8080 in all workflows
- ✅ Added ARIA_HOST=0.0.0.0 env var for container compatibility
- ✅ Updated Python action versions: v4 → v5
- ✅ Simplified CI pipeline to use existing scripts
- ✅ Added PYTHONPATH to all test jobs
- ✅ Fixed server health check endpoints

## Contributing

When adding new workflows:
1. Test locally first using the commands above
2. Use existing scripts from `scripts/` directory
3. Follow naming convention: `kebab-case.yml`
4. Add documentation to this README
5. Use latest action versions (checkout@v4, setup-python@v5)
6. Include artifact uploads for debugging
7. Set proper timeouts (default: 60min, consider reducing)

## Action Version Matrix

Current versions used:
- `actions/checkout@v4`
- `actions/setup-python@v5`
- `actions/upload-artifact@v4`
- `actions/download-artifact@v4`
- `azure/login@v2`
- `azure/cli@v2`
