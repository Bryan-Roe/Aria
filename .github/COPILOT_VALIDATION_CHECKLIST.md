# GitHub Copilot Integration Validation Checklist

Use this checklist to verify that GitHub Copilot is fully integrated and working correctly in your Aria workspace.

## Quick Start (2 minutes)

- [ ] VS Code is open with the Aria project: `code .`
- [ ] Press `Ctrl+Shift+I` to open Copilot Chat
- [ ] See the chat panel with agent options
- [ ] Type `@ai` and see agent dropdown appears
- [ ] Chat input field is responsive

## Extensions (5 minutes)

### Required Extensions

- [ ] GitHub Copilot (GitHub.copilot)
  ```bash
  code --install-extension GitHub.copilot
  ```

- [ ] GitHub Copilot Chat (GitHub.copilot-chat)
  ```bash
  code --install-extension GitHub.copilot-chat
  ```

- [ ] Azure Functions (ms-azuretools.vscode-azurefunctions)
  ```bash
  code --install-extension ms-azuretools.vscode-azurefunctions
  ```

- [ ] Python (ms-python.python)
  ```bash
  code --install-extension ms-python.python
  ```

### Verification

```bash
# Show installed extensions
code --list-extensions | grep -E "copilot|azure|python"
```

Expected output:
```
GitHub.copilot
GitHub.copilot-chat
ms-azuretools.vscode-azurefunctions
ms-python.python
ms-windows-ai-studio.windows-ai-studio
```

## Configuration Files

### `.vscode/settings.json`

- [ ] File exists: `test -f .vscode/settings.json`
- [ ] Valid JSON: `python3 -m json.tool .vscode/settings.json > /dev/null`
- [ ] Contains Copilot settings:
  ```bash
  grep -q "chat.agent.maxRequests\|python.analysis.extraPaths" .vscode/settings.json
  ```

### `.vscode/mcp.json`

- [ ] File exists: `test -f .vscode/mcp.json`
- [ ] Valid JSON: `python3 -m json.tool .vscode/mcp.json > /dev/null`
- [ ] Contains all three servers:
  ```bash
  grep -q "quantum-ai\|llm-maker\|task-complete" .vscode/mcp.json
  ```

### `.vscode/extensions.json`

- [ ] File exists: `test -f .vscode/extensions.json`
- [ ] Valid JSON: `python3 -m json.tool .vscode/extensions.json > /dev/null`
- [ ] Recommends Copilot:
  ```bash
  grep -q "GitHub.copilot" .vscode/extensions.json
  ```

## Custom Agents

Test that custom agents are discoverable:

- [ ] **Primary Agent** (`ai.agent.md`)
  - [ ] File exists: `test -f .github/agents/ai.agent.md`
  - [ ] Can reference via `@ai` in Copilot Chat

- [ ] **Aria Character Agent** (`aria-character.agent.md`)
  - [ ] File exists: `test -f .github/agents/aria-character.agent.md`
  - [ ] Can reference via `@aria-character` in Copilot Chat

- [ ] **Training Agent** (`autonomous-trainer.agent.md`)
  - [ ] File exists: `test -f .github/agents/autonomous-trainer.agent.md`
  - [ ] Can reference via `@autonomous-trainer` in Copilot Chat

- [ ] **Debug Agent** (`full-stack-debugger.agent.md`)
  - [ ] File exists: `test -f .github/agents/full-stack-debugger.agent.md`
  - [ ] Can reference via `@full-stack-debugger` in Copilot Chat

### Count all agents

```bash
ls .github/agents/*.agent.md | wc -l
# Should show 20+
```

## MCP Server Integration

### Quantum AI Server

```bash
# Check file exists
test -f ai-projects/quantum-ml/quantum_mcp_server.py

# Test startup
.venv/bin/python ai-projects/quantum-ml/quantum_mcp_server.py <<< '{}' 2>&1 | head -5
# Should show: {"jsonrpc": "2.0", ...}
```

- [ ] Server file exists
- [ ] Server starts without errors
- [ ] Can be referenced in Copilot Chat via `@quantum-ai`

### LLM Maker Server

```bash
# Check file exists
test -f ai-projects/llm-maker/llm_maker_mcp_server.py

# Test startup
.venv/bin/python ai-projects/llm-maker/llm_maker_mcp_server.py <<< '{}' 2>&1 | head -5
```

- [ ] Server file exists
- [ ] Server starts without errors
- [ ] Can be referenced in Copilot Chat via `@llm-maker`

### Task Complete Server

```bash
# Check file exists
test -f scripts/task_complete_mcp_server.py

# Test startup
.venv/bin/python scripts/task_complete_mcp_server.py <<< '{}' 2>&1 | head -5
```

- [ ] Server file exists
- [ ] Server starts without errors
- [ ] Can be referenced in Copilot Chat via `@task-complete`

## Instructions & Documentation

### Copilot Instructions

- [ ] `copilot-instructions.md` exists
  ```bash
  test -f .github/copilot-instructions.md
  ```

- [ ] `copilot-instructions.full.md` exists
  ```bash
  test -f .github/copilot-instructions.full.md
  ```

- [ ] Both files contain practical guidance
  ```bash
  grep -q "Quick Guide\|Architecture\|Agents" .github/copilot-instructions.md
  ```

### Component Instructions

- [ ] Directory exists: `test -d .github/instructions/`
- [ ] Contains 25+ instruction files:
  ```bash
  ls .github/instructions/*.instructions.md | wc -l
  # Should show 25+
  ```

### Skills & Workflows

- [ ] Skills directory exists: `test -d .github/skills/`
- [ ] Contains 30+ skill workflows:
  ```bash
  ls .github/skills/*/SKILL.md | wc -l
  # Should show 30+
  ```

## Functional Testing

### Test 1: Chat Responsiveness

In Copilot Chat:
```
@ai What are the main components of this project?
```

- [ ] Response appears within 10 seconds
- [ ] Response mentions key components (Aria, quantum, chat)
- [ ] Links to relevant files or sections

### Test 2: Agent Routing

In Copilot Chat:
```
@aria-character Describe what you can do
```

- [ ] Agent responds appropriately
- [ ] References Aria-specific capabilities
- [ ] Mentions action sequences and stage management

### Test 3: MCP Tool Availability

In Copilot Chat:
```
@quantum-ai What quantum tools are available?
```

- [ ] Agent lists quantum tools
- [ ] References circuit creation, simulation, Azure Quantum

### Test 4: Code Assistance

In Copilot Chat:
```
@ai Review the architecture of function_app.py
```

- [ ] Agent analyzes the file
- [ ] Provides specific feedback
- [ ] Suggests improvements if applicable

### Test 5: Skill Application

In Copilot Chat:
```
@full-stack-debugger Explain the debugging workflow for this project
```

- [ ] Agent explains structured debugging
- [ ] References full-stack-debug-escalation-workflow
- [ ] Provides layer-by-layer diagnosis approach

## Performance Validation

### Response Time

Create a simple test:

```python
import time
import subprocess
import json

start = time.time()
# Make a Copilot Chat request
# (This requires manual interaction, but you can measure via browser dev tools)
elapsed = time.time() - start

print(f"Response time: {elapsed:.2f}s")
# Should be < 10s for typical requests
```

- [ ] Initial response time < 10 seconds
- [ ] Streaming responses appear incrementally
- [ ] No freezing or unresponsiveness

### Memory Usage

```bash
# Check VS Code memory
ps aux | grep "code" | grep -v grep | awk '{print $6}'
# Should be < 1GB for normal usage
```

- [ ] VS Code memory usage reasonable (< 1GB)
- [ ] No memory leaks after extended use
- [ ] No crashes during long sessions

## Integration with VS Code

### Settings Sync

- [ ] GitHub account is connected: `Ctrl+Shift+P` → "GitHub: Sign in"
- [ ] Copilot extensions are signed in
- [ ] Settings are synced across machines

### File-Specific Context

Test that instructions load based on file types:

1. Open `function_app.py` — should load functions.instructions.md
2. Open `apps/aria/aria_controller.js` — should load aria*.instructions.md
3. Open `scripts/autonomous_training_orchestrator.py` — should load autonomous-training.instructions.md

- [ ] Appropriate instructions load based on file context
- [ ] Instructions appear in Copilot Chat suggestions

## Documentation Verification

Validate that setup guides exist and are complete:

```bash
# Created during setup
test -f .github/COPILOT_SETUP_GUIDE.md
test -f .vscode/COPILOT_README.md
test -f .github/MCP_SERVERS_REFERENCE.md
test -f .github/COPILOT_ADVANCED_CUSTOMIZATION.md
```

- [ ] COPILOT_SETUP_GUIDE.md exists and is comprehensive
- [ ] COPILOT_README.md exists for quick reference
- [ ] MCP_SERVERS_REFERENCE.md documents all servers
- [ ] COPILOT_ADVANCED_CUSTOMIZATION.md covers extensions

## Integration Tests

### Test Agent to MCP Communication

In Copilot Chat:
```
@quantum-ai Create a simple Bell state circuit
```

- [ ] Agent sends request to quantum-ai MCP server
- [ ] Server responds with circuit definition
- [ ] Response includes QASM format

### Test Custom Instructions

In Copilot Chat:
```
@ai Help me implement a feature following Aria patterns
```

- [ ] Agent references `.github/copilot-instructions.md`
- [ ] Provides guidance specific to this project
- [ ] Suggests relevant component instructions

### Test Skill Application

In Copilot Chat:
```
I'm getting test failures. Help me debug.
```

- [ ] Agent suggests test-first-bugfix-workflow
- [ ] Provides structured debugging approach
- [ ] References test suite configuration

## Troubleshooting Checklist

### Chat Not Opening

- [ ] GitHub.copilot-chat extension is installed
- [ ] GitHub account is signed in
- [ ] VS Code is updated to latest version
- [ ] Try reloading window: `Ctrl+Shift+P` → "Reload Window"

### Agents Not Showing

- [ ] `.github/agents/*.agent.md` files exist
- [ ] Agent YAML frontmatter is valid
- [ ] Reload window and clear cache

### MCP Servers Unavailable

- [ ] `.vscode/mcp.json` is valid JSON
- [ ] Python files are executable (chmod +x)
- [ ] PYTHONPATH environment variables are set
- [ ] Try starting servers manually:
  ```bash
  .venv/bin/python ai-projects/quantum-ml/quantum_mcp_server.py
  ```

### Slow Performance

- [ ] Reduce `chat.agent.maxRequests` in settings
- [ ] Close other VS Code windows
- [ ] Check available memory: `free -h`
- [ ] Monitor network connectivity

## Final Verification

Run the complete validation:

```bash
# Quick validation script
python3 -c "
import json, os
from pathlib import Path

checks = {
    'Settings JSON': os.path.isfile('.vscode/settings.json'),
    'MCP JSON': os.path.isfile('.vscode/mcp.json'),
    'Copilot Instructions': os.path.isfile('.github/copilot-instructions.md'),
    'Agents Folder': os.path.isdir('.github/agents'),
    'Skills Folder': os.path.isdir('.github/skills'),
    'Instructions Folder': os.path.isdir('.github/instructions'),
}

agent_count = len(list(Path('.github/agents').glob('*.agent.md')))
skills_count = len(list(Path('.github/skills').glob('*/SKILL.md')))

print('Copilot Integration Status:')
print('=' * 40)
for check, result in checks.items():
    status = '✓' if result else '✗'
    print(f'{status} {check}')

print(f'✓ {agent_count} custom agents found')
print(f'✓ {skills_count} skill workflows found')
print('=' * 40)
print('Status: Ready ✓' if all(checks.values()) else 'Status: Setup Needed ✗')
"
```

Expected output:
```
Copilot Integration Status:
========================================
✓ Settings JSON
✓ MCP JSON
✓ Copilot Instructions
✓ Agents Folder
✓ Skills Folder
✓ Instructions Folder
✓ 20 custom agents found
✓ 34 skill workflows found
========================================
Status: Ready ✓
```

## Sign-Off

- [ ] All extensions are installed
- [ ] All configuration files are valid
- [ ] All agents are discoverable
- [ ] All MCP servers are functional
- [ ] Documentation is complete and accessible
- [ ] Basic functional tests pass
- [ ] Performance is acceptable
- [ ] Ready for active development with Copilot

---

## Support & Resources

- **Setup Guide**: `.github/COPILOT_SETUP_GUIDE.md`
- **Quick Reference**: `.github/copilot-instructions.md`
- **Full Instructions**: `.github/copilot-instructions.full.md`
- **MCP Reference**: `.github/MCP_SERVERS_REFERENCE.md`
- **Advanced Customization**: `.github/COPILOT_ADVANCED_CUSTOMIZATION.md`
- **Component Instructions**: `.github/instructions/`

**Validation completed! Aria is ready for GitHub Copilot integration. 🎉**
