from __future__ import annotations

from pathlib import Path

import pytest

_DOWNLOAD_CMD = 'python -c "from pyppeteer.chromium_downloader import download_chromium; download_chromium()"'


@pytest.mark.unit
def test_pyppeteer_workflow_uses_supported_chromium_download_command() -> None:
    workflow_path = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "aria-tests.yml"
    content = workflow_path.read_text(encoding="utf-8")

    assert "python -m pyppeteer install" not in content
    assert _DOWNLOAD_CMD in content


@pytest.mark.unit
def test_e2e_tests_workflow_uses_pyppeteer_bundled_chromium() -> None:
    """e2e-tests.yml containerized_chrome job must keep the Bullseye-safe Chromium fallback chain."""
    workflow_path = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "e2e-tests.yml"
    content = workflow_path.read_text(encoding="utf-8")

    assert "python -m pyppeteer install" not in content
    assert _DOWNLOAD_CMD in content
    assert "if apt_get install -y --fix-missing chromium; then" in content
    assert "elif apt_get install -y --fix-missing chromium-browser; then" in content
    assert 'ln -sf "$(command -v chromium-browser)" /usr/bin/chromium' in content


@pytest.mark.unit
def test_e2e_tests_workflow_retries_apt_downloads_for_containerized_chrome() -> None:
    workflow_path = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "e2e-tests.yml"
    content = workflow_path.read_text(encoding="utf-8")

    assert content.count("apt_get() {") == 2
    assert content.count('apt-get -o Acquire::Retries=3 "$@"') == 2
    assert "apt_get install -y --fix-missing chromium" in content
    assert "apt_get install -y --fix-missing chromium-browser" in content
