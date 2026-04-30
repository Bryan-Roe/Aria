# validate-site-bundles

Composite GitHub Action to validate the `generated_sites/` contract.

## Inputs

- `strict-metadata` (default: `true`)
  - `true`: runs `python3 scripts/validate_site_bundles.py --strict-metadata`
  - `false`: runs `python3 scripts/validate_site_bundles.py`

## Usage

```yaml
- name: Validate generated site bundles (strict)
  uses: ./.github/actions/validate-site-bundles
  with:
    strict-metadata: 'true'
```

```yaml
- name: Validate generated site bundles (legacy-compatible)
  uses: ./.github/actions/validate-site-bundles
  with:
    strict-metadata: 'false'
```
