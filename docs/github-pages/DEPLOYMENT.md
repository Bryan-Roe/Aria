# GitHub Pages Deployment Guide

## Overview
The Aria Quantum AI System web hub is now configured for **GitHub Pages deployment**. This guide explains how to deploy and use the web pages on GitHub Pages.

## Current GitHub Pages Features

### ✅ Fully Compatible with GitHub Pages
- **Web Hub** (`web-hub.html`) — Main navigation hub with all interfaces
- **Static Content** — All HTML, CSS, and JavaScript files work on GitHub Pages
- **Responsive Design** — Fully responsive across all devices
- **Environment Detection** — Automatically detects local development vs. GitHub Pages deployment

### ⚠️ Local Development Services (Not Available on GitHub Pages)
The following services require local development environment:
- **Azure Functions API** (port 7071)
- **Aria Server** (port 8080)
- **Dashboard Server** (port 8765)

When deployed to GitHub Pages, these services are not accessible, but the web pages provide helpful guidance and instructions.

## Deploying to GitHub Pages

### Option 1: Using GitHub's Settings (Recommended)

1. **Push to GitHub**
   ```bash
   git add .nojekyll web-hub.html
   git commit -m "feat: Update web hub for GitHub Pages deployment"
   git push origin main
   ```

2. **Enable GitHub Pages**
   - Go to your repository on GitHub
   - Click **Settings** → **Pages**
   - Under "Source", select the branch (`main` or `develop`)
   - Select the directory (usually `/` for root)
   - Click **Save**

3. **Wait for deployment**
   - GitHub will build and deploy your site in 1-2 minutes
   - Your site will be available at: `https://username.github.io/repository-name/`

### Option 2: Using GitHub Actions (Advanced)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./
          cname: aria.yoursite.com  # Optional: Use custom domain
```

## What Works on GitHub Pages

| Feature | Status | Notes |
|---------|--------|-------|
| Web Hub Navigation | ✅ Working | All interface links functional |
| Aria Interface | ✅ Working | Opens `/aria_web/index.html` |
| Chat Interface | ✅ Working | Opens `/chat-web/index.html` |
| Quantum Pages | ✅ Working | All quantum interfaces accessible |
| Dashboards | ✅ Working | All dashboard pages available |
| CSS & Design | ✅ Working | Glassmorphism effects, animations |
| Documentation Links | ⚠️ Limited | Markdown files require local access |
| API Status Check | ⚠️ Limited | Shows instructions for local development |
| Local Service Links | ⚠️ Limited | Display helpful setup instructions |

## What Requires Local Development

The following require the **full development environment** (not available on GitHub Pages):

### API Services
- Health checks (`/api/ai/status`)
- Chat endpoints (`/api/chat`)
- Quantum operations (`/api/quantum/*`)
- Text-to-speech (`/api/tts`)

### Dashboard Servers
- Dashboard Server (port 8765)
- Training monitors
- Real-time metrics

### Aria Services
- Aria Web Server (port 8080)
- Auto-execute planner
- Real-time character control

## Local Development vs. GitHub Pages

### Development Environment
```bash
# Start all services locally
func host start                                    # Azure Functions (7071)
cd aria_web && python server.py                  # Aria Server (8080)
python scripts/monitoring/vs_code_server.py      # Dashboard (8765)

# Access locally
open http://localhost/web-hub.html               # Or your local server
```

### GitHub Pages Deployment
```bash
# Push to GitHub
git push origin main

# Access online
open https://username.github.io/repository-name/web-hub.html
```

**The web pages automatically detect which environment you're in and adjust accordingly!**

## Key Files for GitHub Pages

| File | Purpose |
|------|---------|
| `/index.html` | Root redirect to web-hub.html |
| `/web-hub.html` | Main navigation hub (GitHub Pages compatible) |
| `/.nojekyll` | Prevents Jekyll processing (required) |
| `/aria_web/index.html` | Aria interface (accessible on GitHub Pages) |
| `/chat-web/index.html` | Chat interface (accessible on GitHub Pages) |
| `/dashboard/index.html` | Dashboard (accessible on GitHub Pages) |

## URL Structure on GitHub Pages

```
https://username.github.io/repository-name/
├── web-hub.html                  (Main hub)
├── index.html                     (Redirects to web-hub.html)
├── aria_web/
│   ├── index.html
│   ├── quantum-portal.html
│   ├── quantum-world.html
│   └── ...
├── chat-web/
│   ├── index.html
│   └── ...
└── dashboard/
    ├── index.html
    └── ...
```

## Setting Up a Custom Domain (Optional)

To use a custom domain instead of `github.io`:

1. **Add CNAME file**
   ```bash
   echo "aria.yourdomain.com" > CNAME
   git add CNAME
   git commit -m "Add custom domain"
   git push
   ```

2. **Configure DNS**
   - Add CNAME record: `aria` → `username.github.io`
   - Or A records for GitHub Pages IPs
   - See [GitHub Pages Custom Domain Docs](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site)

3. **Enable in GitHub**
   - Settings → Pages → Custom domain: `aria.yourdomain.com`

## Environment Detection

The web hub automatically detects your environment:

```javascript
isGitHubPages = window.location.hostname.includes('github.io')
isLocalhost = window.location.hostname === 'localhost' || '127.0.0.1'
```

### Behavior by Environment

**Local Development (`localhost:8000`)**
- All links work as-is
- API status checks functional
- Local service links accessible
- Documentation accessible

**GitHub Pages (`username.github.io`)**
- Navigation links work normally
- API status shows setup instructions
- Local service links show helpful guidance
- Documentation accessible in your local repo

## Troubleshooting

### Pages not loading?
1. Ensure `.nojekyll` file exists in repository root
2. Check GitHub Pages is enabled in Settings → Pages
3. Verify branch is set correctly
4. Wait 2-3 minutes for initial deployment

### Links are broken?
- All relative paths are repository-relative
- Links like `aria_web/index.html` work automatically
- No need to add `/repository-name/` prefix

### CSS/JavaScript not loading?
- Check `.nojekyll` file exists
- Verify files are committed and pushed
- Clear browser cache and hard refresh (Ctrl+Shift+R or Cmd+Shift+R)

### API links showing instructions instead of connecting?
- This is expected on GitHub Pages
- API services are only available in local development
- Follow the instructions shown to set up local environment

## Next Steps

1. **Deploy to GitHub Pages** following Option 1 or 2 above
2. **Share your link**: `https://username.github.io/repository-name/`
3. **For full functionality**: Set up local development environment
4. **Feedback**: Issues with specific pages? Create an issue in your repository

## Resources

- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [GitHub Pages Custom Domain](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site)
- [Jekyll Configuration](https://jekyllrb.com/docs/configuration/) (if needed)
- [Local Testing with GitHub Pages](https://docs.github.com/en/pages/setting-up-a-github-pages-site-with-jekyll/testing-your-github-pages-site-locally-with-jekyll)

---

**Last Updated**: January 24, 2026
**GitHub Pages Status**: ✅ Ready for Deployment
