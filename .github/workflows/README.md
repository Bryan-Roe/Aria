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

#### `merge-gate.yml` — Canonical PR validation gate

- **Triggers:** pull requests to `main`, merge queue, manual dispatch
- **Purpose:** single branch-protection check (`Merge Gate / All Gates Passed`) with fan-in across unit tests, PR validation, security review, integration contract checks, setup guardrails, and automatic dependency submission completion
- **Duration:** ~10–20 minutes
- **Owner:** Platform team

#### `ci.yml` — Branch CI validation

- **Triggers:** push to `main`, manual dispatch
- **Purpose:** linting, type-checking (advisory), and matrix unit tests on branch updates
- **Duration:** ~10–25 minutes
- **Owner:** Platform team

#### `pr-tests.yml` — Scheduled/manual regression lane

- **Triggers:** push to `main`, daily schedule (`0 3 * * *` UTC), manual dispatch
- **Purpose:** broader regression lane including pre-commit + unit tests and optional watcher execution
- **Duration:** ~10–20 minutes
- **Owner:** Platform team

#### `ci-pipeline.yml` — Scheduled automation pipeline

- **Triggers:** daily schedule (`0 2 * * *` UTC), manual dispatch
- **Purpose:** orchestrated validation, integration smoke, scheduled training, and deployment chain
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

#### `pr-test-summary-comment.yml` — AI PR comment summary for workflow runs

- **Triggers:** `workflow_run` (currently `AGI smoke`)
- **Purpose:** posts or updates a PR comment with AI-written action-run summaries
- **Duration:** ~1–3 minutes
- **Notes:** uses `OPENAI_API_KEY` when available; falls back to deterministic summary text

### 🔬 Validation Workflows

#### `auto-validation.yml` — Orchestrator validation

- **Triggers:** changes to orchestrator configs/scripts, daily schedule
- **Purpose:** validates `autotrain.yaml` and `quantum_autorun.yaml`
- **Duration:** ~5–10 minutes

#### `default-github-automation.yml` — GitHub baseline verification

- **Triggers:** changes to baseline GitHub automation files, weekly schedule, manual dispatch
- **Purpose:** verifies core repository automation remains configured (merge gate, labeler, stale, dependency review, dependabot)
- **Duration:** ~2–5 minutes

#### `ruleset-json-validation.yml` — Ruleset template validation

- **Triggers:** changes to `.github/rulesets/*.json` and ruleset docs, weekly schedule, manual dispatch
- **Purpose:** validates ruleset JSON template structure and required status-check context alignment
- **Duration:** ~2–5 minutes

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
| `merge-gate.yml` | ❌ | ✅ | ❌ | ✅ | ❌ | 10–20 min |
| `ci.yml` | ✅ | ❌ | ❌ | ✅ | ✅ | 10–25 min |
| `pr-tests.yml` | ✅ | ❌ | ✅ | ✅ | ❌ | 10–20 min |
| `ci-pipeline.yml` | ❌ | ❌ | ✅ | ✅ | ❌ | 15–30 min |
| `aria-tests.yml` | ✅ | ✅ | ❌ | ✅ | ✅ | 20–30 min |
| `e2e-tests.yml` | ✅ | ✅ | ❌ | ✅ | ❌ | 10–15 min |
| `pr-test-summary-comment.yml` | ❌ | ❌ | ❌ | ❌ | n/a | 1–3 min |
| `auto-validation.yml` | ✅ | ✅ | ✅ | ✅ | ✅ | 5–10 min |
| `default-github-automation.yml` | ✅ | ✅ | ✅ | ✅ | ✅ | 2–5 min |
| `ruleset-json-validation.yml` | ✅ | ✅ | ✅ | ✅ | ✅ | 2–5 min |
| `azureml-train.yml` | ❌ | ❌ | ❌ | ✅ | n/a | 30+ min |
| `quantum-orchestration.yml` | ✅ | ❌ | ❌ | ✅ | ❌ | varies |

---

## Canonical PR Merge Policy

- **Single required status check:** `Merge Gate / All Gates Passed`
- **Canonical PR validation workflow:** `.github/workflows/merge-gate.yml`
- **Guardrail gate in merge path:** `setup-guardrails` (runs `./.github/actions/run-setup-verify`)
- **Dependency graph guard in merge path:** `dependency-submission` waits for GitHub's automatic `submit-nuget` check on PR heads before the fan-in gate can pass
- **Support-only lanes (not required for merge):** `ci.yml`, `pr-tests.yml`, and `ci-pipeline.yml`
- **Workflow hygiene checks remain active:** `workflow-validation.yml` and `actionlint.yml` for workflow/config changes

### Auto-Merge Policy

Auto-merge is controlled by `.github/workflows/auto-merge.yml` (consolidated from the old `auto-merge.yml` + `auto-merge-on-ci.yml`).

| Job | Trigger | Behaviour |
|-----|---------|-----------|
| `prepare-github-actions-pr` | `pull_request` from `github-actions[bot]` | Adds the `autofix` label when missing and marks draft PRs ready for review so the standard auto-merge flow can take over |
| `enable` | `pull_request` labeled `auto-merge` or `autofix` | Arms GitHub native auto-merge (squash) and posts an informational comment |
| `disable` | `pull_request` last matching label removed | Disables native auto-merge |
| `merge-on-gate-pass` | `check_run` completed for `All Gates Passed` | Evaluates all associated PRs: checks label, draft, fork, conflicts, and review state; squash-merges eligible PRs and posts results |
| `bot-approve` | `pull_request` with auto-merge label, or any same-repo `github-actions[bot]` PR | Approves PRs authored by bot actors listed in `BOT_APPROVE_ALLOWLIST` using `AUTO_MERGE_APPROVE_TOKEN`; `github-actions[bot]` bypasses the repo-variable gate |
| `finish-open-prs` | `schedule` (every 30 min) or manual dispatch | Sweeps open PRs, verifies labels/checks/reviews/mergeability, and squash-merges eligible PRs (supports dry-run + max PR cap inputs) |

**Eligibility requirements** (enforced by `merge-on-gate-pass` and codified in `.github/actions/check-auto-merge-eligibility/action.yml`):
- PR is not a draft
- PR targets `main`
- PR is from the same repo (forks are always skipped)
- PR has `auto-merge` or `autofix` label
- Merge state is not `DIRTY` / `BEHIND` / `BLOCKED`
- No `CHANGES_REQUESTED` reviews
- At least one `APPROVED` review

**Bot-approve actor allowlist** (`BOT_APPROVE_ALLOWLIST` env var in `auto-merge.yml`):
- `github-actions[bot]`
- `copilot-swe-agent[bot]`

Same-repo PRs authored by `github-actions[bot]` are automatically labeled `autofix`, moved out of draft, and auto-approved (when `AUTO_MERGE_APPROVE_TOKEN` is configured) so they can merge once `Merge Gate / All Gates Passed` succeeds.

Human-authored PRs **always** require a real human approval regardless of the `AUTO_MERGE_BOT_APPROVE` setting.

**Deprecated:** `auto-merge-on-ci.yml` is now a manual-only stub. All auto-merge logic is in `auto-merge.yml`.

---

## Required Secrets & Variables

Configure these under **Settings → Secrets and variables → Actions**.

| Name | Type | Used by | Description |
| -------------------------- | ------- | ------------------------------------------------ | ------------------------------------------ |
| `AZURE_CREDENTIALS` | Secret | `azureml-train.yml`, `quantum-orchestration.yml` | Service principal JSON for Azure login |
| `AZUREML_WORKSPACE` | Variable | `azureml-train.yml` | Azure ML workspace name |
| `AZUREML_RESOURCE_GROUP` | Variable | `azureml-train.yml` | Azure resource group |
| `AZURE_QUANTUM_WORKSPACE` | Variable | `quantum-orchestration.yml` | Azure Quantum workspace name |
| `OPENAI_API_KEY` | Secret | `ci-pipeline.yml`, `pr-test-summary-comment.yml` (optional) | OpenAI API access for provider integration tests and AI-generated PR workflow summaries (falls back to deterministic summary when unset) |
| `AZURE_OPENAI_ENDPOINT` | Secret | `ci-pipeline.yml` (optional) | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_API_KEY` | Secret | `ci-pipeline.yml` (optional) | Azure OpenAI API key |
| `AUTO_MERGE_APPROVE_TOKEN` | Secret | `auto-merge.yml` (bot-approve job) | PAT with `pull-requests:write` scope issued by a separate identity; required for automated approval of bot-authored PRs, including `github-actions[bot]`. Never use `GITHUB_TOKEN` — it cannot approve its own PRs. |
| `AUTO_MERGE_BOT_APPROVE` | Variable | `auto-merge.yml` (bot-approve job) | Set to `'true'` to enable automated approval of allowlisted bot PRs other than `github-actions[bot]`. `github-actions[bot]` always attempts auto-approval when the PAT secret is configured. Human-authored PRs always require a human approval. |

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
- **PR review / merge readiness:** `merge-gate.yml` is the canonical merge decision path
- **Branch CI health:** `ci.yml` validates pushed changes with lint + tests
- **Scheduled regression lane:** `pr-tests.yml` and `ci-pipeline.yml` catch non-PR regressions
- **Aria changes:** `aria-tests.yml` runs automatically via path filters
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
