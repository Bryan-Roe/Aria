---
applyTo: "ai-projects/llm-maker/**"
---

# LLM Maker — Instruction Guide

## Project Structure

```
ai-projects/llm-maker/
    src/
        tool_maker.py       # ToolMaker — LLM-powered Python function generator
        website_maker.py    # WebsiteMaker — HTML/CSS/JS site generator
        tool_validator.py   # ToolValidator — AST-based safety validation
```

## Safety-First Code Generation

### ToolValidator Rules (MANDATORY — never bypass)

**Banned imports (DANGEROUS_IMPORTS):**
`os, sys, subprocess, shutil, pathlib, socket, urllib, requests, http, pickle, threading, multiprocessing, ctypes, cffi`

**Banned builtins (DANGEROUS_BUILTINS):**
`eval, exec, compile, __import__, open, input, breakpoint, exit`

**Validation pipeline:**
1. Parse code into AST
2. Walk AST for import statements → reject banned modules
3. Walk AST for function calls → reject dangerous builtins
4. Regex scan for file I/O patterns
5. Regex scan for network operation patterns
6. Verify function signature matches requested spec

### Code Generation Pattern
```python
# ToolMaker.create_tool() implements:
for attempt in range(max_attempts):  # default: 3
    code = self._generate_code(prompt)
    is_valid, errors = self.validator.validate(code)
    if is_valid:
        sig_ok = self.validator.check_function_signature(code, name, params)
        if sig_ok:
            return code
    # Inject error feedback into next prompt iteration
    prompt += f"\nPrevious errors: {errors}"
```

### Website Generation Pattern
```python
# WebsiteMaker.create_website() returns:
{
    "success": True,
    "files": {"index.html": "...", "style.css": "...", "script.js": "..."},
    "path": "ai-projects/generated_sites/{name}/",
    "metadata": {"created_at": "...", "pages": [...], "features": [...]}
}
```

## Coding Conventions

- All generated code must pass `ToolValidator.validate()` before use
- Generated websites go to `ai-projects/generated_sites/{name}/`
- Use `update_website()` for modifications (preserves metadata.json)
- Provider detection uses `detect_provider()` from shared chain
- Include descriptive docstrings in generated functions
- Keep generated functions pure — no side effects
