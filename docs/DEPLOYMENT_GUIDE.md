# GitHub Pages Deployment Guide

This guide explains how the Aria project is deployed to GitHub Pages and how to maintain it.

## 📋 Overview

The Aria project uses GitHub Pages to host interactive web applications in demo mode. The deployment is automated via GitHub Actions and uses Jekyll as the static site generator.

## 🏗️ Architecture

### Repository Structure

```
Aria/
├── .github/
│   └── workflows/
│       └── pages.yml          # GitHub Actions deployment workflow
├── docs/                      # GitHub Pages root (published to web)
│   ├── index.html            # Main landing page
│   ├── _config.yml           # Jekyll configuration
│   ├── .nojekyll             # Bypass Jekyll for static files
│   ├── README_PAGES.md       # Pages-specific documentation
│   ├── aria/                 # Aria character app (demo mode)
│   │   ├── index.html
│   │   └── aria_controller.js
│   ├── chat/                 # AI chat app (demo mode)
│   │   ├── index.html
│   │   └── chat.js
│   ├── dashboard/            # Training dashboard
│   │   ├── index.html
│   │   └── shared-theme.css
│   └── quantum/              # Quantum ML interface
│       └── index.html
├── aria_web/                 # Source (local development)
├── chat-web/                 # Source (local development)
└── dashboard/                # Source (local development)
```

### Demo Mode vs Local Development

| Feature | GitHub Pages (Demo) | Local Development |
|---------|-------------------|-------------------|
| UI Functionality | ✅ Full | ✅ Full |
| Character Animations | ✅ Full | ✅ Full |
| API Responses | 🔸 Mock | ✅ Real |
| AI Chat | 🔸 Simulated | ✅ Multi-provider |
| Quantum Computing | ❌ No backend | ✅ Azure Quantum |
| Training | ❌ No backend | ✅ LoRA fine-tuning |
| Cost | 🆓 Free | 💰 API usage |

## 🚀 Deployment Process

### Automatic Deployment

GitHub Pages automatically deploys when changes are pushed:

1. **Trigger**: Push to `main` or `copilot/enable-github-pages-for-repo` branch
2. **Build**: GitHub Actions runs Jekyll build on `docs/` directory
3. **Deploy**: Built site is published to GitHub Pages
4. **URL**: https://bryan-roe.github.io/Aria

### Deployment Workflow (.github/workflows/pages.yml)

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [ main, copilot/enable-github-pages-for-repo ]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      - name: Setup Pages
        uses: actions/configure-pages@v4
      - name: Build with Jekyll
        uses: actions/jekyll-build-pages@v1
        with:
          source: ./docs
          destination: ./_site
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        uses: actions/deploy-pages@v4
```

### Manual Deployment

To manually trigger deployment:

1. Go to **Actions** tab in GitHub
2. Select **"Deploy to GitHub Pages"** workflow
3. Click **"Run workflow"** button
4. Select branch and click **"Run workflow"**

## 🔧 Configuration

### Jekyll Configuration (docs/_config.yml)

```yaml
title: Aria - Interactive AI Character Platform
description: Hybrid quantum-AI/ML platform
theme: jekyll-theme-minimal

markdown: kramdown
plugins:
  - jekyll-seo-tag
  - jekyll-sitemap

baseurl: ""
url: "https://bryan-roe.github.io/Aria"
```

### Demo Mode Configuration

Each web app has demo mode configured in JavaScript:

**aria_controller.js:**
```javascript
const DEMO_MODE = true; // Set to false for local backend
const DEMO_API_DELAY = 300; // Simulate network delay in ms

async function mockApiCall(endpoint, options) {
    if (!DEMO_MODE) {
        return fetch(endpoint, options);
    }

    await new Promise(resolve => setTimeout(resolve, DEMO_API_DELAY));

    if (endpoint === '/api/aria/command') {
        return {
            ok: true,
            json: async () => ({
                success: true,
                response: "Mock response in demo mode"
            })
        };
    }
}
```

**chat/index.html:**
```javascript
const DEMO_MODE = true;
const DEMO_RESPONSES = [
    "Hello! I'm Aria in demo mode...",
    "In demo mode, I use pre-programmed responses..."
];
```

## 📝 Updating Content

### Adding a New Web Application

1. **Create app directory in docs/**
   ```bash
   mkdir docs/myapp
   ```

2. **Add HTML/CSS/JS files with demo mode**
   ```javascript
   const DEMO_MODE = true;

   async function mockApiCall(endpoint, options) {
       await new Promise(resolve => setTimeout(resolve, 300));
       return { ok: true, json: async () => ({ demo: true }) };
   }
   ```

3. **Update main index.html**
   ```html
   <a href="myapp/" class="app-card">
       <div class="app-icon">🎨</div>
       <div class="app-title">My App</div>
       <div class="app-description">Description here</div>
       <span class="app-status status-demo">Demo Mode</span>
   </a>
   ```

4. **Commit and push**
   ```bash
   git add docs/myapp
   git commit -m "Add myapp to GitHub Pages"
   git push
   ```

### Updating Existing Applications

1. **Modify source files** in `aria_web/`, `chat-web/`, etc.
2. **Copy changes to docs/** with demo mode enabled
3. **Test locally** before committing
4. **Commit and push** to trigger deployment

### Syncing Source to Docs

When updating source files, remember to sync to docs:

```bash
# Example: Update Aria character
cp aria_web/index.html docs/aria/
cp aria_web/aria_controller.js docs/aria/

# Verify demo mode is enabled
grep "DEMO_MODE = true" docs/aria/aria_controller.js

# Commit changes
git add docs/aria/
git commit -m "Update Aria character interface"
git push
```

## 🧪 Testing

### Local Testing with Jekyll

1. **Install Jekyll**
   ```bash
   gem install jekyll bundler
   ```

2. **Serve locally**
   ```bash
   cd docs
   jekyll serve
   ```

3. **Open browser**
   ```
   http://localhost:4000
   ```

### Local Testing with Python HTTP Server

```bash
cd docs
python3 -m http.server 8000

# Open: http://localhost:8000
```

### Testing Checklist

Before pushing changes:

- [ ] All links work (no 404 errors)
- [ ] Demo mode is enabled (`DEMO_MODE = true`)
- [ ] Demo banners are visible
- [ ] Mock API responses work
- [ ] No console errors (except blocked CDN)
- [ ] Mobile responsive
- [ ] Images load correctly
- [ ] Navigation works between pages

## 🎨 Styling Guidelines

### Consistent Design Elements

All GitHub Pages applications should include:

1. **Demo Mode Banner**
   ```html
   <div class="demo-notice">
       <strong>🌐 Demo Mode:</strong> Running in demo mode...
       <a href="https://github.com/Bryan-Roe/Aria">View on GitHub</a>
   </div>
   ```

2. **Gradient Backgrounds**
   ```css
   body {
       background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
       background-size: 200% 200%;
       animation: gradientShift 15s ease infinite;
   }
   ```

3. **Card-Based Layouts**
   ```css
   .app-card {
       background: rgba(255, 255, 255, 0.98);
       border-radius: 20px;
       padding: 30px;
       box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
   }
   ```

4. **GitHub Links**
   Always include links back to the repository

## 🔍 Troubleshooting

### Deployment Issues

**Problem**: Workflow fails to build

**Solution**:
- Check workflow logs in Actions tab
- Verify Jekyll syntax in _config.yml
- Ensure all files referenced exist

**Problem**: 404 errors on GitHub Pages

**Solution**:
- Verify files are in `docs/` directory
- Check file paths are relative (no leading `/`)
- Ensure branch is set to `main` in Settings > Pages

**Problem**: Styles not loading

**Solution**:
- Check CSS file paths
- Verify .nojekyll file exists
- Clear browser cache

### Demo Mode Issues

**Problem**: API calls failing

**Solution**:
- Verify `DEMO_MODE = true`
- Check mockApiCall implementation
- Test with browser console open

**Problem**: Features not working

**Solution**:
- Ensure mock responses match expected format
- Check for JavaScript errors in console
- Verify all dependencies loaded

## 📊 Monitoring

### GitHub Pages Status

- **Build Status**: Check Actions tab for workflow runs
- **Deployment History**: View in Settings > Pages
- **Usage**: GitHub Pages has bandwidth limits (100GB/month)

### Analytics

To add Google Analytics or similar:

1. **Get tracking code**
2. **Add to docs/_includes/head.html**
3. **Configure in _config.yml**

## 🔐 Security

### Best Practices

- ✅ No API keys in frontend code
- ✅ Demo mode prevents backend calls
- ✅ All links use HTTPS
- ✅ No sensitive data in mock responses
- ✅ CSP headers via _config.yml

### Content Security

```yaml
# In _config.yml
webrick:
  headers:
    Content-Security-Policy: "default-src 'self' https: 'unsafe-inline' 'unsafe-eval'"
```

## 📚 Resources

- **GitHub Pages Docs**: https://docs.github.com/pages
- **Jekyll Docs**: https://jekyllrb.com/docs/
- **GitHub Actions**: https://docs.github.com/actions
- **Repository**: https://github.com/Bryan-Roe/Aria

## 🤝 Contributing

When contributing to GitHub Pages:

1. Make changes in source directories first
2. Test locally with full backend
3. Copy to docs/ with demo mode enabled
4. Test demo mode locally
5. Commit both source and docs/
6. Create PR with screenshots
7. Verify deployment after merge

## 📄 License

See main repository LICENSE file.

---

**Last Updated**: January 19, 2026
