<!--
    Aria Chat Configuration Guide
    ==============================
    
    This file explains how to configure the Aria chat interface to connect
    to the function_app.py backend for different deployment scenarios.
-->

# Aria Chat Server Configuration

## Scenarios

### 1. Local Development (Default)

**Server Running**: `func host start` (port 7071)

**Configuration**:
- Server URL: `http://localhost:7071`
- Provider: `auto` (uses best available)
- No API keys needed for local testing

**Steps**:
1. Open `docs/index.html` in browser
2. Keep server URL as `http://localhost:7071`
3. Click "Test Connection"
4. Start chatting

---

### 2. Azure Functions Deployment

**Server Running**: Azure App Service (HTTPS)

**Configuration**:
- Server URL: `https://<your-app>.azurewebsites.net`
- Provider: Configured via Azure App Settings
- Chat history: Persisted in localStorage (local to browser)

**Steps**:
1. Deploy function_app.py to Azure
   ```bash
   func azure functionapp publish <app-name>
   ```

2. Find your function URL:
   - Go to Azure Portal
   - Find your Function App
   - Copy the URL from Overview (e.g., `https://myapp.azurewebsites.net`)

3. Update `docs/index.html` server URL:
   - Option A: Manually edit in browser each time
   - Option B: Create a config file (see below)
   - Option C: Use environment variable (CI/CD)

4. Enable CORS in function_app.py (already configured)

---

### 3. Local HTTP Server for Testing

**Server Running**: `python -m http.server 8000`

**Configuration**:
- Function Server: `http://localhost:7071` (from func host)
- Website Server: `http://localhost:8000` (for HTML)
- Both servers must be running

**Steps**:
1. Terminal 1: Start function_app
   ```bash
   func host start
   ```

2. Terminal 2: Start HTTP server
   ```bash
   cd /workspaces/AI && python -m http.server 8000
   ```

3. Open browser: `http://localhost:8000/docs/`
4. Keep server URL as `http://localhost:7071`

---

### 4. GitHub Pages + Azure Functions

**Server Running**: Azure Functions (HTTPS) + GitHub Pages

**Configuration**:
- Website: `https://<username>.github.io/AI/docs/`
- Function Server: `https://<your-app>.azurewebsites.net`
- Must use HTTPS for mixed content policy

**Steps**:
1. Deploy Azure Functions
2. Enable GitHub Pages (Settings → Pages → Deploy from /docs)
3. Configure server URL in `docs/index.html` to Azure endpoint
4. OR add parameter to URL:
   ```
   https://username.github.io/AI/docs/?server=https://myapp.azurewebsites.net
   ```

---

### 5. Docker Container Deployment

**Server Running**: Docker container with both services

**Dockerfile Example**:
```dockerfile
FROM mcr.microsoft.com/azure-functions/python:4-python3.11

# Install function dependencies
WORKDIR /home/site/wwwroot
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy source
COPY function_app.py .
COPY talk-to-ai/src/ ./talk-to-ai/src/
COPY shared/ ./shared/
COPY quantum-ai/src/ ./quantum-ai/src/

# Copy static assets
COPY docs/ ./docs/

EXPOSE 8080
CMD ["func", "host", "start", "--port", "8080", "--no-auth"]
```

**Configuration**:
- Website: `http://localhost/docs/`
- Function Server: `http://localhost:8080` (or HTTPS if behind proxy)

---

## URL Configuration Methods

### Method 1: Manual (Browser Input Field)

Simplest for development:
1. Open `docs/index.html`
2. Edit input at top: `http://localhost:7071`
3. Click "Test Connection"

### Method 2: URL Parameter (Best for Sharing)

Share a pre-configured link:
```
https://username.github.io/AI/docs/?server=https://myapp.azurewebsites.net
```

To implement, add this to `docs/index.html`:
```javascript
// After page load
const urlParams = new URLSearchParams(window.location.search);
const serverUrl = urlParams.get('server');
if (serverUrl) {
    document.getElementById('serverUrl').value = serverUrl;
}
```

### Method 3: Environment Variable (CI/CD)

For automated deployment:
```bash
# During build
sed -i 's|http://localhost:7071|'${FUNCTION_URL}'|g' docs/index.html
```

### Method 4: Configuration File (Advanced)

Create `docs/config.json`:
```json
{
  "server": "https://myapp.azurewebsites.net",
  "provider": "auto",
  "temperature": 0.7,
  "maxContextTokens": 4096
}
```

Load in JavaScript:
```javascript
fetch('config.json')
    .then(r => r.json())
    .then(config => {
        document.getElementById('serverUrl').value = config.server;
        document.getElementById('provider').value = config.provider;
        document.getElementById('temperature').value = config.temperature;
    });
```

---

## Provider Configuration

Each provider requires specific setup in function_app.py environment:

### LMStudio (Local)
```bash
export LMSTUDIO_BASE_URL=http://localhost:1234
```

### Azure OpenAI
```bash
export AZURE_OPENAI_API_KEY=your-key
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
export AZURE_OPENAI_DEPLOYMENT=gpt-4
export AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

### OpenAI
```bash
export OPENAI_API_KEY=sk-...
```

### Enable Local TTS
```bash
export QAI_ENABLE_LOCAL_TTS=true
```

---

## Debugging Connection Issues

### Test 1: Frontend is Loading
- [ ] Can see Aria character
- [ ] Can see chat UI
- [ ] Can edit server URL
- [ ] Browser console has no errors (F12)

### Test 2: Backend is Reachable
- [ ] Click "Test Connection"
- [ ] Check network tab (F12 → Network)
- [ ] Should see response from `/api/ai/status`

### Test 3: Chat Endpoint Works
- [ ] Send a test message
- [ ] Check network tab for POST to `/api/chat/stream`
- [ ] Should see 200 status and SSE stream
- [ ] Check function_app.py logs for errors

### Test 4: Provider Detection
- [ ] Check server status response includes provider
- [ ] Try different provider from dropdown
- [ ] Check function_app.py logs for provider info

---

## Common Errors

### "Cannot reach server"
- [ ] Is function_app running? (`func host start`)
- [ ] Is URL correct? (default `http://localhost:7071`)
- [ ] Are both HTTP methods allowed (OPTIONS, POST)?
- [ ] Check CORS headers in function_app.py

### "Mixed Content" (GitHub Pages + Azure Functions)
- [ ] GitHub Pages serves HTTPS
- [ ] Function_app must also use HTTPS
- [ ] Update server URL to HTTPS endpoint

### "Streaming interrupted"
- [ ] Check function timeout (Azure default 5 min)
- [ ] Check network connection stability
- [ ] Try different provider
- [ ] Check function_app.py logs

### "Chat history not saving"
- [ ] Is localStorage enabled in browser?
- [ ] Are you in private/incognito mode?
- [ ] Clear browser cache and try again
- [ ] Check browser developer tools for errors

---

## Performance Tuning

### Fastest Local Setup
```bash
# Terminal 1
cd /workspaces/AI && func host start

# Terminal 2
# Open docs/index.html in browser with server URL http://localhost:7071
```

### Recommended for Production
- Use HTTPS everywhere (GitHub Pages + Azure Functions)
- Set temperature to 0.5-0.7 for consistency
- Use Azure OpenAI for reliability (vs public OpenAI)
- Monitor `/api/ai/status` for health

### Scaling Considerations
- Function_app horizontal scaling (Azure App Service plan)
- Chat persistence (optional SQL via `QAI_DB_CONN`)
- Message caching for popular questions
- WebSocket instead of SSE (future)

---

## File References

- Main site: [docs/index.html](index.html)
- Backend: [function_app.py](../function_app.py)
- Setup guide: [GITHUB_PAGES_SETUP.md](GITHUB_PAGES_SETUP.md)
- Verification: [verify_aria_chat.py](../verify_aria_chat.py)

---

**Last Updated**: January 23, 2026
