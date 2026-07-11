"""Extended tests for apps/aria/server.py — tags_to_actions.

Covers cases not in tests/unit/test_tags_to_actions.py:
- All named positions (left, right, front, back, top, bottom)
- [aria:drop:OBJ] with specific object (vs bare [aria:drop])
- [aria:effect:sparkle/hearts/glow] → wave gesture
- [aria:effect:unknown] → no action produced
- [aria:animation:known_gesture] → that gesture
- [aria:animation:unknown] → wave fallback
- [aria:expression:NAME] → say action with emotion
- Coordinate clamping for positions > 100
- Empty tag list
- Multiple mixed tags in one call
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "aria"))

import server as aria_server

# ---------------------------------------------------------------------------
# Named positions
# ---------------------------------------------------------------------------


class TestNamedPositions:
    def test_position_left(self):
        actions = aria_server.tags_to_actions(["[aria:position:left]"])
        assert len(actions) == 1
        assert actions[0]["action"] == "move"
        assert actions[0]["target"]["x"] == 20

    def test_position_right(self):
        actions = aria_server.tags_to_actions(["[aria:position:right]"])
        assert len(actions) == 1
        assert actions[0]["target"]["x"] == 80

    def test_position_front(self):
        actions = aria_server.tags_to_actions(["[aria:position:front]"])
        assert len(actions) == 1
        assert actions[0]["target"]["y"] == 85

    def test_position_back(self):
        actions = aria_server.tags_to_actions(["[aria:position:back]"])
        assert len(actions) == 1
        assert actions[0]["target"]["y"] == 15

    def test_position_top(self):
        actions = aria_server.tags_to_actions(["[aria:position:top]"])
        assert len(actions) == 1
        assert actions[0]["target"]["y"] == 10

    def test_position_bottom(self):
        actions = aria_server.tags_to_actions(["[aria:position:bottom]"])
        assert len(actions) == 1
        assert actions[0]["target"]["y"] == 90

    def test_unknown_named_position_produces_no_action(self):
        actions = aria_server.tags_to_actions(["[aria:position:nowhere]"])
        assert actions == []


# ---------------------------------------------------------------------------
# Coordinate clamping
# ---------------------------------------------------------------------------


class TestCoordinateClamping:
    def test_x_over_100_clamped(self):
        actions = aria_server.tags_to_actions(["[aria:position:150:50]"])
        # tag regex only allows 1-3 digits → 150 is allowed and then clamped
        assert len(actions) == 1
        assert actions[0]["target"]["x"] == 100

    def test_y_over_100_clamped(self):
        actions = aria_server.tags_to_actions(["[aria:position:50:120]"])
        assert len(actions) == 1
        assert actions[0]["target"]["y"] == 100

    def test_throw_coordinates_clamped(self):
        actions = aria_server.tags_to_actions(["[aria:throw:110:5]"])
        assert len(actions) == 1
        assert actions[0]["target"]["x"] == 100


# ---------------------------------------------------------------------------
# drop with specific object
# ---------------------------------------------------------------------------


class TestDropWithObject:
    def test_drop_with_object_name_produces_drop_action(self):
        actions = aria_server.tags_to_actions(["[aria:drop:apple]"])
        assert len(actions) == 1
        assert actions[0]["action"] == "drop"

    def test_drop_with_object_has_position_none(self):
        actions = aria_server.tags_to_actions(["[aria:drop:book]"])
        assert actions[0].get("position") is None

    def test_bare_drop_produces_drop_action(self):
        actions = aria_server.tags_to_actions(["[aria:drop]"])
        assert len(actions) == 1
        assert actions[0]["action"] == "drop"


# ---------------------------------------------------------------------------
# effect tags
# ---------------------------------------------------------------------------


class TestEffectTags:
    def test_sparkle_effect_maps_to_wave_gesture(self):
        actions = aria_server.tags_to_actions(["[aria:effect:sparkle:large]"])
        assert len(actions) == 1
        assert actions[0]["action"] == "gesture"
        assert actions[0]["gesture_type"] == "wave"

    def test_hearts_effect_maps_to_wave_gesture(self):
        actions = aria_server.tags_to_actions(["[aria:effect:hearts:red]"])
        assert len(actions) == 1
        assert actions[0]["gesture_type"] == "wave"

    def test_glow_effect_maps_to_wave_gesture(self):
        actions = aria_server.tags_to_actions(["[aria:effect:glow:blue]"])
        assert len(actions) == 1
        assert actions[0]["gesture_type"] == "wave"

    def test_unknown_effect_produces_no_action(self):
        actions = aria_server.tags_to_actions(["[aria:effect:explosion:big]"])
        assert actions == []


# ---------------------------------------------------------------------------
# animation tags
# ---------------------------------------------------------------------------


class TestAnimationTags:
    def test_animation_maps_to_valid_gesture(self):
        # "wave" is in VALID_GESTURES
        actions = aria_server.tags_to_actions(["[aria:animation:wave]"])
        assert len(actions) == 1
        assert actions[0]["action"] == "gesture"
        assert actions[0]["gesture_type"] == "wave"

    def test_animation_clap_maps_to_clap(self):
        actions = aria_server.tags_to_actions(["[aria:animation:clap]"])
        assert actions[0]["gesture_type"] == "clap"

    def test_unknown_animation_falls_back_to_wave(self):
        actions = aria_server.tags_to_actions(["[aria:animation:spin]"])
        assert len(actions) == 1
        assert actions[0]["gesture_type"] == "wave"


# ---------------------------------------------------------------------------
# expression tags
# ---------------------------------------------------------------------------


class TestExpressionTags:
    def test_expression_produces_say_action_with_emotion(self):
        actions = aria_server.tags_to_actions(["[aria:expression:happy]"])
        assert len(actions) == 1
        assert actions[0]["action"] == "say"
        assert actions[0]["emotion"] == "happy"
        assert actions[0]["text"] == ""

    def test_expression_sad(self):
        actions = aria_server.tags_to_actions(["[aria:expression:sad]"])
        assert actions[0]["emotion"] == "sad"

    def test_expression_with_complex_name(self):
        actions = aria_server.tags_to_actions(["[aria:expression:surprised]"])
        assert actions[0]["emotion"] == "surprised"


# ---------------------------------------------------------------------------
# empty and mixed inputs
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty_tag_list_returns_empty(self):
        assert aria_server.tags_to_actions([]) == []

    def test_empty_string_tag_returns_empty(self):
        assert aria_server.tags_to_actions([""]) == []

    def test_multiple_tags_all_converted(self):
        tags = [
            "[aria:position:center]",
            "[aria:say:Hello!]",
            "[aria:gesture:wave]",
        ]
        actions = aria_server.tags_to_actions(tags)
        assert len(actions) == 3
        action_types = {a["action"] for a in actions}
        assert "move" in action_types
        assert "say" in action_types
        assert "gesture" in action_types

    def test_order_preserved(self):
        tags = ["[aria:gesture:bow]", "[aria:say:Hi]"]
        actions = aria_server.tags_to_actions(tags)
        assert actions[0]["action"] == "gesture"
        assert actions[1]["action"] == "say"

    def test_wait_zero_duration(self):
        actions = aria_server.tags_to_actions(["[aria:wait:0]"])
        assert len(actions) == 1
        assert actions[0]["duration"] == 0.0

    def test_wait_non_numeric_string_ignored(self):
        # Non-numeric wait tag should not match and produce no action
        actions = aria_server.tags_to_actions(["[aria:wait:infinity]"])
        assert actions == []

    def test_position_speed_field_is_normal(self):
        actions = aria_server.tags_to_actions(["[aria:position:50:50]"])
        assert actions[0]["speed"] == "normal"
