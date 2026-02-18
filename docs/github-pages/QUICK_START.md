# GitHub Pages Quick Reference

## 🚀 One-Minute Deployment

```bash
# 1. Commit your changes
git add .nojekyll web-hub.html GITHUB_PAGES_DEPLOYMENT.md
git commit -m "Deploy: Prepare web hub for GitHub Pages"

# 2. Push to GitHub
git push origin main

# 3. Enable GitHub Pages
# Go to: Settings → Pages → Select main branch → Save
# Your site will be live in 1-2 minutes at:
# https://username.github.io/repository-name/
```

## 📱 What Works

| Feature | Deployed | Local |
|---------|----------|-------|
| Web Hub Navigation | ✅ | ✅ |
| All Interface Links | ✅ | ✅ |
| CSS & Design | ✅ | ✅ |
| API Checks | ⚠️ Info Only | ✅ Works |
| Local Services | ⚠️ Instructions | ✅ Works |
| Markdown Docs | ⚠️ In Repo | ✅ Works |

## 🔧 Local Development

When you want full functionality with APIs and services:

```bash
# Start services (in separate terminals)
func host start                               # Azure Functions
cd aria_web && python server.py              # Aria Server
python scripts/monitoring/vs_code_server.py  # Dashboard

# Access locally
open http://localhost/web-hub.html
```

## 📚 Key Files

```
/web-hub.html                         Main hub
/index.html                           Auto-redirect
/.nojekyll                            GitHub Pages config
/GITHUB_PAGES_DEPLOYMENT.md           Full deployment guide
/WEB_PAGES_NAVIGATION.md              Navigation structure
```

## ⚙️ Configuration

The web hub **automatically detects** your environment:
- **GitHub Pages**: Shows instructions for local services
- **Local Development**: All links work directly
- **Local Server**: Works with relative paths

No manual configuration needed!

## 🆘 Troubleshooting

**Pages not showing up?**
→ Wait 2-3 minutes, refresh, check Settings → Pages is enabled

**Broken links?**
→ All relative paths are correct, hard refresh browser (Ctrl+Shift+R)

**CSS not loading?**
→ Ensure `.nojekyll` file exists in root

## 📖 Full Guide

See `GITHUB_PAGES_DEPLOYMENT.md` for detailed instructions.

---
**Status**: ✅ Ready for GitHub Pages Deployment
