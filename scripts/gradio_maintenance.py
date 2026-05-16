import os
import time
from datetime import datetime, timedelta
from typing import List


def list_conversation_files(conv_dir: str) -> List[str]:
    if not os.path.exists(conv_dir):
        return []
    files = [os.path.join(conv_dir, f) for f in os.listdir(conv_dir) if os.path.isfile(os.path.join(conv_dir, f))]
    return sorted(files)


def cleanup_old_conversations(conv_dir: str, max_age_days: int = 30) -> int:
    """Remove files older than max_age_days from conv_dir. Returns count removed."""
    if not os.path.exists(conv_dir):
        return 0
    now = time.time()
    cutoff = now - max_age_days * 24 * 3600
    removed = 0
    for fname in os.listdir(conv_dir):
        path = os.path.join(conv_dir, fname)
        if not os.path.isfile(path):
            continue
        try:
            mtime = os.path.getmtime(path)
            if mtime < cutoff:
                os.remove(path)
                removed += 1
        except Exception:
            pass
    return removed
