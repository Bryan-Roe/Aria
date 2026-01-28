"""Backward-compatible entrypoint for chat CLI.

Delegates to talk_to_ai.cli.chat_cli.main to preserve existing scripts and tests.
"""
from talk_to_ai.cli.chat_cli import main

if __name__ == "__main__":
    raise SystemExit(main())
