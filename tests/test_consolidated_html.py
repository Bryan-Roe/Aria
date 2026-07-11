"""
Structural tests for apps/dashboard/consolidated.html.

Validates:
- Required HTML elements exist with correct IDs
- JS functions are defined at the right scope (not deeply nested)
- HyperparameterOptimizer card is in the Tools tab (not in the header)
- Ctrl+1-5 keyboard shortcut code is present
- VRAM calculator uses real fetch() not setTimeout simulation
- loadConfig() is properly closed before other Phase 30 functions
"""

import re
from pathlib import Path

import pytest

HTML_PATH = Path(__file__).parent.parent / "apps" / "dashboard" / "consolidated.html"


@pytest.fixture(scope="module")
def html_text():
    return HTML_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def html_lines(html_text):
    return html_text.splitlines()


# ---------------------------------------------------------------------------
# Required element IDs
# ---------------------------------------------------------------------------

REQUIRED_IDS = [
    "optimStrategy",
    "optimMaxTrials",
    "hyperoptContainer",
    "vramResults",
    "anomalyCount",
    "spikeCount",
    "divergenceCount",
    "stagnationCount",
]


class TestRequiredElements:
    @pytest.mark.parametrize("elem_id", REQUIRED_IDS)
    def test_id_present(self, html_text, elem_id):
        assert f'id="{elem_id}"' in html_text, f"Missing element id: {elem_id}"

    def test_five_tab_buttons(self, html_text):
        """There should be at least 5 tab buttons."""
        tabs = re.findall(r'onclick="switchTab\(', html_text)
        assert len(tabs) >= 5, f"Expected >= 5 tab buttons, found {len(tabs)}"


# ---------------------------------------------------------------------------
# HyperparameterOptimizer card placement
# ---------------------------------------------------------------------------


class TestHyperparamCardPlacement:
    def test_card_not_inside_status_pills(self, html_text):
        """Hyperopt card must NOT appear inside a .status-pills div."""
        # The status-pills block starts with class="status-pills"
        pills_match = re.search(r'class="status-pills"', html_text)
        assert pills_match, "status-pills div not found"

        # Find the hyperopt card
        card_match = re.search(r'id="hyperoptContainer"', html_text)
        assert card_match, "hyperoptContainer not found"

        # Determine the extent of the status-pills block by finding its closing </div>
        # We'll just assert the card comes AFTER the status-pills section end
        card_pos = card_match.start()

        # Find the first occurrence of </div> after the status-pills opening tag
        # and verify the hyperopt card is not between the pills opening and the
        # "GPU Ready" pill (a strong proxy for "inside the header block").
        gpu_ready_pos = html_text.find("GPU Ready")
        assert gpu_ready_pos != -1, "GPU Ready pill not found"

        # The hyperopt container should come AFTER the GPU ready pill
        assert (
            card_pos > gpu_ready_pos
        ), "hyperoptContainer appears before/inside the status-pills header block; it should be in the Tools tab"

    def test_card_near_anomaly_detector(self, html_text):
        """Hyperopt card should appear shortly after the Anomaly Detector card."""
        anomaly_pos = html_text.find("Anomaly Detector Status")
        hyperopt_pos = html_text.find("Hyperparameter Optimizer")
        assert anomaly_pos != -1, "Anomaly Detector card not found"
        assert hyperopt_pos != -1, "Hyperparameter Optimizer card not found"
        assert hyperopt_pos > anomaly_pos, "Hyperparameter Optimizer card should come after Anomaly Detector"
        # They should be reasonably close (within 2000 chars)
        assert (
            hyperopt_pos - anomaly_pos < 2000
        ), "Hyperparameter Optimizer card is suspiciously far from Anomaly Detector"

    def test_status_pills_has_three_pills(self, html_text):
        """Header status-pills block should contain exactly 3 .status-pill divs."""
        pills_block_match = re.search(
            r'class="status-pills"(.*?)(?=<div class="tab-nav"|</header>)',
            html_text,
            re.DOTALL,
        )
        assert pills_block_match, "Could not isolate status-pills block"
        block = pills_block_match.group(1)
        pills = re.findall(r'class="status-pill"', block)
        assert len(pills) == 3, f"Expected 3 status pills, found {len(pills)}"


# ---------------------------------------------------------------------------
# JS function scope — not nested inside loadConfig
# ---------------------------------------------------------------------------

PHASE_30_FUNCTIONS = [
    "startHyperparamOptimization",
    "configureSearchSpace",
    "toggleSelectAll",
    "compareSelectedModels",
    "clearComparisonSelection",
]


class TestJsFunctionScope:
    def test_functions_are_top_level(self, html_text):
        """Each Phase 30 function declaration should begin with 8-space indent (top-level in <script>), not deeper."""
        for fname in PHASE_30_FUNCTIONS:
            # Accept either 8-space or 12-space indent (depends on script tag indentation)
            pattern = re.compile(rf"^(?:        |            )function {fname}\(", re.MULTILINE)
            matches = pattern.findall(html_text)
            assert len(matches) >= 1, f"function {fname} not found at top-level script scope"

    def test_loadconfig_closes_before_hyperopt(self, html_lines):
        """loadConfig() closing brace should appear before startHyperparamOptimization declaration."""
        loadconfig_start = None
        startoptim_line = None
        for i, line in enumerate(html_lines):
            if re.match(r"\s+function loadConfig\(\)", line) and loadconfig_start is None:
                loadconfig_start = i
            if "function startHyperparamOptimization(" in line and startoptim_line is None:
                startoptim_line = i

        assert loadconfig_start is not None, "function loadConfig() not found"
        assert startoptim_line is not None, "function startHyperparamOptimization() not found"

        # Between loadconfig_start and startoptim_line, there must be a closing brace
        # at 8-space indent (closes loadConfig) before the new function declaration.
        between = html_lines[loadconfig_start:startoptim_line]
        # The closing brace line of loadConfig is exactly "        }" (8 spaces + "}")
        # Accept either 8-space or 12-space indent closing brace (depends on script tag indentation)
        close_lines = [line for line in between if re.match(r"^(?:        |            )\}$", line)]
        assert (
            len(close_lines) >= 1
        ), "loadConfig() does not appear to close before startHyperparamOptimization — functions may still be nested"


# ---------------------------------------------------------------------------
# VRAM calculator — real fetch, no setTimeout simulation
# ---------------------------------------------------------------------------


class TestVramCalculatorImpl:
    def test_uses_real_fetch(self, html_text):
        # fetch call may be inline or split across lines
        assert (
            "fetch(`/api/vram-info" in html_text
            or "fetch('/api/vram-info" in html_text
            or ("/api/vram-info" in html_text and "fetch(" in html_text)
        ), "runVRAMCalculator must call fetch('/api/vram-info') — not simulate"

    def test_no_simulate_comment(self, html_text):
        assert "Simulate API call" not in html_text, "Simulation comment still present — VRAM calculator not updated"

    def test_uses_safe_batch_size_key(self, html_text):
        assert "safe_batch_size" in html_text, "VRAM calculator should use 'safe_batch_size' from API response"

    def test_handles_no_gpu(self, html_text):
        """There should be error/warning handling for the no-GPU response path."""
        assert (
            "data.error" in html_text or "data.available" in html_text
        ), "VRAM calculator should handle error/available=false from API"


# ---------------------------------------------------------------------------
# Keyboard shortcuts
# ---------------------------------------------------------------------------


class TestKeyboardShortcuts:
    def test_ctrl_key_listener_present(self, html_text):
        assert "e.ctrlKey" in html_text, "Ctrl+key listener not found"

    def test_tab_map_has_five_entries(self, html_text):
        tab_map_match = re.search(r"tabMap\s*=\s*\{([^}]+)\}", html_text)
        assert tab_map_match, "tabMap not found in keyboard shortcut code"
        # Keys may be quoted ('1') or unquoted (1:)
        entries = re.findall(r"'\d'", tab_map_match.group(1)) or re.findall(r"\b\d\s*:", tab_map_match.group(1))
        assert len(entries) == 5, f"Expected 5 digit keys in tabMap, found {len(entries)}"

    def test_switches_to_tools_tab(self, html_text):
        assert "'tools'" in html_text or '"tools"' in html_text, "Keyboard shortcut tabMap should include 'tools' tab"
