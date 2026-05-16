"""Task model used by the Aria core runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict
import uuid


@dataclass(slots=True)
class Task:
    """Structured task envelope for routing and execution."""

    type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
