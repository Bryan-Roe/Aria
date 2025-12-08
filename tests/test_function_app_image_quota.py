# Mark as skipped in CI: function_app imports require a full Azure SDK environment.
import pytest
from pathlib import Path
import types
import sys
from typing import Any, Callable, Dict, Optional, cast
# This test is flaky in the repository test harness because importing
# function_app requires a full azure SDK & environment. Skip here to avoid
# surprising CI failures; the underlying code was improved in the repo
# (image endpoint will show a friendlier quota message when detected).
# Make this test runnable in CI by fully mocking required runtime modules
# (azure.functions, openai). This test exercises the /api/image/generate
# fallback path when the Azure/OpenAI images API raises a quota-like error.


def _make_openai_module_raising():
    """Create a fake `openai` module with OpenAI that raises a quota error for images.generate."""
    mod = types.ModuleType('openai')

    # Provide an openai.error submodule with common exception classes so
    # code that catches openai.error.OpenAIError / RateLimitError will work.
    error_mod = types.ModuleType('openai.error')

    class OpenAIError(Exception):
        pass

    class RateLimitError(OpenAIError):
        pass

    setattr(error_mod, 'OpenAIError', OpenAIError)
    setattr(error_mod, 'RateLimitError', RateLimitError)
    setattr(mod, 'error', error_mod)

    # Ensure imports like `import openai.error` resolve to our stub as well.
    sys.modules['openai.error'] = error_mod

    class OpenAI:
        def __init__(self, *args: object, **kwargs: object):
            # images API is exposed on the instance; raise an OpenAIError that
            # resembles the real message the library would surface on quota.
            def _raise(**kwargs: object):
                raise OpenAIError(
                    'Exceeded your premium request allowance for images API')

            self.images = types.SimpleNamespace(generate=_raise)

    setattr(mod, 'OpenAI', OpenAI)
    return mod


def test_image_generate_azure_quota_fallback(monkeypatch: pytest.MonkeyPatch):
    # Ensure top-level module import works
    repo_root = Path(__file__).resolve().parents[1]
    cast(Any, monkeypatch).syspath_prepend(str(repo_root))
    # Ensure talk-to-ai/src is available for token_utils/chat_providers imports
    tta = str((repo_root / 'talk-to-ai' / 'src').absolute())
    cast(Any, monkeypatch).syspath_prepend(tta)
    # Prepare environment to force Azure path
    monkeypatch.setenv('OPENAI_API_KEY', '')
    monkeypatch.setenv('AZURE_OPENAI_API_KEY', 'fake')
    monkeypatch.setenv('AZURE_OPENAI_ENDPOINT',
                       'https://example.openai.azure.com')

    # The functions app imports azure.functions; provide a minimal stub so
    # function_app can be imported without the real azure.functions package.
    azure_mod: Any = types.ModuleType('azure')
    azure_funcs: Any = types.ModuleType('azure.functions')

    class HttpResponse:
        def __init__(self, body: str | bytes, status_code: int = 200, mimetype: str = "application/json", headers: Optional[Dict[str, str]] = None) -> None:
            # body may be either text or already-bytes; normalize to bytes
            self._body = body.encode() if isinstance(body, str) else body
            self.status_code = status_code
            self.mimetype = mimetype
            self.headers = headers or {}

        def get_body(self) -> bytes:
            return self._body

    class FunctionApp:
        def route(self, *args: Any, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
            def _decorator(f: Callable[..., Any]) -> Callable[..., Any]:
                return f

            return _decorator

    class AuthLevel:
        ANONYMOUS = "ANONYMOUS"

    azure_funcs.HttpResponse = HttpResponse
    azure_funcs.FunctionApp = FunctionApp
    azure_funcs.AuthLevel = AuthLevel
    azure_mod.functions = azure_funcs
    monkeypatch.setitem(sys.modules, 'azure', azure_mod)
    monkeypatch.setitem(sys.modules, 'azure.functions', azure_funcs)

    # Inject fake openai module that raises quota error
    fake = _make_openai_module_raising()
    monkeypatch.setitem(sys.modules, 'openai', fake)

    import function_app as fa

    class DummyReq:
        def __init__(self, body: Dict[str, Any]) -> None:
            self.method = 'POST'
            self._body = body

        def get_json(self) -> Dict[str, Any]:
            return self._body

    req = DummyReq({'prompt': 'a cat', 'size': '512x512', 'style': ''})
    # Cast the image_generate callable so static type checkers know its type
    image_generate_fn = cast(
        Callable[[Any], Any], getattr(fa, 'image_generate'))
    resp = image_generate_fn(req)

    # HttpResponse body is JSON bytes / str depending on runtime.
    # Use runtime-safe getattr + cast to avoid static type complaints in the test harness.
    get_body_fn = getattr(resp, "get_body", None)
    if callable(get_body_fn):
        body_bytes = get_body_fn()
        body = body_bytes.decode() if isinstance(
            body_bytes, (bytes, bytearray)) else str(body_bytes)
    else:
        # No get_body method; fall back to string conversion
        body = str(cast(object, resp))

    expected_keywords = ['quota', 'premium', 'images api']
    assert any(keyword in body.lower() for keyword in expected_keywords), (
        "Expected friendly quota error message in response body, got: %r" % body
    )


def test_image_generate_openai_success(monkeypatch: pytest.MonkeyPatch):
    """When a real OpenAI images.generate call returns a URL, ensure the
    endpoint returns image_url and model in the JSON response.
    """
    repo_root = Path(__file__).resolve().parents[1]
    cast(Any, monkeypatch).syspath_prepend(str(repo_root))
    tta = str((repo_root / 'talk-to-ai' / 'src').absolute())
    cast(Any, monkeypatch).syspath_prepend(tta)

    # Use the non-Azure path
    monkeypatch.setenv('OPENAI_API_KEY', 'fake-openai')
    monkeypatch.delenv('AZURE_OPENAI_API_KEY', raising=False)
    monkeypatch.delenv('AZURE_OPENAI_ENDPOINT', raising=False)

    # Minimal azure.functions stub so function_app imports
    azure_mod: Any = types.ModuleType('azure')
    azure_funcs: Any = types.ModuleType('azure.functions')
    azure_funcs.HttpResponse = lambda *a, **k: None
    azure_funcs.FunctionApp = lambda *a, **k: None
    azure_funcs.AuthLevel = types.SimpleNamespace(ANONYMOUS='ANONYMOUS')
    azure_mod.functions = azure_funcs
    monkeypatch.setitem(sys.modules, 'azure', azure_mod)
    monkeypatch.setitem(sys.modules, 'azure.functions', azure_funcs)

    # Fake OpenAI client that returns a single URL
    mod = types.ModuleType('openai')

    class OpenAI:
        def __init__(self, *a, **kw):
            pass

        def images(self):
            pass

    def fake_generate(*args, **kwargs):
        return types.SimpleNamespace(data=[types.SimpleNamespace(url='https://example.com/cat.png')])

    setattr(OpenAI, '__call__', lambda self, *a, **k: self)
    setattr(OpenAI, 'images', types.SimpleNamespace(generate=fake_generate))
    setattr(mod, 'OpenAI', OpenAI)
    monkeypatch.setitem(sys.modules, 'openai', mod)

    import function_app as fa  # import after stubbing modules

    class DummyReq:
        def __init__(self, body: Dict[str, Any]) -> None:
            self.method = 'POST'
            self._body = body

        def get_json(self) -> Dict[str, Any]:
            return self._body

    req = DummyReq({'prompt': 'a dog', 'size': '512x512', 'style': ''})
    resp = fa.image_generate(req)

    # get_body exists on our test HttpResponse stub
    body_bytes = resp.get_body() if hasattr(resp, 'get_body') else str(resp)
    body = body_bytes.decode() if isinstance(
        body_bytes, (bytes, bytearray)) else str(body_bytes)

    assert 'image_url' in body or 'https://example.com/cat.png' in body


def test_image_generate_azure_status_code_quota(monkeypatch: pytest.MonkeyPatch):
    """Simulate an Azure-style exception (status_code and nested error.code)
    and ensure the endpoint returns a friendly quota message.
    """
    repo_root = Path(__file__).resolve().parents[1]
    cast(Any, monkeypatch).syspath_prepend(str(repo_root))
    tta = str((repo_root / 'talk-to-ai' / 'src').absolute())
    cast(Any, monkeypatch).syspath_prepend(tta)

    monkeypatch.setenv('OPENAI_API_KEY', '')
    monkeypatch.setenv('AZURE_OPENAI_API_KEY', 'fake-azure')
    monkeypatch.setenv('AZURE_OPENAI_ENDPOINT',
                       'https://example.openai.azure.com')

    azure_mod: Any = types.ModuleType('azure')
    azure_funcs: Any = types.ModuleType('azure.functions')

    class HttpResponse:
        def __init__(self, body: str | bytes, status_code: int = 200, mimetype: str = "application/json", headers: Optional[Dict[str, str]] = None) -> None:
            self._body = body.encode() if isinstance(body, str) else body
            self.status_code = status_code
            self.mimetype = mimetype
            self.headers = headers or {}

        def get_body(self) -> bytes:
            return self._body

    azure_funcs.HttpResponse = HttpResponse
    azure_funcs.FunctionApp = types.SimpleNamespace(
        route=lambda *a, **k: (lambda f: f))
    azure_funcs.AuthLevel = types.SimpleNamespace(ANONYMOUS='ANONYMOUS')
    azure_mod.functions = azure_funcs
    monkeypatch.setitem(sys.modules, 'azure', azure_mod)
    monkeypatch.setitem(sys.modules, 'azure.functions', azure_funcs)

    # Fake OpenAI raising an Azure-like exception
    fake = types.ModuleType('openai')

    class AzureLikeError(Exception):
        def __init__(self):
            self.status_code = 403
            self.error = types.SimpleNamespace(
                code='quota_exceeded', message='Quota exceeded')

        def __str__(self):
            return 'Azure quota/premium allowance exceeded'

    class OpenAIMod:
        def __init__(self, *a, **k):
            pass

        def images(self):
            pass

    def raise_azure(*a, **k):
        raise AzureLikeError()

    setattr(OpenAIMod, 'images', types.SimpleNamespace(generate=raise_azure))
    setattr(fake, 'OpenAI', OpenAIMod)
    monkeypatch.setitem(sys.modules, 'openai', fake)

    import function_app as fa

    class DummyReq:
        def __init__(self, body: Dict[str, Any]) -> None:
            self.method = 'POST'
            self._body = body

        def get_json(self) -> Dict[str, Any]:
            return self._body

    req = DummyReq({'prompt': 'a cat', 'size': '512x512', 'style': ''})
    resp = fa.image_generate(req)
    body_bytes = resp.get_body() if hasattr(resp, 'get_body') else str(resp)
    body = body_bytes.decode() if isinstance(
        body_bytes, (bytes, bytearray)) else str(body_bytes)

    assert 'quota' in body.lower() or 'premium' in body.lower()
