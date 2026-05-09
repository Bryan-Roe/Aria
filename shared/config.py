"""Centralized environment-driven application settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

try:
    from pydantic import Field, model_validator
    from pydantic_settings import BaseSettings, SettingsConfigDict

    _PYDANTIC_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency fallback
    _PYDANTIC_AVAILABLE = False

    def Field(default=None, alias=None, **kwargs):
        return default

    def model_validator(*args, **kwargs):
        def _decorator(func):
            return func

        return _decorator

    class BaseSettings:  # type: ignore
        def __init__(self, **kwargs):
            for key, value in self.__class__.__dict__.items():
                if key.startswith("_") or callable(value):
                    continue
                setattr(self, key, kwargs.get(key, value))

    class SettingsConfigDict(dict):  # type: ignore
        pass


class AppSettings(BaseSettings):
    """Runtime configuration for local and cloud execution."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = Field(default="development", alias="QAI_ENV")
    debug: bool = Field(default=False, alias="QAI_DEBUG")

    # Provider chain (deterministic fallback order)
    provider_priority: str = Field(default="azure,openai,lmstudio,local", alias="QAI_PROVIDER_PRIORITY")

    # Azure OpenAI
    azure_openai_api_key: str | None = Field(default=None, alias="AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: str | None = Field(default=None, alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_deployment: str | None = Field(default=None, alias="AZURE_OPENAI_DEPLOYMENT")
    azure_openai_api_version: str | None = Field(default=None, alias="AZURE_OPENAI_API_VERSION")

    # OpenAI
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")

    # Local providers
    lmstudio_base_url: str = Field(default="http://127.0.0.1:1234/v1", alias="LMSTUDIO_BASE_URL")
    local_fallback_model: str = Field(default="local-fallback", alias="QAI_LOCAL_FALLBACK_MODEL")

    # Optional infra
    db_connection: str | None = Field(default=None, alias="QAI_DB_CONN")
    max_concurrency: int = Field(default=4, alias="QAI_MAX_CONCURRENCY", ge=1, le=64)

    # Optional Key Vault (Azure-hosted runtime)
    key_vault_url: str | None = Field(default=None, alias="AZURE_KEY_VAULT_URL")
    key_vault_enabled: bool = Field(default=False, alias="QAI_ENABLE_KEY_VAULT")

    @model_validator(mode="after")
    def _validate_provider_priority(self) -> AppSettings:
        allowed = {"azure", "openai", "lmstudio", "local"}
        ordered = [item.strip().lower() for item in self.provider_priority.split(",") if item.strip()]
        if not ordered:
            ordered = ["azure", "openai", "lmstudio", "local"]
        invalid = [item for item in ordered if item not in allowed]
        if invalid:
            raise ValueError(f"Invalid QAI_PROVIDER_PRIORITY value(s): {invalid}")
        self.provider_priority = ",".join(ordered)
        return self

    def provider_chain(self) -> list[str]:
        return [item.strip().lower() for item in self.provider_priority.split(",") if item.strip()]

    def ready_providers(self) -> list[str]:
        providers: list[str] = []
        if all(
            [
                self.azure_openai_api_key,
                self.azure_openai_endpoint,
                self.azure_openai_deployment,
                self.azure_openai_api_version,
            ]
        ):
            providers.append("azure")
        if self.openai_api_key:
            providers.append("openai")
        if self.lmstudio_base_url:
            providers.append("lmstudio")
        providers.append("local")
        return providers

    def summary(self) -> dict[str, Any]:
        return {
            "environment": self.environment,
            "debug": self.debug,
            "provider_chain": self.provider_chain(),
            "ready_providers": self.ready_providers(),
            "max_concurrency": self.max_concurrency,
            "db_configured": bool(self.db_connection),
            "key_vault_enabled": bool(self.key_vault_enabled and self.key_vault_url),
        }


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    settings = AppSettings()
    if _PYDANTIC_AVAILABLE:
        return settings
    # Best-effort validation parity when pydantic isn't installed.
    settings._validate_provider_priority()
    return settings
