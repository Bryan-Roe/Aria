# Chat Website - Complete Guide

## 🎉 Your AI Chat Website is Ready!

I've created a beautiful, responsive chat website that works with multiple AI providers.

## 🚀 Quick Start

The server is already running! Open your browser to:

**http://localhost:7071/api/chat-web**

Or run the startup script:
```powershell
.\start-chat-web.ps1
```

## ✨ Features

- **Beautiful UI**: Gradient design with smooth animations
- **Multiple Providers**: Local (free), OpenAI, Azure OpenAI
- **Real-time Chat**: Instant responses with typing indicators
- **Responsive**: Works on desktop and mobile
- **Zero Config**: Works immediately with free local provider

## 🏗️ Architecture

```
┌─────────────────┐
│   Browser       │
│  (chat-web/)    │
└────────┬────────┘
         │ HTTP/JSON
         ↓
┌─────────────────┐
│ Azure Functions │
│ (function_app.py)│
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Chat Providers │
│(ai-projects/chat-cli/src) │
└─────────────────┘
```

### Files Created/Modified:

1. **Frontend** (`chat-web/`)
   - `index.html` - Beautiful gradient UI
   - `chat.js` - Client-side logic
   - `README.md` - Documentation

2. **Backend** (`function_app.py`)
   - Chat API endpoint (`/api/chat`)
   - Static file serving (`/api/chat-web`, `/api/chat-web/chat.js`)
   - CORS support for local testing

3. **Utilities**
   - `start-chat-web.ps1` - One-command startup script
   - `test-chat-web.py` - Functionality tests

## 💰 Provider Options

### 1. Local (FREE - Default) ✅
- **Cost**: $0
- **Setup**: None required
- **Best for**: Testing, demos, offline use
- Works immediately without any configuration

### 2. OpenAI
- **Cost**: Pay per token (~$0.002/1K tokens for GPT-4o-mini)
- **Setup**:
  ```powershell
  $env:OPENAI_API_KEY = "sk-..."
  ```
- **Best for**: Production quality responses

### 3. Azure OpenAI
- **Cost**: Similar to OpenAI
- **Setup**:
  ```powershell
  $env:AZURE_OPENAI_API_KEY = "your-key"
  $env:AZURE_OPENAI_ENDPOINT = "https://your-resource.openai.azure.com/"
  $env:AZURE_OPENAI_DEPLOYMENT = "gpt-4o-mini"
  ```
- **Best for**: Enterprise with Azure integration

## 🔧 API Reference

### POST /api/chat

Request:
```json
{
    "messages": [
        {"role": "system", "content": "You are helpful"},
        {"role": "user", "content": "Hello!"}
    ],
    "provider": "auto",
    "model": "gpt-4o-mini"
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

### GET /api/chat-web

Serves the HTML interface

### GET /api/chat-web/chat.js

Serves the JavaScript client

## 🧪 Testing

Run the test suite:
```powershell
python .\test-chat-web.py
```

Expected output:
```
==================================================
Chat Web - Functionality Test
==================================================

Testing local provider...
✓ Provider: local, Model: local-echo
✓ Response: Quick thoughts: Hello Does that help?...
✓ Local provider working!

Testing provider auto-detection...
✓ Auto-detected: local, Model: local-echo
  (Using local fallback - no API keys)

==================================================
✅ All tests passed!
==================================================
```

## 🌐 Deploying to Azure

### Step 1: Create Function App

```powershell
# Login
az login

# Create resource group
az group create --name rg-chat-web --location eastus

# Create storage account
az storage account create --name chatwebstorage123 --resource-group rg-chat-web --location eastus --sku Standard_LRS

# Create Function App
az functionapp create `
  --resource-group rg-chat-web `
  --name chat-web-app-unique-123 `
  --storage-account chatwebstorage123 `
  --consumption-plan-location eastus `
  --runtime python `
  --runtime-version 3.11 `
  --functions-version 4 `
  --os-type Linux
```

### Step 2: Configure Environment (Optional)

If using OpenAI or Azure OpenAI:
```powershell
az functionapp config appsettings set `
  --name chat-web-app-unique-123 `
  --resource-group rg-chat-web `
  --settings OPENAI_API_KEY=sk-...
```

### Step 3: Deploy

```powershell
func azure functionapp publish chat-web-app-unique-123
```

### Step 4: Access Your App

Your chat website will be available at:
```
https://chat-web-app-unique-123.azurewebsites.net/api/chat-web
```

## 🎨 Customization

### Change Colors

Edit `chat-web/index.html`, find the gradient definitions:

```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

Replace with your colors:
```css
background: linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 100%);
```

### Change System Prompt

Edit `function_app.py`, add to the messages array:

```python
messages.insert(0, {
    "role": "system",
    "content": "You are a friendly cooking assistant."
})
```

### Add Authentication

Change `auth_level` in `function_app.py`:

```python
@app.route(route="chat", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
```

Then pass `?code=YOUR_FUNCTION_KEY` in API calls.

## 🐛 Troubleshooting

### "Cannot GET /api/chat-web"

**Problem**: Function not found
**Solution**: Ensure `func start` is running and shows all 4 functions

### CORS Errors

**Problem**: Browser blocks API calls
**Solution**: CORS headers are included. Try opening directly at `http://localhost:7071/api/chat-web`

### "Import could not be resolved"

**Problem**: Python linting errors
**Solution**: These are false positives. Run:
```powershell
pip install azure-functions colorama
cd talk-to-ai; pip install -r requirements.txt
```

### Provider Errors

**Problem**: "Configuration error" messages
**Solution**: Check environment variables match your provider choice

### Server Won't Start

**Problem**: `func start` fails
**Solution**:
1. Check Python version: `python --version` (need 3.8-3.11)
2. Install Core Tools: `npm install -g azure-functions-core-tools@4`
3. Check `local.settings.json` exists

## 📊 Monitoring

### Local Development

Watch the terminal for logs:
```
[2025-11-08T12:27:53.884Z] Chat function invoked
[2025-11-08T12:27:53.891Z] Using provider: local, model: local-echo
```

### Production (Azure)

View logs in Azure Portal:
1. Navigate to Function App
2. Click "Functions" > "chat"
3. Click "Monitor"
4. View Invocations and Application Insights

## 🔐 Security Best Practices

1. **Use Authentication** in production (set `auth_level=FUNCTION` or `ADMIN`)
2. **Set CORS** properly (replace `*` with your domain)
3. **Protect API Keys** (use Azure Key Vault for secrets)
4. **Rate Limiting** (implement in function or use API Management)
5. **Input Validation** (already implemented for message format)

## 💡 Tips

- **Free Tier**: Azure Functions has 1M free executions/month
- **Cost Control**: Use `gpt-4o-mini` instead of `gpt-4` for 60x cost reduction
- **Performance**: Enable Application Insights for monitoring
- **Scaling**: Functions auto-scale based on demand

## 📖 Next Steps

1. **Try Different Providers**: Set API keys and compare responses
2. **Customize UI**: Change colors, fonts, layout
3. **Add Features**:
   - Message history persistence
   - User authentication
   - File upload support
   - Voice input
4. **Deploy to Production**: Follow the Azure deployment guide above

## 🆘 Support

- Report issues in the main QAI repo
- Check `ai-projects/chat-cli/README.md` for provider details
- Review `.github/copilot-instructions.md` for architecture

## 🎉 Congratulations!

You now have a fully functional AI chat website that:
- ✅ Works locally without any API keys
- ✅ Supports multiple AI providers
- ✅ Has a beautiful, responsive UI
- ✅ Can be deployed to Azure in minutes
- ✅ Costs $0 in free tier mode

Enjoy chatting with AI! 🤖
