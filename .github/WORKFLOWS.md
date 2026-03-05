# GitHub Actions Workflows

This repository uses GitHub Actions for continuous integration, testing, deployment, and automation.

**14 workflows, organized by purpose.** Use this page to find the right workflow for your task.

## 📊 Workflow Status

| Status | Workflow | Description |
| --- | --- | --- |
| ![CI Pipeline](https://github.com/Bryan-Roe/Aria/actions/workflows/ci-pipeline.yml/badge.svg) | **CI Pipeline** | Validation → training → deployment (daily + PR) |
| ![Code Quality](https://github.com/Bryan-Roe/Aria/actions/workflows/code-quality.yml/badge.svg) | **Code Quality** | black, flake8, isort, mypy, safety checks |
| ![CodeQL](https://github.com/Bryan-Roe/Aria/actions/workflows/codeql.yml/badge.svg) | **CodeQL Security** | Python & JS vulnerability scanning |
| ![PR Checks](https://github.com/Bryan-Roe/Aria/actions/workflows/pr-checks.yml/badge.svg) | **PR Checks** | Fast validation + auto-labeling |
| ![Auto Validation](https://github.com/Bryan-Roe/Aria/actions/workflows/auto-validation.yml/badge.svg) | **Auto Validation** | Orchestrator config dry-runs |
| ![E2E Tests](https://github.com/Bryan-Roe/Aria/actions/workflows/e2e-tests.yml/badge.svg) | **E2E Tests** | Browser automation (Playwright, Pyppeteer, Selenium) |
| ![Aria Tests](https://github.com/Bryan-Roe/Aria/actions/workflows/aria-tests.yml/badge.svg) | **Aria Tests** | Character runtime (Python 3.10, 3.11, 3.12) |
| ![Quantum](https://github.com/Bryan-Roe/Aria/actions/workflows/quantum-orchestration.yml/badge.svg) | **Quantum Orchestration** | Azure Quantum workflows |
| ![Azure ML](https://github.com/Bryan-Roe/Aria/actions/workflows/azureml-train.yml/badge.svg) | **Azure ML Training** | LoRA training jobs on cloud GPU |
| ![Release](https://github.com/Bryan-Roe/Aria/actions/workflows/release.yml/badge.svg) | **Release** | Automated semantic releases |
| — | **Stale Issues/PRs** | Auto-close inactive issues (60d) and PRs (30d) |
| — | **Pages** | Deploy GitHub Pages documentation |
| — | **Workflow Validation** | Syntax check for workflow files |

## Find by Task

- **Push broke tests** → CI Pipeline / E2E Tests / Code Quality
- **Aria character buggy** → Aria Tests
- **New orchestrator job** → Auto Validation
- **Cloud training needed** → Azure ML Training (manual)
- **Quantum task** → Quantum Orchestration (manual)
- **Release publish** → Release (git tag v*.*.*)
- **Security issues** → CodeQL Security / Code Quality
- **Workflow YAML error** → Workflow Validation (manual)

## 🔄 Workflows Overview

### Core CI/CD Workflows

#### 1. **CI Pipeline** (`ci-pipeline.yml`)

**Triggers:** Push to main/dev, PRs to main, daily at 2 AM UTC

**Jobs:**

- **validate**: Runs orchestrator validation and tests
  - Validates all orchestrators with dry-run
  - Runs unit tests with coverage
  - Runs integration tests
- **train**: Daily scheduled training workflow
  - Runs master orchestrator with full pipeline
- **deploy**: Deploys best models with canary strategy

#### 2. **Code Quality** (`code-quality.yml`) ⭐ NEW

**Triggers:** Push to main/dev, PRs

**Jobs:**

- **lint**: Code linting and formatting checks
  - flake8 for syntax errors and code quality
  - black for code formatting
  - isort for import sorting
  - mypy for type checking
- **security-check**: Dependency vulnerability scanning
  - safety check for known vulnerabilities

#### 3. **CodeQL Security** (`codeql.yml`) ⭐ NEW

**Triggers:** Push to main/dev, PRs to main, weekly on Monday

**Jobs:**

- **analyze**: Security vulnerability analysis
  - Scans Python and JavaScript code
  - Uses extended security queries
  - Reports to GitHub Security tab

#### 4. **PR Checks** (`pr-checks.yml`) ⭐ NEW

**Triggers:** Pull requests opened/updated

**Jobs:**

- **validate**: Quick validation checks
  - Validates YAML syntax
  - Runs fast_validate.py
  - Checks for TODO/FIXME markers
- **size-check**: Analyzes PR size
  - Warns if PR is too large
- **label-pr**: Auto-labels PRs based on changed files

### Testing Workflows

#### 5. **Auto Validation** (`auto-validation.yml`)

**Triggers:** Push to main (specific paths), daily at 5 AM UTC, manual

**Jobs:**

- **dry-run**: Validates orchestrators without execution
  - Runs auto_bootstrap.py
  - Validates autotrain and quantum_autorun

#### 6. **E2E Tests** (`e2e-tests.yml`)

**Triggers:** Push to main, PRs to main

**Jobs:**

- **integration**: Unit and integration tests
- **e2e_playwright**: Playwright E2E tests
- **containerized_chrome**: Pyppeteer E2E tests

#### 7. **Aria Tests** (`aria-tests.yml`)

**Triggers:** Push/PR (web/aria_web changes), manual

**Jobs:**

- **unit-integration-tests**: Tests across Python 3.10, 3.11, 3.12
- **playwright-e2e**: Playwright E2E tests
- **pyppeteer-e2e**: Pyppeteer E2E tests
- **containerized-chrome-e2e**: Selenium E2E tests
- **test-summary**: Aggregates all test results

### Specialized Workflows

#### 8. **Quantum Orchestration** (`quantum-orchestration.yml`)

**Triggers:** Push to main, manual

**Jobs:**

- **run-quantum**: Runs quantum computing workflows
  - Azure login with service principal
  - PowerShell orchestration scripts

#### 9. **Azure ML Training** (`azureml-train.yml`)

**Triggers:** Manual only

**Jobs:**

- **submit-job**: Submits LoRA training to Azure ML
  - Configurable compute target
  - Streams job output

#### 10. **Release** (`release.yml`) ⭐ NEW

**Triggers:** Version tags (v*.*.*), manual

**Jobs:**

- **create-release**: Creates GitHub releases
  - Generates changelog
  - Creates source archives
  - Uploads release artifacts

### Maintenance Workflows

#### 11. **Stale Issues and PRs** (`stale.yml`) ⭐ NEW

**Triggers:** Daily at midnight UTC, manual

**Jobs:**

- **stale**: Manages stale issues and PRs
  - Marks issues stale after 60 days
  - Marks PRs stale after 30 days
  - Auto-closes after warning period

#### 12. **Workflow Validation** (`workflow-validation.yml`) ⭐ NEW

**Triggers:** Changes to workflow files, push to main

**Jobs:**

- **validate-workflows**: Validates workflow syntax
  - YAML syntax checking
  - Structure validation
  - Common issues detection
- **test-workflows**: Tests workflow execution

## 🎯 Quick Actions

### Running Workflows Manually

Most workflows can be triggered manually from the GitHub Actions tab:

1. Go to **Actions** tab in GitHub
2. Select the workflow from the left sidebar
3. Click **Run workflow**
4. Fill in any required inputs
5. Click **Run workflow**

### Workflow Badges

Add workflow status badges to any markdown file:

```markdown
![Workflow Name](https://github.com/Bryan-Roe/Aria/actions/workflows/workflow-file.yml/badge.svg)
```

### Monitoring Workflow Runs

- **All runs**: <https://github.com/Bryan-Roe/Aria/actions>
- **Failed runs**: Filter by "Status: Failure"
- **Scheduled runs**: Filter by "Event: schedule"

## 🛠️ Configuration Files

- **`.github/workflows/`** - Workflow definitions
- **`.github/labeler.yml`** - Auto-labeling configuration
- **`.github/dependabot.yml`** - Dependency update configuration
- **`pytest.ini`** - Test configuration
- **`requirements.txt`** - Python dependencies

## 🔧 Workflow Development

### Testing Workflows Locally

Use [act](https://github.com/nektos/act) to test workflows locally:

```bash
# Install act
brew install act  # macOS
# or
choco install act-cli  # Windows

# Run a workflow
act -j job-name

# Run on push event
act push

# Run on pull request
act pull_request
```

### Best Practices

1. **Use caching** for dependencies to speed up workflows
2. **Set timeouts** to prevent hanging jobs
3. **Use matrix strategy** for testing across multiple versions
4. **Continue on error** for non-critical checks
5. **Upload artifacts** for debugging failed runs
6. **Use secrets** for sensitive data (never hardcode)
7. **Add status checks** to protect branches

### Adding New Workflows

1. Create workflow file in `.github/workflows/`
2. Follow naming convention: `kebab-case.yml`
3. Add descriptive name and documentation
4. Test locally with `act` if possible
5. Add to this documentation
6. Update workflow validation to include new workflow

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax Reference](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [GitHub Actions Marketplace](https://github.com/marketplace?type=actions)
- [Repository Documentation](../README.md)

## 🆘 Troubleshooting

### Common Issues

**Workflow not triggering:**

- Check trigger conditions (branches, paths)
- Verify workflow file syntax
- Check if workflow is disabled

**Tests failing:**

- Check logs in Actions tab
- Download test artifacts for detailed reports
- Run tests locally to reproduce

**Authentication errors:**

- Verify secrets are configured
- Check token permissions
- Ensure service principal credentials are valid

### Getting Help

- Review workflow logs in GitHub Actions tab
- Check [GitHub Status](https://www.githubstatus.com/)
- Create an issue with workflow run link
