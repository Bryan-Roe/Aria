"""
Shared infrastructure for the Aria / QAI platform.

Re-exports key utilities so callers can write:
    from shared import load_json, validate_messages, safe_import
    from shared.chat_providers import BaseChatProvider

Heavy or optional modules (cosmos, telemetry, db_logging, sql_engine) are NOT
eagerly imported here — import them directly when needed so startup stays fast.
"""

from shared.file_cache import DEFAULT_TTL_SECONDS  # noqa: F401
from shared.file_cache import read_json_cached
from shared.http_utils import validate_messages  # noqa: F401
from shared.import_helpers import safe_import  # noqa: F401
# --- Lightweight, no-external-dependency helpers ---
from shared.json_utils import load_json  # noqa: F401
from shared.performance_utils import tail_file  # noqa: F401
from shared.script_utils import get_repo_root  # noqa: F401

__all__ = [
    # json_utils
    "load_json",
    # http_utils
    "validate_messages",
    # file_cache
    "read_json_cached",
    "DEFAULT_TTL_SECONDS",
    # script_utils
    "get_repo_root",
    # import_helpers
    "safe_import",
    # performance_utils
    "tail_file",
]
