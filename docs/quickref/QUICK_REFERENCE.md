# 🚀 Aria Chat Quick Reference

## Start Here (90 seconds)

### Step 1: Start Backend

```bash
cd /workspaces/Aria
func host start
# Runs on http://localhost:7071
```

### Step 2: Open Site

```bash
# Option A: Direct file
open docs/index.html

# Option B: Web server
python -m http.server 8000
# Then visit http://localhost:8000/docs/
```

### Step 3: Configure & Chat

1. Keep server URL: `http://localhost:7071`
2. Click "Test Connection"
3. Type message
4. Press Enter or click Send

## File Locations

| File                         | Purpose               | Access                            |
| ---------------------------- | --------------------- | --------------------------------- |
| `docs/index.html`            | Main site             | Browser / GitHub Pages            |
| `function_app.py`            | Backend API           | `func host start`                 |
| `docs/GITHUB_PAGES_SETUP.md` | Full setup guide      | Read in editor                    |
| `docs/README_PAGES.md`       | Configuration options | Read in editor                    |
| `scripts/fast_validate.py`   | Verify setup          | `python scripts/fast_validate.py` |

## Common Commands

```bash
# Verify setup
python scripts/fast_validate.py

# Run backend
func host start

# Run static server
python -m http.server 8000

# Test API endpoint
curl http://localhost:7071/api/ai/status

# Check logs (after running)
cat data_out/chat.log
```

## Deployment Checklist

- [ ] **Local Test**: Can chat with function_app on localhost
- [ ] **Deploy Backend**: `func azure functionapp publish <app-name>`
- [ ] **Get Azure URL**: Copy from Azure Portal
- [ ] **Update Server URL**: Edit docs/index.html or use param
- [ ] **Enable GitHub Pages**: Settings → Pages → /docs folder
- [ ] **Test Production**: Open GitHub Pages URL
- [ ] **Share URL**: `https://yourusername.github.io/Aria/`

## Server URLs by Scenario

| Scenario               | Server URL                           |
| ---------------------- | ------------------------------------ |
| Local development      | `http://localhost:7071`              |
| Azure Functions        | `https://your-app.azurewebsites.net` |
| GitHub Pages parameter | `?server=https://...`                |
| Docker container       | `http://localhost:8080`              |

## Providers

| Provider     | Setup                     | Speed      | Cost         |
| ------------ | ------------------------- | ---------- | ------------ |
| LMStudio     | LMSTUDIO_BASE_URL env var | ⚡ Fastest | Free (local) |
| Azure OpenAI | AZURE\_\* env vars        | ⚡ Fast    | Paid         |
| OpenAI       | OPENAI_API_KEY env var    | ⚡ Fast    | Paid         |
| Local Echo   | None                      | ⚡ Instant | Free         |

## Troubleshooting 30-Second Fixes

| Problem              | Fix                                |
| -------------------- | ---------------------------------- |
| "Can't connect"      | `func host start` running?         |
| "Wrong URL"          | Default is `http://localhost:7071` |
| "No response"        | Click "Test Connection"            |
| "Streaming stops"    | Check function_app logs            |
| "History disappears" | Disable incognito mode             |

## Performance Tips

- **Fastest Setup**: LMStudio local mode
- **Best Quality**: Azure OpenAI
- **No Cost**: Local echo mode
- **Responsive UI**: Use temperature 0.5-0.7

## URLs to Remember

```text
Local Dev:     http://localhost:7071
Static Site:   http://localhost:8000/docs/
Production:    https://yourusername.github.io/Aria/
Azure Backend: https://your-app.azurewebsites.net
```

## Key Features

✨ Animated Aria character
💬 Real-time streaming chat
🔌 Multi-provider LLM support
📱 Responsive (desktop & mobile)
💾 Chat history persistence
⚙️ Provider selector
🌡️ Temperature control
🧪 Connection test button

## Documentation

| Guide                              | Purpose                    |
| ---------------------------------- | -------------------------- |
| GITHUB_PAGES_SETUP.md              | Complete setup walkthrough |
| SERVER_CONFIGURATION.md            | All deployment scenarios   |
| verify_aria_chat.py                | Automated verification     |
| ARIA_CHAT_GITHUB_PAGES_COMPLETE.md | Full project summary       |

## One-Liners

```bash
# Verify all components
python verify_aria_chat.py && echo "✓ Ready to go!"

# Run backend + open site
(func host start &) && sleep 2 && open docs/index.html

# Deploy to Azure
func azure functionapp publish MyApp && echo "✓ Live!"

# Test connection
curl -s http://localhost:7071/api/ai/status | python -m json.tool
```

## Status Codes

| Code               | Meaning      | Action                  |
| ------------------ | ------------ | ----------------------- |
| 200                | Success      | Proceed normally        |
| 400                | Bad request  | Check message format    |
| 404                | Not found    | Wrong endpoint/URL      |
| 500                | Server error | Check function_app logs |
| Connection refused | Backend down | Run `func host start`   |

---

**Quick Links**:

- 📖 [Full Setup Guide](../GITHUB_PAGES_SETUP.md)
- ⚙️ [Configuration Guide](../README_PAGES.md)
- 🎯 [Project Complete](../summaries/GITHUB_PAGES_SETUP_SUMMARY.md)
- ✅ [Verify Setup](../../scripts/fast_validate.py)

**Status**: ✅ Ready to Use
**Last Updated**: January 23, 2026
