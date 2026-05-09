import importlib.util
import json
import re
import sys
from http import HTTPStatus
from pathlib import Path

# Load apps/aria/server.py by absolute path to avoid cross-test module-name collisions
# when other suites import a different `server` module first.
_ARIA_SERVER_PATH = Path(__file__).parent.parent / "apps" / "aria" / "server.py"
_ARIA_SERVER_SPEC = importlib.util.spec_from_file_location(
    "aria_server_under_test", _ARIA_SERVER_PATH
)
assert _ARIA_SERVER_SPEC is not None and _ARIA_SERVER_SPEC.loader is not None
aria_server = importlib.util.module_from_spec(_ARIA_SERVER_SPEC)
sys.modules[_ARIA_SERVER_SPEC.name] = aria_server
_ARIA_SERVER_SPEC.loader.exec_module(aria_server)


def test_generate_tags_fallback_say_detection():
    tags = aria_server.generate_tags_fallback("please say hello everyone")
    # We expect at least one say tag
    assert any(
        re.match(r"^\[aria:say:.*hello everyone.*\]$", t, flags=re.I) for t in tags
    ), f"Expected say tag in {tags}"


def test_determine_position_for_pickup():
    tag = aria_server.determine_position_from_context("pick up apple")
    assert tag.startswith("[aria:position"), "pickup should return a position tag"


def test_generate_tags_fallback_add_object():
    tags = aria_server.generate_tags_fallback("add a bear to the scene")
    assert any(
        "[aria:interact:add" in t for t in tags
    ), "Expected an interact:add tag for spawn/add commands"


def test_determine_position_come_here_command():
    tag = aria_server.determine_position_from_context("come here please")
    assert tag == "[aria:position:50:85]"


def test_parse_with_fallback_follow_me_adds_nod_and_move():
    parser = aria_server.AriaActionParser()
    actions = parser.parse_with_fallback("follow me")

    assert any(
        a.get("action") == "gesture" and a.get("gesture_type") == "nod" for a in actions
    ), f"Expected nod gesture for 'follow me' but got {actions}"
    assert any(
        a.get("action") == "move" and a.get("target") == {"x": 50, "y": 75}
        for a in actions
    ), f"Expected move action for 'follow me' but got {actions}"


def test_determine_position_bring_me_command():
    tag = aria_server.determine_position_from_context("bring me the cup")
    assert tag == "[aria:position:50:85]"


def test_parse_with_fallback_bring_me_object_sequence():
    parser = aria_server.AriaActionParser()
    actions = parser.parse_with_fallback("bring me the cup")

    cup_pos = aria_server.stage_state["objects"]["cup"]["position"]
    assert any(
        a.get("action") == "move" and a.get("target") == cup_pos for a in actions
    ), f"Expected move-to-cup action but got {actions}"
    assert any(
        a.get("action") == "pickup" and a.get("object_id") == "cup" for a in actions
    ), f"Expected pickup-cup action but got {actions}"
    assert any(
        a.get("action") == "move" and a.get("target") == {"x": 50, "y": 85}
        for a in actions
    ), f"Expected delivery move action but got {actions}"


def test_determine_position_bring_it_command():
    tag = aria_server.determine_position_from_context("bring it here")
    assert tag == "[aria:position:50:85]"


def test_parse_with_fallback_bring_it_when_holding():
    parser = aria_server.AriaActionParser()
    original_held = aria_server.stage_state["aria"].get("held_object")
    try:
        aria_server.stage_state["aria"]["held_object"] = "book"
        actions = parser.parse_with_fallback("bring it here")

        assert any(
            a.get("action") == "move" and a.get("target") == {"x": 50, "y": 85}
            for a in actions
        ), f"Expected delivery move action for bring-it but got {actions}"
        assert any(
            a.get("action") == "gesture" and a.get("gesture_type") == "nod"
            for a in actions
        ), f"Expected nod gesture for bring-it but got {actions}"
    finally:
        aria_server.stage_state["aria"]["held_object"] = original_held


def test_parse_with_fallback_bring_it_when_not_holding():
    parser = aria_server.AriaActionParser()
    original_held = aria_server.stage_state["aria"].get("held_object")
    try:
        aria_server.stage_state["aria"]["held_object"] = None
        actions = parser.parse_with_fallback("bring it here")

        assert any(
            a.get("action") == "say"
            and "pick something up first" in a.get("text", "").lower()
            for a in actions
        ), f"Expected explanatory say action for bring-it but got {actions}"
    finally:
        aria_server.stage_state["aria"]["held_object"] = original_held


def test_determine_position_drop_here_command():
    tag = aria_server.determine_position_from_context("drop it here")
    assert tag == "[aria:position:50:85]"


def test_parse_with_fallback_drop_here_when_holding():
    parser = aria_server.AriaActionParser()
    original_held = aria_server.stage_state["aria"].get("held_object")
    try:
        aria_server.stage_state["aria"]["held_object"] = "cup"
        actions = parser.parse_with_fallback("drop it here")

        assert any(
            a.get("action") == "move" and a.get("target") == {"x": 50, "y": 85}
            for a in actions
        ), f"Expected move-to-drop-target action but got {actions}"
        assert any(
            a.get("action") == "drop" and a.get("position") == {"x": 50, "y": 85}
            for a in actions
        ), f"Expected drop action at front-center but got {actions}"
    finally:
        aria_server.stage_state["aria"]["held_object"] = original_held


def test_parse_with_fallback_drop_here_when_not_holding():
    parser = aria_server.AriaActionParser()
    original_held = aria_server.stage_state["aria"].get("held_object")
    try:
        aria_server.stage_state["aria"]["held_object"] = None
        actions = parser.parse_with_fallback("put it here")

        assert any(
            a.get("action") == "say"
            and "not holding anything" in a.get("text", "").lower()
            for a in actions
        ), f"Expected explanatory say action but got {actions}"
    finally:
        aria_server.stage_state["aria"]["held_object"] = original_held


def test_parse_with_fallback_compound_pickup_bring_drop_table():
    parser = aria_server.AriaActionParser()
    original_held = aria_server.stage_state["aria"].get("held_object")
    try:
        aria_server.stage_state["aria"]["held_object"] = None
        actions = parser.parse_with_fallback(
            "pick up cup and bring it here then put it on table"
        )

        assert any(
            a.get("action") == "pickup" and a.get("object_id") == "cup" for a in actions
        ), f"Expected pickup action for cup but got {actions}"
        assert any(
            a.get("action") == "gesture" and a.get("gesture_type") == "nod"
            for a in actions
        ), f"Expected nod gesture in compound flow but got {actions}"
        assert any(
            a.get("action") == "drop" and a.get("position") == {"x": 60, "y": 35}
            for a in actions
        ), f"Expected drop-on-table action but got {actions}"
    finally:
        aria_server.stage_state["aria"]["held_object"] = original_held


def test_parse_with_fallback_compound_without_object_has_guidance():
    parser = aria_server.AriaActionParser()
    original_held = aria_server.stage_state["aria"].get("held_object")
    try:
        aria_server.stage_state["aria"]["held_object"] = None
        actions = parser.parse_with_fallback("bring it here, then drop it here")
        say_actions = [a for a in actions if a.get("action") == "say"]
        assert (
            len(say_actions) >= 1
        ), f"Expected at least one guidance say action but got {actions}"
    finally:
        aria_server.stage_state["aria"]["held_object"] = original_held


def test_parse_with_fallback_compound_drop_clears_planned_held_object():
    parser = aria_server.AriaActionParser()
    original_held = aria_server.stage_state["aria"].get("held_object")
    try:
        aria_server.stage_state["aria"]["held_object"] = "cup"
        actions = parser.parse_with_fallback("drop it here then bring it here")
        say_actions = [a for a in actions if a.get("action") == "say"]
        assert any(
            "pick something up first" in a.get("text", "").lower() for a in say_actions
        ), f"Expected bring-it guidance after planned drop but got {actions}"
    finally:
        aria_server.stage_state["aria"]["held_object"] = original_held


def test_parse_with_fallback_temporal_separator_after_that():
    parser = aria_server.AriaActionParser()
    original_held = aria_server.stage_state["aria"].get("held_object")
    try:
        aria_server.stage_state["aria"]["held_object"] = None
        actions = parser.parse_with_fallback("pick up cup after that bring it here")

        assert any(
            a.get("action") == "pickup" and a.get("object_id") == "cup" for a in actions
        ), f"Expected pickup in after-that sequence but got {actions}"
        assert any(
            a.get("action") == "move" and a.get("target") == {"x": 50, "y": 85}
            for a in actions
        ), f"Expected bring-it move in after-that sequence but got {actions}"
    finally:
        aria_server.stage_state["aria"]["held_object"] = original_held


def test_parse_with_fallback_temporal_separator_finally():
    parser = aria_server.AriaActionParser()
    original_held = aria_server.stage_state["aria"].get("held_object")
    try:
        aria_server.stage_state["aria"]["held_object"] = None
        actions = parser.parse_with_fallback("pick up cup finally bring it here")

        assert any(
            a.get("action") == "pickup" and a.get("object_id") == "cup" for a in actions
        ), f"Expected pickup in finally sequence but got {actions}"
        assert any(
            a.get("action") == "move" and a.get("target") == {"x": 50, "y": 85}
            for a in actions
        ), f"Expected bring-it move in finally sequence but got {actions}"
    finally:
        aria_server.stage_state["aria"]["held_object"] = original_held


def test_parse_with_fallback_temporal_separator_lastly():
    parser = aria_server.AriaActionParser()
    original_held = aria_server.stage_state["aria"].get("held_object")
    try:
        aria_server.stage_state["aria"]["held_object"] = None
        actions = parser.parse_with_fallback("pick up cup lastly bring it here")

        assert any(
            a.get("action") == "pickup" and a.get("object_id") == "cup" for a in actions
        ), f"Expected pickup in lastly sequence but got {actions}"
        assert any(
            a.get("action") == "move" and a.get("target") == {"x": 50, "y": 85}
            for a in actions
        ), f"Expected bring-it move in lastly sequence but got {actions}"
    finally:
        aria_server.stage_state["aria"]["held_object"] = original_held


def test_parse_with_fallback_temporal_separator_first_second():
    parser = aria_server.AriaActionParser()
    original_held = aria_server.stage_state["aria"].get("held_object")
    try:
        aria_server.stage_state["aria"]["held_object"] = None
        actions = parser.parse_with_fallback("first pick up cup second bring it here")

        assert any(
            a.get("action") == "pickup" and a.get("object_id") == "cup" for a in actions
        ), f"Expected pickup in first/second sequence but got {actions}"
        assert any(
            a.get("action") == "move" and a.get("target") == {"x": 50, "y": 85}
            for a in actions
        ), f"Expected bring-it move in first/second sequence but got {actions}"
    finally:
        aria_server.stage_state["aria"]["held_object"] = original_held


def test_parse_with_fallback_temporal_separator_first_second_finally():
    parser = aria_server.AriaActionParser()
    original_held = aria_server.stage_state["aria"].get("held_object")
    try:
        aria_server.stage_state["aria"]["held_object"] = None
        actions = parser.parse_with_fallback(
            "first pick up cup second bring it here finally put it on table"
        )

        assert any(
            a.get("action") == "pickup" and a.get("object_id") == "cup" for a in actions
        ), f"Expected pickup in first/second/finally sequence but got {actions}"
        assert any(
            a.get("action") == "drop" and a.get("position") == {"x": 60, "y": 35}
            for a in actions
        ), f"Expected final table drop in first/second/finally sequence but got {actions}"
    finally:
        aria_server.stage_state["aria"]["held_object"] = original_held


def test_parse_with_fallback_temporal_separator_step_numbers():
    parser = aria_server.AriaActionParser()
    original_held = aria_server.stage_state["aria"].get("held_object")
    try:
        aria_server.stage_state["aria"]["held_object"] = None
        actions = parser.parse_with_fallback(
            "step 1 pick up cup step 2 bring it here step 3 put it on table"
        )

        assert any(
            a.get("action") == "pickup" and a.get("object_id") == "cup" for a in actions
        ), f"Expected pickup in step-number sequence but got {actions}"
        assert any(
            a.get("action") == "drop" and a.get("position") == {"x": 60, "y": 35}
            for a in actions
        ), f"Expected table drop in step-number sequence but got {actions}"
    finally:
        aria_server.stage_state["aria"]["held_object"] = original_held


def test_parse_with_fallback_temporal_separator_step_numbers_compact():
    parser = aria_server.AriaActionParser()
    original_held = aria_server.stage_state["aria"].get("held_object")
    try:
        aria_server.stage_state["aria"]["held_object"] = None
        actions = parser.parse_with_fallback("step1 pick up cup step2 bring it here")

        assert any(
            a.get("action") == "pickup" and a.get("object_id") == "cup" for a in actions
        ), f"Expected pickup in compact-step sequence but got {actions}"
        assert any(
            a.get("action") == "move" and a.get("target") == {"x": 50, "y": 85}
            for a in actions
        ), f"Expected bring-it move in compact-step sequence but got {actions}"
    finally:
        aria_server.stage_state["aria"]["held_object"] = original_held


def test_parse_with_fallback_temporal_separator_step_roman_numerals():
    parser = aria_server.AriaActionParser()
    original_held = aria_server.stage_state["aria"].get("held_object")
    try:
        aria_server.stage_state["aria"]["held_object"] = None
        actions = parser.parse_with_fallback("step I pick up cup step II bring it here")

        assert any(
            a.get("action") == "pickup" and a.get("object_id") == "cup" for a in actions
        ), f"Expected pickup in Roman step sequence but got {actions}"
        assert any(
            a.get("action") == "move" and a.get("target") == {"x": 50, "y": 85}
            for a in actions
        ), f"Expected bring-it move in Roman step sequence but got {actions}"
    finally:
        aria_server.stage_state["aria"]["held_object"] = original_held


def test_parse_with_fallback_temporal_separator_numbered_list_markers():
    parser = aria_server.AriaActionParser()
    original_held = aria_server.stage_state["aria"].get("held_object")
    try:
        aria_server.stage_state["aria"]["held_object"] = None
        actions = parser.parse_with_fallback(
            "1) pick up cup 2) bring it here 3) put it on table"
        )

        assert any(
            a.get("action") == "pickup" and a.get("object_id") == "cup" for a in actions
        ), f"Expected pickup in numbered-list sequence but got {actions}"
        assert any(
            a.get("action") == "drop" and a.get("position") == {"x": 60, "y": 35}
            for a in actions
        ), f"Expected table drop in numbered-list sequence but got {actions}"
    finally:
        aria_server.stage_state["aria"]["held_object"] = original_held


def test_parse_with_fallback_temporal_separator_phase_numbers():
    parser = aria_server.AriaActionParser()
    original_held = aria_server.stage_state["aria"].get("held_object")
    try:
        aria_server.stage_state["aria"]["held_object"] = None
        actions = parser.parse_with_fallback(
            "phase 1 pick up cup phase 2 bring it here"
        )

        assert any(
            a.get("action") == "pickup" and a.get("object_id") == "cup" for a in actions
        ), f"Expected pickup in phase-number sequence but got {actions}"
        assert any(
            a.get("action") == "move" and a.get("target") == {"x": 50, "y": 85}
            for a in actions
        ), f"Expected bring-it move in phase-number sequence but got {actions}"
    finally:
        aria_server.stage_state["aria"]["held_object"] = original_held


def test_parse_with_fallback_temporal_separator_part_roman_numerals():
    parser = aria_server.AriaActionParser()
    original_held = aria_server.stage_state["aria"].get("held_object")
    try:
        aria_server.stage_state["aria"]["held_object"] = None
        actions = parser.parse_with_fallback(
            "part I pick up cup part II put it on table"
        )

        assert any(
            a.get("action") == "pickup" and a.get("object_id") == "cup" for a in actions
        ), f"Expected pickup in part-Roman sequence but got {actions}"
        assert any(
            a.get("action") == "drop" and a.get("position") == {"x": 60, "y": 35}
            for a in actions
        ), f"Expected table drop in part-Roman sequence but got {actions}"
    finally:
        aria_server.stage_state["aria"]["held_object"] = original_held


def test_parse_with_fallback_temporal_separator_ascii_arrow_flow():
    parser = aria_server.AriaActionParser()
    original_held = aria_server.stage_state["aria"].get("held_object")
    try:
        aria_server.stage_state["aria"]["held_object"] = None
        actions = parser.parse_with_fallback(
            "pick up cup -> bring it here => put it on table"
        )

        assert any(
            a.get("action") == "pickup" and a.get("object_id") == "cup" for a in actions
        ), f"Expected pickup in ASCII arrow sequence but got {actions}"
        assert any(
            a.get("action") == "drop" and a.get("position") == {"x": 60, "y": 35}
            for a in actions
        ), f"Expected table drop in ASCII arrow sequence but got {actions}"
    finally:
        aria_server.stage_state["aria"]["held_object"] = original_held


def test_parse_with_fallback_temporal_separator_unicode_arrow_flow():
    parser = aria_server.AriaActionParser()
    original_held = aria_server.stage_state["aria"].get("held_object")
    try:
        aria_server.stage_state["aria"]["held_object"] = None
        actions = parser.parse_with_fallback("pick up cup → bring it here")

        assert any(
            a.get("action") == "pickup" and a.get("object_id") == "cup" for a in actions
        ), f"Expected pickup in Unicode arrow sequence but got {actions}"
        assert any(
            a.get("action") == "move" and a.get("target") == {"x": 50, "y": 85}
            for a in actions
        ), f"Expected bring-it move in Unicode arrow sequence but got {actions}"
    finally:
        aria_server.stage_state["aria"]["held_object"] = original_held


def test_parse_with_fallback_temporal_separator_newline_bullets():
    parser = aria_server.AriaActionParser()
    original_held = aria_server.stage_state["aria"].get("held_object")
    try:
        aria_server.stage_state["aria"]["held_object"] = None
        actions = parser.parse_with_fallback(
            "pick up cup\n- bring it here\n- put it on table"
        )

        assert any(
            a.get("action") == "pickup" and a.get("object_id") == "cup" for a in actions
        ), f"Expected pickup in newline-bullet sequence but got {actions}"
        assert any(
            a.get("action") == "drop" and a.get("position") == {"x": 60, "y": 35}
            for a in actions
        ), f"Expected table drop in newline-bullet sequence but got {actions}"
    finally:
        aria_server.stage_state["aria"]["held_object"] = original_held


def test_parse_with_fallback_temporal_separator_then_next_labels():
    parser = aria_server.AriaActionParser()
    original_held = aria_server.stage_state["aria"].get("held_object")
    try:
        aria_server.stage_state["aria"]["held_object"] = None
        actions = parser.parse_with_fallback(
            "pick up cup then: bring it here next: put it on table"
        )

        assert any(
            a.get("action") == "pickup" and a.get("object_id") == "cup" for a in actions
        ), f"Expected pickup in then/next-label sequence but got {actions}"
        assert any(
            a.get("action") == "drop" and a.get("position") == {"x": 60, "y": 35}
            for a in actions
        ), f"Expected table drop in then/next-label sequence but got {actions}"
    finally:
        aria_server.stage_state["aria"]["held_object"] = original_held


def test_parse_with_fallback_temporal_separator_afterward_finally_labels():
    parser = aria_server.AriaActionParser()
    original_held = aria_server.stage_state["aria"].get("held_object")
    try:
        aria_server.stage_state["aria"]["held_object"] = None
        actions = parser.parse_with_fallback(
            "pick up cup afterward: bring it here finally: put it on table"
        )

        assert any(
            a.get("action") == "pickup" and a.get("object_id") == "cup" for a in actions
        ), f"Expected pickup in afterward/finally-label sequence but got {actions}"
        assert any(
            a.get("action") == "drop" and a.get("position") == {"x": 60, "y": 35}
            for a in actions
        ), f"Expected table drop in afterward/finally-label sequence but got {actions}"
    finally:
        aria_server.stage_state["aria"]["held_object"] = original_held


def test_parse_with_fallback_temporal_separator_newline_checkbox_bullets():
    parser = aria_server.AriaActionParser()
    original_held = aria_server.stage_state["aria"].get("held_object")
    try:
        aria_server.stage_state["aria"]["held_object"] = None
        actions = parser.parse_with_fallback(
            "pick up cup\n- [ ] bring it here\n- [x] put it on table"
        )

        assert any(
            a.get("action") == "pickup" and a.get("object_id") == "cup" for a in actions
        ), f"Expected pickup in checkbox-bullet sequence but got {actions}"
        assert any(
            a.get("action") == "drop" and a.get("position") == {"x": 60, "y": 35}
            for a in actions
        ), f"Expected table drop in checkbox-bullet sequence but got {actions}"
    finally:
        aria_server.stage_state["aria"]["held_object"] = original_held


def test_parse_with_fallback_temporal_separator_pipe_chain():
    parser = aria_server.AriaActionParser()
    original_held = aria_server.stage_state["aria"].get("held_object")
    try:
        aria_server.stage_state["aria"]["held_object"] = None
        actions = parser.parse_with_fallback(
            "pick up cup | bring it here | put it on table"
        )

        assert any(
            a.get("action") == "pickup" and a.get("object_id") == "cup" for a in actions
        ), f"Expected pickup in pipe-chain sequence but got {actions}"
        assert any(
            a.get("action") == "drop" and a.get("position") == {"x": 60, "y": 35}
            for a in actions
        ), f"Expected table drop in pipe-chain sequence but got {actions}"
    finally:
        aria_server.stage_state["aria"]["held_object"] = original_held


def test_parse_with_fallback_temporal_separator_mixed_pipe_and_arrows():
    parser = aria_server.AriaActionParser()
    original_held = aria_server.stage_state["aria"].get("held_object")
    try:
        aria_server.stage_state["aria"]["held_object"] = None
        actions = parser.parse_with_fallback(
            "pick up cup | bring it here -> put it on table"
        )

        assert any(
            a.get("action") == "pickup" and a.get("object_id") == "cup" for a in actions
        ), f"Expected pickup in mixed pipe/arrow sequence but got {actions}"
        assert any(
            a.get("action") == "drop" and a.get("position") == {"x": 60, "y": 35}
            for a in actions
        ), f"Expected table drop in mixed pipe/arrow sequence but got {actions}"
    finally:
        aria_server.stage_state["aria"]["held_object"] = original_held


def test_parse_with_fallback_compound_dedup_repeated_segment():
    parser = aria_server.AriaActionParser()
    original_held = aria_server.stage_state["aria"].get("held_object")
    try:
        aria_server.stage_state["aria"]["held_object"] = "book"
        actions = parser.parse_with_fallback("bring it here then bring it here")

        front_moves = [
            a
            for a in actions
            if a.get("action") == "move" and a.get("target") == {"x": 50, "y": 85}
        ]
        nods = [
            a
            for a in actions
            if a.get("action") == "gesture" and a.get("gesture_type") == "nod"
        ]

        assert (
            len(front_moves) == 1
        ), f"Expected one deduped front-center move but got {front_moves}"
        assert len(nods) == 1, f"Expected one deduped nod gesture but got {nods}"
    finally:
        aria_server.stage_state["aria"]["held_object"] = original_held


def test_log_message_handles_httpstatus_args(capsys):
    aria_server.AriaRequestHandler.log_message(
        object(),
        "code %d, message %s",
        HTTPStatus.NOT_FOUND,
        "File not found",
    )

    captured = capsys.readouterr()
    assert "code 404, message File not found" in captured.out


def test_generate_world_with_llm_accepts_provider_content_dict():
    class MockProvider:
        def complete(self, messages, stream=False):
            world_payload = {
                "objects": [
                    {
                        "id": "star",
                        "emoji": "⭐",
                        "position": {"x": 20, "y": 30},
                        "state": "on_stage",
                    },
                    {
                        "id": "moon",
                        "emoji": "🌙",
                        "position": {"x": 45, "y": 25},
                        "state": "on_stage",
                    },
                ],
                "environment": {
                    "theme": "space",
                    "stage_bounds": {"width": 100, "height": 100},
                },
            }
            return {"content": json.dumps(world_payload)}

    world = aria_server.generate_world_with_llm("space", 2, MockProvider())
    assert world.get("llm", False) is True
    assert world["environment"]["theme"] == "space"
    assert "star" in world["objects"] or "moon" in world["objects"]


def test_generate_world_with_llm_accepts_object_list_in_response():
    class MockProvider:
        def complete(self, messages, stream=False):
            world_payload = {
                "objects": [
                    {
                        "id": "shell",
                        "emoji": "🐚",
                        "position": {"x": 30, "y": 40},
                        "state": "on_stage",
                    }
                ],
                "environment": {
                    "theme": "ocean",
                    "stage_bounds": {"width": 100, "height": 100},
                },
            }
            return json.dumps(world_payload)

    world = aria_server.generate_world_with_llm("ocean", 1, MockProvider())
    assert world.get("llm", False) is True
    assert world["environment"]["theme"] == "ocean"
    assert any(obj["emoji"] == "🐚" for obj in world["objects"].values())


# ===== Sparkle Functionality Tests =====


def test_sparkle_effect_basic():
    """Test basic sparkle command detection"""
    tags = aria_server.generate_tags_fallback("sparkle")
    assert any(
        "[aria:effect:sparkle" in t for t in tags
    ), f"Expected sparkle effect tag in {tags}"


def test_sparkle_effect_with_synonyms():
    """Test sparkle effect with synonym keywords"""
    test_commands = [
        "make it sparkle",
        "add some glitter",
        "shimmer effect",
        "make it shine",
        "sparkles please",
    ]
    for cmd in test_commands:
        tags = aria_server.generate_tags_fallback(cmd)
        assert any(
            "[aria:effect:sparkle" in t for t in tags
        ), f"Expected sparkle effect tag for command '{cmd}' but got {tags}"


def test_sparkle_intensity_light():
    """Test light sparkle intensity detection"""
    test_commands = ["light sparkle", "subtle sparkle", "gentle shimmer"]
    for cmd in test_commands:
        tags = aria_server.generate_tags_fallback(cmd)
        assert any(
            "[aria:effect:sparkle:light]" in t for t in tags
        ), f"Expected light intensity sparkle tag for '{cmd}' but got {tags}"


def test_sparkle_intensity_normal():
    """Test normal sparkle intensity (default)"""
    tags = aria_server.generate_tags_fallback("sparkle")
    assert any(
        "[aria:effect:sparkle:normal]" in t for t in tags
    ), f"Expected normal intensity sparkle tag but got {tags}"


def test_sparkle_intensity_heavy():
    """Test heavy sparkle intensity detection"""
    test_commands = [
        "heavy sparkle",
        "intense sparkle",
        "lots of sparkles",
        "many sparkles",
    ]
    for cmd in test_commands:
        tags = aria_server.generate_tags_fallback(cmd)
        assert any(
            "[aria:effect:sparkle:heavy]" in t for t in tags
        ), f"Expected heavy intensity sparkle tag for '{cmd}' but got {tags}"


def test_glow_effect_basic():
    """Test glow effect detection"""
    tags = aria_server.generate_tags_fallback("glow")
    assert any(
        "[aria:effect:glow" in t for t in tags
    ), f"Expected glow effect tag in {tags}"


def test_glow_effect_synonyms():
    """Test glow effect with synonym keywords"""
    test_commands = ["make it glow", "glowing effect", "radiate light", "illuminate"]
    for cmd in test_commands:
        tags = aria_server.generate_tags_fallback(cmd)
        assert any(
            "[aria:effect:glow" in t for t in tags
        ), f"Expected glow effect tag for command '{cmd}' but got {tags}"


def test_hearts_effect_basic():
    """Test hearts effect detection"""
    tags = aria_server.generate_tags_fallback("hearts")
    assert any(
        "[aria:effect:hearts" in t for t in tags
    ), f"Expected hearts effect tag in {tags}"


def test_hearts_effect_synonyms():
    """Test hearts effect with synonym keywords"""
    test_commands = ["show hearts", "heart effect", "show some love"]
    for cmd in test_commands:
        tags = aria_server.generate_tags_fallback(cmd)
        assert any(
            "[aria:effect:hearts" in t for t in tags
        ), f"Expected hearts effect tag for command '{cmd}' but got {tags}"


def test_combined_dance_and_sparkle():
    """Test combined commands like 'dance with sparkles'"""
    tags = aria_server.generate_tags_fallback("dance with sparkles")
    assert any(
        "dance" in t.lower() or "animate" in t.lower() for t in tags
    ), f"Expected dance/animate tag in {tags}"
    assert any(
        "[aria:effect:sparkle" in t for t in tags
    ), f"Expected sparkle effect tag in {tags}"


def test_keyword_frozensets_defined():
    """Test that effect keyword frozensets are defined"""
    assert hasattr(
        aria_server, "SPARKLE_KEYWORDS"
    ), "SPARKLE_KEYWORDS should be defined"
    assert hasattr(aria_server, "GLOW_KEYWORDS"), "GLOW_KEYWORDS should be defined"
    assert hasattr(aria_server, "HEARTS_KEYWORDS"), "HEARTS_KEYWORDS should be defined"

    # Verify they are frozensets
    assert isinstance(
        aria_server.SPARKLE_KEYWORDS, frozenset
    ), "SPARKLE_KEYWORDS should be a frozenset"
    assert isinstance(
        aria_server.GLOW_KEYWORDS, frozenset
    ), "GLOW_KEYWORDS should be a frozenset"
    assert isinstance(
        aria_server.HEARTS_KEYWORDS, frozenset
    ), "HEARTS_KEYWORDS should be a frozenset"

    # Verify they contain expected keywords
    assert "sparkle" in aria_server.SPARKLE_KEYWORDS
    assert "glitter" in aria_server.SPARKLE_KEYWORDS
    assert "glow" in aria_server.GLOW_KEYWORDS
    assert "hearts" in aria_server.HEARTS_KEYWORDS


def test_effect_intensity_mutually_exclusive():
    """Test that only one intensity level is applied"""
    # When both keywords are present, 'light' takes precedence due to if-elif order
    tags = aria_server.generate_tags_fallback("light but intense sparkle")
    sparkle_tags = [t for t in tags if "[aria:effect:sparkle" in t]
    assert (
        len(sparkle_tags) == 1
    ), f"Expected exactly one sparkle tag but got {sparkle_tags}"
    # Light should be applied due to if-elif order (light is checked first)
    assert (
        "[aria:effect:sparkle:light]" in sparkle_tags[0]
    ), f"Expected light intensity to take precedence but got {sparkle_tags[0]}"


def test_action_to_tags_move_position_and_say() -> None:
    move_tags = aria_server.action_to_tags(
        {"action": "move", "target": {"x": 42, "y": 73}}
    )
    assert move_tags == ["[aria:position:42:73]"]

    say_tags = aria_server.action_to_tags(
        {"action": "say", "text": "Hello", "emotion": "happy"}
    )
    assert "[aria:say:Hello]" in say_tags
    assert "[aria:expression:happy]" in say_tags


def test_tags_from_actions_flattens_results() -> None:
    tags = aria_server.tags_from_actions(
        [
            {"action": "gesture", "gesture_type": "wave"},
            {"action": "wait", "duration": 1.5},
        ]
    )

    assert tags == ["[aria:gesture:wave]", "[aria:wait:1.5]"]


def test_parse_use_llm_false_bypasses_provider_resolution(monkeypatch) -> None:
    parser = aria_server.AriaActionParser()

    def fail_if_called(*args, **kwargs):
        raise AssertionError("provider resolution should not run when use_llm=False")

    monkeypatch.setattr(parser, "_resolve_provider_for_request", fail_if_called)

    actions = parser.parse("wave", use_llm=False)

    assert any(
        a.get("action") == "gesture" and a.get("gesture_type") == "wave"
        for a in actions
    ), f"Expected fallback gesture action when use_llm=False but got {actions}"


def test_parse_accepts_quantum_llm_provider_alias(monkeypatch):
    captured = {}

    class DummyProvider:
        def complete(self, messages, stream=False):
            return "[]"

    class DummyChoice:
        name = "quantum-llm"
        model = "quantum-llm"

    def fake_detect_provider(explicit=None, model_override=None, **kwargs):
        captured["explicit"] = explicit
        captured["model_override"] = model_override
        return DummyProvider(), DummyChoice()

    monkeypatch.setattr(aria_server, "detect_provider", fake_detect_provider)

    parser = aria_server.AriaActionParser()
    actions = parser.parse(
        "Plan a move",
        use_llm=True,
        provider_choice="quantum-llm",
        model_override="data_out/quantum_llm_training",
    )

    assert actions == []
    assert captured["explicit"] == "quantum"
    assert captured["model_override"] == "data_out/quantum_llm_training"


def test_parse_falls_back_when_provider_resolution_fails(monkeypatch):
    parser = aria_server.AriaActionParser()

    def failing_detect_provider(explicit=None, model_override=None, **kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(aria_server, "detect_provider", failing_detect_provider)

    actions = parser.parse(
        "wave",
        use_llm=True,
        provider_choice="quantum-llm",
        model_override="data_out/quantum_llm_training",
    )

    assert any(
        a.get("action") == "gesture" and a.get("gesture_type") == "wave"
        for a in actions
    ), f"Expected fallback parser action but got {actions}"
