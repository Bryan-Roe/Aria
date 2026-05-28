import sys
from pathlib import Path

# Ensure apps/aria is on the path so tests can import server as module
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "aria"))

import server as aria_server


def test_position_tag_to_move():
    tags = ["[aria:position:30:70]"]
    actions = aria_server.tags_to_actions(tags)
    assert any(a.get("action") == "move" for a in actions)
    move = next(a for a in actions if a.get("action") == "move")
    assert move["target"] == {"x": 30, "y": 70}


def test_named_position_center():
    tags = ["[aria:position:center]"]
    actions = aria_server.tags_to_actions(tags)
    assert actions and actions[0]["action"] == "move"
    assert actions[0]["target"] == {"x": 50, "y": 50}


def test_gesture_and_animation_mapping():
    tags = ["[aria:gesture:wave]", "[aria:animation:spin]"]
    actions = aria_server.tags_to_actions(tags)
    gesture_actions = [a for a in actions if a.get("action") == "gesture"]
    assert len(gesture_actions) >= 1


def test_say_and_expression_mapping():
    tags = ["[aria:say:Hello there]", "[aria:expression:happy]"]
    actions = aria_server.tags_to_actions(tags)
    assert any(a.get("action") == "say" for a in actions)
    say_actions = [a for a in actions if a.get("action") == "say"]
    assert any(a.get("emotion") == "happy" or a.get("text") for a in say_actions)


def test_pickup_drop_look_mapping():
    tags = ["[aria:pickup:apple]", "[aria:drop]", "[aria:look:book]"]
    actions = aria_server.tags_to_actions(tags)
    assert any(a.get("action") == "pickup" and a.get("object_id") == "apple" for a in actions)
    assert any(a.get("action") == "drop" for a in actions)
    assert any(a.get("action") == "look" and a.get("target") == "book" for a in actions)


def test_unknown_tags_ignored():
    tags = ["[aria:unknown:foo]", "[notatag]", "random"]
    actions = aria_server.tags_to_actions(tags)
    assert actions == []


def test_throw_tag_mapping():
    tags = ["[aria:throw:70:40]"]
    actions = aria_server.tags_to_actions(tags)
    assert any(a.get("action") == "throw" for a in actions)
    throw = next(a for a in actions if a.get("action") == "throw")
    assert throw["target"] == {"x": 70, "y": 40}
    assert throw["force"] == "medium"


def test_wait_tag_mapping():
    tags = ["[aria:wait:2.5]"]
    actions = aria_server.tags_to_actions(tags)
    assert actions and actions[0]["action"] == "wait"
    assert actions[0]["duration"] == 2.5


def test_wait_tag_clamps_to_max():
    tags = ["[aria:wait:9999]"]
    actions = aria_server.tags_to_actions(tags)
    assert actions and actions[0]["duration"] == 30.0
