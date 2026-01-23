#!/usr/bin/env python
"""Compatibility shim. Actual implementation in scripts/training/cli/final_validation.py"""
from scripts.training.cli.final_validation import main

if __name__ == "__main__":
    raise SystemExit(main())
