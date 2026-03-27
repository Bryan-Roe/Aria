"""Structural checks for apps/aria/auto-execute.html provider/model payload wiring."""

from pathlib import Path


HTML_PATH = Path(__file__).parent.parent / "apps" / \
    "aria" / "auto-execute.html"


def test_provider_and_model_controls_present() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")

    assert 'id="provider"' in html, "Provider select control should exist"
    assert 'id="model"' in html, "Model/path input should exist"
    assert 'value="quantum-llm"' in html, "Quantum provider option should be present"


def test_execute_payload_includes_provider_and_model() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")

    assert 'provider: provider || undefined' in html, "Execute payload should forward provider override"
    assert 'model: model || undefined' in html, "Execute payload should forward model/path override"


def test_results_show_requested_provider_and_model() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")

    assert 'Provider Requested:' in html, "Results panel should display provider routing info"
    assert 'Model Requested:' in html, "Results panel should display model/path override when provided"


def test_auto_execute_settings_persistence_wiring_present() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")

    assert 'aria-autoexec-provider' in html, "Auto-execute should persist provider selection"
    assert 'aria-autoexec-model' in html, "Auto-execute should persist model/path"
    assert 'aria-autoexec-use-llm' in html, "Auto-execute should persist use-llm toggle"
    assert 'aria-autoexec-show-state' in html, "Auto-execute should persist show-state toggle"
    assert 'restoreAutoExecuteSettings()' in html, "Auto-execute should restore saved settings on load"
    assert 'persistAutoExecuteSettings(provider, model, useLlm, showState)' in html, "Auto-execute should persist settings before requests"
