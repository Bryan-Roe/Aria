#!/usr/bin/env python
"""Compatibility shim. Actual implementation in scripts/training/cli/auto_data_train.py"""
from scripts.training.cli.auto_data_train import main

if __name__ == "__main__":
    raise SystemExit(main())
