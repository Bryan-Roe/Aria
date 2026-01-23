#!/usr/bin/env python
"""Compatibility shim. Actual implementation in scripts/training/cli/fast_validate.py"""
from scripts.training.cli.fast_validate import main

if __name__ == "__main__":
    raise SystemExit(main())
