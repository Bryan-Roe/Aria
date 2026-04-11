# Run Pytest Suite (Composite Action)

Reusable wrapper for `pytest` execution in workflows.

## Inputs

- `test-path` (default: `tests/`)
- `marker-expression` (default: empty)
- `extra-args` (default: `--maxfail=1 -q`)
- `python-executable` (default: `python`)

## Examples

```yaml
- uses: ./.github/actions/run-pytest-suite

- uses: ./.github/actions/run-pytest-suite
  with:
    test-path: tests/
    marker-expression: "not slow and not azure"
    extra-args: "--maxfail=1 -q"

- uses: ./.github/actions/run-pytest-suite
  with:
    test-path: tests/test_ollama_provider.py
    extra-args: "-q"
```
