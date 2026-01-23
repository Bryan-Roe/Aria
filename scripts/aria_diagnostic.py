#!/usr/bin/env python
"""Compatibility shim. Implementation moved to scripts/monitoring/cli/aria_diagnostic.py"""
from scripts.monitoring.cli.aria_diagnostic import main

if __name__ == "__main__":
    raise SystemExit(main())
