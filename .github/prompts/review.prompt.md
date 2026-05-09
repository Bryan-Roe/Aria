---
description: "Perform a comprehensive code review analyzing correctness, security, performance, conventions, and testing coverage for the Aria platform."
name: "Code Review"
argument-hint: "File or component scope + focus area (example: file path + focus: security | performance | correctness)"
agent: agent
---

Perform a thorough code review of the specified code, evaluating these dimensions:

**1. Correctness**
- Logic errors, off-by-one, race conditions
- Null/undefined handling, edge cases
- API contract compliance (request/response shapes)

**2. Security (OWASP Top 10)**
- Input validation at system boundaries
- No hardcoded secrets (use `local.settings.json` or env vars)
- SQL injection prevention (parameterized queries in `shared/sql_engine.py`)
- XSS prevention in web responses
- SSRF checks on external URLs

**3. Performance**
- Unnecessary allocations or copies
- N+1 query patterns
- Missing caching where appropriate
- Frozenset usage for O(1) keyword lookups (Aria convention)

**4. Conventions**
- Provider detection chain: Azure → OpenAI → LMStudio → LoRA → Local
- Config precedence: YAML < CLI < per-job YAML < env vars
- Data immutability: read-only `datasets/`, write-only `data_out/`
- Status files: `data_out/<orchestrator>/status.json`
- Error handling: graceful degradation, non-blocking telemetry

**5. Testing**
- Are new code paths covered by tests?
- Can it be validated with `python scripts/test_runner.py --unit`?
- E2E coverage for UI changes: `pytest tests/test_ui_playwright.py`

**Output format:**
For each finding:
- Severity: critical | warning | suggestion
- Location: file and line
- Issue description
- Recommended fix
