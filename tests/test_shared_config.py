from __future__ import annotations

from shared.config import AppSettings


def test_settings_provider_chain_default_order() -> None:
    settings = AppSettings()
    assert settings.provider_chain() == ["azure", "openai", "lmstudio", "local"]


def test_settings_summary_excludes_secret_values(monkeypatch) -> None:
    monkeypatch.setenv("QAI_PROVIDER_PRIORITY", "openai,local")
    monkeypatch.setenv("OPENAI_API_KEY", "secret-value")
    settings = AppSettings()
    summary = settings.summary()
    assert "secret-value" not in str(summary)
    assert summary["provider_chain"] == ["openai", "local"]
