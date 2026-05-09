# Scan TODO/FIXME in Changed Files (Composite Action)

Scans changed files in a git diff range for TODO/FIXME-like markers.

This action is intentionally non-failing for marker hits; it is intended as a review aid.

## Inputs

- `base-ref` (required): branch/ref to diff from (e.g., `main`)
- `head-ref` (default: `HEAD`)
- `pattern` (default: `TODO|FIXME`)

## Example

```yaml
- uses: ./.github/actions/scan-todo-fixme
  with:
    base-ref: ${{ github.base_ref }}
```
