# Validate Action References (Composite Action)

Scans workflow `uses:` references and warns when external actions do not specify a version tag.

## Inputs

- `workflows-path` (default: `.github/workflows`)

## Example

```yaml
- uses: ./.github/actions/validate-action-references
  with:
    workflows-path: .github/workflows
```
