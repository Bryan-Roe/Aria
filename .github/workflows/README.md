# GitHub Actions Workflows

This directory contains all GitHub Actions workflows for the **Aria** repository. Workflows are organized by purpose and execution pattern to keep CI fast, reliable, and easy to reason about.

> **Last updated:** 2026-05-09
> **Maintainers:** `@Bryan-Roe`
> **Default branch:** `main`

---

## Table of Contents

- [Workflow Inventory](#workflow-inventory)
  - [🔄 Continuous Integration (CI)](#-continuous-integration-ci)
  - [✅ Testing Workflows](#-testing-workflows)
  - [🔬 Validation Workflows](#-validation-workflows)
  - [☁️ Cloud Workflows](#️-cloud-workflows)
- [Workflow Matrix](#workflow-matrix)
- [Required Secrets & Variables](#required-secrets--variables)
- [Common Trigger Patterns](#common-trigger-patterns)
- [Best Practices](#best-practices)
- [Adding a New Workflow](#adding-a-new-workflow)
- [Local Reproduction](#local-reproduction)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)
- [Resources](#resources)

---

## Workflow Inventory

### 🔄 Continuous Integration (CI)

#### `ci-pipeline.yml` — Main CI pipeline
- **Triggers:** push/PR to `main` and `dev`, daily schedule (`0 2 * * *` UTC)
- **Purpose:** code validation, unit/integration tests, daily training, model deployment
- **Duration:** ~15–30 minutes
- **Owner:** Platform team

### ✅ Testing Workflows

#### `aria-tests.yml` — Comprehensive Aria testing
- **Triggers:** changes to `apps/aria/**`, `aria_web/**`, or Aria test files
- **Purpose:** multi-Python (3.10–3.12) and multi-browser end-to-end tests
- **Duration:** ~20–30 minutes
- **Notes:** path-filtered; more thorough than quick regression

#### `e2e-tests.yml` — Quick regression testing
- **Triggers:** any push/PR to `main`
- **Purpose:** fast Aria regression tests
- **Duration:** ~10–15 minutes
- **Notes:** not path-filtered; catches broad regressions

### 🔬 Validation Workflows

#### `auto-validation.yml` — Orchestrator validation
- **Triggers:** changes to orchestrator configs/scripts, daily schedule
- **Purpose:** validates `autotrain.yaml` and `quantum_autorun.yaml`
- **Duration:** ~5–10 minutes

### ☁️ Cloud Workflows

#### `azureml-train.yml` — Azure ML training
- **Triggers:** manual (`workflow_dispatch`) only
- **Purpose:** submit LoRA fine-tuning jobs to Azure ML
- **Requires:** Azure credentials and an ML workspace (see [Required Secrets](#required-secrets--variables))

#### `quantum-orchestration.yml` — Azure Quantum
- **Triggers:** push to `main`, manual (`workflow_dispatch`)
- **Purpose:** execute quantum workflows on Azure Quantum
- **Requires:** Azure credentials and a Quantum workspace

---

## Workflow Matrix

| Workflow | Push | PR | Schedule | Manual | Path-filtered | Typical duration |
| ---------------------------- | :--: | :-: | :------: | :----: | :-----------: | :--------------: |
| `ci-pipeline.yml` | ✅ | ✅ | ✅ | ✅ | ❌ | 15–30 min |
| `aria-tests.yml` | ✅ | ✅ | ❌ | ✅ | ✅ | 20–30 min |
| `e2e-tests.yml` | ✅ | ✅ | ❌ | ✅ | ❌ | 10–15 min |
| `auto-validation.yml` | ✅ | ✅ | ✅ | ✅ | ✅ | 5–10 min |
| `azureml-train.yml` | ❌ | ❌ | ❌ | ✅ | n/a | 30+ min |
| `quantum-orchestration.yml` | ✅ | ❌ | ❌ | ✅ | ❌ | varies |

---

## Required Secrets & Variables

Configure these under **Settings → Secrets and variables → Actions**.

| Name | Type | Used by | Description |
| -------------------------- | ------- | ------------------------------------------------ | ------------------------------------------ |
| `AZURE_CREDENTIALS` | Secret | `azureml-train.yml`, `quantum-orchestration.yml` | Service principal JSON for Azure login |
| `AZUREML_WORKSPACE` | Variable | `azureml-train.yml` | Azure ML workspace name |
| `AZUREML_RESOURCE_GROUP` | Variable | `azureml-train.yml` | Azure resource group |
| `AZURE_QUANTUM_WORKSPACE` | Variable | `quantum-orchestration.yml` | Azure Quantum workspace name |
| `OPENAI_API_KEY` | Secret | `ci-pipeline.yml` (optional) | For provider-integration tests |
| `AZURE_OPENAI_ENDPOINT` | Secret | `ci-pipeline.yml` (optional) | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_API_KEY` | Secret | `ci-pipeline.yml` (optional) | Azure OpenAI API key |

> 🔐 Never log secret values. Always pass secrets via `env:` blocks scoped to the smallest possible step.

---

## Common Trigger Patterns

### Automatic triggers

```yaml
on:
  push:
    branches: [main, dev]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'   # daily at 02:00 UTC
```

### Manual trigger with inputs

```yaml
on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment'
        required: true
        default: 'staging'
        type: choice
        options: [staging, production]
```

### Path filtering

```yaml
on:
  push:
    paths:
      - 'apps/aria/**'
      - 'aria_web/**'
      - 'tests/**'
      - '.github/workflows/aria-tests.yml'
```

> 💡 Always include the workflow file itself in `paths` so changes to the workflow trigger a run.

### Concurrency (recommended for PR workflows)

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

---

## Best Practices

### When to use each workflow

- **Local development:** run tests locally first (`pytest`, `npm test`)
- **PR review:** `e2e-tests.yml` provides quick validation
- **Aria changes:** `aria-tests.yml` runs automatically via path filters
- **Daily CI:** `ci-pipeline.yml` catches integration issues overnight
- **Training:** use `azureml-train.yml` for GPU-accelerated cloud training
- **Quantum:** use `quantum-orchestration.yml` for quantum computing tasks

### Workflow conventions

- **Naming:** descriptive, kebab-case, with a type suffix (`-tests.yml`, `-validation.yml`, `-train.yml`)
- **Header comment:** every workflow starts with a comment block describing purpose, triggers, and ownership
- **Timeouts:** set `timeout-minutes` on every job to prevent runaway runs
- **Permissions:** declare minimum required `permissions:` at the workflow or job level (principle of least privilege)
- **Pinned actions:** pin third-party actions to a full commit SHA for security
  ```yaml
  uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11  # v4.1.1
  ```
- **Caching:** cache `pip`, `npm`, and build outputs to reduce CI time
- **Artifacts:** upload logs, screenshots, and reports on failure for debugging

### Reducing CI time

- Use path filtering to skip unnecessary runs
- Cache dependencies (`actions/setup-python` and `actions/setup-node` have built-in cache support)
- Run expensive jobs only on schedule or manual trigger
- Parallelize independent jobs using `needs:` and `strategy.matrix`
- Cancel superseded PR runs via `concurrency`

---

## Adding a New Workflow

Checklist for new workflows:

- [ ] Choose an appropriate trigger pattern (push / PR / schedule / manual)
- [ ] Add a header comment block (purpose, ownership, runtime)
- [ ] Set `permissions:` to the minimum required
- [ ] Use path filtering when possible
- [ ] Set `timeout-minutes` on all jobs
- [ ] Pin third-party actions to commit SHAs
- [ ] Cache dependencies (pip / npm / etc.)
- [ ] Upload artifacts for debugging on failure
- [ ] Add a `concurrency:` block for PR-triggered workflows
- [ ] Validate locally with [`act`](https://github.com/nektos/act) or `actionlint`
- [ ] Update this README (inventory + matrix)
- [ ] Document any new required secrets or variables

---

## Local Reproduction

Most workflow steps can be reproduced locally:

```bash
# Lint workflow files
actionlint .github/workflows/*.yml

# Run a workflow locally (best-effort)
act -W .github/workflows/e2e-tests.yml

# Reproduce CI tests
pytest -q
pytest tests/aria/ -v
```

---

## Troubleshooting

### Workflow not running

- Check that branch filters match your target branch
- Verify path filters include your changed files (if used)
- Ensure required secrets/variables are configured
- Confirm the workflow file exists on the default branch (push triggers run from the file as it exists on the branch being pushed to; scheduled triggers always run from `main`)

### Workflow failing

- Open the **Actions** tab and inspect job logs
- Download artifacts for detailed results (reports, screenshots, traces)
- Reproduce locally with the same Python/Node version used in CI
- Re-run with debug logging:
  ```
  Set repository variable: ACTIONS_STEP_DEBUG = true
  ```

### Common errors

| Symptom | Likely cause |
| ------------------------------------------------- | --------------------------------------------------- |
| `Resource not accessible by integration` | Missing/insufficient `permissions:` block |
| `Error: secret X not found` | Secret not configured at repo/org level |
| Tests pass locally but fail in CI | Different Python/Node version, missing system deps |
| Workflow runs but skips all jobs | Path filter excludes all changed files |
| Scheduled workflow not running | Repo inactive >60 days, or file not on `main` |

---

## Security Considerations

- **Pin actions to SHAs**, not floating tags (`@v4` can change without notice)
- **Restrict `GITHUB_TOKEN` permissions** at the workflow level:
  ```yaml
  permissions:
    contents: read
  ```
- **Avoid `pull_request_target`** unless you fully understand the security implications
- **Never echo secrets** to logs (`run: echo ${{ secrets.X }}` is unsafe)
- **Review third-party actions** before adding them to the repository
- **Use OpenID Connect (OIDC)** for cloud authentication where possible (e.g., `azure/login@v2` with `federated-credential`) instead of long-lived secrets

---

## Resources

- [GitHub Actions documentation](https://docs.github.com/en/actions)
- [Workflow syntax reference](https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions)
- [Security hardening for GitHub Actions](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [`actionlint`](https://github.com/rhysd/actionlint) — static checker for workflows
- [`act`](https://github.com/nektos/act) — run workflows locally
- [Azure login (OIDC)](https://learn.microsoft.com/azure/developer/github/connect-from-azure)
- Repository root README: [`../../README.md`](../../README.md)
