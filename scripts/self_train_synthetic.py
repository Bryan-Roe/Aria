#!/usr/bin/env python
"""Compatibility shim. Actual implementation in scripts/training/cli/self_train_synthetic.py"""
from scripts.training.cli.self_train_synthetic import main

if __name__ == "__main__":
    raise SystemExit(main())
