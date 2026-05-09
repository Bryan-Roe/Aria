# Generated Site Bundles Index

_Last updated: 2026-04-11_

This index tracks generated static site bundles under `generated_sites/`.

## Bundles

- `portfolio-live/`
- `nebula-launch/`
- `dev-journal/`
- `docs-spark/`
- `quantum-showcase/`
- `aria-studio/`

## Bundle contract

Each bundle should contain:

- `index.html`
- `style.css`
- `script.js`
- `metadata.json`

Multi-page bundles may add additional HTML files such as `about.html`, `gallery.html`, `contact.html`.

## Quick local preview

From repo root:

```bash
python3 -m http.server 8089
# open http://localhost:8089/generated_sites/
```

## Validation

Run the generated-sites contract checks locally:

```bash
# Default (legacy-compatible)
python3 scripts/validate_site_bundles.py

# Strict mode (matches CI)
python3 scripts/validate_site_bundles.py --strict-metadata
```

## Maintenance checklist

- Keep `metadata.json` in sync with page/features.
- Prefer additive updates over overwriting existing bundles.
- Validate HTML/CSS quickly in browser after generation.
