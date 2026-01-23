"""Workspace-level shim forwarding to talk_to_ai.utils.token_utils."""
from pathlib import Path
import sys

_package_root = Path(__file__).resolve().parent / "talk-to-ai" / "src"
if str(_package_root) not in sys.path:
    sys.path.insert(0, str(_package_root))

from talk_to_ai.utils.token_utils import *  # noqa: F401,F403
