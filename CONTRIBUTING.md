## Contributing to Aria

Thank you — contributions are welcome. This file contains focused developer instructions for running tests and the test watcher.

Running tests
-------------
Run the full test suite once:

```bash
python3 -m pytest tests -q --maxfail=1 && echo FULL_PYTEST_OK
```

Reproducible dev environment
----------------------------
Create a virtualenv and install development dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Test watcher
-----------
There is a lightweight watcher at `scripts/test_watcher.py` that re-runs tests on file changes. See `NEXT_STEPS.md` for additional notes and troubleshooting.

Codespaces / Devcontainer
-------------------------
This repo includes a `.devcontainer/devcontainer.json` that sets up a Python dev container and installs `requirements-dev.txt` on first start.

CI
--
A minimal GitHub Actions workflow `.github/workflows/pr-tests.yml` runs `pytest` on pull requests targeting `main`.

If you'd like me to add additional contributor guidelines (linting, PR template, or codeowners), I can add those next.
