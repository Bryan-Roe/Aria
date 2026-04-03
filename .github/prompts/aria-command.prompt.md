---
description: "Control the Aria character — generate movement commands, action sequences, world themes, and object interactions using natural language."
name: "Aria Command"
argument-hint: "Natural language command (example: wave at me and say hello, then move left and pick up the ball)"
agent: aria-character
---

Process the following as an Aria character command. Use either the tag system or structured action sequences depending on the request.

**Tag System** (for simple commands embedded in chat responses):
```
[aria:walk:left]  [aria:jump]  [aria:dance]  [aria:wave]  [aria:smile]
[aria:sparkle]    [aria:glow]  [aria:sit]    [aria:gesture:thumbs_up]
```

**Action Sequences** (for multi-step operations):
```json
[
  {"action": "move", "target": "center", "speed": "walk"},
  {"action": "say", "text": "Hello!", "emotion": "happy"},
  {"action": "gesture", "gesture_type": "wave"}
]
```

**Available actions:** move, say, pickup, drop, throw, gesture, look, wait

**Context to include:**
- Current stage state (position, objects, expression)
- Nearby objects and their positions
- Valid gesture types: wave, thumbs_up, clap, shrug, bow, nod
- Bounds: coordinates 0-100%, text max 200 chars

**World generation** (if creating environments):
- Themes: forest, space, ocean, lab, medieval, desert, garden, cyberpunk, arcade
- Use `POST /api/aria/world` with theme and object count

**Server:** `apps/aria/server.py` on port 8080
**Client:** `apps/aria/aria_controller.js`
