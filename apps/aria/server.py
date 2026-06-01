#!/usr/bin/env python
"""
Simple web server for Aria Visual Command System
Serves the HTML/JS frontend and provides API endpoint for command generation
"""

import datetime
import hashlib
import importlib.util
import json
import logging
import math
import os
import random
import re
import socket
import sys
import urllib.request
from datetime import timezone
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Optional

# Pre-compile regex patterns for performance (avoid recompiling in loops)
_RE_JSON_BLOCK = re.compile(r"\[.*\]", re.DOTALL)


def _sanitize_for_log(value: str) -> str:
    """Sanitize potentially untrusted text for safe plain-text logging."""
    if not isinstance(value, str):
        value = str(value)
    sanitized = value.replace("\r", "").replace("\n", " ")
    sanitized = re.sub(r"[\x00-\x1f\x7f]", "", sanitized)
    return sanitized


_RE_ARIA_TAGS = re.compile(r"\[aria:[^\]]+\]")
_RE_SAY_COMMAND = re.compile(
    r"(?:\b(?:say|announce|shout|speak|tell)\b)(?:\s+(?:everyone|that|to))?[:\-\s]+(.+)",
    re.IGNORECASE,
)
_RE_SANITIZE_BRACKETS = re.compile(r"\]")
_RE_COORDINATES = re.compile(r"(\d{1,3})%?.*?(\d{1,3})%?")
_RE_WAIT_DURATION = re.compile(
    r"\b(?:wait|pause|hold)\s+(\d+(?:\.\d+)?)\s*(?:s|sec|secs|second|seconds)?\b",
    re.IGNORECASE,
)
_RE_COMMAND_SEPARATORS = re.compile(
    r"(?:\s*(?:,|;|\||->|=>|→|\band then\b|\bthen\b|\band\b|\bafter that\b|\bafterwards\b|\bnext\b|\bfinally\b|\blastly\b|\bthen\s*:|\bnext\s*:|\bafterward\s*:|\bafterwards\s*:|\bfinally\s*:|\bfirst\b|\bsecond\b|\bthird\b|\bfourth\b|\bstep\s*(?:\d+|[ivxlcdm]+)\b|\bphase\s*(?:\d+|[ivxlcdm]+)\b|\bpart\s*(?:\d+|[ivxlcdm]+)\b|(?<!\S)\d+[\)\.](?=\s))\s*|\n+\s*(?:[-*•]\s*)?(?:\[[ xX]\]\s*)?)",
    re.IGNORECASE,
)
_UNSET = object()


def _provider_response_to_text(raw) -> str:
    """Normalize provider complete output to plain text."""
    if raw is None:
        return ""
    if isinstance(raw, str):
        return raw

    if isinstance(raw, dict):
        # OpenAI-like providers may return a dict with content field.
        if "content" in raw and isinstance(raw["content"], str):
            return raw["content"]

        # Handle OpenAI response objects with choices list.
        choices = raw.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                msg = first.get("message")
                if isinstance(msg, dict):
                    content = msg.get("content")
                    if isinstance(content, str):
                        return content
                text = first.get("text")
                if isinstance(text, str):
                    return text
            # Fallback for hybrid objects
            content = getattr(first, "content", None)
            if isinstance(content, str):
                return content

        # Generic fallback conversion
        try:
            return json.dumps(raw)
        except Exception:
            return str(raw)

    if hasattr(raw, "get") and callable(raw.get):
        try:
            content = raw.get("content")
            if isinstance(content, str):
                return content
        except Exception:
            pass

    try:
        return str(raw)
    except Exception:
        return ""


def _coerce_and_clamp_position(position, fallback: Optional[dict] = None) -> Optional[dict]:
    """Clamp x/y coordinates to [0,100] and return floats (e.g. {"x":150.0,"y":-10.0} -> {"x":100.0,"y":0.0}); else return fallback."""
    if not isinstance(position, dict):
        return fallback
    if "x" not in position or "y" not in position:
        return fallback
    try:
        x = float(position["x"])
        y = float(position["y"])
    except (TypeError, ValueError):
        return fallback
    return {"x": max(0, min(100, x)), "y": max(0, min(100, y))}


# Configure logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Resolve repository root robustly (apps/aria/server.py -> repo root is parents[2]).
REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_detect_provider():
    """Load shared.chat_providers.detect_provider without mutating sys.path."""
    try:
        from shared.chat_providers import detect_provider as _detect_provider

        return _detect_provider
    except (ImportError, ModuleNotFoundError, AttributeError):
        shared_chat_providers = REPO_ROOT / "shared" / "chat_providers.py"
        if not shared_chat_providers.exists():
            return None
        spec = importlib.util.spec_from_file_location(
            "_aria_shared_chat_providers", shared_chat_providers)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, "detect_provider", None)


detect_provider = _load_detect_provider()
LLM_AVAILABLE = callable(detect_provider)
if LLM_AVAILABLE:
    logger.info("✓ LLM providers available for automatic action generation")
else:
    logger.warning(
        "✗ LLM providers not available - will use rule-based fallback only")

# Skip AI model loading for faster startup - use rule-based fallback
MODEL = None
print("⚠️ Skipping AI model loading - using rule-based fallback for faster startup")

# Pre-compiled keyword sets for O(1) lookup instead of O(n) any() calls
JUMP_KEYWORDS = frozenset(["jump", "leap", "hop"])
DANCE_KEYWORDS = frozenset(["dance", "spin", "twirl"])
WAVE_KEYWORDS = frozenset(["wave", "greet", "hello", "hi"])
LOOK_KEYWORDS = frozenset(["look", "see", "watch", "observe"])
SIT_KEYWORDS = frozenset(["sit", "rest", "relax"])
RUN_KEYWORDS = frozenset(["run", "race", "sprint"])
HIDE_KEYWORDS = frozenset(["hide", "crouch", "duck"])
PRESENT_KEYWORDS = frozenset(["present", "show", "display"])
THINK_KEYWORDS = frozenset(["think", "wonder", "ponder"])
MOVE_KEYWORDS = frozenset(["go", "move", "walk", "run"])
SAY_KEYWORDS = frozenset(["say", "speak", "tell", "greet"])
PICKUP_KEYWORDS = frozenset(["pick", "get", "grab", "take"])
ARM_WAVE_KEYWORDS = frozenset(["wave", "wiggle"])
ARM_RAISE_KEYWORDS = frozenset(["raise", "up", "lift"])
ARM_LOWER_KEYWORDS = frozenset(["lower", "down"])
ARM_FORWARD_KEYWORDS = frozenset(["forward", "front"])
ARM_BACK_KEYWORDS = frozenset(["back", "backward", "behind"])
LEFT_ARM_KEYWORDS = frozenset(["left arm", "arm left", "left hand"])
RIGHT_ARM_KEYWORDS = frozenset(["right arm", "arm right", "right hand"])
LEFT_LEG_KEYWORDS = frozenset(["left leg", "leg left"])
RIGHT_LEG_KEYWORDS = frozenset(["right leg", "leg right"])
SPARKLE_KEYWORDS = frozenset(
    ["sparkle", "sparkles", "glitter", "shimmer", "shine"])
GLOW_KEYWORDS = frozenset(["glow", "glowing", "radiate", "illuminate"])
HEARTS_KEYWORDS = frozenset(["hearts", "heart", "love"])
WALK_LEFT_KEYWORDS = frozenset(["walk left", "go left", "left"])
WALK_RIGHT_KEYWORDS = frozenset(["walk right", "go right", "right"])
COME_HERE_KEYWORDS = frozenset(["come here", "come to me", "over here"])
FOLLOW_ME_KEYWORDS = frozenset(["follow me", "come with me"])
BRING_ME_KEYWORDS = frozenset(["bring me", "fetch", "hand me"])
BRING_IT_KEYWORDS = frozenset(["bring it", "bring it here", "bring it to me"])
DROP_HERE_KEYWORDS = frozenset(
    ["drop it here", "put it here", "place it here", "set it down"])
VALID_GESTURES = frozenset(
    ["wave", "thumbs_up", "clap", "shrug", "bow", "nod"])
PICKUP_X_OFFSET = -10
PICKUP_Y_OFFSET = 5
PICKUP_DISTANCE_THRESHOLD = 30


def _contains_any_keyword(text: str, keywords: frozenset) -> bool:
    """Check if text contains any keyword from set."""
    for kw in keywords:
        if kw in text:
            return True
    return False


def _any_word_in_text(words: frozenset, text: str) -> bool:
    """Backward-compatible helper alias used by older tests."""
    return _contains_any_keyword(text, words)


def _keywords_in_cmd(words: frozenset, text: str) -> bool:
    """Backward-compatible helper alias used by older tests."""
    return _contains_any_keyword(text, words)


# Legacy constant aliases expected by older modules/tests.
_MOVE_KEYWORDS = MOVE_KEYWORDS
_SAY_KEYWORDS = SAY_KEYWORDS
_PICKUP_KEYWORDS = PICKUP_KEYWORDS
_JUMP_KEYWORDS = JUMP_KEYWORDS
_DANCE_KEYWORDS = DANCE_KEYWORDS
_LIMB_KEYWORDS = frozenset(
    set(LEFT_ARM_KEYWORDS) | set(RIGHT_ARM_KEYWORDS) | set(
        LEFT_LEG_KEYWORDS) | set(RIGHT_LEG_KEYWORDS)
)

# Global stage state that AI can see
stage_state = {
    "aria": {
        "position": {"x": 15, "y": 20},  # percentage coordinates
        "expression": "neutral",
        "held_object": None,
        "facing": "right",
    },
    "objects": {
        "apple": {"position": {"x": 55, "y": 35}, "state": "on_table"},
        "book": {"position": {"x": 48, "y": 35}, "state": "on_table"},
        "cup": {"position": {"x": 62, "y": 35}, "state": "on_table"},
        "ball": {"position": {"x": 70, "y": 35}, "state": "on_table"},
        "flower": {"position": {"x": 52, "y": 35}, "state": "on_table"},
    },
    "environment": {
        "table": {"position": {"x": 60, "y": 20}},
        "stage_bounds": {"width": 100, "height": 100},
    },
}

# Structured action schema for LLM-powered automatic execution
ARIA_ACTIONS = {
    "move": {
        "params": ["target", "speed"],
        "description": "Move Aria to a target position or object",
        "example": {"action": "move", "target": {"x": 50, "y": 30}, "speed": "normal"},
    },
    "say": {
        "params": ["text", "emotion"],
        "description": "Make Aria speak with optional emotion",
        "example": {"action": "say", "text": "Hello!", "emotion": "happy"},
    },
    "pickup": {
        "params": ["object_id"],
        "description": "Pick up an object from the stage",
        "example": {"action": "pickup", "object_id": "apple"},
    },
    "drop": {
        "params": ["position"],
        "description": "Drop currently held object at position",
        "example": {"action": "drop", "position": {"x": 50, "y": 30}},
    },
    "throw": {
        "params": ["target", "force"],
        "description": "Throw held object toward target",
        "example": {"action": "throw", "target": {"x": 70, "y": 40}, "force": "medium"},
    },
    "gesture": {
        "params": ["gesture_type"],
        "description": "Perform a gesture animation",
        "example": {"action": "gesture", "gesture_type": "wave"},
    },
    "look": {
        "params": ["target"],
        "description": "Look at a target position or object",
        "example": {"action": "look", "target": "apple"},
    },
    "wait": {
        "params": ["duration"],
        "description": "Wait for specified duration in seconds",
        "example": {"action": "wait", "duration": 2.0},
    },
}


def validate_action(action: dict) -> tuple[bool, str]:
    """Validate one action against safe allowlist and parameter bounds."""
    if not isinstance(action, dict):
        return False, "Action must be an object"

    if "action" not in action:
        return False, "Action must include an 'action' field"
    action_type = action.get("action")
    if action_type not in ARIA_ACTIONS:
        return False, f"Unknown action: {action_type}"

    if action_type in {"move", "throw", "drop"}:
        coordinate_fields = []
        if action_type == "move":
            coordinate_fields.append(action.get("target"))
        elif action_type == "throw":
            coordinate_fields.append(action.get("target"))
        elif action_type == "drop":
            coordinate_fields.append(action.get("position"))

        for coords in coordinate_fields:
            if coords is None:
                continue
            if not isinstance(coords, dict):
                return False, f"{action_type} coordinates must be an object"
            x = coords.get("x")
            y = coords.get("y")
            if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
                return False, f"{action_type} coordinates must contain numeric x/y"
            if not (0 <= x <= 100 and 0 <= y <= 100):
                return False, f"{action_type} coordinates must be between 0 and 100"

    if action_type == "wait":
        duration = action.get("duration", 1.0)
        if not isinstance(duration, (int, float)) or duration < 0 or duration > 30:
            return False, "wait duration must be between 0 and 30 seconds"

    if action_type == "say":
        text = str(action.get("text", ""))
        if len(text) > 200:
            return False, "say text exceeds 200 characters"

    if action_type == "gesture":
        if action.get("gesture_type") not in VALID_GESTURES:
            return False, "unsupported gesture_type"

    return True, ""


def validate_action_sequence(actions: list[dict]) -> tuple[bool, str]:
    """Validate an action sequence before plan/execution."""
    if not isinstance(actions, list) or not actions:
        return False, "actions must be a non-empty list"
    if len(actions) > 25:
        return False, "too many actions in a single request"
    for action in actions:
        ok, reason = validate_action(action)
        if not ok:
            return False, reason
    return True, ""


class AriaActionParser:
    """LLM-powered action parser for automatic command execution"""

    def __init__(self):
        self.provider = None
        self.provider_choice = None
        self._initialize_provider()

    @staticmethod
    def _normalize_provider_alias(explicit: Optional[str]) -> Optional[str]:
        """Normalize provider aliases to canonical detect_provider values."""
        if explicit is None:
            return None

        normalized = str(explicit).strip().lower()
        alias_map = {
            "quantum-llm": "quantum",
            "quantum_llm": "quantum",
            "azure_openai": "azure",
        }
        return alias_map.get(normalized, normalized)

    def _resolve_provider_for_request(
        self,
        *,
        explicit: Optional[str] = None,
        model_override: Optional[str] = None,
    ) -> tuple[object | None, object | None]:
        """Resolve provider for a specific request while preserving cached default."""
        if not LLM_AVAILABLE:
            return None, None

        normalized_explicit = self._normalize_provider_alias(explicit)

        # Fast path: use cached auto provider if no request-level override is set.
        if normalized_explicit in (None, "", "auto") and not model_override:
            return self.provider, self.provider_choice

        detected = detect_provider(
            explicit=normalized_explicit or "auto",
            model_override=model_override,
        )
        if isinstance(detected, tuple) and len(detected) == 2:
            return detected[0], detected[1]
        return detected, None

    def _initialize_provider(self):
        """Initialize LLM provider if available, robust to tuple return values."""
        if not LLM_AVAILABLE:
            logger.info("LLM not available - will use rule-based fallback")
            return

        try:
            configured_explicit = os.getenv("ARIA_LLM_PROVIDER")
            configured_model = os.getenv("ARIA_LLM_MODEL")

            # Convenience: if ARIA_QUANTUM_MODEL_PATH is set and no provider is
            # configured, default Aria LLM parsing to the quantum provider.
            quantum_model_path = os.getenv(
                "ARIA_QUANTUM_MODEL_PATH") or os.getenv("QAI_QUANTUM_MODEL_PATH")
            if not configured_model and quantum_model_path:
                configured_model = quantum_model_path
            if not configured_explicit and configured_model == quantum_model_path and quantum_model_path:
                configured_explicit = "quantum"

            self.provider, self.provider_choice = self._resolve_provider_for_request(
                explicit=configured_explicit,
                model_override=configured_model,
            )
            provider_name = getattr(
                self.provider_choice,
                "name",
                getattr(self.provider, "__class__", type(
                    self.provider)).__class__.__name__,
            )
            logger.info(f"✓ Initialized LLM provider: {provider_name}")
        except Exception as e:
            logger.warning(f"Failed to initialize LLM provider: {e}")
            self.provider = None
            self.provider_choice = None

    def _build_system_prompt(self) -> str:
        """Build system prompt with action schema and current state"""
        actions_json = json.dumps(ARIA_ACTIONS, indent=2)
        state_json = json.dumps(stage_state, indent=2)

        return f"""You are an action planner for Aria, a 3D character assistant.

Available Actions:
{actions_json}

Current Stage State:
{state_json}

Your task: Parse user commands into a sequence of structured actions.
- Return ONLY valid JSON array of actions
- Use exact action names from schema
- Provide all required params for each action
- Consider current state when planning
- Keep actions simple and atomic

Example output:
[
  {{"action": "move", "target": {{"x": 50, "y": 30}}, "speed": "normal"}},
  {{"action": "say", "text": "Hello!", "emotion": "happy"}}
]

Rules:
1. Always move Aria before picking up objects
2. Aria can only hold one object at a time
3. Objects on table are at y=35, x varies
4. Stage bounds: 0-100 for both x and y
5. If command is unclear, choose most reasonable interpretation"""

    def parse_with_llm(self, command: str, provider=None) -> list[dict]:
        """Parse command using LLM provider"""
        active_provider = provider if provider is not None else self.provider

        if not active_provider:
            raise ValueError("LLM provider not available")

        system_prompt = self._build_system_prompt()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": command},
        ]

        try:
            response = active_provider.complete(messages, stream=False)

            # Extract JSON from response
            content = _provider_response_to_text(response).strip()

            # Try to parse as JSON
            if content.startswith("["):
                actions = json.loads(content)
            else:
                # Extract JSON array from markdown or text
                json_match = _RE_JSON_BLOCK.search(content)
                if json_match:
                    actions = json.loads(json_match.group(0))
                else:
                    raise ValueError("No JSON array found in response")

            # Validate actions
            validated = []
            for action in actions:
                if "action" in action and action["action"] in ARIA_ACTIONS:
                    validated.append(action)
                else:
                    logger.warning(f"Skipping invalid action: {action}")

            return validated

        except Exception as e:
            logger.error(f"LLM parsing failed: {e}")
            raise

    def parse_with_fallback(
        self,
        command: str,
        _allow_split: bool = True,
        _planned_held_object=_UNSET,
        _referenced_object=_UNSET,
    ) -> list[dict]:
        """Rule-based fallback parser (uses existing generate_tags_fallback logic)"""
        actions = []
        command_lower = command.lower()
        known_objects = ["apple", "book", "cup", "ball", "flower"]
        planned_held_object = (
            stage_state["aria"].get(
                "held_object") if _planned_held_object is _UNSET else _planned_held_object
        )
        referenced_object = None if _referenced_object is _UNSET else _referenced_object

        # Compound command handling (e.g., "pick up cup and bring it here then put it on table")
        if _allow_split:
            segments = [seg.strip() for seg in _RE_COMMAND_SEPARATORS.split(
                command) if seg and seg.strip()]
            if len(segments) > 1:
                combined_actions = []
                current_planned_held = planned_held_object
                current_referenced_object = referenced_object
                for seg in segments:
                    seg_lower = seg.lower()
                    for obj in known_objects:
                        if obj in seg_lower:
                            current_referenced_object = obj
                            break
                    seg_actions = self.parse_with_fallback(
                        seg,
                        _allow_split=False,
                        _planned_held_object=current_planned_held,
                        _referenced_object=current_referenced_object,
                    )
                    combined_actions.extend(seg_actions)

                    for action in seg_actions:
                        action_type = action.get("action")
                        if action_type == "pickup":
                            picked_obj = action.get(
                                "object_id", current_planned_held)
                            current_planned_held = picked_obj
                            current_referenced_object = picked_obj
                        elif action_type in ("drop", "throw"):
                            current_planned_held = None

                # Remove redundant consecutive actions from repeated segments
                deduped_actions = []
                for action in combined_actions:
                    if deduped_actions and action == deduped_actions[-1]:
                        continue
                    if (
                        deduped_actions
                        and action.get("action") == "move"
                        and deduped_actions[-1].get("action") == "move"
                        and action.get("target") == deduped_actions[-1].get("target")
                    ):
                        continue
                    if (
                        len(deduped_actions) >= 2
                        and action.get("action") == "move"
                        and deduped_actions[-2].get("action") == "move"
                        and deduped_actions[-2].get("target") == action.get("target")
                        and deduped_actions[-1].get("action") == "gesture"
                        and deduped_actions[-1].get("gesture_type") == "nod"
                    ):
                        continue
                    deduped_actions.append(action)

                return deduped_actions

        # Conversational movement commands
        if _contains_any_keyword(command_lower, COME_HERE_KEYWORDS):
            actions.append({"action": "move", "target": {
                           "x": 50, "y": 85}, "speed": "normal"})

        if _contains_any_keyword(command_lower, FOLLOW_ME_KEYWORDS):
            actions.append({"action": "gesture", "gesture_type": "nod"})
            actions.append({"action": "move", "target": {
                           "x": 50, "y": 75}, "speed": "normal"})

        # Conversational object delivery commands
        if _contains_any_keyword(command_lower, BRING_ME_KEYWORDS):
            for obj in known_objects:
                if obj in command_lower and obj in stage_state["objects"]:
                    obj_pos = stage_state["objects"][obj]["position"]
                    actions.append(
                        {"action": "move", "target": obj_pos, "speed": "normal"})
                    actions.append({"action": "pickup", "object_id": obj})
                    actions.append(
                        {
                            "action": "move",
                            "target": {"x": 50, "y": 85},
                            "speed": "normal",
                        }
                    )
                    actions.append(
                        {"action": "gesture", "gesture_type": "nod"})
                    break

        # Pronoun follow-up delivery command (e.g., "bring it here")
        if _contains_any_keyword(command_lower, BRING_IT_KEYWORDS):
            held_obj = planned_held_object
            if not held_obj and _contains_any_keyword(command_lower, PICKUP_KEYWORDS):
                held_obj = referenced_object
                if not held_obj:
                    for obj in known_objects:
                        if obj in command_lower:
                            held_obj = obj
                            break
            if held_obj:
                actions.append({"action": "move", "target": {
                               "x": 50, "y": 85}, "speed": "normal"})
                actions.append({"action": "gesture", "gesture_type": "nod"})
            else:
                actions.append(
                    {
                        "action": "say",
                        "text": "I need to pick something up first.",
                        "emotion": "neutral",
                    }
                )

        # Conversational drop/place commands for currently held object
        has_drop_intent = (
            _contains_any_keyword(command_lower, DROP_HERE_KEYWORDS)
            or ("drop" in command_lower and "here" in command_lower)
            or (
                "put" in command_lower
                and ("here" in command_lower or "down" in command_lower or "table" in command_lower)
            )
            or ("place" in command_lower and ("here" in command_lower or "table" in command_lower))
        )
        if has_drop_intent:
            held_obj = planned_held_object
            if not held_obj:
                actions.append(
                    {
                        "action": "say",
                        "text": "I'm not holding anything yet.",
                        "emotion": "neutral",
                    }
                )
            else:
                drop_target = {"x": 50, "y": 85}
                if "table" in command_lower:
                    table_pos = stage_state["environment"]["table"]["position"]
                    drop_target = {"x": table_pos["x"], "y": 35}
                actions.append(
                    {"action": "move", "target": drop_target, "speed": "normal"})
                actions.append({"action": "drop", "position": drop_target})

        # Parse move commands
        if _contains_any_keyword(command_lower, MOVE_KEYWORDS):
            # Extract target from command
            if "table" in command_lower:
                actions.append({"action": "move", "target": {
                               "x": 60, "y": 35}, "speed": "normal"})
            elif "center" in command_lower or "middle" in command_lower:
                actions.append({"action": "move", "target": {
                               "x": 50, "y": 50}, "speed": "normal"})
            elif "left" in command_lower:
                actions.append({"action": "move", "target": {
                               "x": 20, "y": 50}, "speed": "normal"})
            elif "right" in command_lower:
                actions.append({"action": "move", "target": {
                               "x": 80, "y": 50}, "speed": "normal"})
            else:
                for obj in known_objects:
                    if obj in command_lower and obj in stage_state["objects"]:
                        actions.append(
                            {
                                "action": "move",
                                "target": stage_state["objects"][obj]["position"],
                                "speed": "normal",
                            }
                        )
                        break

        # Parse say commands
        if _contains_any_keyword(command_lower, SAY_KEYWORDS):
            # Extract text after say/speak
            for trigger in ["say ", "speak ", "tell ", "greet "]:
                if trigger in command_lower:
                    text = command[command_lower.index(
                        trigger) + len(trigger):].strip(" \"'")
                    emotion = "happy" if any(w in text.lower() for w in [
                                             "!", "hello", "hi"]) else "neutral"
                    actions.append(
                        {"action": "say", "text": text, "emotion": emotion})
                    break

        # Parse pickup commands
        pickup_added = False
        for obj in known_objects:
            if obj in command_lower and _contains_any_keyword(command_lower, PICKUP_KEYWORDS):
                # Move to object first
                obj_pos = stage_state["objects"][obj]["position"]
                actions.append(
                    {"action": "move", "target": obj_pos, "speed": "normal"})
                actions.append({"action": "pickup", "object_id": obj})
                pickup_added = True
                break
        if (
            not pickup_added
            and _contains_any_keyword(command_lower, PICKUP_KEYWORDS)
            and "it" in command_lower
            and referenced_object is not None
            and referenced_object in stage_state["objects"]
        ):
            obj_pos = stage_state["objects"][referenced_object]["position"]
            actions.append(
                {"action": "move", "target": obj_pos, "speed": "normal"})
            actions.append(
                {"action": "pickup", "object_id": referenced_object})

        # Parse throw commands
        if "throw" in command_lower:
            target = {"x": 70, "y": 40}
            if "left" in command_lower:
                target = {"x": 20, "y": 40}
            elif "right" in command_lower:
                target = {"x": 80, "y": 40}
            elif "here" in command_lower:
                target = {"x": 50, "y": 85}

            if "it" in command_lower:
                actions.append(
                    {"action": "throw", "target": target, "force": "medium"})
            else:
                for obj in known_objects:
                    if obj in command_lower and obj in stage_state["objects"]:
                        obj_pos = stage_state["objects"][obj]["position"]
                        actions.append(
                            {"action": "move", "target": obj_pos, "speed": "normal"})
                        actions.append({"action": "pickup", "object_id": obj})
                        actions.append(
                            {"action": "throw", "target": target, "force": "medium"})
                        break

        # Parse look commands
        if _contains_any_keyword(command_lower, LOOK_KEYWORDS):
            for obj in known_objects:
                if obj in command_lower and obj in stage_state["objects"]:
                    actions.append({"action": "look", "target": obj})
                    break
            else:
                if "left" in command_lower:
                    actions.append(
                        {"action": "look", "target": {"x": 0, "y": 50}})
                elif "right" in command_lower:
                    actions.append(
                        {"action": "look", "target": {"x": 100, "y": 50}})
                else:
                    table_pos = stage_state["environment"]["table"]["position"]
                    actions.append({"action": "look", "target": table_pos})

        # Parse wait commands
        wait_match = _RE_WAIT_DURATION.search(command_lower)
        if wait_match:
            actions.append(
                {"action": "wait", "duration": float(wait_match.group(1))})
        elif "wait" in command_lower or "pause" in command_lower or "hold on" in command_lower:
            actions.append({"action": "wait", "duration": 1.0})

        # Parse gesture commands. Each entry maps a natural-language trigger
        # phrase to a canonical gesture in VALID_GESTURES so AI-issued commands
        # like "thanks", "applaud", or "yo" still resolve to a valid action.
        gesture_triggers = [
            ("wave", "wave"),
            ("hello", "wave"),
            ("hi ", "wave"),
            ("greet", "wave"),
            ("yo ", "wave"),
            ("hey", "wave"),
            ("thumbs up", "thumbs_up"),
            ("thumbs-up", "thumbs_up"),
            ("good job", "thumbs_up"),
            ("nice work", "thumbs_up"),
            ("approve", "thumbs_up"),
            ("clap", "clap"),
            ("applaud", "clap"),
            ("celebrate", "clap"),
            ("shrug", "shrug"),
            ("dunno", "shrug"),
            ("don't know", "shrug"),
            ("bow", "bow"),
            ("bow down", "bow"),
            ("nod", "nod"),
            ("yes", "nod"),
            ("agree", "nod"),
            ("thanks", "nod"),
            ("thank you", "nod"),
        ]
        for trigger, gesture in gesture_triggers:
            if trigger in command_lower:
                actions.append({"action": "gesture", "gesture_type": gesture})
                break

        return actions

    def parse(
        self,
        command: str,
        use_llm: bool = True,
        provider_choice: Optional[str] = None,
        model_override: Optional[str] = None,
    ) -> list[dict]:
        """
        Parse command into structured actions

        Args:
            command: Natural language command
            use_llm: Try LLM first if available
            provider_choice: Optional provider override (e.g. quantum, azure)
            model_override: Optional model/path override for selected provider

        Returns:
            List of action dicts
        """
        if use_llm:
            try:
                request_provider, request_choice = self._resolve_provider_for_request(
                    explicit=provider_choice,
                    model_override=model_override,
                )
                if request_provider is None:
                    raise ValueError("LLM provider not available")

                actions = self.parse_with_llm(
                    command, provider=request_provider)
                used_provider_name = (
                    getattr(request_choice, "name", None)
                    or getattr(self.provider_choice, "name", None)
                    or self._normalize_provider_alias(provider_choice)
                    or "auto"
                )
                safe_provider_name = _sanitize_for_log(str(used_provider_name))
                safe_command = _sanitize_for_log(command)
                logger.info(
                    f"✓ LLM parsed via {safe_provider_name}: {safe_command} -> {len(actions)} actions")
                return actions
            except Exception as e:
                logger.warning(f"LLM parsing failed, using fallback: {e}")

        actions = self.parse_with_fallback(command)
        safe_command = _sanitize_for_log(command)
        logger.info(
            f"✓ Fallback parsed: {safe_command} -> {len(actions)} actions")
        return actions


# --------------------------- World Generation ---------------------------


def _sanitize_id(raw: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]+", "_", raw.strip().lower())
    return cleaned[:30] or f"obj_{random.randint(1000, 9999)}"


THEME_OBJECT_LIBRARY = {
    "forest": [
        ("tree", "🌲"),
        ("mushroom", "🍄"),
        ("rock", "🪨"),
        ("flower", "🌼"),
        ("owl", "🦉"),
        ("fox", "🦊"),
    ],
    "space": [
        ("planet", "🪐"),
        ("star", "⭐"),
        ("rocket", "🚀"),
        ("alien", "👽"),
        ("astronaut", "👩‍🚀"),
        ("satellite", "🛰️"),
    ],
    "ocean": [
        ("fish", "🐟"),
        ("shell", "🐚"),
        ("coral", "🪸"),
        ("whale", "🐋"),
        ("ship", "🚢"),
        ("dolphin", "🐬"),
    ],
    "lab": [
        ("beaker", "🧪"),
        ("microscope", "🔬"),
        ("dna", "🧬"),
        ("robot", "🤖"),
        ("atom", "⚛️"),
        ("chip", "💾"),
    ],
    "medieval": [
        ("sword", "🗡️"),
        ("shield", "🛡️"),
        ("crown", "👑"),
        ("scroll", "📜"),
        ("goblet", "🍷"),
        ("castle", "🏰"),
    ],
    "desert": [
        ("cactus", "🌵"),
        ("skull", "💀"),
        ("camel", "🐪"),
        ("scorpion", "🦂"),
        ("sun", "☀️"),
        ("sand", "🟨"),
    ],
    "garden": [
        ("rose", "🌹"),
        ("tulip", "🌷"),
        ("butterfly", "🦋"),
        ("bee", "🐝"),
        ("bench", "🪑"),
        ("pond", "💧"),
    ],
    "cyberpunk": [
        ("drone", "🛸"),
        ("neon", "💡"),
        ("chip", "💾"),
        ("server", "🖥️"),
        ("bot", "🤖"),
        ("battery", "🔋"),
    ],
    "arcade": [
        ("joystick", "🕹️"),
        ("coin", "🪙"),
        ("ghost", "👻"),
        ("trophy", "🏆"),
        ("console", "🎮"),
        ("heart", "❤️"),
    ],
}


def generate_world_fallback(theme: str, count: int) -> dict:
    """Generate a world procedurally without LLM."""
    objects_catalog = THEME_OBJECT_LIBRARY.get(
        theme.lower(), THEME_OBJECT_LIBRARY["forest"])
    random.shuffle(objects_catalog)
    chosen = objects_catalog[: max(1, count)]
    stage_objects = {}
    used_positions = []
    for name, emoji in chosen:
        # Avoid overlapping positions (simple Poisson-ish attempt)
        for _attempt in range(10):
            x = random.randint(10, 90)
            y = random.randint(20, 80)
            if all(math.hypot(x - px, y - py) > 8 for px, py in used_positions):
                used_positions.append((x, y))
                break
        stage_objects[_sanitize_id(name)] = {
            "id": _sanitize_id(name),
            "emoji": emoji,
            "position": {"x": x, "y": y},
            "state": "on_stage",
        }
    environment = {
        "theme": theme,
        "generated_at": datetime.datetime.now(timezone.utc).isoformat() + "Z",
        "seed": random.randint(100000, 999999),
        "stage_bounds": {"width": 100, "height": 100},
    }
    return {"objects": stage_objects, "environment": environment}


def generate_world_with_llm(theme: str, count: int, provider) -> dict:
    """Use LLM provider to generate a themed world. Returns fallback on failure."""
    system_prompt = (
        "You are a world generator for a 2D stage (coordinates 0-100 for x and y). "
        "Given a theme, produce JSON with 'objects' and 'environment'. Each object must have: id, emoji, position {x,y}, state. "
        "Constrain positions within bounds. Provide at most the requested count. ONLY output JSON, no commentary."
    )
    user_prompt = f"Theme: {theme}\nCount: {count}\nRequirements: diverse, non-overlapping, concise ids."
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        raw = provider.complete(messages, stream=False)
        raw_str = _provider_response_to_text(raw).strip()
        # Strip code fences
        if "```" in raw_str:
            m = re.search(r"```(?:json)?\n(.*?)(```)",
                          raw_str, flags=re.DOTALL)
            if m:
                raw_str = m.group(1).strip()

        # Parse JSON from the LLM response
        try:
            parsed_world_data = json.loads(raw_str)
        except json.JSONDecodeError:
            obj_match = re.search(r"\{.*\}\s*$", raw_str, flags=re.DOTALL)
            if obj_match:
                raw_str = obj_match.group(0)
            parsed_world_data = json.loads(raw_str)
        # Basic validation
        objects = parsed_world_data.get("objects") or {}
        env = parsed_world_data.get("environment") or {}

        # Normalize object list/dict to id->object mapping
        sanitized_objects = {}
        if isinstance(objects, dict):
            object_items = list(objects.items())
        elif isinstance(objects, list):
            object_items = [(str(i), obj) for i, obj in enumerate(objects)]
        else:
            object_items = []

        for key, val in object_items[:count]:
            if not isinstance(val, dict):
                continue
            object_id = val.get("id") or val.get("name") or key
            oid = _sanitize_id(object_id)
            pos = val.get("position", {})
            x = int(max(0, min(100, pos.get("x", random.randint(10, 90)))))
            y = int(max(0, min(100, pos.get("y", random.randint(20, 80)))))
            state = val.get("state", "on_stage")
            emoji = val.get("emoji", "✨")
            sanitized_objects[oid] = {
                "id": oid,
                "emoji": emoji,
                "position": {"x": x, "y": y},
                "state": state,
            }
        if not sanitized_objects:
            return generate_world_fallback(theme, count)
        env.setdefault("theme", theme)
        env.setdefault("generated_at", datetime.datetime.now(
            timezone.utc).isoformat() + "Z")
        env.setdefault("stage_bounds", {"width": 100, "height": 100})
        return {
            "objects": sanitized_objects,
            "environment": env,
            "llm": True,
            "raw_response_len": len(raw_str),
        }
    except Exception as e:
        logger.warning(f"World generation via LLM failed: {e}; falling back.")
        return generate_world_fallback(theme, count) | {"llm": False}


# Initialize global action parser
action_parser = AriaActionParser()


def get_stage_context() -> str:
    """Generate natural language description of current stage state for AI"""
    aria = stage_state["aria"]
    objects = stage_state["objects"]

    # Calculate distances to objects
    aria_pos = aria["position"]
    nearby_objects = []
    for obj_name, obj_data in objects.items():
        # Safety check: ensure object has position data
        if not isinstance(obj_data, dict) or "position" not in obj_data:
            continue
        obj_pos = obj_data["position"]
        if not isinstance(obj_pos, dict) or "x" not in obj_pos or "y" not in obj_pos:
            continue
        distance = ((aria_pos["x"] - obj_pos["x"]) ** 2 +
                    (aria_pos["y"] - obj_pos["y"]) ** 2) ** 0.5
        if distance < 30:  # Within reach
            nearby_objects.append(obj_name)

    context = f"""STAGE VIEW:
- Aria is at position ({aria_pos['x']}%, {aria_pos['y']}%), facing {aria['facing']}
- Expression: {aria['expression']}
- Held object: {aria['held_object'] or 'none'}
- Table is at (60%, 20%) on the right side
- Objects on table: {', '.join([k for k, v in objects.items() if isinstance(v, dict) and v.get('state') == 'on_table'])}
- Objects nearby Aria (within reach): {', '.join(nearby_objects) if nearby_objects else 'none'}
- Stage dimensions: 100% wide x 100% tall (0,0=top-left, 100,100=bottom-right)
"""
    return context


def determine_position_from_context(cmd: str) -> str:
    """AI-driven position determination based on command semantics and stage state"""
    objects = stage_state["objects"]
    table_pos = stage_state["environment"]["table"]["position"]

    # Conversational movement intents
    if _contains_any_keyword(cmd, COME_HERE_KEYWORDS):
        # Front-center, closer to the viewer/user
        return "[aria:position:50:85]"
    if _contains_any_keyword(cmd, FOLLOW_ME_KEYWORDS):
        # Slightly behind the front-center so movement is visible
        return "[aria:position:50:75]"
    if _contains_any_keyword(cmd, BRING_ME_KEYWORDS):
        # For delivery-style commands, move to front-center
        return "[aria:position:50:85]"
    if _contains_any_keyword(cmd, BRING_IT_KEYWORDS):
        # Pronoun follow-up delivery defaults to front-center
        return "[aria:position:50:85]"
    if _contains_any_keyword(cmd, DROP_HERE_KEYWORDS):
        # Default drop target is in front of the user
        return "[aria:position:50:85]"

    # Object interaction positioning - move near the object
    for obj_name in ["apple", "book", "cup", "ball", "flower", "bear"]:
        if obj_name in cmd and ("pick" in cmd or "get" in cmd or "grab" in cmd or "take" in cmd):
            if obj_name in objects:
                obj_data = objects[obj_name]
                # Safety check: ensure object has position data
                if isinstance(obj_data, dict) and "position" in obj_data:
                    obj_pos = obj_data["position"]
                    if isinstance(obj_pos, dict) and "x" in obj_pos and "y" in obj_pos:
                        # Position slightly to the left of object
                        return f'[aria:position:{max(10, obj_pos["x"] - 10)}:{obj_pos["y"] + 10}]'

    # Action-based positioning (using pre-compiled keyword sets for O(1) lookup)
    if _contains_any_keyword(cmd, JUMP_KEYWORDS):
        return "[aria:position:50:60]"  # Center for jumping
    elif _contains_any_keyword(cmd, DANCE_KEYWORDS):
        return "[aria:position:50:50]"  # Center stage for performance
    elif _contains_any_keyword(cmd, WAVE_KEYWORDS):
        return "[aria:position:30:70]"  # Front-left for greeting
    elif _contains_any_keyword(cmd, LOOK_KEYWORDS):
        # Look towards table
        if "table" in cmd:
            return "[aria:position:40:60]"  # Position to see table
        return "[aria:position:20:40]"  # Left side for observing
    elif _contains_any_keyword(cmd, SIT_KEYWORDS):
        # Near table to sit
        return f'[aria:position:{table_pos["x"] - 5}:{table_pos["y"] + 35}]'
    elif _contains_any_keyword(cmd, RUN_KEYWORDS):
        return "[aria:position:85:70]"  # Far right for running space
    elif _contains_any_keyword(cmd, HIDE_KEYWORDS):
        return "[aria:position:10:75]"  # Corner position
    elif _contains_any_keyword(cmd, PRESENT_KEYWORDS):
        return "[aria:position:50:50]"  # Center to present
    elif _contains_any_keyword(cmd, THINK_KEYWORDS):
        return "[aria:position:25:50]"  # Contemplative left position
    elif _contains_any_keyword(cmd, WALK_LEFT_KEYWORDS):
        return "[aria:position:20:70]"  # Moving to left
    elif _contains_any_keyword(cmd, WALK_RIGHT_KEYWORDS):
        return "[aria:position:80:70]"  # Moving to right
    elif "add" in cmd or "create" in cmd or "spawn" in cmd:
        # For adding objects, position near table
        return f'[aria:position:{table_pos["x"] - 15}:{table_pos["y"] + 20}]'
    else:
        # Context-aware positioning: stay put if already in good position
        # or move to interesting area if idle
        pos_hash = int(hashlib.md5(cmd.encode()).hexdigest()[:4], 16)
        x = 30 + (pos_hash % 40)  # Random between 30-70%
        y = 60 + (pos_hash % 20)  # Random between 60-80%
        return f"[aria:position:{x}:{y}]"


def generate_tags_ai(command: str) -> list[str]:
    """Generate tags using AI model"""
    if MODEL is None:
        return []

    try:
        import torch
        from transformers import AutoTokenizer

        base_model = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        tokenizer = AutoTokenizer.from_pretrained(base_model)

        input_text = f"<|user|>\n{command}</s>\n<|assistant|>\n"
        inputs = tokenizer(input_text, return_tensors="pt").to(MODEL.device)

        with torch.no_grad():
            outputs = MODEL.generate(
                **inputs,
                max_new_tokens=30,
                temperature=0.1,
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.5,
                pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
            )

        response = tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        tags = _RE_ARIA_TAGS.findall(response)
        return tags[:2]  # Return first 2 tags max
    except Exception as e:
        print(f"AI generation error: {e}")
        return []


def generate_tags_fallback(command: str) -> list[str]:
    """Simple rule-based fallback tag generation with automatic positioning"""
    cmd = command.lower()
    tags = []

    # AI-driven automatic positioning based on command context
    # Determine optimal position for the action
    auto_position = determine_position_from_context(cmd)
    if auto_position:
        tags.append(auto_position)

    # Track if limb commands are detected to avoid movement conflicts
    # Using pre-compiled keyword sets for O(1) lookup
    has_limb_command = (
        _contains_any_keyword(cmd, LEFT_ARM_KEYWORDS)
        or _contains_any_keyword(cmd, RIGHT_ARM_KEYWORDS)
        or _contains_any_keyword(cmd, LEFT_LEG_KEYWORDS)
        or _contains_any_keyword(cmd, RIGHT_LEG_KEYWORDS)
    )

    # Special: server-side "say" / announce detection (capture original text)
    try:
        say_match = _RE_SAY_COMMAND.search(command)
        if say_match:
            raw_msg = say_match.group(1).strip()
            # basic sanitization and length cap
            safe_msg = _RE_SANITIZE_BRACKETS.sub("", raw_msg)[:200]
            tags.append(f"[aria:say:{safe_msg}]")
    except Exception:
        # ignore parsing errors
        pass

    # Expressions
    if "smile" in cmd or "happy" in cmd:
        tags.append("[aria:expression:smile]")
    elif "sad" in cmd:
        tags.append("[aria:expression:sad]")
    elif "surprised" in cmd:
        tags.append("[aria:expression:surprised]")
    elif "confused" in cmd:
        tags.append("[aria:expression:confused]")
    elif "thinking" in cmd or "think" in cmd:
        tags.append("[aria:expression:thinking]")
    elif "wink" in cmd:
        tags.append("[aria:expression:wink]")

    # Animations
    if "jump" in cmd:
        tags.append("[aria:animate:jump]")
    elif "dance" in cmd:
        tags.append("[aria:animate:dance]")
    elif "spin" in cmd:
        tags.append("[aria:animate:spin]")
    elif "bow" in cmd:
        tags.append("[aria:animate:bow]")
    elif "flip" in cmd:
        tags.append("[aria:animate:flip]")

    # Gestures (allowlist: wave, thumbs_up, clap, shrug, bow, nod)
    if "wave" in cmd:
        tags.append("[aria:gesture:wave]")
    elif "thumbs up" in cmd:
        tags.append("[aria:gesture:thumbs_up]")
    elif "clap" in cmd:
        tags.append("[aria:gesture:clap]")
    elif "shrug" in cmd:
        tags.append("[aria:gesture:shrug]")
    elif "nod" in cmd:
        tags.append("[aria:gesture:nod]")

    # Limb controls and poses (AI may also emit these; fallback supports natural phrases)
    # Hands up / T-pose / Cross arms
    if "hands up" in cmd or "raise hands" in cmd:
        tags.append("[aria:limb:left_arm:raise]")
        tags.append("[aria:limb:right_arm:raise]")
    if "t-pose" in cmd or "tpose" in cmd or "t pose" in cmd:
        tags.append("[aria:pose:t-pose]")
    if "cross arms" in cmd or "arms crossed" in cmd:
        tags.append("[aria:pose:cross_arms]")

    # Per-limb commands
    def limb_tag(part: str, action: str):
        tags.append(f"[aria:limb:{part}:{action}]")

    # Helper maps (using pre-compiled keyword sets)
    left_arm = _contains_any_keyword(cmd, LEFT_ARM_KEYWORDS)
    right_arm = _contains_any_keyword(cmd, RIGHT_ARM_KEYWORDS)
    left_leg = _contains_any_keyword(cmd, LEFT_LEG_KEYWORDS)
    right_leg = _contains_any_keyword(cmd, RIGHT_LEG_KEYWORDS)

    # Numeric angle if present (e.g., "left arm 45 degrees")
    angle_match = re.search(r"(-?\d{1,3})\s*(?:deg|degree|degrees)?", cmd)
    angle_val = angle_match.group(1) if angle_match else None

    # Arm actions
    if left_arm or right_arm or "arm" in cmd:
        # Choose default arm if unspecified
        parts = []
        if left_arm:
            parts.append("left_arm")
        if right_arm:
            parts.append("right_arm")
        if not parts:
            parts = ["right_arm"]
        if _contains_any_keyword(cmd, ARM_WAVE_KEYWORDS):
            for p in parts:
                limb_tag(p, "wave")
        elif _contains_any_keyword(cmd, ARM_RAISE_KEYWORDS):
            for p in parts:
                limb_tag(p, "raise")
        elif _contains_any_keyword(cmd, ARM_LOWER_KEYWORDS):
            for p in parts:
                limb_tag(p, "lower")
        elif _contains_any_keyword(cmd, ARM_FORWARD_KEYWORDS):
            for p in parts:
                limb_tag(p, "forward")
        elif _contains_any_keyword(cmd, ARM_BACK_KEYWORDS):
            for p in parts:
                limb_tag(p, "back")
        elif angle_val is not None:
            for p in parts:
                limb_tag(p, angle_val)

    # Leg actions
    if left_leg or right_leg or "leg" in cmd:
        parts = []
        if left_leg:
            parts.append("left_leg")
        if right_leg:
            parts.append("right_leg")
        if not parts:
            parts = ["left_leg"]
        if "kick" in cmd:
            for p in parts:
                limb_tag(p, "kick")
        elif _contains_any_keyword(cmd, ARM_FORWARD_KEYWORDS):
            for p in parts:
                limb_tag(p, "forward")
        elif _contains_any_keyword(cmd, ARM_BACK_KEYWORDS):
            for p in parts:
                limb_tag(p, "back")
        elif angle_val is not None:
            for p in parts:
                limb_tag(p, angle_val)

    # Movement - only add if not a limb command (to avoid conflicts like "left arm" -> "move:left")
    if not has_limb_command:
        # Determine movement style
        movement_style = None
        if "skip" in cmd:
            movement_style = "skip"
        elif "strut" in cmd or "swagger" in cmd:
            movement_style = "strut"
        elif "run" in cmd:
            movement_style = "run"
        elif "walk" in cmd:
            movement_style = "walk"
        else:
            movement_style = "move"

        # Determine direction - exclude if keywords could be part of limb commands
        has_forward_limb = "leg" in cmd or "arm" in cmd
        if "left" in cmd:
            tags.append(f"[aria:{movement_style}:left]")
        elif "right" in cmd:
            tags.append(f"[aria:{movement_style}:right]")
        elif ("up" in cmd or "forward" in cmd) and not has_forward_limb:
            tags.append(f"[aria:{movement_style}:up]")
        elif ("down" in cmd or "back" in cmd) and not has_forward_limb:
            tags.append(f"[aria:{movement_style}:down]")

    # Effects - with keyword matching and intensity support
    effect_intensity = "normal"
    if "light" in cmd or "subtle" in cmd or "gentle" in cmd:
        effect_intensity = "light"
    elif "heavy" in cmd or "intense" in cmd or "lots" in cmd or "many" in cmd:
        effect_intensity = "heavy"

    if _contains_any_keyword(cmd, SPARKLE_KEYWORDS):
        tags.append(f"[aria:effect:sparkle:{effect_intensity}]")
    elif _contains_any_keyword(cmd, GLOW_KEYWORDS):
        tags.append(f"[aria:effect:glow:{effect_intensity}]")
    elif _contains_any_keyword(cmd, HEARTS_KEYWORDS):
        tags.append(f"[aria:effect:hearts:{effect_intensity}]")

    # Camera
    if "center" in cmd:
        tags.append("[aria:camera:center]")
    elif "zoom" in cmd:
        tags.append(
            "[aria:camera:zoom_in]" if "in" in cmd else "[aria:camera:zoom_out]")

    # Poses (body positions)
    if "sit" in cmd:
        tags.append("[aria:pose:sit]")
    elif "stand" in cmd:
        tags.append("[aria:pose:stand]")
    elif "crouch" in cmd:
        tags.append("[aria:pose:crouch]")
    elif "lie" in cmd or "lay" in cmd:
        tags.append("[aria:pose:lie]")

    # Position control - let AI determine where Aria should be
    # Format: [aria:position:x:y] where x and y are percentages (0-100)
    # Or named positions: [aria:position:center], [aria:position:left], etc.
    position_keywords = {
        "center": "[aria:position:50:50]",
        "left side": "[aria:position:15:80]",
        "right side": "[aria:position:85:80]",
        "top": "[aria:position:50:10]",
        "bottom": "[aria:position:50:90]",
        "corner": "[aria:position:10:10]",
        "stage left": "[aria:position:20:70]",
        "stage right": "[aria:position:80:70]",
        "front": "[aria:position:50:85]",
        "back": "[aria:position:50:15]",
    }

    # Check for position commands
    if "position" in cmd or "move to" in cmd or "go to" in cmd or "stand at" in cmd:
        for keyword, tag in position_keywords.items():
            if keyword in cmd:
                tags.append(tag)
                break
        else:
            # Try to extract numeric coordinates
            coord_match = _RE_COORDINATES.search(cmd)
            if coord_match:
                x, y = coord_match.groups()
                tags.append(f"[aria:position:{x}:{y}]")

    # Object management (add/remove objects)
    if "add" in cmd or "create" in cmd or "spawn" in cmd:
        object_emojis = {
            "bear": "🧸",
            "teddy": "🧸",
            "cat": "🐱",
            "dog": "🐶",
            "bunny": "🐰",
            "rabbit": "🐰",
            "star": "⭐",
            "heart": "❤️",
            "moon": "🌙",
            "sun": "☀️",
            "tree": "🌲",
            "plant": "🌿",
            "mushroom": "🍄",
            "car": "🚗",
            "bike": "🚲",
            "plane": "✈️",
        }
        for obj_name, emoji in object_emojis.items():
            if obj_name in cmd:
                tags.append(f"[aria:interact:add:{obj_name}:{emoji}]")
                break

    return tags


def execute_aria_action(action: dict) -> dict:
    """
    Execute a single structured action and update stage state

    Args:
        action: Action dict with 'action' key and params

    Returns:
        Result dict with status, message, and updated state
    """
    action_type = action.get("action")

    if action_type not in ARIA_ACTIONS:
        return {"status": "error", "message": f"Unknown action: {action_type}"}

    try:
        if action_type == "move":
            target = action.get("target")
            if isinstance(target, dict) and "x" in target and "y" in target:
                original_target = target
                target = _coerce_and_clamp_position(
                    target, fallback=stage_state["aria"]["position"])
                if target == stage_state["aria"]["position"] and original_target != stage_state["aria"]["position"]:
                    logger.warning("Invalid move target coerced to current position: %s", _sanitize_for_log(
                        str(original_target)))
                stage_state["aria"]["position"] = target
                return {
                    "status": "success",
                    "message": f'Moved to ({target["x"]}, {target["y"]})',
                    "tags": [f'[aria:position:{target["x"]}:{target["y"]}]'],
                }
            elif isinstance(target, str) and target in stage_state["objects"]:
                # Move to object
                obj_pos = stage_state["objects"][target]["position"]
                x = max(0, min(100, obj_pos["x"] + PICKUP_X_OFFSET))
                y = max(0, min(100, obj_pos["y"] + PICKUP_Y_OFFSET))
                stage_state["aria"]["position"] = {
                    "x": x,
                    "y": y,
                }
                return {
                    "status": "success",
                    "message": f"Moved to {target}",
                    "tags": [f"[aria:position:{x}:{y}]"],
                }
            return {
                "status": "success",
                "message": "No valid move target provided; staying in place",
                "tags": [],
            }

        elif action_type == "say":
            text = str(action.get("text", ""))[:200]  # Cap at 200 chars
            emotion = action.get("emotion", "neutral")
            stage_state["aria"]["expression"] = emotion
            return {
                "status": "success",
                "message": f'Said: "{text}" with {emotion} emotion',
                "tags": [f"[aria:say:{text}]", f"[aria:expression:{emotion}]"],
            }

        elif action_type == "pickup":
            obj_id = action.get("object_id")
            if obj_id not in stage_state["objects"]:
                return {"status": "error", "message": f"Object not found: {obj_id}"}

            if stage_state["aria"]["held_object"]:
                return {"status": "error", "message": "Already holding an object"}

            # Check distance
            aria_pos = stage_state["aria"]["position"]
            obj_pos = stage_state["objects"][obj_id]["position"]
            distance = ((aria_pos["x"] - obj_pos["x"]) **
                        2 + (aria_pos["y"] - obj_pos["y"]) ** 2) ** 0.5

            if distance > PICKUP_DISTANCE_THRESHOLD:
                auto_target = _coerce_and_clamp_position(
                    {
                        "x": obj_pos["x"] + PICKUP_X_OFFSET,
                        "y": obj_pos["y"] + PICKUP_Y_OFFSET,
                    },
                    fallback=stage_state["aria"]["position"],
                )
                stage_state["aria"]["position"] = auto_target

            stage_state["aria"]["held_object"] = obj_id
            stage_state["objects"][obj_id]["state"] = "held"
            pickup_message = (
                f"Auto-moved closer and picked up {obj_id}"
                if distance > PICKUP_DISTANCE_THRESHOLD
                else f"Picked up {obj_id}"
            )
            return {
                "status": "success",
                "message": pickup_message,
                "tags": (
                    [f"[aria:pickup:{obj_id}]", "[aria:limb:right_arm:grab]"]
                    if distance <= PICKUP_DISTANCE_THRESHOLD
                    else [
                        f"[aria:position:{auto_target['x']}:{auto_target['y']}]",
                        f"[aria:pickup:{obj_id}]",
                        "[aria:limb:right_arm:grab]",
                    ]
                ),
            }

        elif action_type == "drop":
            if not stage_state["aria"]["held_object"]:
                return {"status": "error", "message": "Not holding anything"}

            obj_id = stage_state["aria"]["held_object"]
            position = _coerce_and_clamp_position(
                action.get("position", stage_state["aria"]["position"]),
                fallback=stage_state["aria"]["position"],
            )

            stage_state["objects"][obj_id]["position"] = position
            stage_state["objects"][obj_id]["state"] = "dropped"
            stage_state["aria"]["held_object"] = None

            return {
                "status": "success",
                "message": f"Dropped {obj_id}",
                "tags": [f"[aria:drop:{obj_id}]", "[aria:limb:right_arm:release]"],
            }

        elif action_type == "throw":
            if not stage_state["aria"]["held_object"]:
                return {"status": "error", "message": "Not holding anything"}

            obj_id = stage_state["aria"]["held_object"]
            target = _coerce_and_clamp_position(action.get(
                "target", {"x": 70, "y": 40}), fallback={"x": 70, "y": 40})
            force = action.get("force", "medium")

            stage_state["objects"][obj_id]["position"] = target
            stage_state["objects"][obj_id]["state"] = "thrown"
            stage_state["aria"]["held_object"] = None

            return {
                "status": "success",
                "message": f"Threw {obj_id} with {force} force",
                "tags": [
                    f"[aria:throw:{obj_id}]",
                    "[aria:limb:right_arm:throw]",
                    f"[aria:animation:throw_{force}]",
                ],
            }

        elif action_type == "gesture":
            gesture_type = action.get("gesture_type", "wave")
            if gesture_type not in VALID_GESTURES:
                gesture_type = "wave"  # Default fallback

            return {
                "status": "success",
                "message": f"Performed {gesture_type} gesture",
                "tags": [
                    f"[aria:gesture:{gesture_type}]",
                    f"[aria:animation:{gesture_type}]",
                ],
            }

        elif action_type == "look":
            target = action.get("target")
            if isinstance(target, str) and target in stage_state["objects"]:
                # Look at object
                obj_pos = stage_state["objects"][target]["position"]
                aria_pos = stage_state["aria"]["position"]
                facing = "right" if obj_pos["x"] > aria_pos["x"] else "left"
                stage_state["aria"]["facing"] = facing
                return {
                    "status": "success",
                    "message": f"Looking at {target}",
                    "tags": [f"[aria:look:{target}]", f"[aria:facing:{facing}]"],
                }
            elif isinstance(target, dict) and "x" in target:
                # Look at position
                aria_pos = stage_state["aria"]["position"]
                facing = "right" if target["x"] > aria_pos["x"] else "left"
                stage_state["aria"]["facing"] = facing
                return {
                    "status": "success",
                    "message": "Looking at position",
                    "tags": [f"[aria:facing:{facing}]"],
                }

        elif action_type == "wait":
            duration = action.get("duration", 1.0)
            return {
                "status": "success",
                "message": f"Waiting {duration}s",
                "tags": [f"[aria:wait:{duration}]"],
            }

        return {"status": "error", "message": f"Action not implemented: {action_type}"}

    except Exception as e:
        logger.error(f"Action execution failed: {e}")
        return {"status": "error", "message": str(e)}


def action_to_tags(action: dict) -> list[str]:
    """Convert a structured action to Aria tag(s) without mutating stage state."""
    action_type = action.get("action")
    if not action_type:
        return []

    if action_type == "move":
        target = action.get("target")
        if isinstance(target, dict) and "x" in target and "y" in target:
            x = max(0, min(100, int(target["x"])))
            y = max(0, min(100, int(target["y"])))
            return [f"[aria:position:{x}:{y}]"]
        if isinstance(target, str):
            return [f"[aria:move:to:{target}]"]

    if action_type == "say":
        text = str(action.get("text", ""))[:200]
        emotion = str(action.get("emotion", "neutral"))
        tags = [f"[aria:say:{text}]"] if text else []
        if emotion:
            tags.append(f"[aria:expression:{emotion}]")
        return tags

    if action_type == "pickup":
        obj_id = action.get("object_id")
        return [f"[aria:pickup:{obj_id}]"] if obj_id else []

    if action_type == "drop":
        position = action.get("position")
        tags = ["[aria:drop]"]
        if isinstance(position, dict) and "x" in position and "y" in position:
            x = max(0, min(100, int(position["x"])))
            y = max(0, min(100, int(position["y"])))
            tags.append(f"[aria:position:{x}:{y}]")
        return tags

    if action_type == "throw":
        force = action.get("force", "medium")
        return [f"[aria:throw:{force}]"]

    if action_type == "gesture":
        gesture_type = action.get("gesture_type", "wave")
        return [f"[aria:gesture:{gesture_type}]"]

    if action_type == "look":
        target = action.get("target")
        if isinstance(target, str):
            return [f"[aria:look:{target}]"]
        return ["[aria:look]"]

    if action_type == "wait":
        duration = action.get("duration", 1.0)
        return [f"[aria:wait:{duration}]"]

    return []


def tags_from_actions(actions: list[dict]) -> list[str]:
    """Flatten tags from a list of structured actions."""
    tags: list[str] = []
    for action in actions:
        tags.extend(action_to_tags(action))
    return tags


def tags_to_actions(tags: list[str]) -> list[dict]:
    """Infer a minimal list of structured actions from simple tags.

    This helps the web UI receive actionable 'actions' even when the
    fallback parser returned only tags. It covers common tag types:
    - [aria:position:x:y] -> move
    - [aria:gesture:name] -> gesture
    - [aria:say:...] -> say
    - [aria:pickup:obj] -> pickup
    - [aria:drop] or [aria:drop:obj] -> drop
    - [aria:look:target] -> look
    """
    inferred: list[dict] = []
    for tag in tags:
        try:
            # [aria:position:12:34]
            m = re.match(r"\[aria:position:(\d{1,3}):(\d{1,3})\]", tag)
            if m:
                x = max(0, min(100, int(m.group(1))))
                y = max(0, min(100, int(m.group(2))))
                inferred.append({"action": "move", "target": {
                                "x": x, "y": y}, "speed": "normal"})
                continue

            # Named positions: [aria:position:center]
            m = re.match(r"\[aria:position:([a-z_\-]+)\]", tag)
            if m:
                name = m.group(1)
                named_map = {
                    "center": {"x": 50, "y": 50},
                    "left": {"x": 20, "y": 70},
                    "right": {"x": 80, "y": 70},
                    "front": {"x": 50, "y": 85},
                    "back": {"x": 50, "y": 15},
                    "top": {"x": 50, "y": 10},
                    "bottom": {"x": 50, "y": 90},
                }
                coords = named_map.get(name)
                if coords:
                    inferred.append(
                        {"action": "move", "target": coords, "speed": "normal"})
                    continue

            # gesture & animation -> gesture if allowed
            m = re.match(r"\[aria:gesture:([a-z_]+)\]", tag)
            if m:
                inferred.append(
                    {"action": "gesture", "gesture_type": m.group(1)})
                continue

            m = re.match(r"\[aria:animation:([a-z_]+)\]", tag)
            if m:
                anim = m.group(1)
                # map some animations to allowed gestures; fall back to 'wave'
                if anim in VALID_GESTURES:
                    inferred.append(
                        {"action": "gesture", "gesture_type": anim})
                else:
                    inferred.append(
                        {"action": "gesture", "gesture_type": "wave"})
                continue

            # Expression -> set expression via say action (emotion)
            m = re.match(r"\[aria:expression:([^\]]+)\]", tag)
            if m:
                expr = m.group(1)
                inferred.append({"action": "say", "text": "", "emotion": expr})
                continue

            # say text
            m = re.match(r"\[aria:say:(.+)\]", tag)
            if m:
                text = m.group(1)
                inferred.append(
                    {"action": "say", "text": text, "emotion": "neutral"})
                continue

            # pickup/drop
            m = re.match(r"\[aria:pickup:([^\]]+)\]", tag)
            if m:
                inferred.append({"action": "pickup", "object_id": m.group(1)})
                continue

            m = re.match(r"\[aria:drop:([^\]]+)\]", tag)
            if m:
                inferred.append({"action": "drop", "position": None})
                continue

            if tag.startswith("[aria:drop]"):
                inferred.append({"action": "drop", "position": None})
                continue

            # look
            m = re.match(r"\[aria:look:([^\]]+)\]", tag)
            if m:
                inferred.append({"action": "look", "target": m.group(1)})
                continue

            # effects -> map to a harmless gesture (wave) to represent visual effect
            m = re.match(r"\[aria:effect:([a-z_]+):([a-z_]+)\]", tag)
            if m:
                effect = m.group(1)
                # only map some known effects to gestures
                if effect in ("sparkle", "hearts", "glow"):
                    inferred.append(
                        {"action": "gesture", "gesture_type": "wave"})
                continue

            # throw
            m = re.match(r"\[aria:throw:(\d{1,3}):(\d{1,3})\]", tag)
            if m:
                x = max(0, min(100, int(m.group(1))))
                y = max(0, min(100, int(m.group(2))))
                inferred.append({"action": "throw", "target": {
                                "x": x, "y": y}, "force": "medium"})
                continue

            # wait
            m = re.match(r"\[aria:wait:([0-9]+(?:\.[0-9]+)?)\]", tag)
            if m:
                duration = max(0.0, min(30.0, float(m.group(1))))
                inferred.append({"action": "wait", "duration": duration})
                continue

        except Exception:
            # Be tolerant: skip tags we don't understand
            continue
    return inferred


class AriaRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        """Serve static files"""
        print(f"📥 GET request: {self.path}")
        # API: return either full stage snapshot or object registry
        if self.path == "/api/aria/state":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            payload = {
                "aria": stage_state.get("aria", {}),
                "objects": stage_state.get("objects", {}),
                "environment": stage_state.get("environment", {}),
            }
            self.wfile.write(json.dumps(payload).encode("utf-8"))
            return
        if self.path == "/api/aria/objects":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            payload = {"objects": stage_state.get("objects", {})}
            self.wfile.write(json.dumps(payload).encode("utf-8"))
            return
        if self.path == "/api/aria/schema":
            # Machine-readable action schema so AI agents/clients can discover
            # the canonical action contract (action types, params, examples).
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            payload = {
                "actions": ARIA_ACTIONS,
                "valid_gestures": sorted(VALID_GESTURES),
                "limits": {
                    "max_actions_per_sequence": 25,
                    "coordinate_range": [0, 100],
                    "max_say_text_chars": 200,
                    "max_wait_seconds": 30,
                },
            }
            self.wfile.write(json.dumps(payload).encode("utf-8"))
            return
        if self.path == "/api/aria/presets":
            # Expose curated example commands so AI agents can discover what
            # phrases are well-supported by the parser without trial and error.
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            presets_path = Path(__file__).resolve().parent / \
                "command_presets.generated.json"
            try:
                payload = json.loads(presets_path.read_text(encoding="utf-8"))
            except Exception as exc:  # pragma: no cover - defensive
                payload = {
                    "error": f"presets file unavailable: {exc}", "presets": []}
            self.wfile.write(json.dumps(payload).encode("utf-8"))
            return
        if self.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        # --- /api/aria/object endpoint ---
        # Expected payloads:
        # 1. Bulk update:
        #    {"objects": {"id1": {"position": {...}, "state": ...}, ...}}
        # 2. Single object action:
        #    {"action": "add|update|remove", "object": {"id": "...", "position": {...}, "state": ...}}
        #    - "add": adds a new object
        #    - "update": updates position/state of existing object
        #    - "remove": deletes object by id
        #    - "object" must include "id" or "name"
        """Handle API requests"""
        if self.path == "/api/aria/command":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                post_data = self.rfile.read(content_length)

                request_data = json.loads(post_data.decode("utf-8"))
                if not isinstance(request_data, dict):
                    raise ValueError("Request body must be a JSON object")
                command = request_data.get("command", "")
                if not isinstance(command, str) or not command.strip():
                    raise ValueError("command must be a non-empty string")
                if len(command) > 500:
                    raise ValueError("command exceeds 500 characters")
                use_llm = bool(request_data.get("use_llm", True))
                provider_choice = request_data.get("provider")
                model_override = request_data.get("model")

                # Update stage state if provided
                if "stage_state" in request_data:
                    if not isinstance(request_data["stage_state"], dict):
                        raise ValueError("stage_state must be an object")
                    stage_state.update(request_data["stage_state"])

                print(f"📝 Command received: {command}")
                print(f"👁️  Stage context:\n{get_stage_context()}")

                tags = []
                actions = []

                # Preferred path: parser-backed structured actions (supports
                # provider/model overrides including quantum).
                if use_llm:
                    try:
                        actions = action_parser.parse(
                            command,
                            use_llm=True,
                            provider_choice=provider_choice,
                            model_override=model_override,
                        )
                        tags = tags_from_actions(actions)
                    except Exception as parse_err:
                        logger.warning(
                            f"/api/aria/command parser path failed, falling back: {parse_err}")

                # Legacy fallback path: rule-based tag generation.
                if not tags:
                    legacy_tags = generate_tags_ai(command)
                    tags = legacy_tags if legacy_tags else generate_tags_fallback(
                        command)
                elif actions:
                    valid_actions, validation_reason = validate_action_sequence(
                        actions)
                    if not valid_actions:
                        safe_validation_reason = validation_reason.replace(
                            "\r", "\\r").replace("\n", "\\n")
                        logger.warning(
                            "Rejecting invalid parsed action sequence for /api/aria/command: %s",
                            safe_validation_reason,
                        )
                        actions = []
                        tags = generate_tags_fallback(command)

                # If tags were produced by the fallback path but we have no structured
                # actions, attempt to infer a minimal action sequence for convenience
                # (useful for UIs that prefer actions over raw tags).
                if tags and not actions:
                    inferred_actions = tags_to_actions(tags)
                    if inferred_actions:
                        valid_actions, validation_reason = validate_action_sequence(
                            inferred_actions)
                        if valid_actions:
                            actions = inferred_actions
                        else:
                            logger.info(
                                f"Inferred actions failed validation: {validation_reason}")

                print(f"✨ Generated tags: {tags}")

                response = {
                    "command": command,
                    "tags": tags,
                    "actions": actions if actions else None,
                    "provider_requested": provider_choice or "auto",
                    "model_requested": model_override,
                    "model": ("llm" if actions else ("ai" if (MODEL and tags) else "fallback")),
                    "stage_context": get_stage_context(),
                    "stage_aware": True,
                }

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(response).encode("utf-8"))

            except ConnectionAbortedError:
                # Client disconnected, ignore
                pass
            except Exception as e:
                print(f"❌ Error: {e}")
                try:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    error = {"error": str(e), "tags": []}
                    self.wfile.write(json.dumps(error).encode("utf-8"))
                except Exception:
                    pass
        elif self.path == "/api/aria/object" or self.path == "/api/aria/objects":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                post_data = self.rfile.read(content_length)
                request_data = json.loads(post_data.decode("utf-8"))

                # Support both single object ({action, object}) and bulk ({objects: {...}})
                if "objects" in request_data and isinstance(request_data["objects"], dict):
                    # Merge supplied objects into stage_state
                    for k, v in request_data["objects"].items():
                        if isinstance(v, dict) and "position" in v:
                            stage_state["objects"][k] = v
                    api_response = {"status": "ok",
                                    "objects": stage_state["objects"]}
                elif "object" in request_data and "action" in request_data:
                    action = request_data["action"]
                    obj = request_data["object"]
                    obj_id = obj.get("id") or obj.get("name")
                    if not obj_id:
                        raise ValueError(
                            'Object payload must include "id" or "name" field.')

                    if action == "add":
                        position = obj.get("position", {"x": 50, "y": 50})
                        state = obj.get("state", "on_stage")
                        stage_state["objects"][obj_id] = {
                            "position": position,
                            "state": state,
                        }
                        api_response = {
                            "status": "added",
                            "id": obj_id,
                            "object": stage_state["objects"][obj_id],
                        }
                    elif action == "update":
                        if obj_id not in stage_state["objects"]:
                            stage_state["objects"][obj_id] = {}
                        if "position" in obj:
                            stage_state["objects"][obj_id]["position"] = obj["position"]
                        if "state" in obj:
                            stage_state["objects"][obj_id]["state"] = obj["state"]
                        api_response = {
                            "status": "updated",
                            "id": obj_id,
                            "object": stage_state["objects"][obj_id],
                        }
                    elif action == "remove" or action == "delete":
                        removed = stage_state["objects"].pop(obj_id, None)
                        api_response = {
                            "status": "removed",
                            "id": obj_id,
                            "object": removed,
                        }
                    else:
                        raise ValueError(
                            f"Unknown action: {action}. Supported: add, update, remove/delete.")

                else:
                    raise ValueError(
                        'Invalid payload: must include either "objects" (dict) or both "action" and "object" (dict with id/name).'
                    )

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(api_response).encode("utf-8"))
                return
            except Exception as e:
                print(f"❌ Object API error: {e}")
                try:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(
                        {"error": str(e)}).encode("utf-8"))
                except Exception:
                    pass
                return

        # /api/aria/execute - LLM-powered automatic action execution
        elif self.path == "/api/aria/execute":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length)
                request_data = json.loads(body.decode("utf-8"))
                if not isinstance(request_data, dict):
                    raise ValueError("Request body must be a JSON object")

                command = request_data.get("command", "")
                auto_execute = request_data.get("auto_execute", False)
                use_llm = request_data.get("use_llm", True)
                provider_choice = request_data.get("provider")
                model_override = request_data.get("model")

                if not isinstance(command, str) or not command.strip():
                    raise ValueError("command must be a non-empty string")
                if len(command) > 500:
                    raise ValueError("command exceeds 500 characters")
                if not isinstance(auto_execute, bool):
                    raise ValueError("auto_execute must be a boolean")

                # Sanitize user input before logging to prevent log injection.
                command_for_log = command.replace("\r", "").replace("\n", "")

                # Parse command into actions
                actions = action_parser.parse(
                    command,
                    use_llm=use_llm,
                    provider_choice=provider_choice,
                    model_override=model_override,
                )

                if not actions:
                    api_response = {
                        "status": "error",
                        "message": "Could not parse command into actions",
                        "command": command,
                        "actions": [],
                    }
                else:
                    valid_actions, validation_reason = validate_action_sequence(
                        actions)
                    if not valid_actions:
                        raise ValueError(
                            f"Action sequence failed validation: {validation_reason}")

                    # Execute actions if auto_execute is True
                    execution_results = []
                    all_tags = []

                    if auto_execute:
                        actions_for_log = json.dumps(
                            actions, ensure_ascii=False, separators=(",", ":"))
                        actions_for_log = _sanitize_for_log(actions_for_log)
                        logger.info(
                            "Executing validated action sequence: %s", actions_for_log)
                        for action in actions:
                            exec_result = execute_aria_action(action)
                            execution_results.append(
                                {"action": action, "result": exec_result})
                            if exec_result.get("tags"):
                                all_tags.extend(exec_result["tags"])
                    else:
                        actions_for_log = json.dumps(
                            actions, ensure_ascii=False, separators=(",", ":"))
                        actions_for_log = _sanitize_for_log(actions_for_log)
                        logger.info(
                            "Dry-run plan mode for command '%s': %s", command_for_log, actions_for_log)

                    api_response = {
                        "status": "success",
                        "message": f"Parsed {len(actions)} actions"
                        + (" and executed" if auto_execute else " (plan only)"),
                        "command": command,
                        "provider_requested": provider_choice or "auto",
                        "model_requested": model_override,
                        "actions": actions,
                        "executed": auto_execute,
                        "results": execution_results if auto_execute else None,
                        "tags": all_tags if auto_execute else None,
                        "state": stage_state if auto_execute else None,
                    }

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(
                    api_response, indent=2).encode("utf-8"))

                print(
                    f"✓ Execute API: {command} -> {len(actions)} actions"
                    + (" (executed)" if auto_execute else " (plan only)")
                )
                return

            except Exception as e:
                print(f"❌ Execute API error: {e}")
                import traceback

                traceback.print_exc()
                try:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(
                        json.dumps(
                            {
                                "status": "error",
                                "error": str(e),
                                "message": f"Failed to execute command: {str(e)}",
                            }
                        ).encode("utf-8")
                    )
                except Exception:
                    pass
                return

        # /api/aria/world - Generate or regenerate themed world layout
        elif self.path == "/api/aria/world":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length)
                request_data = json.loads(body.decode("utf-8")) if body else {}
                theme = request_data.get("theme", "forest")
                # Sanitize user-controlled value before writing to logs (prevent log injection)
                safe_theme_for_log = re.sub(
                    r"[\r\n\t\x00-\x1f\x7f]+", " ", str(theme))
                count = int(request_data.get("count", 6))
                use_llm = bool(request_data.get("use_llm", True))
                provider_choice = request_data.get("provider")
                model_override = request_data.get("model")

                # Generate
                if use_llm:
                    try:
                        world_provider, _ = action_parser._resolve_provider_for_request(
                            explicit=provider_choice,
                            model_override=model_override,
                        )
                    except Exception as provider_err:
                        logger.warning(
                            f"World generation provider resolution failed: {provider_err}")
                        world_provider = None

                    if world_provider:
                        world = generate_world_with_llm(
                            theme, count, world_provider)
                    else:
                        world = generate_world_fallback(theme, count)
                        world["llm"] = False
                else:
                    world = generate_world_fallback(theme, count)
                    world["llm"] = False

                # Update global stage_state (replace objects, keep aria position)
                stage_state["objects"] = {}
                for oid, obj in world["objects"].items():
                    stage_state["objects"][oid] = {
                        "position": obj["position"],
                        "state": obj.get("state", "on_stage"),
                        "emoji": obj.get("emoji", ""),
                    }
                # Update environment meta
                stage_state["environment"]["theme"] = world["environment"].get(
                    "theme", theme)
                stage_state["environment"]["generated_at"] = world["environment"].get(
                    "generated_at")

                response = {
                    "status": "success",
                    "theme": theme,
                    "count": len(world["objects"]),
                    "used_llm": world.get("llm", False),
                    "provider_requested": provider_choice or "auto",
                    "model_requested": model_override,
                    "objects": world["objects"],
                    "environment": world["environment"],
                }

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(
                    response, indent=2).encode("utf-8"))
                safe_used_llm_for_log = str(
                    bool(response.get("used_llm", False)))
                safe_count_for_log = str(int(response.get("count", 0)))
                logger.info(
                    f"✓ World generated (theme={safe_theme_for_log}, llm={safe_used_llm_for_log}, count={safe_count_for_log})"
                )
                return
            except Exception as e:
                logger.error(f"World generation error: {e}")
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(
                    {"status": "error", "error": str(e)}).encode("utf-8"))
                return

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Custom logging"""
        try:
            message = format % args if args else str(format)
        except Exception:
            message = str(format)

        if "favicon" not in message:
            print(f"🌐 {message}")


# Backward-compatible module alias used by tests and older integrations:
# `from server import server as aria_server`.
server = sys.modules[__name__]


def main():
    # Change to aria_web directory
    web_dir = Path(__file__).parent
    os.chdir(web_dir)

    # Allow the port to be overridden via the ARIA_PORT environment variable.
    # This helps avoid address‑in‑use errors when the default port is already bound.
    port = int(os.getenv("ARIA_PORT", "8080"))
    # Default to localhost for security; use environment variable to override if needed
    host = os.environ.get("ARIA_HOST", "127.0.0.1")

    try:
        server = HTTPServer((host, port), AriaRequestHandler)
    except OSError as e:
        # Graceful handling when a server is already bound to this port.
        if getattr(e, "errno", None) == 98:
            probe_host = "127.0.0.1"
            state_url = f"http://{probe_host}:{port}/api/aria/state"
            try:
                with urllib.request.urlopen(state_url, timeout=1.0) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
                if isinstance(payload, dict) and "aria" in payload and "objects" in payload:
                    print(
                        f"⚠️ Aria server already running at http://{probe_host}:{port} (detected healthy /api/aria/state)."
                    )
                    print("ℹ️ Reusing existing server; exiting this process cleanly.")
                    return
            except Exception:
                pass

            # If another service occupies the port, fall back to a free port.
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind((host, 0))
                fallback_port = sock.getsockname()[1]

            print(
                f"⚠️ Port {port} is in use by another service; starting Aria on free port {fallback_port}.")
            print(
                f"💡 Set ARIA_PORT={fallback_port} (or another free port) to control startup port explicitly.")
            port = fallback_port
            server = HTTPServer((host, port), AriaRequestHandler)
        else:
            raise

    print("\n" + "=" * 70)
    print("🎨 Aria Visual Command System - Web Server")
    print("=" * 70)
    print(f"🌐 Open in browser: http://localhost:{port}")
    print(
        f"🤖 Model: {'AI (aria_expanded_v2)' if MODEL else 'Rule-based fallback'}")
    print("📝 Type commands in the web interface to control Aria")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 70 + "\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped")


if __name__ == "__main__":
    main()
