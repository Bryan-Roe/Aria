import os
import time
from scripts import gradio_maintenance


def test_cleanup_old_conversations(tmp_path):
    d = tmp_path
    # create recent and old files
    recent = d / "recent.json"
    old = d / "old.json"
    recent.write_text('x')
    old.write_text('y')
    # set mtime of old to 40 days ago
    old_time = time.time() - 40 * 24 * 3600
    os.utime(str(old), (old_time, old_time))
    removed = gradio_maintenance.cleanup_old_conversations(str(d), max_age_days=30)
    assert removed == 1
    remaining = os.listdir(str(d))
    assert 'recent.json' in remaining
