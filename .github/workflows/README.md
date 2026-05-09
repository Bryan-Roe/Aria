# GitHub Actions Workflows

This directory contains all GitHub Actions workflows for the Aria repository. Workflows are organized by purpose and execution pattern.

## Workflow Inventory

### 🔄 Continuous Integration (CI)

- **`ci-pipeline.yml`** — Main CI pipeline
  - Runs on: push/PR to `main` and `dev`, daily schedule
  - Purpose: code validation, tests, daily training, model deployment
  - Typical duration: ~15–30 minutes

### ✅ Testing Workflows

- **`aria-tests.yml`** — Comprehensive Aria testing
  - Runs on: changes to `aria_web/` or Aria test files
  - Purpose: multi-Python (3.10–3.12), multi-browser E2E tests
  - Typical duration: ~20–30 minutes
  - Notes: path-filtered, more thorough than quick regression

- **`e2e-tests.yml`** — Quick regression testing
  - Runs on: any push/PR to `main`
  - Purpose: fast Aria regression tests
  - Typical duration: ~10–15 minutes
  - Notes: not path-filtered; catches broad regressions

### 🔬 Validation Workflows

- **`auto-validation.yml`** — Orchestrator validation
  - Runs on: changes to orchestrator configs/scripts, daily schedule
  - Purpose: validates `autotrain.yaml` and `quantum_autorun.yaml`
  - Typical duration: ~5–10 minutes

### ☁️ Cloud Workflows

- **`azureml-train.yml`** — Azure ML training
  - Runs on: manual trigger only
  - Purpose: submit LoRA fine-tuning jobs to Azure ML
  - Requires: Azure credentials and an ML workspace

- **`quantum-orchestration.yml`** — Azure Quantum
  - Runs on: push to `main`, manual trigger
  - Purpose: execute quantum workflows on Azure Quantum
  - Requires: Azure credentials and a Quantum workspace

## Common Trigger Patterns

### Automatic Triggers

```yaml
on:
  push:
    branches: [main]           # Runs on commits to main
  pull_request:
    branches: [main]           # Runs on PRs targeting main
  schedule:
    - cron: '0 2 * * *'        # Runs daily at 2 AM UTC
```

### Manual Triggers

```yaml
on:
  workflow_dispatch:           # Allows manual execution via GitHub UI
    inputs:
      parameter: ...           # Custom parameters
```

### Path Filtering

```yaml
on:
  push:
    paths:
      - 'aria_web/**'          # Only runs if these paths change
      - 'tests/**'
```

## Best Practices

### When to Use Each Workflow

- **Local Development**: run tests locally first (e.g., `pytest`)
- **PR Review**: `e2e-tests.yml` provides quick validation
- **Aria Changes**: `aria-tests.yml` runs comprehensive tests automatically
- **Daily CI**: `ci-pipeline.yml` catches integration issues overnight
- **Training**: use `azureml-train.yml` for GPU-accelerated cloud training
- **Quantum**: use `quantum-orchestration.yml` for quantum computing tasks

### Workflow Naming Convention

- Use descriptive names that indicate purpose
- Use a type suffix: `-tests.yml`, `-validation.yml`, `-train.yml`
- Group related workflows with consistent prefixes

### Adding a New Workflow (Checklist)

1. Choose an appropriate trigger pattern (push/PR/schedule/manual)
2. Add a header comment block explaining purpose and ownership
3. Use path filtering when possible to reduce unnecessary runs
4. Set appropriate `timeout-minutes` limits
5. Upload artifacts for debugging (logs, screenshots, reports)
6. Cache dependencies where it helps (pip/npm)
7. Update this README with the new workflow description

## Troubleshooting

### Workflow Not Running

- Check branch filters match your target branch
- Verify path filters include your changed files (if used)
- Ensure required secrets are configured
- Confirm the workflow file is on the default branch (or the branch you are pushing to)

### Workflow Failing

- Check job logs in the **Actions** tab
- Download artifacts for detailed results (reports, screenshots)
- Run equivalent commands locally to reproduce issues

### Reducing CI Time

- Use path filtering to avoid unnecessary runs
- Cache dependencies (pip, npm)
- Run expensive jobs only on schedule or manual trigger
- Parallelize independent jobs using `needs:` dependencies

## Resources

- GitHub Actions Documentation: https://docs.github.com/en/actions
- Workflow syntax: https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions
- Repository root README: ../../README.md
