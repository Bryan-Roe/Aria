from typing import List, Optional
from datetime import datetime


def timestamp_now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def edit_message_in_hist(hist_state: List[dict], index: int, side: str, new_text: str) -> List[dict]:
    """Edit a message in hist_state at the given index.
    side must be 'user' or 'assistant'. Returns the modified hist_state (mutates a copy).
    """
    if hist_state is None:
        return []
    try:
        i = int(index)
    except Exception:
        return hist_state
    if i < 0 or i >= len(hist_state):
        return hist_state
    if side not in ("user", "assistant"):
        side = "assistant"
    # copy
    new_hist = list(hist_state)
    entry = dict(new_hist[i])
    entry[side] = str(new_text)
    if side == "assistant":
        entry["assistant_ts"] = timestamp_now()
    new_hist[i] = entry
    return new_hist


def delete_message_in_hist(hist_state: List[dict], index: int) -> List[dict]:
    if hist_state is None:
        return []
    try:
        i = int(index)
    except Exception:
        return hist_state
    if i < 0 or i >= len(hist_state):
        return hist_state
    new_hist = list(hist_state)
    new_hist.pop(i)
    return new_hist
