from scripts import gradio_webhook
import os


def test_post_conversation_to_webhook(tmp_path):
    hist = [{"user": "hello", "assistant": "hi", "user_ts": "u1", "assistant_ts": "a1"}]
    out_dir = str(tmp_path)
    fname = gradio_webhook.post_conversation_to_webhook(hist, webhook_name="testhook", webhook_dir=out_dir)
    assert os.path.exists(fname)
    with open(fname, "r", encoding="utf-8") as f:
        data = f.read()
    assert "conversation" in data
