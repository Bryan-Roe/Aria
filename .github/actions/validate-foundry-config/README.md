# validate-foundry-config

Composite action that validates `.foundry/.deployment.json` via `scripts/validate_foundry_config.py`.

## Inputs

- `script-path` (default: `scripts/validate_foundry_config.py`)

## Usage

```yaml
- name: Validate Foundry config
  uses: ./.github/actions/validate-foundry-config
```
