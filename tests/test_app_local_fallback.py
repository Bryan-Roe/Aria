import os
import sys
import pytest

# Ensure tests import the local module from workspace
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app


def test_provider_local_returns_ok_and_summary(capsys):
    argv = [
        "--provider",
        "local",
        (
            "Summarize this. Alpha release improves local summaries by ranking sentences. "
            "It removes prompt boilerplate before scoring. "
            "The fallback stays fully offline and deterministic."
        ),
    ]
    rc = app.main(argv)
    captured = capsys.readouterr()

    assert rc == app.EXIT_OK
    assert "Alpha release improves local summaries by ranking sentences." in captured.out
    assert "It removes prompt boilerplate before scoring." in captured.out
    assert "Summarize this" not in captured.out


def test_auto_fallback_without_key_uses_local(capsys, monkeypatch):
    # Ensure OPENAI_API_KEY is not set
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    argv = ["This is a test prompt that should trigger the local fallback because no key is set."]
    rc = app.main(argv)
    captured = capsys.readouterr()
    assert rc == app.EXIT_OK
    assert "Local fallback" in captured.out or "Local fallback" in captured.err or "fallback" in captured.out.lower()
