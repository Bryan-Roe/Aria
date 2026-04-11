# Run Integration Contract Gate (Composite Action)

Wrapper action for `scripts/integration_contract_gate.sh`.

## Inputs

- `strict-endpoints` (default: `false`)
  - `true`: runs `--strict-endpoints`

## Example

```yaml
- uses: ./.github/actions/run-integration-contract-gate

- uses: ./.github/actions/run-integration-contract-gate
  with:
    strict-endpoints: 'true'
```
