# Check Workflow Common Issues (Composite Action)

Runs a lightweight policy scan across workflow files:
- warns on deprecated action versions (`checkout@v1/v2`, `setup-python@v1-v4`, `setup-node@v1-v3`, `cache@v1-v3`)
- fails on hardcoded GitHub token-like patterns

Only workflow files (`*.yml`, `*.yaml`) are scanned.

## Inputs

- `workflows-path` (default: `.github/workflows`)

## Example

```yaml
- uses: ./.github/actions/check-workflow-common-issues
  with:
    workflows-path: .github/workflows
```
