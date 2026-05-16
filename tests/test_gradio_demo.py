import importlib.util
import os
import json


def load_module():
    path = os.path.join(os.path.dirname(__file__), "..", "scripts", "gradio_demo.py")
    path = os.path.abspath(path)
    spec = importlib.util.spec_from_file_location("gradio_demo", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_save_and_load(tmp_path):
    m = load_module()
    conv_dir = tmp_path / "conv"
    # Point module to a temp conv dir
    m.CONV_DIR = str(conv_dir)
    m.LATEST_PATH = os.path.join(m.CONV_DIR, "latest.json")
    hist = [{"user": "hi", "assistant": "hello", "user_ts": "u", "assistant_ts": "a"}]
    fname = m.save_conversation_json(hist, "testsession")
    assert os.path.exists(fname)
    # load latest via helper
    display, loaded = m.load_latest_conversation()
    assert loaded == hist
    assert isinstance(display, list)
    assert display and "hi" in display[0][0]
    # Latest path should exist
    assert os.path.exists(m.LATEST_PATH)


def test_respond_simulation():
    m = load_module()
    # call respond directly in simulation mode
    chat_history = []
    hist_state = []
    import types
    gen = m.respond("hello", chat_history, hist_state, True, "auto", None, 0.5, 256, "English", "Aria", False, 100, "test")
    # respond is a generator-function (contains yield); collect final output
    if isinstance(gen, types.GeneratorType):
        last = None
        try:
            while True:
                last = next(gen)
        except StopIteration as e:
            if hasattr(e, 'value') and e.value is not None:
                last = e.value
        out = last
    else:
        out = gen
    assert isinstance(out, tuple)
    chatbot, cleared_input, new_hist_state, provider_info, status = out
    assert cleared_input == ""
    assert isinstance(new_hist_state, list)
    assert new_hist_state and new_hist_state[-1]["assistant"].startswith("[Aria-")
