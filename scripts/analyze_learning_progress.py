#!/usr/bin/env python
"""Compatibility shim. Actual implementation in scripts/training/cli/analyze_learning_progress.py"""
from scripts.training.cli.analyze_learning_progress import main

if __name__ == "__main__":
    raise SystemExit(main())
