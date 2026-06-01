import importlib.util
import os


def load_module():
    path = os.path.join(os.path.dirname(__file__), "..", "scripts", "gradio_demo.py")
    path = os.path.abspath(path)
    spec = importlib.util.spec_from_file_location("gradio_demo", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_send_to_webhook(tmp_path):
    m = load_module()
    # prepare a simple history
    hist = [{"user": "hello", "assistant": "hi", "user_ts": "u1", "assistant_ts": "a1"}]
    # call the send_to_webhook function
    path, status = m.send_to_webhook(hist, "testhook", str(tmp_path), False)
    assert status and "Sent" in status
    assert path and os.path.exists(path)
