"""Cosmos DB client scaffold for QAI.

Provides lazy singleton client & container access for chat sessions and quantum job metadata.
Initialization is gated by env var QAI_ENABLE_COSMOS=true and required Cosmos settings.

Env variables required:
  COSMOS_ENDPOINT
  COSMOS_KEY
  COSMOS_DATABASE (default: qai)
  COSMOS_CONTAINER (default: chat_sessions)

Partition key strategy:
  /userId for chat sessions (high cardinality recommended)
  For quantum jobs, you may create a separate container with /jobGroup or HPK later.
"""
from __future__ import annotations
import os
import logging
from typing import Optional, Dict, Any, Union

try:
    from azure.cosmos import CosmosClient, PartitionKey  # type: ignore
except Exception:  # pragma: no cover - dependency optional until installed
    CosmosClient = None  # type: ignore

_CLIENT: Optional[CosmosClient] = None
_CONTAINER: Optional[Any] = None  # Container proxy object when initialized


def _enabled() -> bool:
    return os.getenv("QAI_ENABLE_COSMOS", "false").lower() == "true"


def _settings_present() -> bool:
    return all(os.getenv(k) for k in ["COSMOS_ENDPOINT", "COSMOS_KEY"])


def init() -> bool:
    global _CLIENT, _CONTAINER
    if not _enabled():
        logging.info("[cosmos] Disabled via QAI_ENABLE_COSMOS flag.")
        return False
    if _CLIENT is not None:
        return True
    if CosmosClient is None:
        logging.warning("[cosmos] azure-cosmos package not available; cannot initialize.")
        return False
    if not _settings_present():
        logging.warning("[cosmos] Missing required settings (COSMOS_ENDPOINT / COSMOS_KEY).")
        return False

    endpoint = os.getenv("COSMOS_ENDPOINT")
    key = os.getenv("COSMOS_KEY")
    database_name = os.getenv("COSMOS_DATABASE", "qai")
    container_name = os.getenv("COSMOS_CONTAINER", "chat_sessions")

    try:
        _CLIENT = CosmosClient(endpoint, credential=key)  # type: ignore
        db = None
        # Create DB if not exists
        try:
            db = _CLIENT.create_database_if_not_exists(id=database_name)
        except Exception as e:
            logging.error(f"[cosmos] Failed creating database {database_name}: {e}")
            return False
        # Create container if not exists
        try:
            _CONTAINER = db.create_container_if_not_exists(
                id=container_name,
                partition_key=PartitionKey(path="/userId"),
                offer_throughput=400,
            )
        except Exception as e:
            logging.error(f"[cosmos] Failed creating container {container_name}: {e}")
            return False
        logging.info(f"[cosmos] Initialized container {container_name} in database {database_name}.")
        return True
    except Exception as e:
        logging.error(f"[cosmos] Initialization error: {e}")
        return False


def container():
    if _CLIENT is None or _CONTAINER is None:
        return None
    return _CONTAINER


def health() -> Dict[str, Any]:
    """Return Cosmos client health/status details without raising.

    Attempts lazy init if enabled to surface container readiness.
    """
    status: Dict[str, Any] = {
        "enabled": _enabled(),
        "settings_present": _settings_present(),
        "initialized": False,
        "container_id": None,
        "database": os.getenv("COSMOS_DATABASE", "qai"),
        "container": os.getenv("COSMOS_CONTAINER", "chat_sessions"),
        "error": None,
    }
    if not status["enabled"]:
        return status
    try:
        if init():
            status["initialized"] = _CLIENT is not None and _CONTAINER is not None
            if _CONTAINER is not None:
                try:
                    status["container_id"] = getattr(_CONTAINER, "id", None)
                except Exception:  # pragma: no cover - defensive
                    pass
    except Exception as e:  # pragma: no cover - defensive
        status["error"] = str(e)
    return status


def record_chat_message(user_id: str, message: Dict[str, Any], provider: str, model: str) -> bool:
    """Persist a single chat message. user_id may be 'anonymous' if not provided."""
    if not init():  # ensures initialization or early exit
        return False
    c = container()
    if c is None:
        return False
    try:
        doc = {
            "id": f"{user_id}-{message.get('timestamp')}-{hash(message.get('content','')) & 0xffffffff}",
            "userId": user_id,
            "role": message.get("role"),
            "content": message.get("content"),
            "provider": provider,
            "model": model,
        }
        c.upsert_item(doc)
        return True
    except Exception as e:
        logging.warning(f"[cosmos] Failed to upsert chat message: {e}")
        return False


def record_chat_session(user_id: str, messages: list[Dict[str, Any]], provider: str, model: str) -> bool:
    """Persist entire chat session as one document (alternative strategy)."""
    if not init():
        return False
    c = container()
    if c is None:
        return False
    try:
        doc = {
            "id": f"session-{user_id}-{len(messages)}-{hash(str(messages)) & 0xffffffff}",
            "userId": user_id,
            "messages": messages,
            "provider": provider,
            "model": model,
            "messageCount": len(messages),
        }
        c.upsert_item(doc)
        return True
    except Exception as e:
        logging.warning(f"[cosmos] Failed to upsert chat session: {e}")
        return False

__all__ = [
    "init",
    "record_chat_message",
    "record_chat_session",
    "container",
    "health",
]
