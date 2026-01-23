"""Backward-compatible shim for AGI provider - delegates to actual implementation."""
# Direct import from the actual module location
import sys
from pathlib import Path

_providers_path = Path(__file__).resolve().parent / "talk_to_ai" / "providers"
if str(_providers_path) not in sys.path:
    sys.path.insert(0, str(_providers_path))

# Import from the actual agi_provider module in the providers package
from agi_provider import *  # noqa: F401,F403
