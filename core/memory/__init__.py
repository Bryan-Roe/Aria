"""Memory helpers for the Aria core runtime.

This module intentionally supports two invocation modes:

- Package import: ``from core.memory import MemoryStore``
- Direct script run: ``python core/memory/__init__.py`` (demo mode)
"""

from __future__ import annotations

from datetime import datetime, timezone
import json

try:  # Normal package import
    from core.memory.store import MemoryStore
except ModuleNotFoundError:  # Direct script execution fallback
    from store import MemoryStore  # type: ignore[no-redef]


def demo_memory_store() -> dict:
    """Run a tiny deterministic memory-store demo and return its snapshot."""
    memory = MemoryStore(max_events=20)
    memory.write("goal_created", {"goal": "improve core runtime"})
    memory.write("task_result", {"task": "health_check", "status": "ok"})
    memory.write(
        "task_result",
        {"task": "summarize", "status": "ok"},
        timestamp=datetime.now(timezone.utc),
    )
    return {
        "total_events": len(memory),
        "counts": memory.count_by_type(),
        "recent": memory.last(2),
    }


__all__ = ["MemoryStore", "demo_memory_store"]


if __name__ == "__main__":
    print(json.dumps(demo_memory_store(), indent=2))
