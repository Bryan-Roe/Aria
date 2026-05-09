---
name: "Aria-Web"
description: "Guidance for aria_web server module"
applyTo: "aria_web/**"
---
# Aria Web Module — Implementation Guidance

- Alternative entry point for the Aria character web server.
- Canonical server logic is in `apps/aria/server.py` (port 8080).
- This module re-exports or wraps the core server functionality.
- API endpoints follow the same contract as `apps/aria/server.py`:
  - `GET /api/aria/state`, `POST /api/aria/command`, `POST /api/aria/execute`, etc.
- Static files served from `apps/aria/` (index.html, aria_controller.js, auto-execute.html).
- CORS enabled for cross-origin frontend access.
- Keep in sync with `apps/aria/server.py` when modifying API contracts.
- Tests: `pytest tests/test_aria_server.py` covers both entry points.
