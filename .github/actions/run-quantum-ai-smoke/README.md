# Run Quantum AI Smoke (Composite Action)

Wrapper around `quantum-ai/scripts/smoke_quantum_code_llm.py`.

## Inputs

- `backend` (default: `classical`)
- `epochs` (default: `1`)

## Example

```yaml
- uses: ./.github/actions/run-quantum-ai-smoke

- uses: ./.github/actions/run-quantum-ai-smoke
  with:
    backend: classical
    epochs: '1'
```
