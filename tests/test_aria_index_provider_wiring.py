"""Structural checks for main Aria UI provider/model override wiring."""

from pathlib import Path

INDEX_HTML = Path(__file__).parent.parent / "apps" / "aria" / "index.html"
CONTROLLER_JS = Path(__file__).parent.parent / "apps" / "aria" / "aria_controller.js"
THREEJS_JS = Path(__file__).parent.parent / "apps" / "aria" / "aria_threejs.js"


def test_index_has_provider_and_model_controls() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")

    assert 'id="providerSelect"' in html, "Main Aria UI should expose provider selector"
    assert 'id="modelInput"' in html, "Main Aria UI should expose model/path input"
    assert 'id="useLlmToggle"' in html, "Main Aria UI should expose use-llm toggle"
    assert 'value="quantum-llm"' in html, "Main Aria UI should include quantum provider option"


def test_controller_reads_override_inputs() -> None:
    js = CONTROLLER_JS.read_text(encoding="utf-8")

    assert (
        'getElementById("providerSelect")' in js or "getElementById('providerSelect')" in js
    ), "Controller should read provider selector"
    assert (
        'getElementById("modelInput")' in js or "getElementById('modelInput')" in js
    ), "Controller should read model/path input"
    assert (
        'getElementById("useLlmToggle")' in js or "getElementById('useLlmToggle')" in js
    ), "Controller should read LLM toggle"


def test_controller_forwards_overrides_to_command_endpoint() -> None:
    js = CONTROLLER_JS.read_text(encoding="utf-8")

    assert "use_llm: useLlm" in js, "Controller payload should include use_llm toggle"
    assert "provider: provider || undefined" in js, "Controller payload should include provider override"
    assert "model: model || undefined" in js, "Controller payload should include model override"


def test_controller_persists_provider_settings_in_localstorage() -> None:
    js = CONTROLLER_JS.read_text(encoding="utf-8")

    assert "aria-provider-select" in js, "Controller should persist selected provider"
    assert "aria-model-input" in js, "Controller should persist model/path"
    assert "aria-use-llm-toggle" in js, "Controller should persist use_llm toggle"
    assert "restoreProviderSettings()" in js, "Controller should restore provider settings on load"
    assert (
        "persistProviderSettings(provider, model, useLlm)" in js
    ), "Controller should persist settings before requests"


def test_index_loads_stage_controller_and_threejs() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")

    assert 'src="aria_controller.js"' in html, "Main stage should load aria_controller.js"
    assert 'src="aria_threejs.js"' in html, "Main stage should load aria_threejs.js"
    assert "three@0.152" in html, "Main stage should load Three.js r152 CDN"
    assert 'id="commandInput"' in html, "Main stage should expose command input"
    assert 'id="aria"' in html, "Main stage should expose Aria character DOM"
    assert "loadQuantumStage(" in html, "Main stage should expose Load Quantum World controls"

    three_idx = html.index('src="aria_threejs.js"')
    controller_idx = html.index('src="aria_controller.js"')
    cdn_idx = html.index("three@0.152")
    assert cdn_idx < three_idx < controller_idx, "Scripts must load CDN → threejs → controller"


def test_controller_has_quantum_stage_sync_helpers() -> None:
    js = CONTROLLER_JS.read_text(encoding="utf-8")

    assert "applyServerEnvironmentState" in js
    assert "syncWorldObjectsFromServer" in js
    assert "loadQuantumStage" in js
    assert "updateStageLabel" in js
    assert "environment.stage_style" in js or "stage_style" in js
    assert "window.loadQuantumStage" in js
    assert "window.aria3D?.setStageTheme" in js, "Controller should delegate theme to Three.js overlay"
    assert "/api/aria/quantum/setup" in js, "Controller should call quantum setup endpoint"


def test_threejs_exposes_stage_theme_hook() -> None:
    js = THREEJS_JS.read_text(encoding="utf-8")

    assert "setStageTheme" in js
    assert "window.aria3D" in js


def test_index_quantum_ux_integrations() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")

    assert 'id="stage-label"' in html, "Stage should show a theme/status label"
    assert 'id="quantum-live-status"' in html, "Quantum toolbar should expose aria-live status"
    assert 'aria-live="polite"' in html, "Quantum feedback should be screen-reader friendly"
    assert "showToast" in html, "Main stage should expose toast feedback helper"
    assert "loadQuantumSampleChips" in html, "Main stage should load Quantum Lab preset chips"
    assert 'id="quantum-sample-chips"' in html, "Quantum sample chip container should exist"
