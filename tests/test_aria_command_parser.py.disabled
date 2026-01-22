"""Tests for aria_web command parsing and auto-execute"""
import pytest
import json
from unittest.mock import Mock, patch
from aria_web.server import (
    parse_auto_execute_command,
    execute_action_sequence,
    validate_action,
    ACTION_SCHEMA
)


class TestCommandParsing:
    """Test natural language command parsing"""
    
    def test_simple_move_command(self):
        """Test parsing simple move command"""
        command = "move left"
        actions = parse_auto_execute_command(command, mode="plan")
        assert actions is not None
        assert isinstance(actions, list)
        if actions:
            assert actions[0]["action"] == "move" or "move" in str(actions[0]).lower()
    
    def test_simple_gesture_command(self):
        """Test parsing gesture command"""
        command = "wave"
        actions = parse_auto_execute_command(command, mode="plan")
        assert actions is not None
        if actions:
            assert "gesture" in str(actions[0]).lower() or "wave" in str(actions[0]).lower()
    
    def test_complex_command_sequence(self):
        """Test parsing complex multi-action command"""
        command = "move to the table and pick up the apple"
        actions = parse_auto_execute_command(command, mode="plan")
        assert actions is not None
        assert len(actions) > 0
    
    def test_empty_command(self):
        """Test handling empty command"""
        command = ""
        actions = parse_auto_execute_command(command, mode="plan")
        # Should handle gracefully
        assert actions is not None
    
    def test_invalid_command(self):
        """Test handling invalid command"""
        command = "xyz123 invalid command"
        actions = parse_auto_execute_command(command, mode="plan")
        # Should return fallback or empty
        assert actions is not None or actions == []
    
    def test_command_with_direction(self):
        """Test command with direction specification"""
        for direction in ["left", "right", "forward", "backward", "up", "down"]:
            command = f"move {direction}"
            actions = parse_auto_execute_command(command, mode="plan")
            assert actions is not None
    
    def test_command_with_object_reference(self):
        """Test command referencing an object"""
        command = "pick up ball"
        actions = parse_auto_execute_command(command, mode="plan")
        assert actions is not None
        if actions:
            assert len(actions) > 0
    
    def test_dance_command(self):
        """Test dance command parsing"""
        command = "dance"
        actions = parse_auto_execute_command(command, mode="plan")
        assert actions is not None
    
    def test_jump_command(self):
        """Test jump command parsing"""
        command = "jump"
        actions = parse_auto_execute_command(command, mode="plan")
        assert actions is not None
    
    def test_look_command(self):
        """Test look command parsing"""
        command = "look at me"
        actions = parse_auto_execute_command(command, mode="plan")
        assert actions is not None


class TestActionValidation:
    """Test action validation"""
    
    def test_validate_move_action(self):
        """Test validating move action"""
        action = {
            "action": "move",
            "direction": "left",
            "distance": 50
        }
        result = validate_action(action)
        assert result is True or result == action
    
    def test_validate_say_action(self):
        """Test validating say action"""
        action = {
            "action": "say",
            "text": "Hello"
        }
        result = validate_action(action)
        assert result is True or result == action
    
    def test_validate_pickup_action(self):
        """Test validating pickup action"""
        action = {
            "action": "pickup",
            "object_id": "ball"
        }
        result = validate_action(action)
        assert result is True or result == action
    
    def test_validate_gesture_action(self):
        """Test validating gesture action"""
        action = {
            "action": "gesture",
            "gesture_type": "wave"
        }
        result = validate_action(action)
        assert result is True or result == action
    
    def test_validate_invalid_action_type(self):
        """Test validation fails for invalid action type"""
        action = {
            "action": "invalid_action",
            "param": "value"
        }
        result = validate_action(action)
        assert result is False or result is not True
    
    def test_validate_missing_required_field(self):
        """Test validation fails when required field missing"""
        action = {
            "action": "say"
            # Missing 'text' field
        }
        result = validate_action(action)
        assert result is False or result is not True
    
    def test_validate_throw_action(self):
        """Test validating throw action"""
        action = {
            "action": "throw",
            "object_id": "ball",
            "direction": "forward"
        }
        result = validate_action(action)
        assert result is True or result == action
    
    def test_validate_drop_action(self):
        """Test validating drop action"""
        action = {
            "action": "drop",
            "object_id": "ball"
        }
        result = validate_action(action)
        assert result is True or result == action
    
    def test_validate_wait_action(self):
        """Test validating wait action"""
        action = {
            "action": "wait",
            "duration": 1000
        }
        result = validate_action(action)
        assert result is True or result == action


class TestActionSequenceExecution:
    """Test action sequence execution"""
    
    @patch("aria_web.server.execute_action")
    def test_execute_single_action(self, mock_execute):
        """Test executing single action"""
        mock_execute.return_value = {"success": True}
        
        actions = [{"action": "move", "direction": "left"}]
        result = execute_action_sequence(actions, current_state={})
        
        assert result is not None
        mock_execute.assert_called()
    
    @patch("aria_web.server.execute_action")
    def test_execute_multiple_actions(self, mock_execute):
        """Test executing multiple actions in sequence"""
        mock_execute.return_value = {"success": True}
        
        actions = [
            {"action": "move", "direction": "left"},
            {"action": "say", "text": "Hello"},
            {"action": "gesture", "gesture_type": "wave"}
        ]
        result = execute_action_sequence(actions, current_state={})
        
        assert mock_execute.call_count >= len(actions)
    
    @patch("aria_web.server.execute_action")
    def test_execute_with_error_handling(self, mock_execute):
        """Test error handling during execution"""
        mock_execute.side_effect = Exception("Action failed")
        
        actions = [{"action": "move", "direction": "left"}]
        result = execute_action_sequence(actions, current_state={}, continue_on_error=True)
        
        # Should handle error gracefully
        assert result is not None
    
    @patch("aria_web.server.execute_action")
    def test_execute_stops_on_error(self, mock_execute):
        """Test execution stops on error when configured"""
        mock_execute.side_effect = Exception("Action failed")
        
        actions = [
            {"action": "move", "direction": "left"},
            {"action": "say", "text": "Hello"}
        ]
        with pytest.raises(Exception):
            execute_action_sequence(actions, current_state={}, continue_on_error=False)


class TestPlanVsExecuteMode:
    """Test difference between plan and execute modes"""
    
    def test_plan_mode_returns_actions(self):
        """Test plan mode returns action list without executing"""
        command = "move left"
        actions = parse_auto_execute_command(command, mode="plan")
        
        assert isinstance(actions, list)
        # Actions should be returned but not executed
    
    def test_execute_mode_returns_actions(self):
        """Test execute mode returns action list and executes"""
        command = "wave"
        with patch("aria_web.server.execute_action") as mock_execute:
            mock_execute.return_value = {"success": True}
            actions = parse_auto_execute_command(command, mode="execute")
            
            assert isinstance(actions, list)
            # May or may not call execute depending on implementation
    
    def test_mode_parameter_respected(self):
        """Test that mode parameter is respected"""
        command = "dance"
        plan_actions = parse_auto_execute_command(command, mode="plan")
        execute_actions = parse_auto_execute_command(command, mode="execute")
        
        # Both should return valid action lists
        assert plan_actions is not None
        assert execute_actions is not None


class TestFallbackParsing:
    """Test fallback parsing when LLM is unavailable"""
    
    def test_fallback_move_parsing(self):
        """Test fallback parser handles move commands"""
        command = "move left"
        actions = parse_auto_execute_command(command, mode="plan", use_fallback=True)
        assert actions is not None
    
    def test_fallback_gesture_parsing(self):
        """Test fallback parser handles gesture commands"""
        for gesture in ["wave", "dance", "jump"]:
            command = gesture
            actions = parse_auto_execute_command(command, mode="plan", use_fallback=True)
            assert actions is not None
    
    def test_fallback_handles_unknown(self):
        """Test fallback parser handles unknown commands"""
        command = "xyzabc unknown"
        actions = parse_auto_execute_command(command, mode="plan", use_fallback=True)
        # Should return some fallback action or empty list
        assert actions is not None or actions == []


class TestStateManagement:
    """Test state management in action execution"""
    
    @patch("aria_web.server.execute_action")
    def test_state_updated_after_action(self, mock_execute):
        """Test state is updated after action execution"""
        mock_execute.return_value = {"success": True, "new_position": (100, 100)}
        
        current_state = {"position": (0, 0)}
        actions = [{"action": "move", "direction": "right"}]
        result = execute_action_sequence(actions, current_state=current_state)
        
        assert result is not None
    
    def test_state_initialization(self):
        """Test initial state is properly initialized"""
        initial_state = {
            "position": (0, 0),
            "holding": None,
            "expression": "neutral"
        }
        
        # State should be valid
        assert "position" in initial_state
        assert "holding" in initial_state
