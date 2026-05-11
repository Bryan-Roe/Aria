"""Central configuration layer for the Aria platform.

Uses environment variables with safe defaults for local development.
Azure Key Vault integration is enabled when ``QAI_KEYVAULT_URL`` is set.

Usage::

    from shared.config import get_settings

    settings = get_settings()
    print(settings.azure_openai_endpoint)
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import List, Optional

_LOG = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Try to import pydantic v2 BaseSettings; fall back to a plain dataclass-style
# class so the module never hard-fails in environments without pydantic.
# ---------------------------------------------------------------------------
try:
    from pydantic import Field, field_validator
    from pydantic_settings import BaseSettings
    try:
        from pydantic import ConfigDict as _ConfigDict
    except ImportError:
        _ConfigDict = None  # type: ignore[assignment,misc]

    _PYDANTIC_AVAILABLE = True
except ImportError:  # pragma: no cover
    try:
        # pydantic v1 compatibility
        from pydantic import BaseSettings, Field, validator as field_validator  # type: ignore[assignment,no-redef]
        _ConfigDict = None  # type: ignore[assignment]

        _PYDANTIC_AVAILABLE = True
    except ImportError:
        _PYDANTIC_AVAILABLE = False
        BaseSettings = object  # type: ignore[assignment,misc]
        Field = None  # type: ignore[assignment]
        field_validator = None  # type: ignore[assignment]
        _ConfigDict = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Settings definition
# ---------------------------------------------------------------------------


if _PYDANTIC_AVAILABLE:

    class Settings(BaseSettings):  # type: ignore[misc]
        """Platform-wide settings driven by environment variables.

        All values have safe local-dev defaults so the application starts without
        any cloud credentials.  Azure-specific features are disabled by default
        and activated by setting the corresponding env vars.
        """

        # ------------------------------------------------------------------
        # Azure OpenAI
        # ------------------------------------------------------------------
        azure_openai_api_key: Optional[str] = Field(default=None, alias="AZURE_OPENAI_API_KEY")
        azure_openai_endpoint: Optional[str] = Field(default=None, alias="AZURE_OPENAI_ENDPOINT")
        azure_openai_deployment: Optional[str] = Field(
            default=None, alias="AZURE_OPENAI_DEPLOYMENT"
        )
        azure_openai_api_version: str = Field(
            default="2024-02-01", alias="AZURE_OPENAI_API_VERSION"
        )

        # ------------------------------------------------------------------
        # OpenAI
        # ------------------------------------------------------------------
        openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")

        # ------------------------------------------------------------------
        # LM Studio / local inference
        # ------------------------------------------------------------------
        lmstudio_base_url: Optional[str] = Field(default=None, alias="LMSTUDIO_BASE_URL")

        # ------------------------------------------------------------------
        # Provider selection
        # ------------------------------------------------------------------
        provider_priority: List[str] = Field(
            default=["azure", "openai", "lmstudio", "local"],
            alias="QAI_PROVIDER_PRIORITY",
        )

        # ------------------------------------------------------------------
        # Database
        # ------------------------------------------------------------------
        db_connection_string: Optional[str] = Field(default=None, alias="QAI_DB_CONN")
        sql_pool_size: int = Field(default=10, alias="QAI_SQL_POOL_SIZE")

        # ------------------------------------------------------------------
        # Cosmos DB (optional, feature-flagged)
        # ------------------------------------------------------------------
        enable_cosmos: bool = Field(default=False, alias="QAI_ENABLE_COSMOS")
        cosmos_endpoint: Optional[str] = Field(default=None, alias="COSMOS_ENDPOINT")
        cosmos_key: Optional[str] = Field(default=None, alias="COSMOS_KEY")
        cosmos_database: Optional[str] = Field(default=None, alias="COSMOS_DATABASE")
        cosmos_container: Optional[str] = Field(default=None, alias="COSMOS_CONTAINER")

        # ------------------------------------------------------------------
        # Azure Key Vault (optional)
        # ------------------------------------------------------------------
        keyvault_url: Optional[str] = Field(default=None, alias="QAI_KEYVAULT_URL")

        # ------------------------------------------------------------------
        # Observability
        # ------------------------------------------------------------------
        log_level: str = Field(default="INFO", alias="QAI_LOG_LEVEL")
        enable_structured_logging: bool = Field(
            default=False, alias="QAI_STRUCTURED_LOGGING"
        )
        applicationinsights_connection_string: Optional[str] = Field(
            default=None, alias="APPLICATIONINSIGHTS_CONNECTION_STRING"
        )

        # ------------------------------------------------------------------
        # Autonomous training orchestrator
        # ------------------------------------------------------------------
        orchestrator_cycle_interval_minutes: int = Field(
            default=30, alias="QAI_ORCHESTRATOR_CYCLE_MINUTES"
        )
        orchestrator_max_retries: int = Field(default=3, alias="QAI_ORCHESTRATOR_MAX_RETRIES")
        orchestrator_backoff_base: float = Field(
            default=2.0, alias="QAI_ORCHESTRATOR_BACKOFF_BASE"
        )

        # ------------------------------------------------------------------
        # Local TTS fallback
        # ------------------------------------------------------------------
        enable_local_tts: bool = Field(default=False, alias="QAI_ENABLE_LOCAL_TTS")

        # ------------------------------------------------------------------
        # Concurrency limits
        # ------------------------------------------------------------------
        max_concurrent_training_jobs: int = Field(
            default=4, alias="QAI_MAX_CONCURRENT_TRAINING_JOBS"
        )

        if _ConfigDict is not None:
            model_config = _ConfigDict(
                extra="ignore",
                env_file=".env",
                env_file_encoding="utf-8",
                populate_by_name=True,
            )
        else:
            model_config = {  # type: ignore[assignment]
                "extra": "ignore",
                "env_file": ".env",
                "env_file_encoding": "utf-8",
                "populate_by_name": True,
            }

        @field_validator("log_level", mode="before")
        @classmethod
        def _validate_log_level(cls, v: str) -> str:
            upper = str(v).upper()
            valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
            if upper not in valid:
                _LOG.warning("Invalid log level '%s'; defaulting to INFO", v)
                return "INFO"
            return upper

        # ------------------------------------------------------------------
        # Derived helpers
        # ------------------------------------------------------------------

        @property
        def azure_openai_ready(self) -> bool:
            """Return True when all four Azure OpenAI vars are set."""
            return all(
                [
                    self.azure_openai_api_key,
                    self.azure_openai_endpoint,
                    self.azure_openai_deployment,
                    self.azure_openai_api_version,
                ]
            )

        @property
        def openai_ready(self) -> bool:
            """Return True when the OpenAI key is set."""
            return bool(self.openai_api_key)

        @property
        def lmstudio_ready(self) -> bool:
            """Return True when an LM Studio URL is configured."""
            return bool(self.lmstudio_base_url)

        def active_provider(self) -> str:
            """Return the name of the first ready provider in the priority list."""
            checks = {
                "azure": self.azure_openai_ready,
                "openai": self.openai_ready,
                "lmstudio": self.lmstudio_ready,
            }
            for name in self.provider_priority:
                if checks.get(name, False):
                    return name
            return "local"

        def summary(self) -> dict:
            """Return a non-secret summary suitable for health endpoints."""
            return {
                "active_provider": self.active_provider(),
                "azure_openai_ready": self.azure_openai_ready,
                "openai_ready": self.openai_ready,
                "lmstudio_ready": self.lmstudio_ready,
                "db_enabled": bool(self.db_connection_string),
                "cosmos_enabled": self.enable_cosmos,
                "keyvault_enabled": bool(self.keyvault_url),
                "log_level": self.log_level,
                "structured_logging": self.enable_structured_logging,
                "local_tts_enabled": self.enable_local_tts,
            }

else:
    # Minimal fallback when pydantic is not installed
    class Settings:  # type: ignore[no-redef]
        """Fallback settings when pydantic is unavailable."""

        def __init__(self) -> None:
            self.azure_openai_api_key = os.environ.get("AZURE_OPENAI_API_KEY")
            self.azure_openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
            self.azure_openai_deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT")
            self.azure_openai_api_version = os.environ.get(
                "AZURE_OPENAI_API_VERSION", "2024-02-01"
            )
            self.openai_api_key = os.environ.get("OPENAI_API_KEY")
            self.lmstudio_base_url = os.environ.get("LMSTUDIO_BASE_URL")
            self.db_connection_string = os.environ.get("QAI_DB_CONN")
            self.sql_pool_size = int(os.environ.get("QAI_SQL_POOL_SIZE", "10"))
            self.enable_cosmos = os.environ.get("QAI_ENABLE_COSMOS", "").lower() in (
                "1",
                "true",
                "yes",
            )
            self.keyvault_url = os.environ.get("QAI_KEYVAULT_URL")
            self.log_level = os.environ.get("QAI_LOG_LEVEL", "INFO").upper()
            self.enable_structured_logging = os.environ.get(
                "QAI_STRUCTURED_LOGGING", ""
            ).lower() in ("1", "true", "yes")
            self.orchestrator_cycle_interval_minutes = int(
                os.environ.get("QAI_ORCHESTRATOR_CYCLE_MINUTES", "30")
            )
            self.orchestrator_max_retries = int(
                os.environ.get("QAI_ORCHESTRATOR_MAX_RETRIES", "3")
            )
            self.orchestrator_backoff_base = float(
                os.environ.get("QAI_ORCHESTRATOR_BACKOFF_BASE", "2.0")
            )
            self.enable_local_tts = os.environ.get("QAI_ENABLE_LOCAL_TTS", "").lower() in (
                "1",
                "true",
                "yes",
            )
            self.max_concurrent_training_jobs = int(
                os.environ.get("QAI_MAX_CONCURRENT_TRAINING_JOBS", "4")
            )

        @property
        def azure_openai_ready(self) -> bool:
            return all(
                [
                    self.azure_openai_api_key,
                    self.azure_openai_endpoint,
                    self.azure_openai_deployment,
                    self.azure_openai_api_version,
                ]
            )

        @property
        def openai_ready(self) -> bool:
            return bool(self.openai_api_key)

        @property
        def lmstudio_ready(self) -> bool:
            return bool(self.lmstudio_base_url)

        def active_provider(self) -> str:
            priority = os.environ.get(
                "QAI_PROVIDER_PRIORITY", "azure,openai,lmstudio,local"
            ).split(",")
            checks = {
                "azure": self.azure_openai_ready,
                "openai": self.openai_ready,
                "lmstudio": self.lmstudio_ready,
            }
            for name in priority:
                name = name.strip()
                if checks.get(name, False):
                    return name
            return "local"

        def summary(self) -> dict:
            return {
                "active_provider": self.active_provider(),
                "azure_openai_ready": self.azure_openai_ready,
                "openai_ready": self.openai_ready,
                "lmstudio_ready": self.lmstudio_ready,
                "db_enabled": bool(self.db_connection_string),
                "cosmos_enabled": self.enable_cosmos,
                "keyvault_enabled": bool(self.keyvault_url),
                "log_level": self.log_level,
                "structured_logging": self.enable_structured_logging,
                "local_tts_enabled": self.enable_local_tts,
            }


# ---------------------------------------------------------------------------
# Azure Key Vault integration (optional)
# ---------------------------------------------------------------------------


def _load_keyvault_secrets(settings: Settings) -> None:
    """Populate Settings fields from Azure Key Vault when ``keyvault_url`` is set.

    Secrets are stored directly in settings fields rather than in ``os.environ``
    to avoid leaking credentials to child processes or subprocess inheritance.

    Silently skips if the azure-keyvault-secrets package is not installed or
    if credentials are unavailable.
    """
    keyvault_url = getattr(settings, "keyvault_url", None)
    if not keyvault_url:
        return

    try:
        from azure.identity import DefaultAzureCredential  # type: ignore[import]
        from azure.keyvault.secrets import SecretClient  # type: ignore[import]

        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=keyvault_url, credential=credential)

        # Map Key Vault secret names → Settings field names
        _SECRET_MAP = {
            "azure-openai-api-key": "azure_openai_api_key",
            "openai-api-key": "openai_api_key",
            "qai-db-conn": "db_connection_string",
            "cosmos-key": "cosmos_key",
        }
        loaded = 0
        for secret_name, field_name in _SECRET_MAP.items():
            try:
                secret = client.get_secret(secret_name)
                if secret.value and not getattr(settings, field_name, None):
                    # Set directly on the instance, bypassing pydantic validation
                    object.__setattr__(settings, field_name, secret.value)
                    loaded += 1
            except Exception:  # noqa: BLE001
                pass  # Secret not found or inaccessible; skip silently

        if loaded:
            _LOG.info("[config] Loaded %d secret(s) from Key Vault", loaded)

    except Exception as exc:  # noqa: BLE001
        _LOG.info("Key Vault integration skipped: %s", exc)


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the singleton Settings instance.

    On first call, loads Key Vault secrets (if configured) before returning.
    Subsequent calls return the cached instance via ``lru_cache``.
    """
    if _PYDANTIC_AVAILABLE:
        instance = Settings()  # type: ignore[call-arg]
    else:
        instance = Settings()
    _load_keyvault_secrets(instance)
    return instance


def reset_settings() -> None:
    """Clear the cached settings (useful in tests)."""
    get_settings.cache_clear()


__all__ = ["Settings", "get_settings", "reset_settings"]
