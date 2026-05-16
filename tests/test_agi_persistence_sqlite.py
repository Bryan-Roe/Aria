import os
import json

import agi_provider


def test_agi_persistence_sqlite(tmp_path, monkeypatch):
    dbpath = tmp_path / "agi_test.db"
    monkeypatch.setenv("QAI_AGI_PERSIST_DB", str(dbpath))

    provider, info = agi_provider.create_agi_provider(verbose=False)

    messages = [{"role": "user", "content": "Plan the next step"}]
    # Non-streaming call so the generator is not required.
    _ = provider.complete(messages, stream=False)

    assert dbpath.exists(), "SQLite DB file was not created"
    assert getattr(provider, "persistence", None) is not None
    entries = provider.persistence.read_last(5)
    assert entries, "No entries found in SQLite persistence"

    last = entries[-1]
    assert last.get("type") == "reasoning_chain"
    assert isinstance(last.get("chain"), list)

    # cleanup
    monkeypatch.delenv("QAI_AGI_PERSIST_DB", raising=False)
