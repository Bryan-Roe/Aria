# GitHub Actions Workflows

This directory contains **14 GitHub Actions workflows** for the Aria repository, organized by purpose and execution pattern.

## Quick Navigation

- **Need to find the right workflow?** See [../WORKFLOWS.md](../WORKFLOWS.md) for full details.
- **Want to run tests locally?** Use `pytest` — see `pytest.ini` at repo root.
- **Want to trigger a workflow?** Go to Actions tab → Select workflow → Run workflow.
- **Want to understand trigger patterns?** See "When workflows run" below.

## Workflow Organization

### 🔄 Continuous Integration (CI)

- **`ci-pipeline.yml`** - Main CI pipeline
  - Runs on: Push/PR to main/dev, daily schedule
  - Purpose: Code validation, tests, daily training, model deployment
  - Duration: ~15-30 minutes

### ✅ Testing Workflows

- **`aria-tests.yml`** - Comprehensive Aria testing
  - Runs on: Changes to `web/aria_web/` or Aria test files
  - Purpose: Multi-version (3.10-3.12), multi-browser E2E tests
  - Duration: ~20-30 minutes
  - Note: Path-filtered, more thorough

- **`e2e-tests.yml`** - Quick regression testing
  - Runs on: Any push/PR to main
  - Purpose: Fast Aria regression tests
  - Duration: ~10-15 minutes
  - Note: No path filtering, catches broader regressions

### 🔬 Validation Workflows

- **`auto-validation.yml`** - Orchestrator validation
  - Runs on: Changes to orchestrator configs/scripts, daily schedule
  - Purpose: Validates orchestrator configs under `config/training/`, `config/quantum/`, and `config/evaluation/`
  - Duration: ~5-10 minutes

### ☁️ Cloud Workflows

- **`azureml-train.yml`** - Azure ML training
  - Runs on: Manual trigger only
  - Purpose: Submit LoRA fine-tuning jobs to Azure ML
  - Requires: Azure credentials, ML workspace

- **`quantum-orchestration.yml`** - Azure Quantum
  - Runs on: Push to main, manual trigger
  - Purpose: Execute quantum workflows on Azure Quantum
  - Requires: Azure credentials, Quantum workspace

## Maintenance & Deployment Workflows

- **`release.yml`** - Automated releases
  - Runs on: Git tags (v*.*.*), manual
  - Purpose: Create GitHub releases with changelog and artifacts
  
- **`stale.yml`** - Auto-close stale issues/PRs
  - Runs on: Daily midnight UTC, manual
  - Purpose: Issues (60d) and PRs (30d) auto-close
  
- **`pages.yml`** - Documentation deployment
  - Runs on: docs/ changes, manual
  - Purpose: Deploy docs to GitHub Pages
  
- **`workflow-validation.yml`** - Workflow syntax checks
  - Runs on: Workflow file changes, push to main
  - Purpose: Validate YAML syntax for all workflows

## Workflow Patterns

### Automatic Triggers

```yaml
on:
  push:
    branches: [main]           # Runs on commits to main
  pull_request:
    branches: [main]           # Runs on PRs targeting main
  schedule:
    - cron: '0 2 * * *'       # Runs daily at 2 AM UTC
```

### Manual Triggers

```yaml
on:
  workflow_dispatch:            # Allows manual execution via GitHub UI
    inputs:
      parameter: ...            # Custom parameters
```

### Path Filtering

```yaml
on:
  push:
    paths:
      - 'web/aria_web/**'          # Only runs if these paths change
      - 'tests/**'
```

## Best Practices

### When to Use Each Workflow

- **Local Development**: Run tests locally first with `pytest`
- **PR Review**: `e2e-tests.yml` provides quick validation
- **Aria Changes**: `aria-tests.yml` runs comprehensive tests automatically
- **Daily CI**: `ci-pipeline.yml` catches integration issues overnight
- **Training**: Use `azureml-train.yml` for GPU-accelerated cloud training
- **Quantum**: Use `quantum-orchestration.yml` for quantum computing tasks

### Workflow Naming Convention

- Use descriptive names that indicate purpose
- Suffix with type: `-tests.yml`, `-validation.yml`, `-train.yml`
- Group related workflows with consistent prefixes

### Adding New Workflows

1. Choose appropriate trigger pattern (push/PR/schedule/manual)
2. Add header comment block explaining purpose
3. Use path filtering when possible to reduce unnecessary runs
4. Set appropriate timeout limits
5. Upload artifacts for debugging
6. Update this README with workflow description

## Troubleshooting

### Workflow Not Running

- Check branch filters match your target branch
- Verify path filters include your changed files
- Ensure required secrets are configured

### Workflow Failing

- Check job logs in GitHub Actions tab
- Download artifacts for detailed results
- Run equivalent commands locally for debugging

### Reducing CI Time

- Use path filtering to avoid unnecessary runs
- Cache dependencies (pip, npm)
- Run expensive jobs only on schedule or manual trigger
- Parallelize independent jobs with `needs:` dependencies

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [Repository Root README](../../README.md)
