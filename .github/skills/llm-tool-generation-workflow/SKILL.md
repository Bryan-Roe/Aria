---
name: llm-tool-generation-workflow
description: "Generate, validate, and debug LLM-powered Python tools and complete HTML/CSS/JS websites using the ToolMaker and WebsiteMaker modules in ai-projects/llm-maker/. Use when an LLM-generated function fails safety validation, ToolValidator rejects imports, website output is missing files, retry attempts are exhausted, or you need to understand the AST-based security pipeline."
argument-hint: "Describe what you need: a Python tool name + parameters, or a website name + pages/features. Also describe any validation errors you're hitting (banned import, dangerous builtin, signature mismatch)."
---

# LLM Tool Generation Workflow

## What This Skill Produces
- Safe Python function generated through the ToolMaker retry pipeline
- Complete multi-file website via WebsiteMaker
- Root cause for ToolValidator rejections (banned import, dangerous builtin, signature mismatch, regex scan hit)
- Hardened prompt that avoids the exact validation failure on retry

## When to Use

Trigger phrases:
- "generate a Python tool with LLM"
- "ToolMaker failing validation"
- "banned import rejected"
- "ToolValidator says dangerous builtin"
- "generated code uses eval/exec"
- "os import in generated function"
- "website generation missing index.html"
- "create_tool() retries exhausted"
- "signature mismatch in generated code"
- "WebsiteMaker not producing CSS"
- "how do I use ToolMaker safely"
- "generated site overwriting metadata"

## Procedure

### Step 1 — Understand the project structure
```
ai-projects/llm-maker/
    src/
        tool_maker.py       # ToolMaker — generates Python functions
        website_maker.py    # WebsiteMaker — generates HTML/CSS/JS sites
        tool_validator.py   # ToolValidator — AST-based safety gate
```

### Step 2 — Know the banned lists (NEVER include these)

**Banned imports (DANGEROUS_IMPORTS):**
```
os, sys, subprocess, shutil, pathlib, socket, urllib, requests,
http, pickle, threading, multiprocessing, ctypes, cffi
```

**Banned builtins (DANGEROUS_BUILTINS):**
```
eval, exec, compile, __import__, open, input, breakpoint, exit
```

Any generated code containing these will be rejected by `ToolValidator.validate()`. The prompt for regeneration should explicitly say "do not import or call: [list]".

### Step 3 — Trace the ToolMaker validation pipeline
```python
# ToolMaker.create_tool() retry loop (up to 3 attempts by default):
for attempt in range(max_attempts):  # default: 3
    code = self._generate_code(prompt)
    is_valid, errors = self.validator.validate(code)
    if is_valid:
        sig_ok = self.validator.check_function_signature(code, name, params)
        if sig_ok:
            return code  # success
    # Error feedback injected into next attempt:
    prompt += f"\nPrevious attempt failed. Errors: {errors}"
```

Validation steps in order:
1. Parse code AST — reject if syntax error
2. Walk AST imports — reject if any `DANGEROUS_IMPORTS` found
3. Walk AST function calls — reject if any `DANGEROUS_BUILTINS` used
4. Regex scan for file I/O patterns (e.g. `open(`, `with open`)
5. Regex scan for network patterns (e.g. `socket.`, `urllib.request`)
6. Verify function signature matches requested name + parameter list

### Step 4 — Debug a ToolValidator rejection
```python
from ai_projects.llm_maker.src.tool_validator import ToolValidator

validator = ToolValidator()
is_valid, errors = validator.validate(suspect_code)
print(errors)  # ['Import of "os" is not allowed', ...]

# Common error messages and their fixes:
# "Import of 'os' is not allowed"     → remove os import, use pure Python
# "Use of 'eval' is not allowed"      → replace eval with ast.literal_eval equivalent
# "File I/O pattern detected"         → remove open() call entirely
# "Network pattern detected"          → remove socket/urllib usage
# "Signature mismatch"                → fix function name or parameter names to match spec
```

### Step 5 — Generate a website
```python
from ai_projects.llm_maker.src.website_maker import WebsiteMaker

maker = WebsiteMaker()
result = maker.create_website(
    name="my-portfolio",
    description="Personal portfolio with about and contact pages",
    pages=["index", "about", "contact"],
    features=["responsive", "dark-mode"]
)
# result = {
#   "success": True,
#   "files": {"index.html": "...", "style.css": "...", "script.js": "..."},
#   "path": "ai-projects/generated_sites/my-portfolio/",
#   "metadata": {"created_at": "...", "pages": [...], "features": [...]}
# }
```

For updates, use `update_website()` — this preserves `metadata.json` and doesn't overwrite unchanged files.

### Step 6 — Handle exhausted retries
If all 3 attempts fail:
1. Inspect `errors` from the last attempt
2. Rewrite the prompt spec to explicitly prohibit the failing pattern
3. Consider breaking the function into smaller pieces (one purpose each)
4. For signature mismatches: ensure parameter names in the spec use simple Python-safe identifiers (no reserved words)

### Step 7 — Validate generated output is pure
```python
# Generated functions must be pure — no side effects:
# ✅ Pure: input → computation → return value
# ❌ Not pure: writes to filesystem, calls network, modifies globals

# Before deploying any generated tool, always run:
is_valid, errors = validator.validate(generated_code)
assert is_valid, f"Generated code failed validation: {errors}"
```

## Quality Checks
- [ ] Generated code passes `ToolValidator.validate()` — no banned imports or builtins
- [ ] Function signature matches the spec (name + parameter names)
- [ ] No file I/O, no network calls, no `eval`/`exec` in generated output
- [ ] Website output includes all requested pages as separate HTML files
- [ ] `update_website()` used for modifications — not `create_website()` which may reset metadata
- [ ] Generated sites saved to `ai-projects/generated_sites/{name}/`
- [ ] Provider detection uses `detect_provider()` from shared chain (no hardcoded provider)
- [ ] Retry loop exhaustion handled gracefully — error surfaced to caller, not silently swallowed
