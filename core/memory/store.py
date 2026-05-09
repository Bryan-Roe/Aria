"""
Aria Memory Store
Enables shared context across agents for autonomous planning and execution.
"""

from typing import Any, Dict, List, Optional
import time


class MemoryStore:
    def __init__(self):
        self.events: List[Dict[str, Any]] = []

    def write(self, event_type: str, data: Dict[str, Any]):
        self.events.append({
            "timestamp": time.time(),
            "type": event_type,
            "data": data,
        })

    def query(self, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        if event_type is None:
            return self.events
        return [e for e in self.events if e["type"] == event_type]

    def last(self, n: int = 10) -> List[Dict[str, Any]]:
        return self.events[-n:]
