"""Module entrypoint so ``python -m aria_bot`` works."""

from __future__ import annotations

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
