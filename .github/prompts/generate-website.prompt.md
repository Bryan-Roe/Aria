---
description: "Generate a complete website using the LLM Maker WebsiteMaker"
name: "Generate Website"
argument-hint: "Site spec + purpose (example: site purpose + pages + style preferences + any required sections)"
agent: llm-maker
---
# Generate Website

Create a complete website (HTML + CSS + JS) using the WebsiteMaker system.

## Specification

Describe your website with:

1. **Name**: Project identifier (used for output directory)
2. **Description**: What the site does and who it's for
3. **Style**: Visual style (modern, minimal, dark, corporate, playful, etc.)
4. **Pages**: List of pages with their purpose
5. **Features**: Interactive features needed (forms, animations, charts, etc.)

## Output

WebsiteMaker generates:
- `index.html` — Main page with semantic HTML
- `style.css` — Complete stylesheet
- `script.js` — Interactive functionality
- Additional pages as specified
- `metadata.json` — Creation timestamp, pages, features

Files are saved to: `ai-projects/generated_sites/{name}/`

## Quality Standards

- Responsive design (mobile-first)
- Semantic HTML5 elements
- Accessible (ARIA labels, alt text, keyboard navigation)
- Modern CSS (flexbox/grid, custom properties)
- Clean, commented JavaScript

## Update Existing Sites

Use `WebsiteMaker.update_website(name, update_description, target_file)` to modify existing sites while preserving metadata.

Generate the website for: {{input}}
