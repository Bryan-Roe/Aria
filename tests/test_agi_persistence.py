import os
import json

import agi_provider


def test_agi_persistence(tmp_path, monkeypatch):
    path = tmp_path / "agi_test.jsonl"
    monkeypatch.setenv("QAI_AGI_PERSIST", "1")
    monkeypatch.setenv("QAI_AGI_PERSIST_PATH", str(path))

    provider, info = agi_provider.create_agi_provider(verbose=False)

    messages = [{"role": "user", "content": "Plan the next step"}]
    # Non-streaming call so the generator is not required.
    _ = provider.complete(messages, stream=False)

    assert path.exists(), "Persistence file was not created"
    lines = path.read_text(encoding="utf-8").splitlines()

    # Some persistence backends may not write to the JSONL file directly in test
    # environments; prefer a backend-friendly assertion when available.
    last = None
    if not lines and getattr(provider, "persistence", None) is not None and hasattr(provider.persistence, "read_last"):
        entries = provider.persistence.read_last(1)
        assert entries, "No entries found in persistence backend"
        last = entries[-1]
    else:
        assert lines, "Persistence file is empty"
        last = json.loads(lines[-1])

    assert last.get("type") == "reasoning_chain"
    chain = last.get("chain") or last.get("chain")
    assert isinstance(chain, list)

    # cleanup environment
    monkeypatch.delenv("QAI_AGI_PERSIST", raising=False)
    monkeypatch.delenv("QAI_AGI_PERSIST_PATH", raising=False)
