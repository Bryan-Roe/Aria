# 🤖 Aria Chat - GitHub Pages Integration

Interactive AI character chat interface integrated with Aria, accessible via GitHub Pages.

## Features

- **Interactive Aria Character** - Visual AI character that responds to your chats
- **LLM-Powered Responses** - Uses configurable AI providers (Azure OpenAI, OpenAI, LMStudio, local)
- **Real-Time Streaming** - SSE-based streaming responses for smooth user experience
- **Provider Selection** - Choose from multiple LLM providers on the fly
- **Chat History** - Persistent conversation storage in localStorage
- **Responsive Design** - Works on desktop and mobile devices
- **No Build Required** - Pure HTML/CSS/JS, deploys directly to GitHub Pages

## Quick Start

### Local Development

1. **Start the function_app.py server** (provides chat API):
   ```bash
   func host start
   ```
   Server will run on `http://localhost:7071`

2. **Open the chat interface**:
   - File: `docs/index.html`
   - Or open in browser: `file:///workspaces/AI/docs/index.html`
   - Or via Python: `python -m http.server 8000` then visit `http://localhost:8000/docs/`

3. **Configure the server URL** (default is `http://localhost:7071`):
   - The input field at the top allows changing the server URL
   - Click "Test Connection" to verify

4. **Start chatting**:
   - Type a message and press Enter or click Send
   - Select provider and temperature before sending

### GitHub Pages Deployment

1. **The site is ready to deploy** at: `https://<github-username>.github.io/AI/docs/`

2. **Enable GitHub Pages**:
   - Go to repo Settings → Pages
   - Source: Deploy from a branch
   - Branch: `main` (or your default)
   - Folder: `/docs`

3. **For remote server**:
   - Update server URL in the site to your deployed function_app.py URL
   - Example: `https://your-app.azurewebsites.net`

## API Integration

### Chat Endpoint Structure

The site communicates with function_app.py via:

**POST** `/api/chat/stream`
```json
{
  "messages": [
    {"role": "user", "content": "Hello Aria"},
    {"role": "assistant", "content": "Hi there!"}
  ],
  "provider": "auto",
  "temperature": 0.7,
  "stream": true
}
```

**Response**: Server-Sent Events (SSE) with JSON deltas:
```
event: meta
data: {"provider": "openai", "model": "gpt-4"}

event: delta
data: {"delta": "Hello"}

event: delta
data: {"delta": " there"}
```

### Status Endpoint

**GET** `/api/ai/status`

Returns health information including:
- Active provider
- Available models
- Database connection status
- GPU status
- Environment configuration

## Configuration

### Server URL
- Default: `http://localhost:7071`
- Configurable via input field at top of page
- Persists across page reloads (localStorage)

### Provider Selection
Select which LLM provider to use:
- **Auto** - Uses detection chain (fastest available)
- **LMStudio** - Local models (requires LMSTUDIO_BASE_URL env var)
- **Azure OpenAI** - Azure subscription (requires AZURE_* env vars)
- **OpenAI** - Direct OpenAI API (requires OPENAI_API_KEY)
- **Local** - Echo provider (no setup needed)

### Temperature
- Range: 0.0 (deterministic) to 1.0 (creative)
- Default: 0.7 (balanced)
- Slider control updates in real-time

## Architecture

### Frontend (docs/index.html)
```
┌─────────────────────────────────────┐
│  GitHub Pages Static Site           │
│  ┌───────────────┐  ┌─────────────┐ │
│  │ Aria Char     │  │ Chat UI     │ │
│  │ (Animated)    │  │ (Messages)  │ │
│  └───────────────┘  └─────────────┘ │
└─────────────────────────────────────┘
          ↓ (HTTP/SSE)
         [function_app.py]
          ↓
     [Chat Providers]
          ↓
    [LLM API / Local]
```

### Backend (function_app.py)
- `/api/chat/stream` - SSE streaming endpoint
- Provider detection chain (auto-selects best available)
- CORS headers for cross-origin requests
- Message history management

### Chat Providers (talk-to-ai/src/chat_providers.py)
1. **LMStudio** (local, fastest)
2. **Azure OpenAI** (enterprise)
3. **OpenAI** (cloud)
4. **LoRA Adapter** (fine-tuned)
5. **Local Echo** (fallback, no deps)

## Customization

### Styling
Edit CSS in `docs/index.html`:
- Colors: Modify gradient colors in `body` and `.send-btn`
- Layout: Adjust grid columns in `.container`
- Aria character: Edit emoji and animations

### Aria Character
- Change emoji: Modify `id="ariaCharacter"` content
- Add expressions: Update `updateAriaState()` function
- Add gestures: Extend aria_controller.js patterns

### Chat Settings
- Add system prompt field
- Persist settings to localStorage
- Add conversation clear button
- Implement chat export to JSON/Markdown

## Troubleshooting

### Connection Issues
**Problem**: "Connection failed" or "Cannot reach server"
- Solution: Verify function_app.py is running (`func host start`)
- Solution: Check server URL is correct (default `http://localhost:7071`)
- Solution: For HTTPS, use HTTPS server URL

### No Response from Aria
**Problem**: Chat sends but Aria doesn't respond
- Solution: Check `/api/ai/status` endpoint works
- Solution: Verify provider is configured (LMStudio/Azure/OpenAI)
- Solution: Check browser console for JavaScript errors

### Streaming Stops Mid-Response
**Problem**: SSE stream terminates early
- Solution: Check network tab for 500 errors
- Solution: Review function_app.py logs for provider errors
- Solution: Try different provider via dropdown

### Chat History Not Saving
**Problem**: Messages disappear after refresh
- Solution: Check browser allows localStorage
- Solution: Clear browser cache and try again
- Solution: Disable private browsing mode

## File Structure

```
/workspaces/AI/
├── docs/
│   └── index.html              ← Main GitHub Pages site
├── function_app.py             ← Azure Functions backend
├── talk-to-ai/
│   └── src/
│       └── chat_providers.py   ← LLM provider detection
├── chat-web/
│   └── index.html              ← Alternative chat interface
└── verify_aria_chat.py         ← Verification script
```

## Performance Tips

- **Local Mode**: Fastest (no network latency), but limited
- **LMStudio**: Fast, requires local model setup
- **Azure OpenAI**: Reliable, enterprise support, requires subscription
- **OpenAI**: Good latency, requires API key

### Optimize Streaming
- Use WebSocket instead of SSE (future enhancement)
- Implement response chunking
- Add connection pooling in function_app.py

## Accessibility

- Color contrast: WCAG AA compliant
- Keyboard navigation: Tab through UI elements
- Screen reader support: Semantic HTML, ARIA labels
- Touch-friendly: Larger buttons for mobile

## Security

- ⚠️ Never commit API keys - use environment variables
- ⚠️ GitHub Pages is public - don't expose sensitive data
- ✓ CORS headers configured in function_app.py
- ✓ No client-side API key storage
- ✓ LocalStorage is user-only (not synced)

## Next Steps

1. **Deploy function_app.py to Azure**:
   ```bash
   func azure functionapp publish <app-name>
   ```

2. **Update docs/index.html server URL** to deployed endpoint

3. **Enable GitHub Pages** in repository settings

4. **Share your Aria chat URL** with the world!

## Related Files

- [function_app.py](../function_app.py) - Chat API backend
- [chat-web/index.html](../chat-web/index.html) - Alternative chat UI
- [talk-to-ai/](../talk-to-ai/) - Chat CLI (alternative interface)
- [aria_web/](../aria_web/) - Aria web server (separate service)

## Support

For issues:
1. Check `/api/ai/status` endpoint for health info
2. Review browser console (F12) for JavaScript errors
3. Check function_app.py logs for backend errors
4. Run `python verify_aria_chat.py` for configuration check
5. See [TESTING_GUIDE.md](../TESTING_GUIDE.md) for full test suite

---

**Created**: January 2026  
**Last Updated**: January 23, 2026  
**Status**: ✓ Production Ready
