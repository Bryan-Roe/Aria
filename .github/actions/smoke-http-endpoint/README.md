# Smoke HTTP Endpoint (Composite Action)

Simple reusable endpoint smoke check for CI jobs.

## Inputs

- `url` (required)
- `method` (default: `GET`)
- `body` (optional JSON string for POST)
- `expected-status` (default: `200`)

## Example

```yaml
- uses: ./.github/actions/smoke-http-endpoint
  with:
    url: http://localhost:7071/api/ai/status

- uses: ./.github/actions/smoke-http-endpoint
  with:
    url: http://localhost:7071/api/ai/provider-probe
    method: POST
    body: '{"provider":"auto"}'
    expected-status: '200'
```
