# Aria 3D Character Web Interface

A real-time 3D character controller with object management and server synchronization.

## Features

- **3D Character Control**: Move Aria character around the stage using waypoints
- **Object Management**: Add, pickup, drop, and throw objects
- **Server Sync**: All client actions synchronized to Python backend
- **Chat Interface**: Send commands via chat that generate server-side tags
- **Real-time Updates**: Bidirectional communication between UI and server

## Quick Start

```bash
# Start the server
cd aria_web
python server.py

# Open in browser
# Navigate to: http://localhost:8000
```

## Architecture

### Frontend (`index.html` + `aria_controller.js`)
- 3D CSS transforms for character positioning
- Drag-and-drop object placement
- Click waypoints for movement
- Chat command processing

### Backend (`server.py`)
- REST API for object management
- Global `stage_state` dictionary
- Tag generation for speech/movement commands
- HTTP server on port 8000

## API Endpoints

### GET `/api/aria/state`
Returns current stage state including character position and all objects.

**Response:**
```json
{
  "position": {"x": 0, "y": 0, "z": 0},
  "objects": {
    "apple": {
      "id": "apple",
      "emoji": "🍎",
      "position": {"x": 100, "y": 200, "z": 0},
      "state": "on_stage"
    }
  }
}
```

### GET `/api/aria/objects`
Returns list of all objects on stage.

**Response:**
```json
{
  "objects": {
    "apple": {...},
    "book": {...}
  }
}
```

### POST `/api/aria/object`
Add, update, or remove an object.

**Add Object:**
```json
{
  "action": "add",
  "object": {
    "id": "apple",
    "emoji": "🍎",
    "position": {"x": 100, "y": 200, "z": 0}
  }
}
```

**Update Object:**
```json
{
  "action": "update",
  "object": {
    "id": "apple",
    "position": {"x": 150, "y": 250, "z": 0},
    "state": "held"
  }
}
```

**Remove Object:**
```json
{
  "action": "remove",
  "object": {
    "id": "apple"
  }
}
```

### POST `/api/aria/command`
Process a chat command and return generated tags.

**Request:**
```json
{
  "command": "Say hello and move to center"
}
```

**Response:**
```json
{
  "tags": "[aria:say:hello][aria:position:center]"
}
```

### POST `/api/aria/world`
Generate (or regenerate) a themed world layout using the LLM (if available) or a deterministic fallback.

**Request:**
```json
{
  "theme": "forest",      // optional (default: "forest")
  "count": 7,              // optional number of objects (default: 6)
  "use_llm": true          // optional, force fallback if false
}
```

**Successful Response:**
```json
{
  "status": "success",
  "theme": "forest",
  "count": 6,
  "used_llm": true,
  "objects": {
    "tree": {"id": "tree", "emoji": "🌲", "position": {"x": 42, "y": 33}, "state": "on_stage"},
    "rock": {"id": "rock", "emoji": "🪨", "position": {"x": 55, "y": 61}, "state": "on_stage"}
  },
  "environment": {
    "theme": "forest",
    "generated_at": "2025-11-28T17:20:00Z",
    "stage_bounds": {"width": 100, "height": 100}
  }
}
```

**Notes:**
- If the LLM response is malformed, the server automatically falls back to procedural generation.
- Object IDs are sanitized (alphanumeric + underscore, max 30 chars).
- Positions are guaranteed to lie within stage bounds (0–100).
- Existing objects are replaced; Aria's position is preserved.

**Example cURL:**
```bash
curl -X POST http://localhost:8080/api/aria/world \
  -H 'Content-Type: application/json' \
  -d '{"theme":"space","count":5,"use_llm":true}' | jq
```

## Object States

- `on_stage` - Object is on the stage floor
- `on_table` - Object is on a table/elevated surface
- `held` - Object is being held by character
- `thrown` - Object is in mid-air

## Client-Server Sync Flow

```
User Action (Click/Drag)
    ↓
aria_controller.js
    ↓
sendObjectUpdate()
    ↓
POST /api/aria/object
    ↓
server.py updates stage_state
    ↓
GET /api/aria/state (polling/refresh)
    ↓
UI reflects new state
```

## Testing

Comprehensive testing strategy with multiple layers:

- **Unit Tests**: Server-side tag generation and helpers
- **Integration Tests**: HTTP API endpoints
- **E2E Tests**: Full browser automation (Playwright, Pyppeteer, Selenium)

See [TESTING.md](TESTING.md) for detailed testing guide.

### Quick Test Commands

```bash
# Run all unit and integration tests
pytest tests/test_aria_server.py tests/test_object_api_integration.py -v

# Run E2E tests (requires browser setup)
pytest tests/test_ui_playwright.py -m playwright -v

# Run all tests
pytest tests/test_*aria*.py tests/test_ui_*.py -v
```

## Development

### File Structure

```
aria_web/
├── index.html           # Main UI
├── test.html            # Test page for features
├── aria_controller.js   # Client-side logic
├── server.py            # Backend server
├── README.md            # This file
└── TESTING.md           # Testing guide
```

### Adding New Features

1. Update `aria_controller.js` for client-side behavior
2. Add corresponding endpoint in `server.py`
3. Write unit tests in `tests/test_aria_server.py`
4. Write integration tests in `tests/test_object_api_integration.py`
5. Add E2E test if it's a critical user flow
6. Update this documentation

### Key Functions

#### Client-Side (`aria_controller.js`)

- `addObject(name, emoji)` - Add a new object to the stage
- `pickUpObject(objectId)` - Pick up an object
- `dropObject()` - Drop the currently held object
- `throwObject(targetX, targetY)` - Throw the held object
- `sendObjectUpdate(data)` - Sync object state to server

#### Server-Side (`server.py`)

- `handle_object(action, obj)` - Process object operations
- `get_stage_state()` - Return current state
- `generate_speech_tag(text)` - Create `[aria:say:...]` tag
- `generate_position_tag(x, y)` - Create `[aria:position:...]` tag

## CI/CD

GitHub Actions workflow (`.github/workflows/aria-tests.yml`) runs automatically on:
- Push to `main` or `develop`
- Pull requests
- Changes to `aria_web/` or test files

Workflow includes:
- Unit & integration tests (Python 3.10, 3.11, 3.12)
- Playwright E2E tests
- Pyppeteer E2E tests
- Selenium containerized Chrome tests
- Test result aggregation

## Future Enhancements

- [ ] WebSocket for real-time updates (replace polling)
- [ ] Physics engine for object interactions
- [ ] Inventory system
- [ ] Multi-character support
- [ ] 3D model rendering (Three.js/Babylon.js)
- [ ] Save/load stage state
- [ ] Undo/redo functionality
- [ ] Collaborative editing (multiple users)

## Troubleshooting

### Server won't start
- Check if port 8000 is already in use: `lsof -i :8000`
- Try different port: `python server.py --port 8080`

### Objects not syncing
- Check browser console for errors
- Verify server is running: `curl http://localhost:8000/api/aria/state`
- Check server logs for error messages

### Tests failing
- Ensure server is not running during tests (tests auto-start server)
- Check all dependencies are installed: `pip install -r requirements.txt`
- See [TESTING.md](TESTING.md) for detailed troubleshooting

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for your changes
4. Ensure all tests pass
5. Submit a pull request

## License

See main repository LICENSE file.

## Related Documentation

- [TESTING.md](TESTING.md) - Comprehensive testing guide
- [Main Project README](/workspaces/AI/README.md) - Overall project documentation
- [GitHub Actions Workflow](/.github/workflows/aria-tests.yml) - CI/CD configuration
