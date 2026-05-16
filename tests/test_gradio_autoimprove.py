import importlib.util
import os


def load_module():
    path = os.path.join(os.path.dirname(__file__), "..", "scripts", "gradio_demo.py")
    path = os.path.abspath(path)
    spec = importlib.util.spec_from_file_location("gradio_demo", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generate_html_export(tmp_path):
    m = load_module()
    m.CONV_DIR = str(tmp_path)
    fname = m.generate_html_export([{"user": "hi", "assistant": "hello", "user_ts": "u", "assistant_ts": "a"}], "testsession")
    assert os.path.exists(fname)
    assert fname.endswith('.html')
    with open(fname, 'r', encoding='utf-8') as f:
        content = f.read()
    assert 'User' in content and 'Assistant' in content


def test_summarize_conversation_simple():
    m = load_module()
    hist = [
        {"user": "tell me about ai", "assistant": "ai is a field"},
        {"user": "what about LLMs", "assistant": "LLMs are helpful"},
    ]
    s = m.summarize_conversation_simple(hist)
    assert isinstance(s, str)
    assert len(s) > 0
