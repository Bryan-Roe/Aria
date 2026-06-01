import os
import json
import time
from typing import List, Dict


DEFAULT_WEBHOOK_DIR = "data_out/gradio_conversations/webhooks"


def post_conversation_to_webhook(
    hist_state: List[dict], webhook_name: str = "webhook", webhook_dir: str | None = None
) -> str:
    """Simulated webhook delivery: save payload to webhook_dir (local) with timestamp. Returns path written."""
    target_dir = webhook_dir or DEFAULT_WEBHOOK_DIR
    os.makedirs(target_dir, exist_ok=True)
    ts = int(time.time())
    fname = os.path.join(target_dir, f"{webhook_name}_{ts}.json")
    payload = {
        "timestamp": ts,
        "conversation": hist_state,
    }
    temp = fname + ".tmp"
    with open(temp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(temp, fname)
    return fname
