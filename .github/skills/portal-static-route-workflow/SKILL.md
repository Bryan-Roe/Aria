---
name: portal-static-route-workflow
description: 'Add or debug static page and asset routes in `function_app.py` for chat or portal-style web surfaces. Use when HTML/JS routes 404, page assets are stale, MIME types are wrong, or cache behavior causes confusing frontend results.'
argument-hint: 'Describe the page/asset route, file path, and observed serving issue.'
---

# Portal Static Route Workflow

## What This Skill Produces

Use this skill to implement and troubleshoot static web routes safely in `function_app.py`. The expected result is:
- a clear URL-to-file mapping for each static page or asset
- consistent route behavior with correct MIME, cache headers, and error handling
- minimal route changes that preserve existing API behavior
- verification through direct endpoint checks and browser validation

## When to Use

Use this skill when you need to:
- add a new static HTML/JS/CSS route to the Functions host
- fix a static route returning 404/500
- correct cache-control behavior for frontend assets
- fix MIME/content-type issues that break page execution
- align web surface routes with actual file locations

Common trigger phrases:
- "add a static page route"
- "this page returns 404"
- "chat web route is broken"
- "JS file is served with wrong content type"
- "cache keeps serving stale page"
- "make this portal page reachable via /api"

## Procedure

1. Define route and file mapping first
   - Confirm desired public path (for example `/api/<route>`) and exact file location.
   - Verify the file actually exists before editing route code.

2. Follow existing route patterns in `function_app.py`
   - Use the same decorator style and auth level as neighboring static routes.
   - Resolve file paths from repository context consistently (avoid hardcoded absolute paths).

3. Set response semantics deliberately
   - Use correct MIME type (`text/html`, `application/javascript`, `text/css`, etc.).
   - Apply cache headers intentionally for developer-facing freshness when required.
   - Keep 404 and 500 behavior explicit and user-debuggable.

4. Preserve API stability
   - Avoid touching unrelated dynamic endpoints while adding static routes.
   - If static changes share helpers, verify nearby routes still behave identically.

5. Validate with direct requests and browser checks
   - Request the exact route and confirm status code, content type, and body.
   - Load the page in a browser and verify assets resolve and execute.

6. Check integration edges
   - If the page uses chat/SSE or health calls, confirm backend endpoints still match client expectations.
   - Confirm no secret values are embedded into served static content.

7. Finalize with explicit route inventory
   - Summarize added/changed routes, mapped files, and verification outcomes.

## Quality Checks

Before finishing, confirm that:
- every static route maps to an existing file
- MIME and cache behavior are correct for each asset type
- error responses are clear and intentional
- unrelated API routes were not regressed
- browser behavior matches endpoint-level verification
