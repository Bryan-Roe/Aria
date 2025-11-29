# Aria Auto-Execute System 🤖

## Overview

The Aria Auto-Execute system adds LLM-powered automatic action generation and execution to the Aria 3D character assistant. Users can type natural language commands that are automatically parsed into structured actions and executed in real-time.

## Features

✨ **LLM-Powered Parsing**: Uses shared chat providers (Azure OpenAI, OpenAI, LoRA, Local) to parse commands
📋 **Action Planning**: Preview planned actions before execution
▶️ **Auto-Execution**: Execute action sequences automatically
🔄 **State Management**: Track and update stage state (Aria position, objects, expressions)
🛡️ **Fallback System**: Rule-based parser when LLM unavailable
🎯 **8 Core Actions**: move, say, pickup, drop, throw, gesture, look, wait

## Quick Start

### 1. Start the Server

```bash
cd /workspaces/AI/aria_web
python server.py
```

Server will start on `http://localhost:8080`

### 2. Open Auto-Execute Interface

Open in browser: `http://localhost:8080/auto-execute.html`

### 3. Try Example Commands

Click any example command or type your own:

- "Walk to the table and pick up the apple"
- "Say hello and wave at the audience"
- "Go to the center and do a little dance"
- "Pick up the book, move to stage left, and drop it"
- "Look at the flower and say how beautiful it is"
- "Throw the ball toward the right side of the stage"

### 4. Plan or Execute

- **Plan Actions Only**: Preview the action sequence without executing
- **Execute Actions**: Run the full action sequence and update stage state

## Architecture

### Action Schema (ARIA_ACTIONS)

```python
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
```

### AriaActionParser Class

```python
class AriaActionParser:
    """LLM-powered action parser for automatic command execution"""
    
    def parse(command: str, use_llm: bool = True) -> List[dict]:
        """Parse command into structured actions"""
        # Try LLM first if available
        if use_llm and self.provider:
            return self.parse_with_llm(command)
        # Fallback to rule-based
        return self.parse_with_fallback(command)
```

**LLM Parsing Flow:**
1. Build system prompt with action schema + current stage state
2. Send command to LLM provider
3. Extract JSON array from response
4. Validate actions against schema
5. Return validated action list

**Fallback Parsing:**
- Uses regex patterns similar to existing `generate_tags_fallback()`
- Parses move, say, pickup, gesture commands
- Returns structured actions without LLM

### Action Execution

```python
def execute_aria_action(action: dict) -> dict:
    """Execute single action and update stage state"""
    # Validates action type
    # Updates stage_state (position, held_object, expression, etc.)
    # Returns result with status, message, tags
```

**Execution Results:**
```json
{
    "status": "success",
    "message": "Moved to apple",
    "tags": ["[aria:position:45:40]"]
}
```

## API Endpoints

### POST /api/aria/execute

Execute commands with automatic action generation.

**Request:**
```json
{
    "command": "Walk to the table and pick up the apple",
    "auto_execute": true,
    "use_llm": true
}
```

**Response (Plan Only - auto_execute=false):**
```json
{
    "status": "success",
    "message": "Parsed 2 actions (plan only)",
    "command": "Walk to the table and pick up the apple",
    "actions": [
        {"action": "move", "target": {"x": 60, "y": 35}, "speed": "normal"},
        {"action": "pickup", "object_id": "apple"}
    ],
    "executed": false,
    "results": null,
    "tags": null,
    "state": null
}
```

**Response (Executed - auto_execute=true):**
```json
{
    "status": "success",
    "message": "Parsed 2 actions and executed",
    "command": "Walk to the table and pick up the apple",
    "actions": [
        {"action": "move", "target": {"x": 60, "y": 35}, "speed": "normal"},
        {"action": "pickup", "object_id": "apple"}
    ],
    "executed": true,
    "results": [
        {
            "action": {"action": "move", "target": {"x": 60, "y": 35}, "speed": "normal"},
            "result": {
                "status": "success",
                "message": "Moved to (60, 35)",
                "tags": ["[aria:position:60:35]"]
            }
        },
        {
            "action": {"action": "pickup", "object_id": "apple"},
            "result": {
                "status": "success",
                "message": "Picked up apple",
                "tags": ["[aria:pickup:apple]", "[aria:limb:right_arm:grab]"]
            }
        }
    ],
    "tags": ["[aria:position:60:35]", "[aria:pickup:apple]", "[aria:limb:right_arm:grab]"],
    "state": {
        "aria": {
            "position": {"x": 60, "y": 35},
            "expression": "neutral",
            "held_object": "apple",
            "facing": "right"
        },
        "objects": {
            "apple": {"position": {"x": 55, "y": 35}, "state": "held"}
        }
    }
}
```

**Error Response:**
```json
{
    "status": "error",
    "error": "Too far from apple. Move closer first.",
    "message": "Failed to execute command: Too far from apple. Move closer first."
}
```

## LLM Provider Detection

Auto-detects available providers in order:

1. **Azure OpenAI**: Requires all 4 env vars
   - `AZURE_OPENAI_API_KEY`
   - `AZURE_OPENAI_ENDPOINT`
   - `AZURE_OPENAI_DEPLOYMENT`
   - `AZURE_OPENAI_API_VERSION`

2. **OpenAI**: Requires `OPENAI_API_KEY`

3. **LoRA**: Auto-detect adapter in configured path

4. **Local Echo**: Zero-dependency fallback

**Check Provider Status:**
```bash
curl http://localhost:8080/api/ai/status | jq '.active_provider'
```

## Stage State Management

The global `stage_state` dict tracks:

```python
stage_state = {
    'aria': {
        'position': {'x': 15, 'y': 20},    # % coordinates (0-100)
        'expression': 'neutral',            # facial expression
        'held_object': None,                # currently held object ID
        'facing': 'right'                   # left or right
    },
    'objects': {
        'apple': {
            'position': {'x': 55, 'y': 35},
            'state': 'on_table'             # on_table, held, dropped, thrown
        }
    },
    'environment': {
        'table': {'position': {'x': 60, 'y': 20}},
        'stage_bounds': {'width': 100, 'height': 100}
    }
}
```

**State Updates:**
- `move` → updates `aria.position`
- `say` → updates `aria.expression`
- `pickup` → sets `aria.held_object`, updates `object.state` to "held"
- `drop` → clears `aria.held_object`, moves object to new position
- `throw` → clears `aria.held_object`, moves object to target
- `look` → updates `aria.facing`

## Action Validation Rules

### Move Action
- Target can be `{x, y}` position or object name
- Position must be within stage bounds (0-100)
- Updates Aria's position immediately

### Pickup Action
- Aria must be within 30 units of object
- Aria can only hold one object at a time
- Object must exist in `stage_state.objects`

### Drop/Throw Actions
- Aria must be holding an object
- Updates object position and state
- Clears `held_object`

### Gesture Action
- Valid gestures: wave, bow, nod, shake, point, shrug, clap
- Fallback to 'wave' if invalid

## Testing

### Unit Test Example

```python
def test_action_parser():
    parser = AriaActionParser()
    
    # Test LLM parsing (if available)
    actions = parser.parse("Walk to the apple and pick it up", use_llm=True)
    assert len(actions) == 2
    assert actions[0]['action'] == 'move'
    assert actions[1]['action'] == 'pickup'
    
    # Test fallback parsing
    actions = parser.parse("Say hello", use_llm=False)
    assert len(actions) == 1
    assert actions[0]['action'] == 'say'
    assert 'hello' in actions[0]['text'].lower()
```

### Integration Test

```bash
# Start server
python server.py &

# Test plan-only
curl -X POST http://localhost:8080/api/aria/execute \
  -H "Content-Type: application/json" \
  -d '{"command": "Walk to the table", "auto_execute": false}'

# Test execution
curl -X POST http://localhost:8080/api/aria/execute \
  -H "Content-Type: application/json" \
  -d '{"command": "Pick up the apple", "auto_execute": true}'

# Check state
curl http://localhost:8080/api/aria/state
```

## Troubleshooting

### LLM Not Available

**Symptom**: Server logs show "✗ LLM providers not available"

**Solution**:
1. Check environment variables (Azure OpenAI or OpenAI keys)
2. Verify `shared/chat_providers.py` is accessible
3. System will automatically fall back to rule-based parsing

### Action Parsing Fails

**Symptom**: API returns 0 actions or unexpected actions

**Solution**:
1. Try with `use_llm: false` to test fallback parser
2. Check command clarity (be specific about objects and actions)
3. Review server logs for parsing errors

### Execution Fails

**Symptom**: Actions return error status

**Common Errors:**
- "Too far from object" → Move Aria closer first
- "Already holding an object" → Drop current object before pickup
- "Not holding anything" → Pick up an object first
- "Object not found" → Check object name spelling (apple, book, cup, ball, flower)

**Debug:**
```python
# Check current state
curl http://localhost:8080/api/aria/state | jq

# Check Aria's position and held object
curl http://localhost:8080/api/aria/state | jq '.aria'

# Check object positions
curl http://localhost:8080/api/aria/state | jq '.objects'
```

## Performance

- **LLM Parsing**: 1-3 seconds (depends on provider)
- **Fallback Parsing**: <10ms
- **Action Execution**: <1ms per action
- **State Updates**: Immediate (in-memory dict)

## Limitations

1. **Single Object Holding**: Aria can only hold one object at a time
2. **Distance Checks**: Objects must be within 30 units for pickup
3. **No Animation Timing**: Wait action duration is logical (not animated)
4. **2D Coordinates**: Stage uses 2D percentage coordinates (0-100)
5. **Limited Gestures**: Only 7 predefined gesture types

## Future Enhancements

- [ ] Multi-object inventory system
- [ ] Complex gesture sequences
- [ ] Natural language state queries ("Where is the apple?")
- [ ] Action history and undo
- [ ] Conditional actions ("If holding apple, drop it")
- [ ] Parallel action execution
- [ ] Animation timing integration
- [ ] 3D coordinate system

## Related Files

- `server.py` - Main server with action parser and execution logic
- `auto-execute.html` - Web UI for testing auto-execution
- `index.html` - Original Aria visual command interface
- `shared/chat_providers.py` - LLM provider detection and abstraction
- `tests/test_aria_auto_execute.py` - Unit and integration tests (TODO)

## Contributing

When adding new actions:

1. Add action to `ARIA_ACTIONS` dict with params and example
2. Implement execution logic in `execute_aria_action()`
3. Add parsing pattern to `parse_with_fallback()`
4. Update LLM system prompt (auto-included from schema)
5. Add example command to `auto-execute.html`
6. Write tests for new action

## License

Part of the QAI (Quantum-AI) project. See root LICENSE file.

---

**Need Help?** Check the [main README](/README.md) or [copilot instructions](/.github/copilot-instructions.md)
