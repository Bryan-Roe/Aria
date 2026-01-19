# GitHub Pages Deployment Guide

This guide explains how to enable and deploy the Aria 3D character demo to GitHub Pages.

## 🚀 Quick Setup

### Option 1: Automatic Deployment (Recommended)

The repository is configured with a GitHub Actions workflow that automatically deploys to GitHub Pages.

**Steps:**
1. Merge this PR to `main` branch
2. Go to repository **Settings** → **Pages**
3. Under "Build and deployment", set:
   - **Source**: GitHub Actions
4. The workflow will automatically trigger and deploy
5. Your site will be live at: `https://bryan-roe.github.io/Aria/`

### Option 2: Manual Branch Deployment

Alternatively, you can deploy directly from the branch:

1. Go to repository **Settings** → **Pages**
2. Under "Build and deployment", set:
   - **Source**: Deploy from a branch
   - **Branch**: `main`
   - **Folder**: `/docs`
3. Click **Save**
4. GitHub will build and deploy automatically
5. Your site will be live at: `https://bryan-roe.github.io/Aria/`

## 📋 Deployment Checklist

Before deploying, ensure:

- [ ] `docs/index.html` exists and contains the Aria interface
- [ ] `docs/aria_controller.js` exists with all animations
- [ ] `docs/README.md` exists with user documentation
- [ ] `.github/workflows/pages.yml` exists (for GitHub Actions method)
- [ ] All files are committed and pushed to the branch
- [ ] Repository is public (or you have GitHub Pages enabled for private repos)

## 🔍 Verification

After deployment completes (usually 1-2 minutes):

1. **Visit the site**: Go to `https://bryan-roe.github.io/Aria/`
2. **Test basic commands**: Try "jump", "wave", "dance"
3. **Test object interaction**: Click and drag objects
4. **Test waypoints**: Use `/goto center` in chat
5. **Check console**: Should show "Network error, using fallback" (expected)

## ⚙️ Configuration Details

### GitHub Actions Workflow

The workflow (`.github/workflows/pages.yml`) automatically:
- Triggers on push to `main` or feature branches
- Sets up GitHub Pages environment
- Uploads the `docs/` directory as artifact
- Deploys to GitHub Pages
- Provides deployment URL in workflow output

**Permissions required:**
```yaml
permissions:
  contents: read
  pages: write
  id-token: write
```

### Repository Permissions

Ensure GitHub Actions has the necessary permissions:
1. Go to **Settings** → **Actions** → **General**
2. Under "Workflow permissions", select:
   - ✅ Read and write permissions
3. Check: ✅ Allow GitHub Actions to create and approve pull requests

## 🎨 Static Mode Features

The deployed site runs in **static mode**:

- ✅ **No Backend Required**: All logic runs in browser
- ✅ **Offline Capable**: Works without internet after initial load
- ✅ **Local Fallback**: Commands processed client-side
- ✅ **Graceful Degradation**: API errors handled silently

**What works:**
- All animations (jump, dance, wave, spin)
- Character movement and positioning
- Object interactions (drag, pickup, drop, throw)
- 3D waypoint navigation
- Expression changes
- Chat commands

**What requires the full backend (not available in static mode):**
- AI-powered natural language processing
- Server-side state persistence
- Multi-user synchronization
- Advanced LLM-based world generation

## 🔧 Customization

To customize the deployment:

### Change Page Title
Edit `docs/index.html` line 6:
```html
<title>Your Custom Title</title>
```

### Modify Banner
Edit the `.github-pages-banner` styles and content in `docs/index.html`

### Add Analytics
Add tracking code before closing `</body>` tag in `docs/index.html`

### Change Domain
1. Add `CNAME` file to `docs/` directory with your domain
2. Configure DNS CNAME record pointing to `bryan-roe.github.io`
3. Enable "Enforce HTTPS" in Pages settings

## 📊 Monitoring

### Check Deployment Status

1. Go to **Actions** tab in repository
2. Look for "Deploy to GitHub Pages" workflow runs
3. Click on a run to see detailed logs
4. Green checkmark = successful deployment
5. Red X = deployment failed (check logs)

### View Deployment URL

After successful deployment:
1. Go to **Settings** → **Pages**
2. See "Your site is live at" message with URL
3. Click "Visit site" button

## 🐛 Troubleshooting

### Deployment Fails

**Problem**: Workflow fails with "403 Forbidden"
- **Solution**: Enable Pages in Settings and set source to "GitHub Actions"

**Problem**: Workflow doesn't trigger
- **Solution**: Check workflow file syntax, ensure correct branch name

**Problem**: 404 Not Found after deployment
- **Solution**: Ensure `index.html` is in `docs/` directory, not subdirectory

### Site Issues

**Problem**: Page loads but no styling
- **Solution**: Check console for CSS load errors, verify file paths

**Problem**: Character doesn't respond to commands
- **Solution**: Check browser console for JavaScript errors
- Verify `aria_controller.js` is loaded

**Problem**: Objects don't appear
- **Solution**: Check that emoji rendering is supported in browser
- Try different browser (Chrome, Firefox, Safari)

### Performance

**Problem**: Site loads slowly
- **Solution**: GitHub Pages uses CDN, should be fast globally
- Check browser cache settings
- Test on different network

## 📚 Additional Resources

- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [GitHub Actions for Pages](https://github.com/actions/deploy-pages)
- [Aria Main Repository](https://github.com/Bryan-Roe/Aria)
- [Aria Web Interface Guide](../aria_web/README.md)

## 🎉 Success!

Once deployed, share your demo:
- Tweet the URL with #AriaAI #GitHubPages
- Add badge to main README: `[![Demo](https://img.shields.io/badge/demo-live-success)](https://bryan-roe.github.io/Aria/)`
- Link from project documentation

---

**Questions?** Open an issue in the [main repository](https://github.com/Bryan-Roe/Aria/issues)
