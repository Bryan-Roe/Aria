"""Unit tests for the rule-based fallback gesture parser.

These guard the natural-language gesture trigger map so AI-issued commands
like "thanks" and "applaud" continue to resolve to a valid VALID_GESTURES
action without requiring an LLM.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "aria"))

import server as aria_server  # type: ignore  # noqa: E402


def _gestures_for(command: str) -> list[str]:
    """Run the fallback parser and return the gesture_type values it emits."""
    handler_cls = aria_server.ActionParser if hasattr(aria_server, "ActionParser") else None
    if handler_cls is None:
        # ActionParser is nested inside the request handler module; find any
        # class that exposes parse_with_fallback.
        for name in dir(aria_server):
            obj = getattr(aria_server, name)
            if isinstance(obj, type) and hasattr(obj, "parse_with_fallback"):
                handler_cls = obj
                break
    assert handler_cls is not None, "Could not locate parse_with_fallback owner class"
    parser = handler_cls.__new__(handler_cls)  # bypass __init__ side effects
    actions = handler_cls.parse_with_fallback(parser, command)
    return [a.get("gesture_type") for a in actions if a.get("action") == "gesture"]


def test_thanks_maps_to_nod():
    assert "nod" in _gestures_for("thanks for that")


def test_applaud_maps_to_clap():
    assert "clap" in _gestures_for("please applaud")


def test_good_job_maps_to_thumbs_up():
    assert "thumbs_up" in _gestures_for("good job")


def test_dunno_maps_to_shrug():
    assert "shrug" in _gestures_for("dunno")


def test_yo_maps_to_wave():
    assert "wave" in _gestures_for("yo aria")


def test_all_returned_gestures_are_valid():
    valid = set(aria_server.VALID_GESTURES)
    for cmd in ["wave", "hello", "thanks", "applaud", "good job", "shrug", "bow", "nod"]:
        for g in _gestures_for(cmd):
            assert g in valid, f"Gesture '{g}' from command '{cmd}' is not in VALID_GESTURES"
