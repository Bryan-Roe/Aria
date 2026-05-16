# Aria GitHub Pages

This directory contains the GitHub Pages deployment of the Aria project web applications.

## 🌐 Live Demo

Visit the live demo at: <https://bryan-roe.github.io/Aria>

## 📁 Structure

- **index.html** - Main landing page with links to all applications
- **aria/** - Aria 3D character interface (demo mode)
- **chat/** - AI chat interface (demo mode)
- **dashboard/** - Training and monitoring dashboard (demo mode)
- **quantum/** - Quantum ML interface (demo mode)

## 🔧 Demo Mode vs. Local Development

### Demo Mode (GitHub Pages)

All web applications run in **demo mode** when hosted on GitHub Pages:

- ✅ Full UI functionality
- ✅ Interactive character animations
- ✅ Simulated API responses
- ❌ No real AI chat (uses mock responses)
- ❌ No backend Python services
- ❌ No real-time training or quantum computing

### Local Development (Full Features)

For complete functionality with AI, quantum computing, and training:

1. **Clone the repository**

   ```bash
   git clone https://github.com/Bryan-Roe/Aria.git
   cd Aria
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API keys** (optional)

   ```bash
   # For Azure OpenAI
   export AZURE_OPENAI_API_KEY="..."
   export AZURE_OPENAI_ENDPOINT="..."
   export AZURE_OPENAI_DEPLOYMENT="..."

   # For OpenAI
   export OPENAI_API_KEY="..."
   ```

4. **Start services**

   ```bash
   # Aria web server
   cd aria_web && python server.py

   # Azure Functions (chat API)
   func start

   # Dashboard
   cd dashboard && python app.py
   ```

## 🚀 Deployment

GitHub Pages automatically deploys when changes are pushed to the main branch:

1. Changes pushed to `main` or `copilot/enable-github-pages-for-repo` branch
2. GitHub Actions workflow (`.github/workflows/pages.yml`) runs
3. Jekyll builds the site from the `docs/` directory
4. Site is deployed to GitHub Pages

### Manual Deployment

To manually trigger deployment:

1. Go to the repository's Actions tab
2. Select "Deploy to GitHub Pages" workflow
3. Click "Run workflow"

## 📝 Configuration

### Jekyll Configuration

The `_config.yml` file contains Jekyll settings:

- Site title and description
- Theme selection
- Build exclusions
- URL configuration

### Demo Mode Configuration

Each web app has a `DEMO_MODE` flag in its JavaScript:

```javascript
const DEMO_MODE = true; // Set to false for local backend
```

To test with local backend before deployment:

1. Set `DEMO_MODE = false` in the JavaScript files
2. Start local Python servers
3. Test functionality
4. Set `DEMO_MODE = true` before committing

## 🔍 Testing Locally

To test the GitHub Pages site locally:

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

   ```text
   http://localhost:4000
   ```

## 📦 Adding New Applications

To add a new web application to GitHub Pages:

1. **Create app directory**

   ```bash
   mkdir docs/myapp
   ```

2. **Add HTML/CSS/JS files**
   - Copy your application files
   - Add demo mode configuration
   - Update API calls to use mock responses

3. **Update main index**
   - Add a new card in `docs/index.html`
   - Link to `/myapp/`

4. **Test and commit**

   ```bash
   git add docs/myapp
   git commit -m "Add myapp to GitHub Pages"
   git push
   ```

## 🎨 Customization

### Styling

All applications use inline CSS or imported stylesheets. To maintain consistency:

- Use gradient backgrounds with similar color schemes
- Follow card-based layouts
- Include demo mode banners
- Add GitHub repository links

### Mock Data

Each app implements mock API responses in JavaScript:

```javascript
async function mockApiCall(endpoint, options) {
    await new Promise(resolve => setTimeout(resolve, 300));

    if (endpoint === '/api/myendpoint') {
        return {
            ok: true,
            json: async () => ({ data: 'mock response' })
        };
    }
}
```

## 📚 Documentation

- Main README: `/README.md`
- Aria Documentation: `/docs/aria/`
- Quantum Documentation: `/docs/quantum/`
- Training Guides: `/docs/training/`

## 🤝 Contributing

When adding or modifying GitHub Pages content:

1. Ensure demo mode works without backend
2. Add clear demo mode notices
3. Test all links and interactions
4. Verify mobile responsiveness
5. Update this README if adding new sections

### Note on CLI scripts

If you include Python CLI scripts referenced from docs or demo pages (for example `scripts/foo.py`), prefer adding the repository root to `sys.path` at script startup so the script can import local packages regardless of working directory. Use the snippet below as a copy-paste example:

```python
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
   sys.path.insert(0, str(REPO_ROOT))

# Now import local packages safely:
from shared.json_utils import load_status_json
```

## 🔗 Links

- **Repository**: <https://github.com/Bryan-Roe/Aria>
- **Issues**: <https://github.com/Bryan-Roe/Aria/issues>
- **Live Demo**: <https://bryan-roe.github.io/Aria>

## 📄 License

See the main repository LICENSE file for details.

---

**Last Updated**: January 19, 2026
