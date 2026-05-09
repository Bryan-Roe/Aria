Next steps and how to run the test watcher

Summary
-------
A lightweight test watcher script was added at `scripts/test_watcher.py` and tests were run successfully once. This document explains how to run the watcher, run full test suites, troubleshooting, and recommended next steps.

How to run the watcher (development)
----------------------------------
Start the watcher to automatically re-run tests when files change:

```bash
python3 scripts/test_watcher.py
```

What the watcher does
- Runs the project's tests on file change and prints results to stdout.
- Stops on first failure by default (configurable in the watcher script).

Run full tests manually
----------------------
To run the test suite manually (single run):

```bash
python3 -m pytest tests -q --maxfail=1 && echo FULL_PYTEST_OK
```

Troubleshooting
---------------
- If Python or pytest is missing: install via your system package manager or virtualenv; recommended virtualenv steps:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # or `pip install pytest` if requirements not provided
```

- If the watcher doesn't pick up changes, ensure inotify/FS events are available (Linux) or use editor save behavior that actually writes the file.

Recommended next actions
------------------------
1. Add a short README section referencing `scripts/test_watcher.py` and `NEXT_STEPS.md` for contributors.
2. Integrate the watcher or test invocation into CI (e.g., GitHub Actions) to run the full test suite on PRs.
3. Consider adding a lightweight dev dependency manifest (`requirements-dev.txt` or `pyproject.toml`) listing `pytest` and any tooling used by the watcher.
4. Optionally add a `--watch` mode to the test runner or support cross-platform file-watch libraries for broader compatibility.

If you want, I can: create/update a README entry, add a minimal CI job for running tests, or add a `requirements-dev.txt` — tell me which and I'll proceed.
