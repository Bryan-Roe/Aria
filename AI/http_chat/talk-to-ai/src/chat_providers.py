"""Backward-compatible shim for chat providers.

This module now lives in talk_to_ai.providers. Importing from here forwards
symbols to the package while keeping legacy imports working.
"""
from talk_to_ai.providers import *  # noqa: F401,F403
