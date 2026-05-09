# GitHub Actions Workflows

This repository uses GitHub Actions for continuous integration, testing, deployment, and automation.

## 📊 Workflow Status

| Workflow                  | Status                                                                                                               | Description                                        |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| CI Pipeline               | ![CI Pipeline](https://github.com/Bryan-Roe/Aria/actions/workflows/ci-pipeline.yml/badge.svg)                        | Main CI with validation, training, and deployment  |
| Code Quality              | ![Code Quality](https://github.com/Bryan-Roe/Aria/actions/workflows/code-quality.yml/badge.svg)                      | Linting, formatting, and security checks           |
| CodeQL Security           | ![CodeQL](https://github.com/Bryan-Roe/Aria/actions/workflows/codeql.yml/badge.svg)                                  | Security vulnerability scanning                    |
| PR Checks                 | ![PR Checks](https://github.com/Bryan-Roe/Aria/actions/workflows/pr-checks.yml/badge.svg)                            | Fast validation for pull requests                  |
| Auto Validation           | ![Auto Validation](https://github.com/Bryan-Roe/Aria/actions/workflows/auto-validation.yml/badge.svg)                | Orchestrator dry-run validation                    |
| E2E Tests                 | ![E2E Tests](https://github.com/Bryan-Roe/Aria/actions/workflows/e2e-tests.yml/badge.svg)                            | End-to-end browser tests                           |
| Aria Tests                | ![Aria Tests](https://github.com/Bryan-Roe/Aria/actions/workflows/aria-tests.yml/badge.svg)                          | Aria character tests                               |
| Quantum                   | ![Quantum](https://github.com/Bryan-Roe/Aria/actions/workflows/quantum-orchestration.yml/badge.svg)                  | Quantum computing workflows                        |
| Azure ML                  | ![Azure ML](https://github.com/Bryan-Roe/Aria/actions/workflows/azureml-train.yml/badge.svg)                         | Azure ML training jobs                             |
| Release                   | ![Release](https://github.com/Bryan-Roe/Aria/actions/workflows/release.yml/badge.svg)                                | Automated releases                                 |
| Dependabot Auto-merge     | ![Dependabot Auto-merge](https://github.com/Bryan-Roe/Aria/actions/workflows/dependabot-automerge.yml/badge.svg)     | Auto-merge safe Dependabot PRs                     |
| Integration Contract Gate | ![Integration Contract](https://github.com/Bryan-Roe/Aria/actions/workflows/integration-contract-gate.yml/badge.svg) | API contract validation on push/PR                 |
| Nightly Regression        | ![Nightly Regression](https://github.com/Bryan-Roe/Aria/actions/workflows/nightly-regression.yml/badge.svg)          | Nightly full suite with regression detection       |
| Training Health Report    | ![Training Health](https://github.com/Bryan-Roe/Aria/actions/workflows/training-health-report.yml/badge.svg)         | Weekly training pipeline digest                    |
| Coverage Report           | ![Coverage Report](https://github.com/Bryan-Roe/Aria/actions/workflows/coverage-report.yml/badge.svg)                | Test coverage tracking and PR diff comments        |
| Dataset Integrity         | ![Dataset Integrity](https://github.com/Bryan-Roe/Aria/actions/workflows/dataset-integrity.yml/badge.svg)            | Enforces datasets/ immutability and schema rules   |
| Secrets Scan              | ![Secrets Scan](https://github.com/Bryan-Roe/Aria/actions/workflows/secrets-scan.yml/badge.svg)                      | Gitleaks secret detection and sensitive file guard |
| Dependency Review         | ![Dependency Review](https://github.com/Bryan-Roe/Aria/actions/workflows/dependency-review.yml/badge.svg)            | Blocks risky dependency changes in PRs             |
| Workflow Lint             | ![Workflow Lint](https://github.com/Bryan-Roe/Aria/actions/workflows/actionlint.yml/badge.svg)                       | Lints GitHub Actions with actionlint               |
| Markdown Quality          | ![Markdown Quality](https://github.com/Bryan-Roe/Aria/actions/workflows/markdown-quality.yml/badge.svg)              | Lints Markdown style and structure                 |
| Broken Links Check        | ![Broken Links](https://github.com/Bryan-Roe/Aria/actions/workflows/broken-links.yml/badge.svg)                      | Validates links in docs and markdown               |
| API Health Smoke          | ![API Health Smoke](https://github.com/Bryan-Roe/Aria/actions/workflows/api-health-smoke.yml/badge.svg)              | Fast smoke gate for API route health               |
| Artifact Lifecycle        | ![Artifact Lifecycle](https://github.com/Bryan-Roe/Aria/actions/workflows/artifact-lifecycle.yml/badge.svg)          | Weekly artifact retention audit/cleanup            |
| Platform Health Daily     | ![Platform Health Daily](https://github.com/Bryan-Roe/Aria/actions/workflows/platform-health-daily.yml/badge.svg)    | Daily health pulse and resource snapshot           |

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

**Triggers:** Push/PR (aria_web changes), manual

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

**Triggers:** Version tags (v*.*.\*), manual

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

### Automation Workflows

#### 13. **Dependabot Auto-merge** (`dependabot-automerge.yml`)

**Triggers:** Pull requests opened/updated by `dependabot[bot]`

**Jobs:**

- **automerge**: Auto-approve and enable squash-merge for safe Dependabot PRs
  - Fetches Dependabot PR metadata (package name, update type, versions)
  - Auto-approves **minor** and **patch** version bumps
  - Enables GitHub auto-merge (squash) — merge only happens once CI passes
  - Posts a warning comment on **major** version bumps requiring manual review
  - Writes a step summary table with package and version info

#### 14. **Integration Contract Gate** (`integration-contract-gate.yml`)

**Triggers:** Push to `main` (strict mode), PR to `main`/`dev`, manual dispatch

**Jobs:**

- **contract-gate**: Runs `scripts/integration_contract_gate.sh`
  - Standard mode on PRs — verifies smoke tests + CI orchestrator contracts
  - Strict mode on pushes to `main` — adds `--strict-endpoints` (8/8 checks)
  - Uploads `data_out/integration_smoke/` and `data_out/ci_orchestrator/status.json` as artifacts (14-day retention)
  - Displays CI orchestrator status JSON in step summary

#### 15. **Nightly Regression Baseline** (`nightly-regression.yml`)

**Triggers:** Nightly at 03:00 UTC, manual dispatch (optional `--maxfail=1`)

**Jobs:**

- **full-test-suite**: Full `pytest tests/` run with coverage
  - JUnit XML + coverage XML uploaded as 30-day artifacts
  - Parses pass/fail/skip counts from pytest output
- **detect-regression**: Compares against previous run artifact
  - Downloads prior nightly artifact via `dawidd6/action-download-artifact`
  - Opens a labelled GitHub Issue (`regression`, `automated`, `bug`) on any failures
  - Deduplicates: skips creating a second issue if one is already open for today

#### 16. **Training Health Report** (`training-health-report.yml`)

**Triggers:** Every Monday at 08:00 UTC, manual dispatch (with optional force-issue flag)

**Jobs:**

- **health-report**: Reads `data_out/` status artifacts and reports training pipeline health
  - Parses `data_out/autonomous_training_status.json` (cycles, best_accuracy, performance_history)
  - Parses `data_out/ci_orchestrator/status.json` (succeeded/failed job counts)
  - Detects degradation: accuracy < 0.6, accuracy trend declining, or CI failure rate > 20 %
  - Runs `scripts/training_analytics.py` if available (non-blocking)
  - Posts rich step summary with health badge (✅ Healthy / ⚠️ DEGRADED)
  - Opens a labelled GitHub Issue (`training`, `automated`) — `performance` label added when degraded
  - Deduplicates issues by week

#### 17. **Coverage Report** (`coverage-report.yml`)

**Triggers:** Push to `main`, PR to `main`/`dev`, manual dispatch

**Jobs:**

- **coverage**: Measures test coverage on every push and PR
  - Runs `pytest --cov` and extracts line-rate from `coverage.xml`
  - On pushes to `main`: uploads coverage XML as 90-day `coverage-main-baseline` artifact
  - On PRs: downloads baseline, computes Δ vs `main`, posts/updates a PR comment with badge (🟢≥80%, 🟡≥60%, 🔴<60%)
  - Writes a collapsible step summary with the last 40 lines of pytest output
  - **No hard fail** — warns only; use to track trends and spot regressions early

#### 18. **Dataset Integrity** (`dataset-integrity.yml`)

**Triggers:** Push/PR to `main`/`dev` that touch `datasets/**`, manual dispatch

**Jobs:**

- **immutability-check**: Enforces the `datasets/` read-only convention
  - Computes diff range (handles PRs, force-pushes, and initial branch pushes)
  - Fails if any Modified (M), Deleted (D), Renamed (R), Copied (C), or Type-changed (T) files are found
  - Only Additions (A) are permitted — preserves existing dataset history
- **schema-validate**: Validates newly added `.json`/`.jsonl` files
  - Spot-checks up to 20 records per file against chat message schema
  - Expects `{"messages": [{"role": "user|assistant|system", "content": "..."}]}`
  - Fails on JSON parse errors, missing `messages` key, or unknown roles

#### 19. **Secrets Scan** (`secrets-scan.yml`)

**Triggers:** Push to `main`/`dev`, PR to `main`/`dev`, manual dispatch

**Jobs:**

- **gitleaks**: Authoritative secret detection via `gitleaks/gitleaks-action@v2`
  - Scans full git history (`fetch-depth: 0`) for API keys, tokens, passwords, private keys
  - **Blocking** — fails the workflow if any secret is detected
  - Integrates with GitHub's security advisory system
- **sensitive-file-guard**: Advisory checks for credential file changes
  - Detects changes to `local.settings.json`, `.env`, `.pem`, `.p12`, private key files
  - Validates `local.settings.json` contains only placeholder values (heuristic check)
  - **Advisory only** — warns in step summary but does not block (Gitleaks is the gate)

#### 20. **Dependency Review** (`dependency-review.yml`)

**Triggers:** Pull requests to `main`/`dev`

**Jobs:**

- **dependency-review**: Reviews dependency changes introduced by PRs
  - Uses `actions/dependency-review-action@v4`
  - Fails on vulnerabilities with severity **high** or above
  - Denies high-risk copyleft licenses (`GPL-2.0`, `GPL-3.0`, `AGPL-3.0`)
  - Posts dependency review summary directly on PRs

#### 21. **Workflow Lint** (`actionlint.yml`)

**Triggers:** Push/PR when `.github/workflows/**` or `.github/actions/**` change, manual dispatch

**Jobs:**

- **actionlint**: Lints GitHub Actions workflows and embedded shell snippets
  - Uses `reviewdog/action-actionlint@v1` with blocking mode (`fail_on_error: true`)
  - Installs `shellcheck` so shell fragments in workflows are validated too
  - Catches invalid expressions, runner matrix mistakes, and shell anti-patterns before merge

#### 22. **Markdown Quality** (`markdown-quality.yml`)

**Triggers:** Push/PR to `main`/`dev` when Markdown files change, manual dispatch

**Jobs:**

- **markdownlint**: Enforces Markdown style and structural consistency
  - Uses `DavidAnson/markdownlint-cli2-action@v20`
  - Scans `**/*.md` while excluding generated/ephemeral paths (`data_out/**`, `mount/**`)
  - Adds run summary in `GITHUB_STEP_SUMMARY`

#### 23. **Broken Links Check** (`broken-links.yml`)

**Triggers:** Push/PR to `main`/`dev` on docs/Markdown changes, manual dispatch

**Jobs:**

- **link-check**: Verifies outbound and repo links in Markdown/docs
  - Uses `lycheeverse/lychee-action@v2`
  - Accepts common redirect/auth/rate-limit status codes (`301`, `302`, `401`, `403`, `429`)
  - Fails the workflow on unresolved/broken links to prevent stale docs
  - Adds run summary in `GITHUB_STEP_SUMMARY`

#### 24. **API Health Smoke** (`api-health-smoke.yml`)

**Triggers:** Push/PR on backend route changes, daily schedule, manual dispatch

**Jobs:**

- **smoke**: Fast route and contract smoke checks for API surfaces
  - Runs `python scripts/integration_smoke.py --json`
  - Runs strict endpoint smoke daily (`--strict-endpoints`) on scheduled runs
  - Runs `python scripts/ci_orchestrator.py --integration-contract-tests`
  - Uploads `data_out/integration_smoke/` and `data_out/ci_orchestrator/status.json` artifacts
  - Adds a concise run checklist in `GITHUB_STEP_SUMMARY`

#### 25. **Artifact Lifecycle** (`artifact-lifecycle.yml`)

**Triggers:** Weekly schedule, manual dispatch

**Jobs:**

- **cleanup**: Retention management for `data_out/` artifacts
  - Scheduled run executes dry-run only (`python scripts/cleanup_artifacts.py`)
  - Manual run supports configurable `max_age` and `max_count`
  - Manual run can optionally apply deletion (`--apply=true`) for controlled cleanup
  - Uploads `data_out/cleanup_summary.json` artifact and writes JSON summary to step output

#### 26. **Platform Health Daily** (`platform-health-daily.yml`)

**Triggers:** Daily schedule, manual dispatch

**Jobs:**

- **health-pulse**: Generates daily health and resource snapshots
  - Runs `python scripts/system_health_check.py --json`
  - Runs `python scripts/resource_monitor.py --snapshot --export ...`
  - Uploads machine-readable health artifacts under `data_out/platform_health/`
  - Adds quick status counts to `GITHUB_STEP_SUMMARY` for triage

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

- **All runs**: [GitHub Actions dashboard](https://github.com/Bryan-Roe/Aria/actions)
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
