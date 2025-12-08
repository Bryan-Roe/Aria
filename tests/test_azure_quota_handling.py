import sys
from pathlib import Path
import types


def _ensure_talk_to_ai_in_path():
    # Ensure talk-to-ai/src is importable for tests that import chat_providers
    repo_root = Path(__file__).resolve().parents[1]
    tta = str((repo_root / 'talk-to-ai' / 'src').absolute())
    if tta not in sys.path:
        sys.path.insert(0, tta)


def test_azure_provider_handles_quota_non_stream(monkeypatch):
    """When the Azure SDK raises a premium/quota error, the provider should
    return a friendly message (non-stream mode) instead of raising.
    """
    _ensure_talk_to_ai_in_path()
    import chat_providers as cp

    # Fake Azure client that raises a quota/premium exception on create
    class FakeAzure:
        def __init__(self, **kwargs):
            pass

        class _chat:
            class _completions:
                @staticmethod
                def create(**kwargs):
                    raise Exception(
                        "Error: exceeded your premium request allowance on this resource")

            completions = _completions()

        chat = _chat()

    monkeypatch.setattr(cp, 'AzureOpenAI', FakeAzure)

    provider = cp.AzureOpenAIProvider(
        deployment='dummy', endpoint='http://example', api_key='k')
    resp = provider.complete(
        [{"role": "user", "content": "Hello"}], stream=False)
    assert isinstance(resp, str)
    assert 'quota' in resp.lower() or 'premium' in resp.lower()


def test_azure_provider_stream_handles_quota_during_iteration(monkeypatch):
    """When streaming and the SDK raises during iteration, the provider's
    generator should yield a friendly quota message.
    """
    _ensure_talk_to_ai_in_path()
    import chat_providers as cp

    # Create generator that yields one chunk then raises
    def fake_stream():
        class Delta:
            def __init__(self, content):
                self.content = content

        class Choice:
            def __init__(self, content):
                self.delta = Delta(content)

        class Chunk:
            def __init__(self, content):
                self.choices = [Choice(content)]

        yield Chunk('early ')
        raise Exception(
            'Exceeded your premium request allowance - billing limit')

    class FakeAzure2:
        def __init__(self, **kwargs):
            pass

        class _chat:
            class _completions:
                @staticmethod
                def create(**kwargs):
                    return fake_stream()

            completions = _completions()

        chat = _chat()

    monkeypatch.setattr(cp, 'AzureOpenAI', FakeAzure2)
    provider = cp.AzureOpenAIProvider(
        deployment='d', endpoint='http://example', api_key='k')
    gen = provider.complete(
        [{"role": "user", "content": "Hello"}], stream=True)
    out = ''.join([c for c in gen])
    assert 'early' in out
    assert 'quota' in out.lower() or 'premium' in out.lower()


def test_generate_embedding_falls_back_on_azure_quota(monkeypatch):
    """If Azure embedding call fails due to premium/quota the function should
    fall back to the local hash embedding.
    """
    repo_root = Path(__file__).resolve().parents[1]
    sm = str((repo_root / 'shared').absolute())
    if sm not in sys.path:
        sys.path.insert(0, sm)

    import shared.chat_memory as cm

    # Fake Azure client that raises quota-like exception
    class FakeAzureEmbedding:
        def __init__(self, **kwargs):
            pass

        class _embeddings:
            @staticmethod
            def create(**kwargs):
                raise Exception(
                    'Exceeded your premium request allowance (embeddings)')

        embeddings = _embeddings()

    monkeypatch.setattr(cm, 'AzureOpenAI', FakeAzureEmbedding)

    emb = cm.generate_embedding('some test text')
    # When Azure fails we fall back to local hashing dim
    assert isinstance(emb, list)
    assert len(emb) == cm._LOCAL_DIM
