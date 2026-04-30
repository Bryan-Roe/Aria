# Validate Composite Actions (Composite Action)

Runs repository script-based validation for local composite actions.

## Inputs

- `script-path` (default: `scripts/validate_composite_actions.py`)

## Example

```yaml
- uses: ./.github/actions/validate-composite-actions

- uses: ./.github/actions/validate-composite-actions
  with:
    script-path: scripts/validate_composite_actions.py
```
