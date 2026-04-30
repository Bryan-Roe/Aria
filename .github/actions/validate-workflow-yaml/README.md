# Validate Workflow YAML (Composite Action)

Validates workflow YAML files for:
- parseable YAML
- top-level trigger (`on` or YAML 1.1 bool-aliased `True` key)
- optional `jobs` key requirement

## Inputs

- `workflows-path` (default: `.github/workflows`)
- `require-jobs` (default: `true`)

## Example

```yaml
- uses: ./.github/actions/validate-workflow-yaml
  with:
    workflows-path: .github/workflows
    require-jobs: 'true'
```
