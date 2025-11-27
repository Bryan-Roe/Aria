# QAI Chat Web Page Architecture

## Overview

The QAI chat interface (`chat-web/`) implements a dual-mode architecture that supports both:
- **Standalone UI mode**: Full-featured chat interface with `chat.js` handling all UI interactions
- **Embedded mode** (reserved for future use): Minimal inline controller for streaming chat only

## Key Components

### Files

- **`index.html`** (4,300+ lines): Main HTML shell containing:
  - CSS styles for anime character, chat UI, vision preview, avatar display
  - Aria anime character container with animation
  - Chat interface (messages, input, send button)
  - Vision upload UI (button, file input, preview)
  - Avatar display container (image, close, regenerate buttons)
  - Minimal embedded controller script (streaming chat + character animation)

- **`chat.js`** (900+ lines): ES6 module responsible for:
  - All UI event wiring (send, vision upload, avatar buttons)
  - Vision image analysis via `/api/vision/infer`
  - AI avatar generation via `/api/image/generate`
  - Chat message handling (one-shot and streaming via SSE)
  - Markdown rendering with syntax highlighting
  - localStorage persistence for chat history

### Backend Endpoints

- **`/api/chat-web`**: Serves index.html
- **`/api/chat-web/chat.js`**: Serves chat.js module
- **`/api/chat`**: One-shot chat completion (POST)
- **`/api/chat/stream`**: Server-sent events streaming chat (POST)
- **`/api/vision/infer`**: Vision inference using TinyConvNet (POST)
- **`/api/image/generate`**: AI avatar generation with SVG fallback (POST)
- **`/api/ai/status`**: System diagnostics and health checks (GET)

## The ARIA_EMBEDDED Flag

### Purpose

The `window.ARIA_EMBEDDED` flag controls which code path handles UI interactions:

```html
<script>
    // Allow chat.js to wire up vision and avatar features
    // The embedded controller will handle streaming chat separately
    window.ARIA_EMBEDDED = false;
</script>
```

### Behavior

**When `ARIA_EMBEDDED = false` (current/default)**:
- `chat.js` DOMContentLoaded handler executes normally
- All UI elements wired up by `chat.js`:
  - Send button → `sendMessage()`
  - Vision upload button → `handleImageUpload()`
  - Vision clear button → `clearVisionUpload()`
  - Avatar regenerate button → `generateAriaAvatar(true)`
  - Avatar close button → `hideAriaAvatar()`
- Embedded controller only handles character animation (`ariaDance()`)
- **Recommended for standard deployment**

**When `ARIA_EMBEDDED = true` (reserved)**:
- `chat.js` detects flag and returns early from DOMContentLoaded:
  ```javascript
  if (window && window.ARIA_EMBEDDED) {
      console.log('chat.js: ARIA_EMBEDDED detected — skipping default UI wiring');
      return;
  }
  ```
- Embedded inline controller would need to implement all UI handlers
- **Use case**: Future scenarios requiring custom inline implementation
- **Current status**: Not recommended; duplicate handlers were removed from embedded script

## Architecture Decisions

### Why Dual-Mode?

1. **Modularity**: Separates concerns between character animation (embedded) and UI logic (chat.js)
2. **Flexibility**: Allows future embedded scenarios without modifying chat.js
3. **Testability**: chat.js can be tested independently as an ES6 module
4. **Performance**: Embedded controller is minimal (only character animation), reducing inline script bloat

### Why Remove Duplicate Handlers?

Originally, both `chat.js` and the embedded script implemented vision/avatar handlers. This caused:
- **Duplicate API calls**: Same action triggered twice (e.g., avatar generation)
- **State conflicts**: Two code paths managing same UI elements
- **Maintenance burden**: Changes required in two places

**Solution**: Removed duplicate handlers from embedded script. `chat.js` is now the single source of truth for:
- Vision upload/analysis (`handleImageUpload`, `clearVisionUpload`)
- Avatar generation/display (`generateAriaAvatar`, `hideAriaAvatar`)
- Chat send button (`sendMessage`)
- Markdown rendering (`renderMarkdown`)

Embedded script focuses solely on:
- Character animation (`ariaDance()`, movement, positioning)
- Chat bubble visibility (drag-and-drop if needed)

## Vision Upload Flow

### User Interaction

1. User clicks "Upload Image" button
2. Hidden file input (`<input type="file" id="visionImageInput">`) opens
3. User selects image file

### Processing (chat.js)

1. `handleImageUpload(event)` reads file via FileReader
2. Converts image to base64
3. Displays preview in `#visionPreview`
4. POSTs to `/api/vision/infer` with base64 payload
5. Receives expression classification result (label + confidence + scores)
6. Displays analysis in chat as assistant message with markdown formatting

### Backend (function_app.py)

1. `/api/vision/infer` endpoint receives base64 image
2. Decodes to PIL Image
3. Loads TinyConvNet model from `data_out/vision_training/`
4. Runs inference (FER2013 7-class expression classification)
5. Returns JSON: `{"label": "happy", "confidence": 0.87, "scores": {...}}`

## Avatar Generation Flow

### Auto-Generation

1. Page loads with `ARIA_EMBEDDED = false`
2. `chat.js` DOMContentLoaded handler sets 2-second timeout
3. Calls `generateAriaAvatar(false)` (non-regenerate)

### Manual Regeneration

1. User clicks "Regenerate" button on avatar
2. `generateAriaAvatar(true)` called
3. Adds assistant message: "✨ How do I look? I just got a fresh new appearance from the AI! 💜"

### Processing (chat.js)

1. POSTs to `/api/image/generate` with anime-style prompt:
   ```json
   {
     "prompt": "Portrait of Aria, anime-style AI assistant character, purple gradient hair, cute anime girl, friendly expression, digital art, high quality, detailed, vibrant colors, soft lighting",
     "size": "512x512",
     "style": "anime"
   }
   ```
2. Displays loading state (optional)
3. Receives image URL or base64 data
4. Sets `<img id="ariaAvatarImage" src="...">` 
5. Shows avatar container

### Fallback (SVG Gradient)

If OpenAI Images API fails (no key, quota exceeded, network error):
1. Backend generates purple gradient SVG with emoji
2. Returns as base64 data URI
3. `chat.js` displays gracefully without user-facing error

## Streaming Chat Flow

### User Sends Message

1. User types message and clicks Send (or presses Enter)
2. `sendMessage()` in `chat.js` fires
3. If streaming enabled: calls `streamResponse()`
4. Creates EventSource to `/api/chat/stream`

### Backend Processing

1. `/api/chat/stream` receives message + optional vision context
2. Calls `chat_providers.complete(messages, stream=True)`
3. Yields SSE chunks: `data: {"delta": "Hello"}\n\n`
4. Final chunk: `data: [DONE]\n\n`

### Frontend Display

1. `streamResponse()` receives SSE events
2. Appends text deltas incrementally to assistant message div
3. Calls `renderMarkdown()` after each delta for live rendering
4. On `[DONE]`, finalizes message and saves to localStorage

## Troubleshooting

### Issue: Chat UI doesn't initialize, buttons don't respond

**Symptom**: Clicking send/vision/avatar buttons has no effect, no console errors

**Diagnosis**: ARIA_EMBEDDED flag may be set incorrectly

**Fix**: Check `chat-web/index.html` around line 2507:
```html
<script>
    window.ARIA_EMBEDDED = false;  // Must be false for chat.js to wire up UI
</script>
```

**Verify**: Open browser console (F12) and check for:
```
chat.js: ARIA_EMBEDDED detected — skipping default UI wiring
```
If you see this message, flag is incorrectly `true`.

### Issue: Vision upload or avatar generation not working

**Symptom**: Clicking buttons does nothing or throws JavaScript errors

**Common Causes**:
1. **ARIA_EMBEDDED flag true**: See above fix
2. **Missing DOM elements**: Check HTML has `#visionUploadButton`, `#visionImageInput`, `#ariaAvatarRegenerate`
3. **Backend endpoint down**: Verify Functions host running with `func start`
4. **CORS errors**: Check browser console for cross-origin errors

**Debugging**:
1. Open browser console (F12)
2. Check for JavaScript errors
3. Verify network tab shows requests to `/api/vision/infer` or `/api/image/generate`
4. Test endpoints directly: `curl http://localhost:7071/api/ai/status`

### Issue: Avatar shows gradient placeholder instead of AI image

**Symptom**: Avatar displays purple gradient SVG with emoji, not generated image

**Cause**: OpenAI Images API failed (expected fallback behavior)

**Common Reasons**:
1. **No API key**: `OPENAI_API_KEY` not set in environment
2. **Quota exceeded**: Billing limit reached or rate limited
3. **Network error**: Timeout or connectivity issue

**Solution**: Check `local.settings.json` or Azure App Settings for API key:
```json
{
  "Values": {
    "OPENAI_API_KEY": "sk-..."
  }
}
```

**Verify**: Call `/api/ai/status` to see OpenAI provider status

### Issue: Chat messages not streaming, appear all at once

**Symptom**: Assistant responses don't type out incrementally

**Causes**:
1. **Browser doesn't support EventSource**: Rare, but check compatibility
2. **Backend not streaming**: Provider doesn't support streaming (e.g., local echo)
3. **Network buffering**: Proxy or CDN buffering SSE chunks

**Debugging**:
1. Check browser console for EventSource errors
2. Inspect network tab: `/api/chat/stream` should show "event-stream" type
3. Check provider in `/api/ai/status`: Azure OpenAI and OpenAI support streaming, LoRA and Local do not

### Issue: Markdown not rendering, raw markdown visible

**Symptom**: Messages show `**bold**` instead of **bold**

**Causes**:
1. **marked.js not loaded**: Check `<script src="https://cdn.jsdelivr.net/npm/marked@12.0.1/marked.min.js">`
2. **highlight.js not loaded**: Check syntax highlighting library
3. **renderMarkdown() not called**: Logic error in chat.js

**Fix**: Verify in browser console:
```javascript
typeof marked  // Should be "function"
typeof hljs    // Should be "object"
```

## Development Workflow

### Local Testing

1. Start Functions host:
   ```powershell
   func start
   ```

2. Open browser to http://localhost:7071/api/chat-web

3. Open DevTools (F12) → Console tab

4. Test features:
   - Send message → verify streaming or one-shot response
   - Upload image → verify vision analysis appears in chat
   - Check avatar → should auto-generate after 2 seconds
   - Click regenerate → should fetch new avatar and show message

### Making Changes

**To modify UI behavior**:
1. Edit `chat-web/chat.js`
2. Reload page (no restart needed, served on-demand)

**To modify HTML/CSS**:
1. Edit `chat-web/index.html`
2. Reload page

**To modify backend**:
1. Edit `function_app.py` or shared modules
2. Functions host auto-reloads (watch for reload message)

**To disable ARIA_EMBEDDED mode**:
1. Never needed in normal development
2. Only set `true` if implementing custom embedded controller

### Deployment

1. Ensure `ARIA_EMBEDDED = false` in production HTML
2. Set environment variables in Azure App Settings:
   - `AZURE_OPENAI_API_KEY` (or `OPENAI_API_KEY`)
   - `AZURE_OPENAI_ENDPOINT`
   - `AZURE_OPENAI_DEPLOYMENT`
   - Optional: `QAI_SQL_URL`, `APPLICATIONINSIGHTS_CONNECTION_STRING`

3. Deploy via:
   ```powershell
   func azure functionapp publish <app-name>
   ```

4. Test deployed app: `https://<app-name>.azurewebsites.net/api/chat-web`

## Integration Testing

### Unit Tests (chat.js)

Currently, chat.js doesn't have dedicated unit tests. Consider adding:
- Mock EventSource for streaming tests
- Mock fetch for API call tests
- DOM manipulation tests with JSDOM

### Integration Tests (backend)

Located in `tests/test_*_integration.py`:
- **test_avatar_integration.py**: Tests vision model + avatar inference
- **test_autotrain_integration.py**: Tests orchestrator with 24 passing tests
- **test_database_integration.py**: Tests memory persistence
- **test_quantum_autorun_integration.py**: Tests quantum job orchestration
- **test_sql_integration.py**: Tests SQL engine (skips without SQLAlchemy)

Run via:
```powershell
python .\scripts\test_runner.py --integration
```

### Manual Testing Checklist

- [ ] Page loads without JavaScript errors
- [ ] Aria avatar auto-generates after 2 seconds
- [ ] Send button works (streaming or one-shot based on provider)
- [ ] Vision upload button opens file picker
- [ ] Selected image shows preview
- [ ] Vision analysis appears in chat with confidence scores
- [ ] Vision clear button removes preview
- [ ] Avatar regenerate button fetches new image
- [ ] Avatar close button hides avatar container
- [ ] Markdown renders correctly (bold, code blocks, lists)
- [ ] Code syntax highlighting works
- [ ] Chat history persists across page reloads (localStorage)

## Future Enhancements

### Planned Features

1. **Voice Input**: Add microphone button for speech-to-text
2. **TTS Output**: Add speaker button to read assistant messages aloud
3. **Multi-turn Memory**: Integrate conversation memory from Cosmos DB
4. **Avatar Emotions**: Generate avatars with different expressions based on conversation context
5. **Vision Context**: Allow uploaded image to persist across multiple chat turns

### Architecture Evolution

1. **Web Components**: Refactor chat UI into reusable components
2. **TypeScript Migration**: Add type safety to chat.js
3. **Framework Integration**: Consider React/Vue wrapper for advanced features
4. **PWA Support**: Add offline capability with service workers
5. **Real-time Collaboration**: Enable multi-user chat sessions with SignalR

## Summary

The QAI chat web page uses a clean separation of concerns:
- **HTML**: Structure and embedded character animation
- **chat.js**: All UI logic, API calls, and user interactions
- **function_app.py**: Backend endpoints, AI providers, model inference

The `ARIA_EMBEDDED` flag provides flexibility for future embedded scenarios while keeping the default mode simple and maintainable. All vision upload and avatar generation features are handled by `chat.js`, with the embedded controller focusing solely on character animation.

For most use cases, **keep `ARIA_EMBEDDED = false`** and let `chat.js` do the work.

---

**Last Updated**: November 26, 2025  
**Version**: 1.0.0  
**Maintainer**: QAI Development Team
