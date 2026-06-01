from scripts import gradio_utils


def test_edit_message_in_hist():
    hist = [
        {"user": "hi", "assistant": "hello", "user_ts": "u1", "assistant_ts": "a1"},
        {"user": "how are you", "assistant": "fine", "user_ts": "u2", "assistant_ts": "a2"},
    ]
    new_hist = gradio_utils.edit_message_in_hist(hist, 1, "assistant", "great")
    assert new_hist[1]["assistant"] == "great"
    assert "assistant_ts" in new_hist[1]


def test_delete_message_in_hist():
    hist = [{"user": "x", "assistant": "y"}, {"user": "a", "assistant": "b"}]
    new_hist = gradio_utils.delete_message_in_hist(hist, 0)
    assert len(new_hist) == 1
    assert new_hist[0]["user"] == "a"
