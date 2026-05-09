---
name: "Aria-Character"
description: "Guidance for Aria interactive character system"
applyTo: "apps/aria/**"
---
# Aria Character System — Implementation Guidance

## Server (`apps/aria/server.py`)
- HTTP server on port 8080 with CORS support.
- 8 core actions: `move`, `say`, `pickup`, `drop`, `throw`, `gesture`, `look`, `wait`.
- `AriaActionParser`: LLM-powered parsing with rule-based fallback. Always try LLM first.
- `execute_aria_action(action)`: State machine — validates preconditions (distance, bounds, holding), mutates `stage_state`, returns `{status, message, tags}`.
- Stage state: `stage_state['aria']` (position, expression, held_object, facing) + `stage_state['objects']` + `stage_state['environment']`.
- Position bounds: 0-100% for both x and y coordinates. Always validate.
- Pickup distance threshold: <30% euclidean distance from object.
- Text sanitization: max 200 chars for `say` action text.
- Valid gestures: wave, thumbs_up, clap, shrug, bow, nod (allowlist enforced).
- World generation themes: forest, space, ocean, lab, medieval, desert, garden, cyberpunk, arcade.
- Keyword matching: use pre-compiled `frozenset` for O(1) lookups.

## Client (`apps/aria/aria_controller.js`)
- `characterState`: mood, energy, personality, colors, size, style, heldObject, position, rotation.
- `analyzeAIResponse(text)`: Extracts mood + energy from AI text for character visualization.
- `generateCharacterFromMood(mood, energy)`: Mood-specific color palettes and animations.
- 3D CSS transforms for limbs, eye tracking, sparkle/glow effects.

## API Endpoints
- `GET /api/aria/state` — Full state snapshot.
- `GET /api/aria/objects` — Object registry.
- `POST /api/aria/command` — NL command → tags/actions.
- `POST /api/aria/execute` — Auto-execute structured action sequences.
- `POST /api/aria/object` — Add/update/remove objects.
- `POST /api/aria/world` — LLM-powered themed world generation.

## Tag Format
`[aria:action:param]` — Examples: `[aria:walk:left]`, `[aria:jump]`, `[aria:gesture:thumbs_up]`.

## Testing
- Unit: `pytest tests/test_aria_server.py tests/test_object_api_integration.py -v`
- E2E: `pytest tests/test_ui_playwright.py -v` (requires server running)
- Auto-execute: `apps/aria/test_auto_execute.py`
