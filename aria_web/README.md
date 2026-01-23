# Aria 3D Character Web Interface

A real-time 3D character controller with object management, procedural world generation, and Azure Cosmos DB persistence.

## Features

- **3D Character Control**: Move Aria character around the stage using waypoints
- **Object Management**: Add, pickup, drop, and throw objects
- **Procedural World Generation**: Spatially distributed 3D worlds with Poisson-disc or rejection sampling
- **Cosmos DB Persistence**: Production-ready Azure Cosmos integration with graceful fallback
- **Dual-Source Retrieval**: Worlds persisted to both filesystem and Cosmos DB for high availability
- **Server Sync**: All client actions synchronized to Python backend
- **Chat Interface**: Send commands via chat that generate server-side tags
- **Real-time Updates**: Bidirectional communication between UI and server

> **🆕 Cosmos DB Integration**: See [COSMOS_IMPLEMENTATION.md](COSMOS_IMPLEMENTATION.md) for complete details on the dedicated `aria_worlds` container, retrieval APIs, cost optimization, and migration guide.

## Quick Start

```bash
# Start the server
cd aria_web
python server.py

# Open in browser
# Navigate to: http://localhost:8080
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
Generate (or regenerate) a themed world layout using the LLM (if available) or a deterministic, *spaced* fallback.

**Request Parameters:**
```jsonc
{
  "theme": "forest",        // optional (default: "forest")
  "count": 7,                // optional number of objects (default: 6)
  "use_llm": true,           // optional, force fallback if false
  "seed": 12345,             // optional deterministic seed (repeatable worlds)
  "spacing": 12,             // optional minimum desired distance between objects (default: 10)
  "algorithm": "poisson",   // optional placement algorithm: "rejection" (default) | "poisson"
  "persist": true            // optional; override env ARIA_WORLD_PERSIST
}
```

**Successful Response (LLM or fallback):**
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
    "seed": 12345,
    "spacing": 12,
    "generation_method": "llm",              // or "fallback_rejection" / "fallback_poisson_disc"
    "stage_bounds": {"width": 100, "height": 100}
  },
  "persisted": true,
  "persisted_path": "data_out/aria_worlds/world_forest_20251128_172000_12345.json",
  "cosmos_persisted": false                    // true if stored in Cosmos DB
}
```

**Notes:**
- Malformed LLM output triggers automatic fallback with spaced sampling.
- Two fallback algorithms:
  - `rejection` (default): fast rejection sampling with distance relaxation for dense requests.
  - `poisson`: Bridson Poisson-disc sampling (higher uniformity) with padding if not enough points found.
- Object IDs are sanitized (alphanumeric + underscore, max 30 chars).
- Deterministic generation when a `seed` is supplied (same theme+seed+count+spacing+algorithm → same layout).
- If `count` exceeds catalog size, objects cycle with suffixes (e.g. `tree_7`).
- Set env `ARIA_WORLD_PERSIST=true` to persist by default; can override per request with `persist`.
- Fallback exposes `generation_method` = `fallback_rejection` or `fallback_poisson_disc`.
- If Cosmos DB is enabled (see main project docs) worlds attempt cloud persistence; failures are silent and `cosmos_persisted`=false.

**Example cURL (persist + deterministic Poisson fallback):**
```bash
curl -X POST http://localhost:8080/api/aria/world \
  -H 'Content-Type: application/json' \
  -d '{"theme":"space","count":8,"use_llm":false,"seed":777,"spacing":14,"algorithm":"poisson","persist":true}' | jq
```

**Example cURL (attempt LLM, seed for reproducible fallback if fails):**
```bash
curl -X POST http://localhost:8080/api/aria/world \
  -H 'Content-Type: application/json' \
  -d '{"theme":"lab","count":5,"use_llm":true,"seed":202401,"persist":true}' | jq
```

### GET `/api/aria/world/get?theme=<theme>&seed=<seed>`
Retrieve a previously generated world by theme and seed. Attempts Cosmos DB first (if enabled), then falls back to filesystem snapshots.

**Query Parameters:**
- `theme` (required): World theme name (e.g., `forest`, `space`)
- `seed` (required): Generation seed (deterministic worlds)

**Success Response (200):**
```json
{
  "status": "success",
  "theme": "forest",
  "seed": "12345",
  "source": "cosmos",  // or "filesystem"
  "objects": {
    "tree": {"id": "tree", "emoji": "🌲", "position": {"x": 42, "y": 33}, "state": "on_stage"}
  },
  "environment": {
    "theme": "forest",
    "generated_at": "2025-11-29T10:00:00Z",
    "seed": 12345,
    "spacing": 10,
    "generation_method": "fallback_rejection",
    "stage_bounds": {"width": 100, "height": 100}
  }
}
```

**Not Found Response (404):**
```json
{
  "status": "not_found",
  "theme": "forest",
  "seed": "999999"
}
```

**Example cURL:**
```bash
curl http://localhost:8080/api/aria/world/get?theme=forest&seed=12345 | jq
```

**Notes:**
- Cosmos DB lookups use the dedicated `aria_worlds` container with partition key `/theme_seed` for point-read efficiency.
- Fallback to filesystem if Cosmos is disabled or document not found.
- Filesystem search scans `data_out/aria_worlds/` for matching `world_<theme>_*_<seed>.json` files.

### GET `/api/aria/world/list`
List persisted world JSON files and report Cosmos availability.

**Sample Response:**
```json
{
  "status": "success",
  "worlds": [
    {"file": "data_out/aria_worlds/world_forest_20251128_172000_12345.json", "theme": "forest", "seed": "12345"}
  ],
  "cosmos": {
    "available": true,
    "count": 3,
    "worlds": [
      {"id": "world-space-456", "theme": "space", "seed": 456, "objectCount": 8, "generationMethod": "llm", "createdUtc": "2025-11-29T09:30:00Z"}
    ]
  }
}
```

**Notes:**
- Returns **both** filesystem snapshots and Cosmos metadata (if enabled).
- Cosmos enumeration queries the dedicated `aria_worlds` container with lightweight projections (id, theme, seed, objectCount, generationMethod, createdUtc).
- Use the `seed` and `theme` values to fetch complete worlds via `/api/aria/world/get` or regenerate identical layouts on demand.

## Cosmos DB Integration

The Aria world generation system supports optional cloud persistence via **Azure Cosmos DB**.

### Container Schema

**Container Name**: `aria_worlds` (configurable via `COSMOS_WORLDS_CONTAINER` env var)  
**Partition Key**: `/theme_seed` (format: `<theme>_<seed>`, e.g., `forest_12345`)  
**Document Structure**:
```json
{
  "id": "world-forest-12345",
  "theme_seed": "forest_12345",
  "theme": "forest",
  "seed": 12345,
  "objectCount": 6,
  "objects": { ... },
  "environment": { ... },
  "createdUtc": "2025-11-29T10:00:00Z",
  "generationMethod": "fallback_rejection",
  "type": "aria_world"
}
```

### Setup

**Required Environment Variables**:
```bash
QAI_ENABLE_COSMOS=true
COSMOS_ENDPOINT=https://<account>.documents.azure.com:443/
COSMOS_KEY=<primary-key>
COSMOS_DATABASE=qai                # default
COSMOS_WORLDS_CONTAINER=aria_worlds  # default
```

**Container Creation**:
- Container is **auto-created** on first use with partition key `/theme_seed`.
- Default throughput: 400 RU/s (autoscale recommended for production).

**Cost Optimization**:
- Point reads (by theme+seed): **1 RU** per retrieval.
- Writes (upsert): ~5-10 RU depending on document size.
- Cross-partition list queries: ~10 RU per page.
- Optional: Enable **TTL** for ephemeral worlds (e.g., 30 days).

### Graceful Degradation

All Cosmos DB operations are **non-blocking**:
- If Cosmos is disabled or unavailable, world generation continues using filesystem persistence only.
- Retrieval APIs (`/api/aria/world/get`) automatically fallback to filesystem snapshots if Cosmos lookup fails.
- Listing APIs (`/api/aria/world/list`) show filesystem entries even if Cosmos is down.

### Migration from Legacy Container

Previous implementation used the `chat_sessions` container with partition key `/userId` and a workaround field `userId: "worlds"`. This has been **replaced** with the dedicated `aria_worlds` container using partition key `/theme_seed` for:
- High-cardinality partitioning (unique per world).
- Point-read efficiency (fetch by theme+seed in 1 RU).
- Clean separation from chat/session data.

Existing worlds in the old container will not be automatically migrated; regenerate worlds or manually copy documents if needed.


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
