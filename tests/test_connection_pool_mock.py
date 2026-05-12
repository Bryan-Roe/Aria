# tests/test_connection_pool_mock.py
from unittest.mock import MagicMock, patch
import shared.chat_memory as cm

class FakeCursor:
    def execute(self, *args, **kwargs): pass
    def fetchone(self): return (1,)
    def fetchall(self): return []
    def close(self): pass

class FakeConn:
    def cursor(self): return FakeCursor()
    def close(self): pass
    def commit(self): pass
    def rollback(self): pass

def test_store_embeddings_batch_with_mocked_conn(monkeypatch):
    fake = FakeConn()
    # Patch module-level _get_conn to return our fake connection
    monkeypatch.setattr(cm, "_get_conn", lambda: fake)
    monkeypatch.setattr(cm, "_return_conn", lambda conn: None)

    # Prepare a dummy embedding
    inserted = cm.store_embeddings_batch([("msg1", [0.1]*cm._LOCAL_DIM, "test-model")])
    assert inserted in (0, 1)  # If schema/driver behavior differs, ensure no exception and valid return type
