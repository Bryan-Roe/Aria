#!/usr/bin/env python
"""Compatibility shim. Actual implementation in scripts/training/cli/self_learning_chat.py"""
from scripts.training.cli.self_learning_chat import main

if __name__ == "__main__":
    raise SystemExit(main())
