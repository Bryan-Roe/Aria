# Validate Function Bindings (Composite Action)

Validates Azure Functions `function.json` files for:
- valid JSON
- non-empty `bindings`
- basic HTTP trigger requirements

## Inputs

- `functions-path` (default: `functions`)
- `require-http-route` (default: `true`)

## Example

```yaml
- uses: ./.github/actions/validate-function-bindings

- uses: ./.github/actions/validate-function-bindings
  with:
    functions-path: functions
    require-http-route: 'true'
```
