#!/usr/bin/env python
"""
Simple web server for Aria Visual Command System
Serves the HTML/JS frontend and provides API endpoint for command generation
"""
import random
import math
import sys
import hashlib
from pathlib import Path
import datetime
from datetime import timezone
from typing import List
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import re
from urllib.parse import urlparse, parse_qs
import logging

# Pre-compile regex patterns for performance (avoid recompiling in loops)
_RE_JSON_BLOCK = re.compile(r'\[.*\]', re.DOTALL)
_RE_ARIA_TAGS = re.compile(r'\[aria:[^\]]+\]')
_RE_SAY_COMMAND = re.compile(
    r"(?:\b(?:say|announce|shout|speak|tell)\b)(?:\s+(?:everyone|that|to))?[:\-\s]+(.+)", 
    re.IGNORECASE
)
_RE_SANITIZE_BRACKETS = re.compile(r'\]')
_RE_COORDINATES = re.compile(r'(\d{1,3})%?.*?(\d{1,3})%?')

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project paths
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "AI" / "microsoft_phi-silica-3.6_v1"))
sys.path.insert(0, str(REPO_ROOT))  # Add root for shared imports

# Try to import shared chat providers for LLM integration
try:
    from shared.chat_providers import detect_provider
    LLM_AVAILABLE = True
    logger.info("✓ LLM providers available for automatic action generation")
except ImportError:
    LLM_AVAILABLE = False
    logger.warning(
        "✗ LLM providers not available - will use rule-based fallback only")

# Skip AI model loading for faster startup - use rule-based fallback
MODEL = None
print("⚠️ Skipping AI model loading - using rule-based fallback for faster startup")

# Pre-compiled keyword sets for O(1) lookup instead of O(n) any() calls
JUMP_KEYWORDS = frozenset(['jump', 'leap', 'hop'])
DANCE_KEYWORDS = frozenset(['dance', 'spin', 'twirl'])
WAVE_KEYWORDS = frozenset(['wave', 'greet', 'hello', 'hi'])
LOOK_KEYWORDS = frozenset(['look', 'see', 'watch', 'observe'])
SIT_KEYWORDS = frozenset(['sit', 'rest', 'relax'])
RUN_KEYWORDS = frozenset(['run', 'race', 'sprint'])
HIDE_KEYWORDS = frozenset(['hide', 'crouch', 'duck'])
PRESENT_KEYWORDS = frozenset(['present', 'show', 'display'])
THINK_KEYWORDS = frozenset(['think', 'wonder', 'ponder'])
MOVE_KEYWORDS = frozenset(['go', 'move', 'walk', 'run'])
SAY_KEYWORDS = frozenset(['say', 'speak', 'tell', 'greet'])
PICKUP_KEYWORDS = frozenset(['pick', 'get', 'grab', 'take'])
ARM_WAVE_KEYWORDS = frozenset(['wave', 'wiggle'])
ARM_RAISE_KEYWORDS = frozenset(['raise', 'up', 'lift'])
ARM_LOWER_KEYWORDS = frozenset(['lower', 'down'])
ARM_FORWARD_KEYWORDS = frozenset(['forward', 'front'])
ARM_BACK_KEYWORDS = frozenset(['back', 'backward', 'behind'])
LEFT_ARM_KEYWORDS = frozenset(['left arm', 'arm left', 'left hand'])
RIGHT_ARM_KEYWORDS = frozenset(['right arm', 'arm right', 'right hand'])
LEFT_LEG_KEYWORDS = frozenset(['left leg', 'leg left'])
RIGHT_LEG_KEYWORDS = frozenset(['right leg', 'leg right'])
SPARKLE_KEYWORDS = frozenset(['sparkle', 'sparkles', 'glitter', 'shimmer', 'shine'])
GLOW_KEYWORDS = frozenset(['glow', 'glowing', 'radiate', 'illuminate'])
HEARTS_KEYWORDS = frozenset(['hearts', 'heart', 'love'])
WALK_LEFT_KEYWORDS = frozenset(['walk left', 'go left', 'left'])
WALK_RIGHT_KEYWORDS = frozenset(['walk right', 'go right', 'right'])

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
    set(LEFT_ARM_KEYWORDS)
    | set(RIGHT_ARM_KEYWORDS)
    | set(LEFT_LEG_KEYWORDS)
    | set(RIGHT_LEG_KEYWORDS)
)

# Global stage state that AI can see
stage_state = {
    'aria': {
        'position': {'x': 15, 'y': 20},  # percentage coordinates
        'expression': 'neutral',
        'held_object': None,
        'facing': 'right'
    },
    'objects': {
        'apple': {'position': {'x': 55, 'y': 35}, 'state': 'on_table'},
        'book': {'position': {'x': 48, 'y': 35}, 'state': 'on_table'},
        'cup': {'position': {'x': 62, 'y': 35}, 'state': 'on_table'},
        'ball': {'position': {'x': 70, 'y': 35}, 'state': 'on_table'},
        'flower': {'position': {'x': 52, 'y': 35}, 'state': 'on_table'}
    },
    'environment': {
        'table': {'position': {'x': 60, 'y': 20}},
        'stage_bounds': {'width': 100, 'height': 100}
    }
}

# Structured action schema for LLM-powered automatic execution
ARIA_ACTIONS = {
    "move": {
        "params": ["target", "speed"],
        "description": "Move Aria to a target position or object",
        "example": {"action": "move", "target": {"x": 50, "y": 30}, "speed": "normal"}
    },
    "say": {
        "params": ["text", "emotion"],
        "description": "Make Aria speak with optional emotion",
        "example": {"action": "say", "text": "Hello!", "emotion": "happy"}
    },
    "pickup": {
        "params": ["object_id"],
        "description": "Pick up an object from the stage",
        "example": {"action": "pickup", "object_id": "apple"}
    },
    "drop": {
        "params": ["position"],
        "description": "Drop currently held object at position",
        "example": {"action": "drop", "position": {"x": 50, "y": 30}}
    },
    "throw": {
        "params": ["target", "force"],
        "description": "Throw held object toward target",
        "example": {"action": "throw", "target": {"x": 70, "y": 40}, "force": "medium"}
    },
    "gesture": {
        "params": ["gesture_type"],
        "description": "Perform a gesture animation",
        "example": {"action": "gesture", "gesture_type": "wave"}
    },
    "look": {
        "params": ["target"],
        "description": "Look at a target position or object",
        "example": {"action": "look", "target": "apple"}
    },
    "wait": {
        "params": ["duration"],
        "description": "Wait for specified duration in seconds",
        "example": {"action": "wait", "duration": 2.0}
    }
}


class AriaActionParser:
    """LLM-powered action parser for automatic command execution"""

    def __init__(self):
        self.provider = None
        self.provider_choice = None
        self._initialize_provider()

    def _initialize_provider(self):
        """Initialize LLM provider if available, robust to tuple return values."""
        if not LLM_AVAILABLE:
            logger.info("LLM not available - will use rule-based fallback")
            return

        try:
            detected = detect_provider()
            # detect_provider returns (provider_instance, ProviderChoice)
            if isinstance(detected, tuple) and len(detected) == 2:
                self.provider, self.provider_choice = detected
            else:
                # older style (just provider)
                self.provider = detected
            provider_name = getattr(self.provider_choice, 'name', getattr(
                self.provider, '__class__', type(self.provider)).__class__.__name__)
            logger.info(f"✓ Initialized LLM provider: {provider_name}")
        except Exception as e:
            logger.warning(f"Failed to initialize LLM provider: {e}")
            self.provider = None

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

    def parse_with_llm(self, command: str) -> List[dict]:
        """Parse command using LLM provider"""
        if not self.provider:
            raise ValueError("LLM provider not available")

        system_prompt = self._build_system_prompt()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": command}
        ]

        try:
            response = self.provider.complete(messages, stream=False)

            # Extract JSON from response
            content = response.get('content', '').strip()

            # Try to parse as JSON
            if content.startswith('['):
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
                if 'action' in action and action['action'] in ARIA_ACTIONS:
                    validated.append(action)
                else:
                    logger.warning(f"Skipping invalid action: {action}")

            return validated

        except Exception as e:
            logger.error(f"LLM parsing failed: {e}")
            raise

    def parse_with_fallback(self, command: str) -> List[dict]:
        """Rule-based fallback parser (uses existing generate_tags_fallback logic)"""
        actions = []
        command_lower = command.lower()

        # Parse move commands
        if _contains_any_keyword(command_lower, MOVE_KEYWORDS):
            # Extract target from command
            if 'table' in command_lower:
                actions.append({"action": "move", "target": {
                               "x": 60, "y": 35}, "speed": "normal"})
            elif 'center' in command_lower or 'middle' in command_lower:
                actions.append({"action": "move", "target": {
                               "x": 50, "y": 50}, "speed": "normal"})
            elif 'left' in command_lower:
                actions.append({"action": "move", "target": {
                               "x": 20, "y": 50}, "speed": "normal"})
            elif 'right' in command_lower:
                actions.append({"action": "move", "target": {
                               "x": 80, "y": 50}, "speed": "normal"})

        # Parse say commands
        if _contains_any_keyword(command_lower, SAY_KEYWORDS):
            # Extract text after say/speak
            for trigger in ['say ', 'speak ', 'tell ', 'greet ']:
                if trigger in command_lower:
                    text = command[command_lower.index(
                        trigger) + len(trigger):].strip(' "\'')
                    emotion = 'happy' if any(w in text.lower() for w in [
                                             '!', 'hello', 'hi']) else 'neutral'
                    actions.append(
                        {"action": "say", "text": text, "emotion": emotion})
                    break

        # Parse pickup commands
        for obj in ['apple', 'book', 'cup', 'ball', 'flower']:
            if obj in command_lower and _contains_any_keyword(command_lower, PICKUP_KEYWORDS):
                # Move to object first
                obj_pos = stage_state['objects'][obj]['position']
                actions.append(
                    {"action": "move", "target": obj_pos, "speed": "normal"})
                actions.append({"action": "pickup", "object_id": obj})
                break

        # Parse gesture commands
        gestures = ['wave', 'thumbs_up', 'clap', 'shrug', 'bow', 'nod']
        for gesture in gestures:
            trigger = gesture.replace('_', ' ')
            if trigger in command_lower:
                actions.append({"action": "gesture", "gesture_type": gesture})
                break

        return actions

    def parse(self, command: str, use_llm: bool = True) -> List[dict]:
        """
        Parse command into structured actions

        Args:
            command: Natural language command
            use_llm: Try LLM first if available

        Returns:
            List of action dicts
        """
        if use_llm and self.provider:
            try:
                actions = self.parse_with_llm(command)
                logger.info(
                    f"✓ LLM parsed: {command} -> {len(actions)} actions")
                return actions
            except Exception as e:
                logger.warning(f"LLM parsing failed, using fallback: {e}")

        actions = self.parse_with_fallback(command)
        logger.info(f"✓ Fallback parsed: {command} -> {len(actions)} actions")
        return actions


# --------------------------- World Generation ---------------------------


def _sanitize_id(raw: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]+", "_", raw.strip().lower())
    return cleaned[:30] or f"obj_{random.randint(1000, 9999)}"


THEME_OBJECT_LIBRARY = {
    'forest': [
        ("tree", "🌲"), ("mushroom", "🍄"), ("rock",
                                           "🪨"), ("flower", "🌼"), ("owl", "🦉"), ("fox", "🦊")
    ],
    'space': [
        ("planet", "🪐"), ("star", "⭐"), ("rocket", "🚀"), ("alien",
                                                          "👽"), ("astronaut", "👩‍🚀"), ("satellite", "🛰️")
    ],
    'ocean': [
        ("fish", "🐟"), ("shell", "🐚"), ("coral",
                                        "🪸"), ("whale", "🐋"), ("ship", "🚢"), ("dolphin", "🐬")
    ],
    'lab': [
        ("beaker", "🧪"), ("microscope", "🔬"), ("dna",
                                               "🧬"), ("robot", "🤖"), ("atom", "⚛️"), ("chip", "💾")
    ],
    'medieval': [
        ("sword", "🗡️"), ("shield", "🛡️"), ("crown",
                                            "👑"), ("scroll", "📜"), ("goblet", "🍷"), ("castle", "🏰")
    ],
    'desert': [
        ("cactus", "🌵"), ("skull", "💀"), ("camel",
                                          "🐪"), ("scorpion", "🦂"), ("sun", "☀️"), ("sand", "🟨")
    ],
    'garden': [
        ("rose", "🌹"), ("tulip", "🌷"), ("butterfly",
                                        "🦋"), ("bee", "🐝"), ("bench", "🪑"), ("pond", "💧")
    ],
    'cyberpunk': [
        ("drone", "🛸"), ("neon", "💡"), ("chip",
                                        "💾"), ("server", "🖥️"), ("bot", "🤖"), ("battery", "🔋")
    ],
    'arcade': [
        ("joystick", "🕹️"), ("coin", "🪙"), ("ghost",
                                            "👻"), ("trophy", "🏆"), ("console", "🎮"), ("heart", "❤️")
    ],
}


def generate_world_fallback(theme: str, count: int) -> dict:
    """Generate a world procedurally without LLM."""
    objects_catalog = THEME_OBJECT_LIBRARY.get(
        theme.lower(), THEME_OBJECT_LIBRARY['forest'])
    random.shuffle(objects_catalog)
    chosen = objects_catalog[: max(1, count)]
    stage_objects = {}
    used_positions = []
    for name, emoji in chosen:
        # Avoid overlapping positions (simple Poisson-ish attempt)
        for attempt in range(10):
            x = random.randint(10, 90)
            y = random.randint(20, 80)
            if all(math.hypot(x - px, y - py) > 8 for px, py in used_positions):
                used_positions.append((x, y))
                break
        stage_objects[_sanitize_id(name)] = {
            'id': _sanitize_id(name),
            'emoji': emoji,
            'position': {'x': x, 'y': y},
            'state': 'on_stage'
        }
    environment = {
        'theme': theme,
        'generated_at': datetime.datetime.now(timezone.utc).isoformat() + 'Z',
        'seed': random.randint(100000, 999999),
        'stage_bounds': {'width': 100, 'height': 100}
    }
    return {
        'objects': stage_objects,
        'environment': environment
    }


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
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]
        raw = provider.complete(messages, stream=False)
        raw_str = raw if isinstance(raw, str) else str(raw)
        # Strip code fences
        if '```' in raw_str:
            m = re.search(r"```(?:json)?\n(.*?)(```)$",
                          raw_str, flags=re.DOTALL)
            if m:
                raw_str = m.group(1).strip()
        # Extract first JSON object
        obj_match = re.search(r"\{.*\}\s*$", raw_str, flags=re.DOTALL)
        if obj_match:
            raw_str = obj_match.group(0)
        parsed_world_data = json.loads(raw_str)
        # Basic validation
        objects = parsed_world_data.get('objects') or {}
        env = parsed_world_data.get('environment') or {}
        # Sanitize
        sanitized_objects = {}
        for key, val in list(objects.items())[:count]:
            if not isinstance(val, dict):
                continue
            oid = _sanitize_id(val.get('id') or key)
            pos = val.get('position', {})
            x = int(max(0, min(100, pos.get('x', random.randint(10, 90)))))
            y = int(max(0, min(100, pos.get('y', random.randint(20, 80)))))
            state = val.get('state', 'on_stage')
            emoji = val.get('emoji', '✨')
            sanitized_objects[oid] = {
                'id': oid,
                'emoji': emoji,
                'position': {'x': x, 'y': y},
                'state': state
            }
        if not sanitized_objects:
            return generate_world_fallback(theme, count)
        env.setdefault('theme', theme)
        env.setdefault('generated_at', datetime.datetime.now(
            timezone.utc).isoformat() + 'Z')
        env.setdefault('stage_bounds', {'width': 100, 'height': 100})
        return {
            'objects': sanitized_objects,
            'environment': env,
            'llm': True,
            'raw_response_len': len(raw_str)
        }
    except Exception as e:
        logger.warning(f"World generation via LLM failed: {e}; falling back.")
        return generate_world_fallback(theme, count) | {'llm': False}


# Initialize global action parser
action_parser = AriaActionParser()


def get_stage_context() -> str:
    """Generate natural language description of current stage state for AI"""
    aria = stage_state['aria']
    objects = stage_state['objects']

    # Calculate distances to objects
    aria_pos = aria['position']
    nearby_objects = []
    for obj_name, obj_data in objects.items():
        # Safety check: ensure object has position data
        if not isinstance(obj_data, dict) or 'position' not in obj_data:
            continue
        obj_pos = obj_data['position']
        if not isinstance(obj_pos, dict) or 'x' not in obj_pos or 'y' not in obj_pos:
            continue
        distance = ((aria_pos['x'] - obj_pos['x'])**2 +
                    (aria_pos['y'] - obj_pos['y'])**2)**0.5
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
    aria_pos = stage_state['aria']['position']
    objects = stage_state['objects']
    table_pos = stage_state['environment']['table']['position']

    # Object interaction positioning - move near the object
    for obj_name in ['apple', 'book', 'cup', 'ball', 'flower', 'bear']:
        if obj_name in cmd and ('pick' in cmd or 'get' in cmd or 'grab' in cmd or 'take' in cmd):
            if obj_name in objects:
                obj_data = objects[obj_name]
                # Safety check: ensure object has position data
                if isinstance(obj_data, dict) and 'position' in obj_data:
                    obj_pos = obj_data['position']
                    if isinstance(obj_pos, dict) and 'x' in obj_pos and 'y' in obj_pos:
                        # Position slightly to the left of object
                        return f'[aria:position:{max(10, obj_pos["x"] - 10)}:{obj_pos["y"] + 10}]'

    # Action-based positioning (using pre-compiled keyword sets for O(1) lookup)
    if _contains_any_keyword(cmd, JUMP_KEYWORDS):
        return '[aria:position:50:60]'  # Center for jumping
    elif _contains_any_keyword(cmd, DANCE_KEYWORDS):
        return '[aria:position:50:50]'  # Center stage for performance
    elif _contains_any_keyword(cmd, WAVE_KEYWORDS):
        return '[aria:position:30:70]'  # Front-left for greeting
    elif _contains_any_keyword(cmd, LOOK_KEYWORDS):
        # Look towards table
        if 'table' in cmd:
            return '[aria:position:40:60]'  # Position to see table
        return '[aria:position:20:40]'  # Left side for observing
    elif _contains_any_keyword(cmd, SIT_KEYWORDS):
        # Near table to sit
        return f'[aria:position:{table_pos["x"] - 5}:{table_pos["y"] + 35}]'
    elif _contains_any_keyword(cmd, RUN_KEYWORDS):
        return '[aria:position:85:70]'  # Far right for running space
    elif _contains_any_keyword(cmd, HIDE_KEYWORDS):
        return '[aria:position:10:75]'  # Corner position
    elif _contains_any_keyword(cmd, PRESENT_KEYWORDS):
        return '[aria:position:50:50]'  # Center to present
    elif _contains_any_keyword(cmd, THINK_KEYWORDS):
        return '[aria:position:25:50]'  # Contemplative left position
    elif _contains_any_keyword(cmd, WALK_LEFT_KEYWORDS):
        return '[aria:position:20:70]'  # Moving to left
    elif _contains_any_keyword(cmd, WALK_RIGHT_KEYWORDS):
        return '[aria:position:80:70]'  # Moving to right
    elif 'add' in cmd or 'create' in cmd or 'spawn' in cmd:
        # For adding objects, position near table
        return f'[aria:position:{table_pos["x"] - 15}:{table_pos["y"] + 20}]'
    else:
        # Context-aware positioning: stay put if already in good position
        # or move to interesting area if idle
        pos_hash = int(hashlib.md5(cmd.encode()).hexdigest()[:4], 16)
        x = 30 + (pos_hash % 40)  # Random between 30-70%
        y = 60 + (pos_hash % 20)  # Random between 60-80%
        return f'[aria:position:{x}:{y}]'


def generate_tags_ai(command: str) -> List[str]:
    """Generate tags using AI model"""
    if MODEL is None:
        return []

    try:
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
                pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id
            )

        response = tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
        tags = _RE_ARIA_TAGS.findall(response)
        return tags[:2]  # Return first 2 tags max
    except Exception as e:
        print(f"AI generation error: {e}")
        return []


def generate_tags_fallback(command: str) -> List[str]:
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
    has_limb_command = (_contains_any_keyword(cmd, LEFT_ARM_KEYWORDS) or 
                       _contains_any_keyword(cmd, RIGHT_ARM_KEYWORDS) or
                       _contains_any_keyword(cmd, LEFT_LEG_KEYWORDS) or
                       _contains_any_keyword(cmd, RIGHT_LEG_KEYWORDS))

    # Special: server-side "say" / announce detection (capture original text)
    try:
        say_match = _RE_SAY_COMMAND.search(command)
        if say_match:
            raw_msg = say_match.group(1).strip()
            # basic sanitization and length cap
            safe_msg = _RE_SANITIZE_BRACKETS.sub('', raw_msg)[:200]
            tags.append(f'[aria:say:{safe_msg}]')
    except Exception:
        # ignore parsing errors
        pass

    # Expressions
    if 'smile' in cmd or 'happy' in cmd:
        tags.append('[aria:expression:smile]')
    elif 'sad' in cmd:
        tags.append('[aria:expression:sad]')
    elif 'surprised' in cmd:
        tags.append('[aria:expression:surprised]')
    elif 'confused' in cmd:
        tags.append('[aria:expression:confused]')
    elif 'thinking' in cmd or 'think' in cmd:
        tags.append('[aria:expression:thinking]')
    elif 'wink' in cmd:
        tags.append('[aria:expression:wink]')

    # Animations
    if 'jump' in cmd:
        tags.append('[aria:animate:jump]')
    elif 'dance' in cmd:
        tags.append('[aria:animate:dance]')
    elif 'spin' in cmd:
        tags.append('[aria:animate:spin]')
    elif 'bow' in cmd:
        tags.append('[aria:animate:bow]')
    elif 'flip' in cmd:
        tags.append('[aria:animate:flip]')

    # Gestures (allowlist: wave, thumbs_up, clap, shrug, bow, nod)
    if 'wave' in cmd:
        tags.append('[aria:gesture:wave]')
    elif 'thumbs up' in cmd:
        tags.append('[aria:gesture:thumbs_up]')
    elif 'clap' in cmd:
        tags.append('[aria:gesture:clap]')
    elif 'shrug' in cmd:
        tags.append('[aria:gesture:shrug]')
    elif 'nod' in cmd:
        tags.append('[aria:gesture:nod]')

    # Limb controls and poses (AI may also emit these; fallback supports natural phrases)
    # Hands up / T-pose / Cross arms
    if 'hands up' in cmd or 'raise hands' in cmd:
        tags.append('[aria:limb:left_arm:raise]')
        tags.append('[aria:limb:right_arm:raise]')
    if 't-pose' in cmd or 'tpose' in cmd or 't pose' in cmd:
        tags.append('[aria:pose:t-pose]')
    if 'cross arms' in cmd or 'arms crossed' in cmd:
        tags.append('[aria:pose:cross_arms]')

    # Per-limb commands
    def limb_tag(part: str, action: str):
        tags.append(f'[aria:limb:{part}:{action}]')

    # Helper maps (using pre-compiled keyword sets)
    left_arm = _contains_any_keyword(cmd, LEFT_ARM_KEYWORDS)
    right_arm = _contains_any_keyword(cmd, RIGHT_ARM_KEYWORDS)
    left_leg = _contains_any_keyword(cmd, LEFT_LEG_KEYWORDS)
    right_leg = _contains_any_keyword(cmd, RIGHT_LEG_KEYWORDS)

    # Numeric angle if present (e.g., "left arm 45 degrees")
    angle_match = re.search(r'(-?\d{1,3})\s*(?:deg|degree|degrees)?', cmd)
    angle_val = angle_match.group(1) if angle_match else None

    # Arm actions
    if left_arm or right_arm or 'arm' in cmd:
        # Choose default arm if unspecified
        parts = []
        if left_arm:
            parts.append('left_arm')
        if right_arm:
            parts.append('right_arm')
        if not parts:
            parts = ['right_arm']
        if _contains_any_keyword(cmd, ARM_WAVE_KEYWORDS):
            for p in parts:
                limb_tag(p, 'wave')
        elif _contains_any_keyword(cmd, ARM_RAISE_KEYWORDS):
            for p in parts:
                limb_tag(p, 'raise')
        elif _contains_any_keyword(cmd, ARM_LOWER_KEYWORDS):
            for p in parts:
                limb_tag(p, 'lower')
        elif _contains_any_keyword(cmd, ARM_FORWARD_KEYWORDS):
            for p in parts:
                limb_tag(p, 'forward')
        elif _contains_any_keyword(cmd, ARM_BACK_KEYWORDS):
            for p in parts:
                limb_tag(p, 'back')
        elif angle_val is not None:
            for p in parts:
                limb_tag(p, angle_val)

    # Leg actions
    if left_leg or right_leg or 'leg' in cmd:
        parts = []
        if left_leg:
            parts.append('left_leg')
        if right_leg:
            parts.append('right_leg')
        if not parts:
            parts = ['left_leg']
        if 'kick' in cmd:
            for p in parts:
                limb_tag(p, 'kick')
        elif _contains_any_keyword(cmd, ARM_FORWARD_KEYWORDS):
            for p in parts:
                limb_tag(p, 'forward')
        elif _contains_any_keyword(cmd, ARM_BACK_KEYWORDS):
            for p in parts:
                limb_tag(p, 'back')
        elif angle_val is not None:
            for p in parts:
                limb_tag(p, angle_val)

    # Movement - only add if not a limb command (to avoid conflicts like "left arm" -> "move:left")
    if not has_limb_command:
        # Determine movement style
        movement_style = None
        if 'skip' in cmd:
            movement_style = 'skip'
        elif 'strut' in cmd or 'swagger' in cmd:
            movement_style = 'strut'
        elif 'run' in cmd:
            movement_style = 'run'
        elif 'walk' in cmd:
            movement_style = 'walk'
        else:
            movement_style = 'move'

        # Determine direction - exclude if keywords could be part of limb commands
        has_forward_limb = 'leg' in cmd or 'arm' in cmd
        if 'left' in cmd:
            tags.append(f'[aria:{movement_style}:left]')
        elif 'right' in cmd:
            tags.append(f'[aria:{movement_style}:right]')
        elif ('up' in cmd or 'forward' in cmd) and not has_forward_limb:
            tags.append(f'[aria:{movement_style}:up]')
        elif ('down' in cmd or 'back' in cmd) and not has_forward_limb:
            tags.append(f'[aria:{movement_style}:down]')

    # Effects - with keyword matching and intensity support
    effect_intensity = 'normal'
    if 'light' in cmd or 'subtle' in cmd or 'gentle' in cmd:
        effect_intensity = 'light'
    elif 'heavy' in cmd or 'intense' in cmd or 'lots' in cmd or 'many' in cmd:
        effect_intensity = 'heavy'

    if _contains_any_keyword(cmd, SPARKLE_KEYWORDS):
        tags.append(f'[aria:effect:sparkle:{effect_intensity}]')
    elif _contains_any_keyword(cmd, GLOW_KEYWORDS):
        tags.append(f'[aria:effect:glow:{effect_intensity}]')
    elif _contains_any_keyword(cmd, HEARTS_KEYWORDS):
        tags.append(f'[aria:effect:hearts:{effect_intensity}]')

    # Camera
    if 'center' in cmd:
        tags.append('[aria:camera:center]')
    elif 'zoom' in cmd:
        tags.append(
            '[aria:camera:zoom_in]' if 'in' in cmd else '[aria:camera:zoom_out]')

    # Poses (body positions)
    if 'sit' in cmd:
        tags.append('[aria:pose:sit]')
    elif 'stand' in cmd:
        tags.append('[aria:pose:stand]')
    elif 'crouch' in cmd:
        tags.append('[aria:pose:crouch]')
    elif 'lie' in cmd or 'lay' in cmd:
        tags.append('[aria:pose:lie]')

    # Position control - let AI determine where Aria should be
    # Format: [aria:position:x:y] where x and y are percentages (0-100)
    # Or named positions: [aria:position:center], [aria:position:left], etc.
    position_keywords = {
        'center': '[aria:position:50:50]',
        'left side': '[aria:position:15:80]',
        'right side': '[aria:position:85:80]',
        'top': '[aria:position:50:10]',
        'bottom': '[aria:position:50:90]',
        'corner': '[aria:position:10:10]',
        'stage left': '[aria:position:20:70]',
        'stage right': '[aria:position:80:70]',
        'front': '[aria:position:50:85]',
        'back': '[aria:position:50:15]'
    }

    # Check for position commands
    if 'position' in cmd or 'move to' in cmd or 'go to' in cmd or 'stand at' in cmd:
        for keyword, tag in position_keywords.items():
            if keyword in cmd:
                tags.append(tag)
                break
        else:
            # Try to extract numeric coordinates
            coord_match = _RE_COORDINATES.search(cmd)
            if coord_match:
                x, y = coord_match.groups()
                tags.append(f'[aria:position:{x}:{y}]')

    # Object management (add/remove objects)
    if 'add' in cmd or 'create' in cmd or 'spawn' in cmd:
        object_emojis = {
            'bear': '🧸', 'teddy': '🧸',
            'cat': '🐱', 'dog': '🐶', 'bunny': '🐰', 'rabbit': '🐰',
            'star': '⭐', 'heart': '❤️', 'moon': '🌙', 'sun': '☀️',
            'tree': '🌲', 'plant': '🌿', 'mushroom': '🍄',
            'car': '🚗', 'bike': '🚲', 'plane': '✈️'
        }
        for obj_name, emoji in object_emojis.items():
            if obj_name in cmd:
                tags.append(f'[aria:interact:add:{obj_name}:{emoji}]')
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
    action_type = action.get('action')

    if action_type not in ARIA_ACTIONS:
        return {'status': 'error', 'message': f'Unknown action: {action_type}'}

    try:
        if action_type == 'move':
            target = action.get('target')
            if isinstance(target, dict) and 'x' in target and 'y' in target:
                # Clamp position to stage bounds (0-100)
                target = {
                    'x': max(0, min(100, target['x'])),
                    'y': max(0, min(100, target['y']))
                }
                stage_state['aria']['position'] = target
                return {
                    'status': 'success',
                    'message': f'Moved to ({target["x"]}, {target["y"]})',
                    'tags': [f'[aria:position:{target["x"]}:{target["y"]}]']
                }
            elif isinstance(target, str) and target in stage_state['objects']:
                # Move to object
                obj_pos = stage_state['objects'][target]['position']
                stage_state['aria']['position'] = {
                    'x': obj_pos['x'] - 10, 'y': obj_pos['y'] + 5}
                return {
                    'status': 'success',
                    'message': f'Moved to {target}',
                    'tags': [f'[aria:position:{obj_pos["x"] - 10}:{obj_pos["y"] + 5}]']
                }

        elif action_type == 'say':
            text = str(action.get('text', ''))[:200]  # Cap at 200 chars
            emotion = action.get('emotion', 'neutral')
            stage_state['aria']['expression'] = emotion
            return {
                'status': 'success',
                'message': f'Said: "{text}" with {emotion} emotion',
                'tags': [f'[aria:say:{text}]', f'[aria:expression:{emotion}]']
            }

        elif action_type == 'pickup':
            obj_id = action.get('object_id')
            if obj_id not in stage_state['objects']:
                return {'status': 'error', 'message': f'Object not found: {obj_id}'}

            if stage_state['aria']['held_object']:
                return {'status': 'error', 'message': 'Already holding an object'}

            # Check distance
            aria_pos = stage_state['aria']['position']
            obj_pos = stage_state['objects'][obj_id]['position']
            distance = ((aria_pos['x'] - obj_pos['x']) **
                        2 + (aria_pos['y'] - obj_pos['y'])**2)**0.5

            if distance > 30:
                return {'status': 'error', 'message': f'Too far from {obj_id}. Move closer first.'}

            stage_state['aria']['held_object'] = obj_id
            stage_state['objects'][obj_id]['state'] = 'held'
            return {
                'status': 'success',
                'message': f'Picked up {obj_id}',
                'tags': [f'[aria:pickup:{obj_id}]', f'[aria:limb:right_arm:grab]']
            }

        elif action_type == 'drop':
            if not stage_state['aria']['held_object']:
                return {'status': 'error', 'message': 'Not holding anything'}

            obj_id = stage_state['aria']['held_object']
            position = action.get('position', stage_state['aria']['position'])

            stage_state['objects'][obj_id]['position'] = position
            stage_state['objects'][obj_id]['state'] = 'dropped'
            stage_state['aria']['held_object'] = None

            return {
                'status': 'success',
                'message': f'Dropped {obj_id}',
                'tags': [f'[aria:drop:{obj_id}]', '[aria:limb:right_arm:release]']
            }

        elif action_type == 'throw':
            if not stage_state['aria']['held_object']:
                return {'status': 'error', 'message': 'Not holding anything'}

            obj_id = stage_state['aria']['held_object']
            target = action.get('target', {'x': 70, 'y': 40})
            force = action.get('force', 'medium')

            stage_state['objects'][obj_id]['position'] = target
            stage_state['objects'][obj_id]['state'] = 'thrown'
            stage_state['aria']['held_object'] = None

            return {
                'status': 'success',
                'message': f'Threw {obj_id} with {force} force',
                'tags': [f'[aria:throw:{obj_id}]', '[aria:limb:right_arm:throw]', f'[aria:animation:throw_{force}]']
            }

        elif action_type == 'gesture':
            gesture_type = action.get('gesture_type', 'wave')
            valid_gestures = frozenset(['wave', 'thumbs_up', 'clap', 'shrug', 'bow', 'nod'])

            if gesture_type not in valid_gestures:
                gesture_type = 'wave'  # Default fallback

            return {
                'status': 'success',
                'message': f'Performed {gesture_type} gesture',
                'tags': [f'[aria:gesture:{gesture_type}]', f'[aria:animation:{gesture_type}]']
            }

        elif action_type == 'look':
            target = action.get('target')
            if isinstance(target, str) and target in stage_state['objects']:
                # Look at object
                obj_pos = stage_state['objects'][target]['position']
                aria_pos = stage_state['aria']['position']
                facing = 'right' if obj_pos['x'] > aria_pos['x'] else 'left'
                stage_state['aria']['facing'] = facing
                return {
                    'status': 'success',
                    'message': f'Looking at {target}',
                    'tags': [f'[aria:look:{target}]', f'[aria:facing:{facing}]']
                }
            elif isinstance(target, dict) and 'x' in target:
                # Look at position
                aria_pos = stage_state['aria']['position']
                facing = 'right' if target['x'] > aria_pos['x'] else 'left'
                stage_state['aria']['facing'] = facing
                return {
                    'status': 'success',
                    'message': f'Looking at position',
                    'tags': [f'[aria:facing:{facing}]']
                }

        elif action_type == 'wait':
            duration = action.get('duration', 1.0)
            return {
                'status': 'success',
                'message': f'Waiting {duration}s',
                'tags': [f'[aria:wait:{duration}]']
            }

        return {'status': 'error', 'message': f'Action not implemented: {action_type}'}

    except Exception as e:
        logger.error(f"Action execution failed: {e}")
        return {'status': 'error', 'message': str(e)}


class AriaRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        """Serve static files"""
        print(f"📥 GET request: {self.path}")
        # API: return objects or full stage_state if requested
        if self.path == '/api/aria/objects' or self.path == '/api/aria/state':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            payload = {'objects': stage_state.get(
                'objects', {}), 'aria': stage_state.get('aria', {})}
            self.wfile.write(json.dumps(payload).encode('utf-8'))
            return
        if self.path == '/':
            self.path = '/index.html'
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
        if self.path == '/api/aria/command':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)

                request_data = json.loads(post_data.decode('utf-8'))
                command = request_data.get('command', '')

                # Update stage state if provided
                if 'stage_state' in request_data:
                    stage_state.update(request_data['stage_state'])

                print(f"📝 Command received: {command}")
                print(f"👁️  Stage context:\n{get_stage_context()}")

                # Try AI first with full context, fallback to rules
                tags = generate_tags_ai(command)
                if not tags:
                    tags = generate_tags_fallback(command)

                print(f"✨ Generated tags: {tags}")

                response = {
                    'command': command,
                    'tags': tags,
                    'model': 'ai' if (MODEL and tags) else 'fallback',
                    'stage_context': get_stage_context(),
                    'stage_aware': True
                }

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))

            except ConnectionAbortedError:
                # Client disconnected, ignore
                pass
            except Exception as e:
                print(f"❌ Error: {e}")
                try:
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    error = {'error': str(e), 'tags': []}
                    self.wfile.write(json.dumps(error).encode('utf-8'))
                except:
                    pass
        elif self.path == '/api/aria/object' or self.path == '/api/aria/objects':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                request_data = json.loads(post_data.decode('utf-8'))

                # Support both single object ({action, object}) and bulk ({objects: {...}})
                if 'objects' in request_data and isinstance(request_data['objects'], dict):
                    # Merge supplied objects into stage_state
                    for k, v in request_data['objects'].items():
                        if isinstance(v, dict) and 'position' in v:
                            stage_state['objects'][k] = v
                    api_response = {'status': 'ok',
                              'objects': stage_state['objects']}
                elif 'object' in request_data and 'action' in request_data:
                    action = request_data['action']
                    obj = request_data['object']
                    obj_id = obj.get('id') or obj.get('name')
                    if not obj_id:
                        raise ValueError(
                            'Object payload must include "id" or "name" field.')

                    if action == 'add':
                        position = obj.get('position', {'x': 50, 'y': 50})
                        state = obj.get('state', 'on_stage')
                        stage_state['objects'][obj_id] = {
                            'position': position, 'state': state}
                        api_response = {'status': 'added', 'id': obj_id,
                                  'object': stage_state['objects'][obj_id]}
                    elif action == 'update':
                        if obj_id not in stage_state['objects']:
                            stage_state['objects'][obj_id] = {}
                        if 'position' in obj:
                            stage_state['objects'][obj_id]['position'] = obj['position']
                        if 'state' in obj:
                            stage_state['objects'][obj_id]['state'] = obj['state']
                        api_response = {'status': 'updated', 'id': obj_id,
                                  'object': stage_state['objects'][obj_id]}
                    elif action == 'remove' or action == 'delete':
                        removed = stage_state['objects'].pop(obj_id, None)
                        api_response = {'status': 'removed',
                                  'id': obj_id, 'object': removed}
                    else:
                        raise ValueError(
                            f'Unknown action: {action}. Supported: add, update, remove/delete.')

                else:
                    raise ValueError(
                        'Invalid payload: must include either "objects" (dict) or both "action" and "object" (dict with id/name).')

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(api_response).encode('utf-8'))
                return
            except Exception as e:
                print(f"❌ Object API error: {e}")
                try:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(
                        {'error': str(e)}).encode('utf-8'))
                except:
                    pass
                return

        # /api/aria/execute - LLM-powered automatic action execution
        elif self.path == '/api/aria/execute':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)
                request_data = json.loads(body.decode('utf-8'))

                command = request_data.get('command', '')
                auto_execute = request_data.get('auto_execute', False)
                use_llm = request_data.get('use_llm', True)

                if not command:
                    raise ValueError('command is required')

                # Parse command into actions
                actions = action_parser.parse(command, use_llm=use_llm)

                if not actions:
                    api_response = {
                        'status': 'error',
                        'message': 'Could not parse command into actions',
                        'command': command,
                        'actions': []
                    }
                else:
                    # Execute actions if auto_execute is True
                    execution_results = []
                    all_tags = []

                    if auto_execute:
                        for action in actions:
                            exec_result = execute_aria_action(action)
                            execution_results.append({
                                'action': action,
                                'result': exec_result
                            })
                            if exec_result.get('tags'):
                                all_tags.extend(exec_result['tags'])

                    api_response = {
                        'status': 'success',
                        'message': f'Parsed {len(actions)} actions' + (' and executed' if auto_execute else ' (plan only)'),
                        'command': command,
                        'actions': actions,
                        'executed': auto_execute,
                        'results': execution_results if auto_execute else None,
                        'tags': all_tags if auto_execute else None,
                        'state': stage_state if auto_execute else None
                    }

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(api_response, indent=2).encode('utf-8'))

                print(f"✓ Execute API: {command} -> {len(actions)} actions" +
                      (f" (executed)" if auto_execute else " (plan only)"))
                return

            except Exception as e:
                print(f"❌ Execute API error: {e}")
                import traceback
                traceback.print_exc()
                try:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'status': 'error',
                        'error': str(e),
                        'message': f'Failed to execute command: {str(e)}'
                    }).encode('utf-8'))
                except:
                    pass
                return

        # /api/aria/world - Generate or regenerate themed world layout
        elif self.path == '/api/aria/world':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)
                request_data = json.loads(body.decode('utf-8')) if body else {}
                theme = request_data.get('theme', 'forest')
                count = int(request_data.get('count', 6))
                use_llm = bool(request_data.get('use_llm', True))

                # Generate
                if use_llm and action_parser.provider:
                    world = generate_world_with_llm(
                        theme, count, action_parser.provider)
                else:
                    world = generate_world_fallback(theme, count)
                    world['llm'] = False

                # Update global stage_state (replace objects, keep aria position)
                stage_state['objects'] = {}
                for oid, obj in world['objects'].items():
                    stage_state['objects'][oid] = {
                        'position': obj['position'],
                        'state': obj.get('state', 'on_stage'),
                        'emoji': obj.get('emoji', '')
                    }
                # Update environment meta
                stage_state['environment']['theme'] = world['environment'].get(
                    'theme', theme)
                stage_state['environment']['generated_at'] = world['environment'].get(
                    'generated_at')

                response = {
                    'status': 'success',
                    'theme': theme,
                    'count': len(world['objects']),
                    'used_llm': world.get('llm', False),
                    'objects': world['objects'],
                    'environment': world['environment']
                }

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(
                    response, indent=2).encode('utf-8'))
                logger.info(
                    f"✓ World generated (theme={theme}, llm={response['used_llm']}, count={response['count']})")
                return
            except Exception as e:
                logger.error(f"World generation error: {e}")
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(
                    {'status': 'error', 'error': str(e)}).encode('utf-8'))
                return

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Custom logging"""
        if 'favicon' not in args[0] if args else True:
            print(f"🌐 {args[0] if args else format}")


# Backward-compatible module alias used by tests and older integrations:
# `from server import server as aria_server`.
server = sys.modules[__name__]


def main():
    import os

    # Change to aria_web directory
    web_dir = Path(__file__).parent
    os.chdir(web_dir)

    # Allow the port to be overridden via the ARIA_PORT environment variable.
    # This helps avoid address‑in‑use errors when the default port is already bound.
    port = int(os.getenv('ARIA_PORT', '8080'))
    # Default to localhost for security; use environment variable to override if needed
    host = os.environ.get('ARIA_HOST', '127.0.0.1')
    server = HTTPServer((host, port), AriaRequestHandler)

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


if __name__ == '__main__':
    main()
