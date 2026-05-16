# GitHub Copilot Integration Guide for Aria

This guide provides a complete overview of GitHub Copilot integration in the Aria project, including setup instructions, custom agents, MCP servers, skills, and best practices.

**Last updated**: March 29, 2026

## Table of Contents

- [Quick Start](#quick-start)
- [Architecture Overview](#architecture-overview)
- [VS Code Configuration](#vs-code-configuration)
- [Custom Agents](#custom-agents)
- [MCP Server Integration](#mcp-server-integration)
- [Skills & Workflows](#skills--workflows)
- [Component-Specific Instructions](#component-specific-instructions)
- [Prompts & Best Practices](#prompts--best-practices)
- [Troubleshooting](#troubleshooting)

## Quick Start

### 1. Install Required Extensions

Aria requires these VS Code extensions for full Copilot integration:

```bash
# Install from Extensions panel (Ctrl+Shift+X) or CLI
code --install-extension ms-azuretools.vscode-azurefunctions
code --install-extension ms-python.python
code --install-extension ms-windows-ai-studio.windows-ai-studio
code --install-extension GitHub.copilot
code --install-extension GitHub.copilot-chat
```

**Note**: Recommended extensions are pre-configured in `.vscode/extensions.json`.

### 2. Open the Project in VS Code

```bash
cd /workspaces/Aria
code .
```

### 3. Verify Copilot Chat is Active

- Open GitHub Copilot Chat: Press `Ctrl+Shift+I` (or `Cmd+Shift+I` on Mac)
- You should see the chat panel with agent options
- Aria-specific agents will appear in the agent dropdown

### 4. Start with an Agent

Use `@` to mention an agent or select from the dropdown:

```
@ai-architect Design a new RAG pipeline for semantic memory
@aria-character Make Aria wave and say hello
@autonomous-trainer Start training the next LoRA model
```

## Architecture Overview

### Copilot Integration Layers

```
┌─────────────────────────────────────────────┐
│   GitHub Copilot Chat (VS Code)             │
├─────────────────────────────────────────────┤
│   Agents Layer (.github/agents/*.agent.md)  │
│   - ai.agent.md (primary autonomous agent)  │
│   - aria-character.agent.md (Aria control)  │
│   - autonomous-trainer.agent.md (ML ops)    │
│   - [15+ domain-specific agents]            │
├─────────────────────────────────────────────┤
│   Instructions Layer                        │
│   - copilot-instructions.md (quick ref)     │
│   - copilot-instructions.full.md (comprehensive)
│   - .github/instructions/*.md (per-component)
├─────────────────────────────────────────────┤
│   Skills Layer (.github/skills/)            │
│   - debug workflows                         │
│   - refactoring workflows                   │
│   - testing workflows                       │
│   - optimization workflows                  │
├─────────────────────────────────────────────┤
│   MCP Servers (Model Context Protocol)      │
│   - quantum-ai (quantum ML)                 │
│   - llm-maker (code generation)             │
│   - task-complete (task tracking)           │
├─────────────────────────────────────────────┤
│   Prompts Layer (.github/prompts/)          │
│   - Specialized prompts for reasoning       │
│   - Chain-of-thought templates              │
│   - Domain-specific workflows               │
└─────────────────────────────────────────────┘
```

## VS Code Configuration

### Settings File: `.vscode/settings.json`

Key Copilot-related settings:

```json
{
  // Copilot Chat Agent Configuration
  "chat.agent.maxRequests": 200,

  // Python Analysis for Code Intelligence
  "python.analysis.extraPaths": [
    "./ai-projects/llm-maker/src",
    "./aria_web",
    "./tests/test_",
    "./ai-projects/quantum-ml/src"
  ],
  "python.analysis.autoImportCompletions": true,

  // MCP Server Sampling (Model routing)
  "chat.mcp.serverSampling": {
    "Aria/.vscode/mcp.json: phi-model-server": {
      "allowedModels": [
        "copilot/auto",
        "copilot/gpt-4o",
        "copilot/claude-opus-4.6",
        "copilot/gemini-2.5-pro"
      ]
    }
  },

  // Testing Configuration for Copilot-aware test discovery
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["-v", "--tb=short", "--no-header"]
}
```

### MCP Configuration: `.vscode/mcp.json`

The MCP (Model Context Protocol) configuration connects Copilot to specialized servers:

```json
{
  "servers": {
    "quantum-ai": {
      "description": "Quantum ML pipelines, circuit design, and Azure Quantum integration",
      "type": "stdio",
      "command": "python3",
      "args": ["${workspaceFolder}/ai-projects/quantum-ml/quantum_mcp_server.py"],
      "env": {
        "PYTHONPATH": "${workspaceFolder}/ai-projects/quantum-ml"
      }
    },
    "llm-maker": {
      "description": "Safe LLM-powered code generation and website creation",
      "type": "stdio",
      "command": "python3",
      "args": ["${workspaceFolder}/ai-projects/llm-maker/llm_maker_mcp_server.py"],
      "env": {
        "PYTHONPATH": "${workspaceFolder}/ai-projects/llm-maker:${workspaceFolder}"
      }
    },
    "task-complete": {
      "description": "Task completion tracking and artifact management",
      "type": "stdio",
      "command": "python3",
      "args": ["${workspaceFolder}/scripts/task_complete_mcp_server.py"]
    }
  }
}
```

**How MCP Servers Work**:
- Copilot Chat automatically discovers and loads these servers
- Each server exposes domain-specific tools and capabilities
- Tools appear in Copilot Chat's tool suggestions
- Use `@mcp-server-name` to route requests to specific servers

## Custom Agents

Aria includes **20+ specialized agents** for different development workflows. Each agent is configured in `.github/agents/`.

### Core Agents

| Agent | Purpose | Trigger Phrases |
| ------- | --------- | ---------------- |
| `ai.agent.md` | Primary autonomous agent for task decomposition | "break this down", "reason through this" |
| `aria-character.agent.md` | Aria interactive character control | "make Aria", "create a world", "action sequence" |
| `autonomous-trainer.agent.md` | LoRA training & model lifecycle | "train a model", "fine-tune", "evaluate models" |
| `ai-architect.agent.md` | AI system architecture & design | "design an AI pipeline", "plan the architecture" |
| `full-stack-debugger.agent.md` | Cross-stack issue diagnosis | "debug this", "why is this failing", "troubleshoot" |

### Specialized Agents

**Training & ML**:
- `AI_model_training.agent.md` — End-to-end training workflow
- `autonomous-trainer.agent.md` — Autonomous training orchestration
- `data-pipeline.agent.md` — Batch evaluation & dataset curation

**Chat & Memory**:
- `chat-provider.agent.md` — Multi-provider chat integration
- `AI_chat_development.agent.md` — Chat system development

**Quantum**:
- `Quantum_ML_development.agent.md` — Quantum circuits & Azure Quantum

**Character & UI**:
- `Aria_character_development.agent.md` — Character system & animations
- `aria-character.agent.md` — Real-time character control

**Code Generation**:
- `llm-maker.agent.md` — Safe tool & website generation
- `automated-code-fixer.agent.md` — Autonomous code improvements

**Platform Operations**:
- `platform-ops.agent.md` — Subscriptions, monitoring, deployment
- `vision-ai.agent.md` — Vision inference & expression classification

### How to Use Agents

**In Copilot Chat:**
```
@aria-character Walk Aria to the table and pick up the sphere
```

**Or select from dropdown:**
1. Open Copilot Chat (`Ctrl+Shift+I`)
2. Click the agent dropdown
3. Select the agent you want
4. Type your request

**Agent Selection Tips**:
- **Unsure?** Start with `@ai` (primary agent) — it will route to specialists automatically
- **Know the domain?** Pick the specialized agent directly for better context
- **Complex task?** Use `@ai` for automatic task decomposition and delegat­ion
- **Quick fix?** Use domain-specific agents for faster, focused responses

## MCP Server Integration

### Starting MCP Servers

MCP servers start automatically when you open the project in VS Code. To manually test:

```bash
# Test quantum-ai MCP server
python3 ai-projects/quantum-ml/quantum_mcp_server.py

# Test llm-maker MCP server
python3 ai-projects/llm-maker/llm_maker_mcp_server.py

# Test task-complete MCP server
python3 scripts/task_complete_mcp_server.py
```

### Available MCP Tools

#### Quantum AI Server
Provides quantum circuit design, simulation, and Azure Quantum integration:
- Create quantum circuits (QASM format)
- Simulate circuits locally (Qiskit Aer)
- Submit jobs to Azure Quantum
- Cost estimation and safety gates

**Example**:
```
@quantum-ai Design a Bell state circuit and simulate it
```

#### LLM Maker Server
Safe, validated code and website generation:
- Generate Python functions with AST validation
- Create complete HTML/CSS/JS websites
- Built-in safety checks (no dangerous imports)
- Retry & regeneration on validation failure

**Example**:
```
@llm-maker Create a Python function that validates email addresses
```

#### Task Complete Server
Task tracking and completion management:
- Mark tasks as complete with summaries
- Track task status and artifacts
- Manage memory and history

**Example**:
```
@task-complete Mark this training run as complete with evaluation results
```

### Debugging MCP Connections

If MCP servers don't appear in Copilot Chat:

1. **Check server status**:
   ```bash
   # Look for server processes
   ps aux | grep "quantum_mcp_server\|llm_maker_mcp_server\|task_complete_mcp_server"
   ```

2. **Test individual server**:
   ```bash
   python3 ai-projects/quantum-ml/quantum_mcp_server.py 2>&1 | head -20
   ```

3. **Verify configuration**:
   - Open VS Code settings: `Ctrl+,`
   - Search for "mcp"
   - Check `.vscode/mcp.json` exists and is valid JSON

4. **Reload window**:
   - `Ctrl+Shift+P` → "Developer: Reload Window"

## Skills & Workflows

Aria includes **34+ skill workflows** in `.github/skills/` for structured problem-solving.

### Skill Categories

**Debugging Workflows**:
- `agi-reasoning-debug-workflow` — AGI provider reasoning chains
- `aria-character-debug-workflow` — Character command parsing
- `chat-cli-debug-workflow` — Chat CLI provider selection
- `chat-provider-debug-workflow` — Provider detection issues
- `quantum-pipeline-debug-workflow` — Quantum job failures
- `full-stack-debug-escalation-workflow` — Cross-stack debugging

**Refactoring & Optimization**:
- `safe-refactor-workflow` — Safe, multi-file refactoring
- `repo-change-workflow` — Systematic code changes
- `release-readiness-workflow` — Pre-release validation

**Feature & Testing**:
- `test-first-bugfix-workflow` — Test-driven bug fixes
- `test-suite-triage-workflow` — Test failure isolation
- `model-evaluation-workflow` — Model benchmarking

**Configuration & Operations**:
- `orchestrator-config-debug-workflow` — YAML config issues
- `platform-health-triage-workflow` — System health diagnostics
- `provider-config-audit-workflow` — Provider setup verification

### Using Skills

Copilot automatically applies relevant skills based on your request. You can also explicitly reference them:

```
Use the safe-refactor-workflow to refactor the chat_providers module
Use the test-first-bugfix-workflow to fix the failing token_utils tests
Use the platform-health-triage-workflow to diagnose why services are degraded
```

**Skills are loaded automatically** based on:
- File paths being edited
- Keywords in your request
- Current context in the workspace

## Component-Specific Instructions

Detailed instructions for each major component:

| Component | Instruction File |
| ----------- | ------------------ |
| Azure Functions API endpoints | `instructions/functions.instructions.md` |
| Aria interactive character | `instructions/aria-character.instructions.md` |
| Chat providers & multi-provider | `instructions/chat-providers.instructions.md` |
| Quantum ML pipelines | `instructions/quantum-ai.instructions.md` |
| LoRA fine-tuning training | `instructions/lora.instructions.md` |
| Autonomous training orchestration | `instructions/autonomous-training.instructions.md` |
| Chat memory & embeddings | `instructions/chat-memory.instructions.md` |
| Dashboard & monitoring | `instructions/dashboard.instructions.md` |
| Shared infra (SQL, Cosmos, telemetry) | `instructions/shared-python.instructions.md` |
| Testing infrastructure | `instructions/tests.instructions.md` |
| Token management & budget | `instructions/token-utils.instructions.md` |
| Vision inference & emotions | `instructions/vision-inference.instructions.md` |
| LLM-powered code generation | `instructions/llm-maker.instructions.md` |

**These load automatically** when you edit related files. Specific instructions apply based on file paths.

## Prompts & Best Practices

Aria includes **20+ specialized prompts** in `.github/prompts/` that guide Copilot for specific tasks.

### Common Prompts

| Prompt | Purpose |
| -------- | --------- |
| `agi.prompt.md` | Autonomous long-running work with internal reasoning (chain-of-thought is hidden) |
| `debug.prompt.md` | Systematic debugging protocol |
| `reason.prompt.md` | Structured analysis & planning |
| `review.prompt.md` | Security, performance, correctness review |
| `train.prompt.md` | Safe training execution |
| `quantum.prompt.md` | Cost-aware quantum workflows |
| `deploy.prompt.md` | Safe deployment pipelines |

### Using Prompts Effectively

**Explicit reference**:
```
Use the agi.prompt for autonomous long-running work requiring internal reasoning
Use the debug.prompt to systematically diagnose this error
```

**Implicit loading**:
- Prompts load automatically based on context
- Copilot routes to relevant prompts based on request type
- No explicit mention needed — they're part of the agent's reasoning

## Best Practices

### 1. Start with the Right Agent

- **Unsure?** → Use `@ai` (automatic routing)
- **Building features?** → Use domain-specific agents
- **Debugging?** → Use `@full-stack-debugger`
- **Character system?** → Use `@aria-character`
- **Model training?** → Use `@autonomous-trainer`

### 2. Provide Context

```
Good: "Make Aria walk to the table and pick up the sphere"
Better: "In stage mode, make Aria walk to the table at coordinates (5,5) and pick up the blue sphere object"

Good: "Fix the failing test"
Better: "The test_chat_streaming test is failing with timeout in the SSE response handler. Use the test-first-bugfix-workflow to reproduce and fix it."
```

### 3. Use the Right Tools

- Use **MCP servers** for specialized domains (quantum, code gen)
- Use **skills** for structured problem-solving
- Use **agents** for creative work or complex decomposition
- Use **instructions** as reference (they load automatically)

### 4. Leverage Multi-Provider Safety

The system includes fallback providers. If one fails:
- Azure OpenAI → OpenAI → LMStudio → Local
- Copilot will automatically retry with appropriate prompts

### 5. Review Before Committing

Always:
- Run `python3 scripts/pre_commit_check.py` before pushing
- Run integration tests: `./scripts/integration_contract_gate.sh`
- Run full validation: `python3 scripts/test_runner.py --unit`

## Troubleshooting

### Copilot Chat Not Appearing

**Problem**: Copilot Chat sidebar missing

**Solution**:
1. Install GitHub Copilot Chat extension
2. Sign in to GitHub (Ctrl+Shift+P → "GitHub: Sign in")
3. Restart VS Code

### Agents Not Showing

**Problem**: Custom agents not in dropdown

**Solution**:
1. Verify `.github/agents/` files exist
2. Reload VS Code: `Ctrl+Shift+P` → "Developer: Reload Window"
3. Check `.github/copilot-instructions.md` is present

### MCP Servers Not Available

**Problem**: MCP tools not showing in chat

**Solution**:
1. Check `.vscode/mcp.json` is valid JSON
2. Verify Python files exist:
   - `ai-projects/quantum-ml/quantum_mcp_server.py`
   - `ai-projects/llm-maker/llm_maker_mcp_server.py`
   - `scripts/task_complete_mcp_server.py`
3. Reload VS Code
4. Check terminal for MCP startup errors

### Slow Response Time

**Problem**: Copilot Chat is slow

**Solutions**:
- Reduce project scope by using file-specific agents
- Use simpler requests to warm up the model
- Check `chat.agent.maxRequests` setting (default: 200)
- Verify network connection to Copilot backend

### Memory Issues

**Problem**: "Memory limit exceeded" error

**Solution**:
- Check available memory: `free -h`
- Close other VS Code windows
- Reload the current window
- Disable unused extensions

## Advanced Configuration

### Custom Model Routing

Edit `.vscode/settings.json` to route requests to specific models:

```json
{
  "chat.mcp.serverSampling": {
    "Aria/.vscode/mcp.json: phi-model-server": {
      "allowedModels": [
        "copilot/gpt-4o",      // Default
        "copilot/claude-opus-4.6",  // Reasoning tasks
        "copilot/gemini-2.5-pro"   // Long context
      ]
    }
  }
}
```

### Adding New Agents

1. Create `/.github/agents/my-agent.agent.md`:
   ```yaml
   ---
   name: my-agent
   description: "What this agent does"
   tools:
     - edit
     - vscode/runCommand
     - execute/runInTerminal
   ---
   # My Custom Agent
   Description and behavior...
   ```

2. Reload VS Code
3. Agent appears in dropdown

### Adding New MCP Servers

1. Create MCP server script (Python, Node.js, etc.)
2. Add to `.vscode/mcp.json`:
   ```json
   {
     "servers": {
       "my-server": {
         "type": "stdio",
         "command": "python3",
         "args": ["./path/to/server.py"]
       }
     }
   }
```

3. Reload VS Code

## Resources

- **Copilot Chat Basics**: https://docs.github.com/en/copilot/using-github-copilot/using-copilot-in-the-cli
- **MCP Protocol**: https://modelcontextprotocol.io/
- **Aria Quick Reference**: `./ARIA_QUICKREF.txt`
- **Full Instructions**: `.github/copilot-instructions.full.md`
- **Component Guides**: `.github/instructions/`

## Support

For issues or questions:
1. Check this guide's troubleshooting section
2. Review `.github/copilot-instructions.full.md` for detailed patterns
3. Use `@full-stack-debugger` agent to diagnose issues
4. Check specific component instructions in `.github/instructions/`

---

**Happy coding with Aria's Copilot integration! 🚀**
