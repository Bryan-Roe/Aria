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
    assert lines, "Persistence file is empty"

    last = json.loads(lines[-1])
    assert last.get("type") == "reasoning_chain"
    assert isinstance(last.get("chain"), list)

    # cleanup environment
    monkeypatch.delenv("QAI_AGI_PERSIST", raising=False)
    monkeypatch.delenv("QAI_AGI_PERSIST_PATH", raising=False)
