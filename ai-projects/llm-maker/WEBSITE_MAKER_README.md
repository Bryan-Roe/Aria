# AI Website Maker - Documentation

## Overview

The AI Website Maker is an automated website generation and update system that uses Large Language Models to create complete, modern, responsive websites from natural language descriptions.

## Features

### 🎨 Automated Website Generation
- **Natural Language Input**: Describe what you want in plain English
- **Multiple Visual Styles**: Modern, minimal, corporate, creative, dark theme, colorful
- **Multi-Page Support**: Generate websites with multiple pages (index, about, contact, etc.)
- **Feature Customization**: Add specific features like contact forms, navigation, galleries
- **Responsive Design**: All generated sites are mobile-friendly
- **Modern Code**: HTML5, CSS3, and JavaScript with best practices

### 🔄 Intelligent Updates
- **AI-Powered Modifications**: Update existing websites with natural language instructions
- **Selective Updates**: Update specific files or entire projects
- **Version Tracking**: Metadata tracks creation and update history
- **Context-Aware**: AI understands current website structure when making changes

### 📊 Website Management
- **Visual Library**: Browse all generated websites
- **Code Preview**: View complete source code for any website
- **Easy Deletion**: Remove websites you no longer need
- **File Access**: All sites saved in `llm-maker/generated_sites/`

## Quick Start

### 1. Start the Server

```bash
cd llm-maker
python web_server.py
```

### 2. Access the Interface

Open your browser to: `http://localhost:8090/website-maker`

### 3. Create Your First Website

**Example 1: Personal Portfolio**
- Name: `my-portfolio`
- Description: `A personal portfolio website with a hero section, about me, skills showcase with progress bars, project gallery with hover effects, and contact form. Use a modern, professional design with smooth animations.`
- Style: `Modern`
- Pages: `index`, `projects`, `contact`
- Features: `responsive design`, `smooth scrolling`, `hover animations`, `contact form`

**Example 2: Landing Page**
- Name: `product-landing`
- Description: `A product landing page with headline, 3 feature cards with icons, pricing table with 3 tiers, testimonials carousel, and call-to-action button. Clean and conversion-focused.`
- Style: `Minimal`
- Pages: `index`
- Features: `responsive design`, `pricing table`, `testimonials`

**Example 3: Restaurant Website**
- Name: `restaurant-site`
- Description: `A restaurant website with image carousel, menu sections for appetizers/entrees/desserts, location map, hours of operation, and reservation form. Warm, inviting design.`
- Style: `Creative`
- Pages: `index`, `menu`, `about`, `contact`
- Features: `image carousel`, `menu sections`, `reservation form`, `google maps`

## API Reference

### Create Website

**Endpoint:** `POST /api/websites`

**Request Body:**
```json
{
  "name": "my-website",
  "description": "A modern portfolio website with...",
  "style": "modern",
  "pages": ["index", "about", "contact"],
  "features": ["responsive design", "contact form", "navigation"]
}
```

**Response:**
```json{
  "success": true,
  "message": "Website 'my-website' created successfully",
  "files": {
    "index.html": "<!DOCTYPE html>...",
    "styles.css": "body { ... }",
    "script.js": "// JavaScript code..."
  },
  "path": "/path/to/generated_sites/my-website",
  "metadata": {
    "name": "my-website",
    "description": "...",
    "style": "modern",
    "pages": ["index", "about", "contact"],
    "features": [...],
    "created_at": "2025-12-08T12:00:00",
    "files": ["index.html", "styles.css", "script.js"]
  }
}
```

### Update Website

**Endpoint:** `POST /api/websites/update`

**Request Body:**
```json
{
  "name": "my-website",
  "update_description": "Change the header background to gradient, make buttons bigger, add smooth scroll",
  "target_file": "styles.css"  // Optional
}
```

**Response:**
```json
{
  "success": true,
  "message": "Website 'my-website' updated successfully",
  "updated_files": {
    "styles.css": "/* Updated CSS */"
  },
  "path": "/path/to/generated_sites/my-website",
  "metadata": {...}
}
```

### List Websites

**Endpoint:** `GET /api/websites`

**Response:**
```json
{
  "websites": [
    {
      "name": "my-website",
      "description": "...",
      "style": "modern",
      "pages": ["index", "about"],
      "features": ["responsive design"],
      "created_at": "2025-12-08T12:00:00",
      "last_updated": "2025-12-08T13:00:00",
      "files": ["index.html", "styles.css"],
      "path": "/path/to/generated_sites/my-website"
    }
  ],
  "count": 1
}
```

### Get Website

**Endpoint:** `GET /api/websites/{name}`

**Response:**
```json
{
  "success": true,
  "website": {
    "name": "my-website",
    "description": "...",
    "created_at": "2025-12-08T12:00:00",
    "files": ["index.html", "styles.css"],
    "files_content": {
      "index.html": "<!DOCTYPE html>...",
      "styles.css": "body { ... }"
    },
    "path": "/path/to/generated_sites/my-website"
  }
}
```

### Delete Website

**Endpoint:** `DELETE /api/websites/{name}`

**Response:**
```json
{
  "success": true,
  "message": "Website 'my-website' deleted successfully"
}
```

## Command-Line Interface

### Create Website
```bash
python src/website_maker.py create my-portfolio \
  "A personal portfolio with projects and contact form" \
  --style modern \
  --pages index about projects contact \
  --features "responsive design" "contact form" "smooth scrolling"
```

### Update Website
```bash
python src/website_maker.py update my-portfolio \
  "Change the color scheme to blue and purple gradients" \
  --file styles.css
```

### List Websites
```bash
python src/website_maker.py list
```

### Delete Website
```bash
python src/website_maker.py delete my-portfolio
```

## Best Practices

### Writing Good Descriptions

**❌ Too Vague:**
"A website for my business"

**✅ Good:**
"A website for my photography business with a hero image, portfolio gallery grid with lightbox, about me section with my photo, services list with pricing, and contact form. Modern, clean design with smooth transitions."

**Key Elements:**
1. **Purpose**: What the website is for
2. **Sections**: What content/sections to include
3. **Features**: Specific functionality (forms, galleries, etc.)
4. **Design Style**: Visual direction (modern, minimal, colorful)
5. **Special Requirements**: Animations, interactions, colors

### Choosing Visual Styles

- **Modern**: Clean, gradients, shadows, contemporary
- **Minimal**: Simple, lots of white space, typography-focused
- **Corporate**: Professional, blues/grays, structured
- **Creative**: Colorful, unique layouts, artistic
- **Dark**: Dark backgrounds, neon accents, high contrast
- **Colorful**: Vibrant colors, playful, energetic

### Adding Features

Common features to request:
- `responsive design` - Mobile-friendly layout
- `navigation menu` - Header navigation with links
- `footer` - Footer with links/copyright
- `contact form` - Email contact form
- `smooth scrolling` - Smooth page scroll animation
- `hover effects` - Interactive hover animations
- `image gallery` - Photo/image grid
- `testimonials` - Customer reviews section
- `pricing table` - Product/service pricing
- `call-to-action` - Prominent CTA buttons
- `social media links` - Social icon links
- `animations` - Entry/scroll animations
- `lightbox` - Image modal viewer

## Tips for Success

### 1. Be Specific
The more detail you provide, the better the results. Instead of "a nice website", describe exactly what you want.

### 2. Start Simple
Create a basic version first, then use updates to refine and add features.

### 3. Use Examples
Look at websites you like and describe similar layouts/features.

### 4. Iterate
Don't expect perfection on the first try. Use the update feature to refine.

### 5. Check the Code
View the generated code to understand what was created and learn from it.

## Troubleshooting

### Website Generation Takes Too Long
- **Cause**: Complex descriptions or slow AI provider
- **Solution**: Simplify description, break into multiple pages, or check AI provider status

### Generated Code Has Issues
- **Cause**: Ambiguous description or AI interpretation
- **Solution**: Use more specific language, provide examples, or manually edit the generated files

### Update Doesn't Apply Changes
- **Cause**: Unclear update instructions
- **Solution**: Be specific about what to change and where (e.g., "in the header section" or "in styles.css")

### Files Not Found
- **Cause**: Website deleted or path issue
- **Solution**: Check `llm-maker/generated_sites/` directory for your website

## File Structure

Generated websites are saved in:
```
llm-maker/generated_sites/
└── my-website/
    ├── index.html
    ├── about.html
    ├── contact.html
    ├── styles.css
    ├── script.js
    └── metadata.json
```

### metadata.json
Contains website information:
```json
{
  "name": "my-website",
  "description": "...",
  "style": "modern",
  "pages": ["index", "about", "contact"],
  "features": ["responsive design", "contact form"],
  "created_at": "2025-12-08T12:00:00Z",
  "last_updated": "2025-12-08T13:00:00Z",
  "last_update_description": "Added smooth scrolling",
  "files": ["index.html", "about.html", "contact.html", "styles.css", "script.js"]
}
```

## Integration Examples

### JavaScript Fetch
```javascript
// Create website
const response = await fetch('http://localhost:8090/api/websites', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'my-site',
    description: 'A portfolio website...',
    style: 'modern',
    pages: ['index', 'about'],
    features: ['responsive design']
  })
});

const result = await response.json();
console.log(result);
```

### Python Requests
```python
import requests

# Create website
response = requests.post(
    'http://localhost:8090/api/websites',
    json={
        'name': 'my-site',
        'description': 'A portfolio website...',
        'style': 'modern',
        'pages': ['index', 'about'],
        'features': ['responsive design']
    }
)

result = response.json()
print(result)
```

### cURL
```bash
# Create website
curl -X POST http://localhost:8090/api/websites \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-site",
    "description": "A portfolio website...",
    "style": "modern",
    "pages": ["index", "about"],
    "features": ["responsive design"]
  }'
```

## Security Considerations

### Generated Code Review
- Always review generated code before deploying to production
- Check for any placeholder content or TODO comments
- Verify form actions and API endpoints

### Form Handling
- Generated contact forms are client-side only
- Implement server-side validation and email sending separately
- Add CAPTCHA to prevent spam

### Production Deployment
- Minify CSS/JS for performance
- Add proper form handling backend
- Configure proper security headers
- Use HTTPS in production

## Advanced Usage

### Custom AI Provider
```python
from website_maker import WebsiteMaker

# Use specific provider
maker = WebsiteMaker(provider_name='azure')  # or 'openai', 'local'

# Create website
result = maker.create_website(
    name='my-site',
    description='...',
    style='modern'
)
```

### Batch Generation
```python
from website_maker import WebsiteMaker

maker = WebsiteMaker()

websites = [
    {'name': 'site1', 'description': '...', 'style': 'modern'},
    {'name': 'site2', 'description': '...', 'style': 'minimal'},
    {'name': 'site3', 'description': '...', 'style': 'creative'}
]

for site_config in websites:
    result = maker.create_website(**site_config)
    print(f"Created: {result['message']}")
```

### Code Validation
```python
from website_maker import WebsiteValidator

validator = WebsiteValidator()

# Validate HTML
html = "<html>...</html>"
is_valid, warnings = validator.validate_html(html)

print(f"Valid: {is_valid}")
print(f"Warnings: {warnings}")

# Validate CSS
css = "body { ... }"
is_valid, warnings = validator.validate_css(css)

print(f"Valid: {is_valid}")
print(f"Warnings: {warnings}")
```

## Future Enhancements

Planned features for future releases:
- **Templates**: Pre-built templates for common site types
- **Component Library**: Reusable UI components
- **Theme System**: Customizable color schemes
- **Asset Management**: Image upload and management
- **Preview Server**: Live preview of generated sites
- **Version Control**: Git integration for site history
- **Deployment**: One-click deploy to hosting services
- **CMS Integration**: Connect to content management systems
- **SEO Optimization**: Automatic SEO best practices
- **A/B Testing**: Multiple variant generation

## Support

For issues, questions, or feature requests:
1. Check the troubleshooting section above
2. Review the examples in the UI
3. Check the main LLM Maker README
4. Submit an issue on GitHub

## License

Same license as the main LLM Maker project.

## Credits

Built on top of the LLM Maker framework, leveraging existing chat provider infrastructure for AI-powered website generation.
