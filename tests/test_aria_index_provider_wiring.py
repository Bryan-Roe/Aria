"""Structural checks for main Aria UI provider/model override wiring."""

from pathlib import Path


INDEX_HTML = Path(__file__).parent.parent / "apps" / "aria" / "index.html"
CONTROLLER_JS = Path(__file__).parent.parent / "apps" / \
    "aria" / "aria_controller.js"


def test_index_has_provider_and_model_controls() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")

    assert 'id="providerSelect"' in html, "Main Aria UI should expose provider selector"
    assert 'id="modelInput"' in html, "Main Aria UI should expose model/path input"
    assert 'id="useLlmToggle"' in html, "Main Aria UI should expose use-llm toggle"
    assert 'value="quantum-llm"' in html, "Main Aria UI should include quantum provider option"


def test_controller_reads_override_inputs() -> None:
    js = CONTROLLER_JS.read_text(encoding="utf-8")

    assert "getElementById('providerSelect')" in js, "Controller should read provider selector"
    assert "getElementById('modelInput')" in js, "Controller should read model/path input"
    assert "getElementById('useLlmToggle')" in js, "Controller should read LLM toggle"


def test_controller_forwards_overrides_to_command_endpoint() -> None:
    js = CONTROLLER_JS.read_text(encoding="utf-8")

    assert 'use_llm: useLlm' in js, "Controller payload should include use_llm toggle"
    assert 'provider: provider || undefined' in js, "Controller payload should include provider override"
    assert 'model: model || undefined' in js, "Controller payload should include model override"


def test_controller_persists_provider_settings_in_localstorage() -> None:
    js = CONTROLLER_JS.read_text(encoding="utf-8")

    assert "aria-provider-select" in js, "Controller should persist selected provider"
    assert "aria-model-input" in js, "Controller should persist model/path"
    assert "aria-use-llm-toggle" in js, "Controller should persist use_llm toggle"
    assert "restoreProviderSettings()" in js, "Controller should restore provider settings on load"
    assert "persistProviderSettings(provider, model, useLlm)" in js, "Controller should persist settings before requests"
