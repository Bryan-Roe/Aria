# Chat Web Application

A modern, responsive web-based chat interface that works with multiple AI providers.

## Features

- 🎨 Beautiful, responsive UI with gradient design
- 💬 Real-time chat with AI assistants
- 🔄 Support for multiple providers (Local, LM Studio, Ollama, OpenAI, Azure OpenAI)
- 🆓 Free local mode (no API keys required)
- 🌐 Accessible via web browser

## Quick Start (Free Local Mode)

No API keys or cloud services required:

```powershell
# 1. Install dependencies
cd c:\Users\Bryan\OneDrive\AI
pip install azure-functions colorama

# 2. Start the Azure Functions local server
func start

# 3. Open your browser to http://localhost:7071/api/chat-web
```

The chat will work immediately with the free local provider!

## Architecture

- **Frontend**: `apps/chat/` - Pure HTML/CSS/JS, no build required
- **Backend**: `function_app.py` - Azure Functions endpoint
- **Chat Logic**: Reuses `ai-projects/chat-cli/src/chat_providers.py`

## Provider Configuration

### Local (Free - Default)
No configuration needed! Works offline.

### OpenAI
Set environment variable:
```powershell
$env:OPENAI_API_KEY = "sk-..."
```

### Azure OpenAI
Set environment variables:
```powershell
$env:AZURE_OPENAI_API_KEY = "your-key"
$env:AZURE_OPENAI_ENDPOINT = "https://your-resource.openai.azure.com/"
$env:AZURE_OPENAI_DEPLOYMENT = "gpt-4o-mini"
$env:AZURE_OPENAI_API_VERSION = "2024-08-01-preview"
```

The backend auto-detects the best available provider.

Auto-detection order in runtime:

1. LM Studio (if reachable)
2. Ollama (if reachable)
3. Azure OpenAI (if env is complete)
4. OpenAI (if key is set)
5. Local fallback

## API Endpoint

**POST** `/api/chat`

Request:
```json
{
    "messages": [
        {"role": "user", "content": "Hello!"}
    ],
    "provider": "auto",
    "model": null
}
```

Response:
```json
{
    "response": "Hi! How can I help you?",
    "provider": "local",
    "model": "local-echo"
}
```

## Development

### Local Testing
```powershell
# Terminal 1: Start Functions
func start

# Terminal 2: Test API
$body = @{
    messages = @(@{role="user"; content="Test"})
} | ConvertTo-Json -Depth 3

Invoke-RestMethod -Uri http://localhost:7071/api/chat -Method POST -Body $body -ContentType "application/json"
```

### Deployment to Azure

1. **Create Function App** (Azure Portal or CLI):
   ```powershell
   az functionapp create --resource-group rg-chat --name chat-app-unique-name --consumption-plan-location eastus --runtime python --runtime-version 3.11 --functions-version 4 --storage-account mystorageaccount
   ```

2. **Configure Settings** (if using cloud providers):
   ```powershell
   az functionapp config appsettings set --name chat-app-unique-name --resource-group rg-chat --settings OPENAI_API_KEY=sk-...
   ```

3. **Deploy**:
   ```powershell
   cd http_chat
   func azure functionapp publish chat-app-unique-name
   ```

4. **Deploy Static Web** (optional):
   - Upload `chat-web/` to Azure Static Web Apps or Blob Storage
   - Update `chat.js` `API_BASE` to your Function App URL

## Troubleshooting

**"Module not found" errors:**
```powershell
pip install azure-functions colorama
cd ai-projects/chat-cli
pip install -r requirements.txt
```

**CORS errors in browser:**
The function includes CORS headers. If testing locally, ensure you're accessing via `http://localhost:7071`.

**Provider errors:**
Check environment variables and ensure `ai-projects/chat-cli/src/chat_providers.py` is accessible.

## Cost Optimization

- **Free tier**: Use local provider (default, unlimited)
- **Paid tier**: OpenAI/Azure charges per token
  - Monitor usage in provider dashboards
  - Set rate limits on API keys
  - Use cheaper models (gpt-4o-mini vs gpt-4)

## Files Structure

```
chat-web/
  index.html          # Main UI
  chat.js            # Frontend logic

http_chat/
  function_app.py    # Azure Functions endpoint

ai-projects/chat-cli/src/
  chat_providers.py  # Provider implementations (shared)
```

## License

Part of the QAI project. See root README for details.
