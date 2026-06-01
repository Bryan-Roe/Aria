"""Thread-safe pub/sub bus for lightweight agent coordination."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, DefaultDict, Dict, List
import threading


class AgentBus:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._subscribers: DefaultDict[str, List[Callable[[Dict[str, Any]], Any]]] = defaultdict(list)

    def subscribe(self, topic: str, callback: Callable[[Dict[str, Any]], Any]) -> None:
        with self._lock:
            self._subscribers[topic].append(callback)

    def unsubscribe(self, topic: str, callback: Callable[[Dict[str, Any]], Any]) -> None:
        with self._lock:
            callbacks = self._subscribers.get(topic, [])
            self._subscribers[topic] = [entry for entry in callbacks if entry is not callback]
            if not self._subscribers[topic]:
                self._subscribers.pop(topic, None)

    def publish(self, topic: str, message: Dict[str, Any]) -> List[Any]:
        with self._lock:
            callbacks = list(self._subscribers.get(topic, []))
        results: List[Any] = []
        for callback in callbacks:
            results.append(callback(dict(message)))
        return results
