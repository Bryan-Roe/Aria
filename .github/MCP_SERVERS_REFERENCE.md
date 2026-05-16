# MCP Server Integration Reference

This document provides a comprehensive reference for the Model Context Protocol (MCP) servers integrated into the Aria GitHub Copilot workspace.

## Table of Contents

- [Overview](#overview)
- [Installed MCP Servers](#installed-mcp-servers)
- [Communicating with MCP Servers](#communicating-with-mcp-servers)
- [Quantum AI Server](#quantum-ai-server)
- [LLM Maker Server](#llm-maker-server)
- [Task Complete Server](#task-complete-server)
- [Adding New MCP Servers](#adding-new-mcp-servers)
- [Troubleshooting](#troubleshooting)

## Overview

MCP (Model Context Protocol) servers extend GitHub Copilot Chat with specialized tools and capabilities. Each server:

- Runs as a separate Python process
- Communicates via stdio with JSON-RPC messages
- Exposes domain-specific tools
- Automatically starts when Copilot Chat opens

### Architecture

```
GitHub Copilot Chat
         ↓
    [MCP Client]
         ↓
  ┌──────────────────┐
  │ MCP Servers      │
  ├──────────────────┤
  │ · quantum-ai     │  →  Quantum ML
  │ · llm-maker      │  →  Code Generation
  │ · task-complete  │  →  Task Tracking
  └──────────────────┘
```

## Installed MCP Servers

### Server Locations

| Server | Path | Status |
| -------- | ------ | -------- |
| quantum-ai | `ai-projects/quantum-ml/quantum_mcp_server.py` | ✅ Active |
| llm-maker | `ai-projects/llm-maker/llm_maker_mcp_server.py` | ✅ Active |
| task-complete | `scripts/task_complete_mcp_server.py` | ✅ Active |

### Configuration

All servers are configured in `.vscode/mcp.json`:

```json
{
  "servers": {
    "quantum-ai": {
      "type": "stdio",
      "command": "python3",
      "args": ["${workspaceFolder}/ai-projects/quantum-ml/quantum_mcp_server.py"],
      "env": {
        "PYTHONPATH": "${workspaceFolder}/ai-projects/quantum-ml"
      }
    },
    "llm-maker": {
      "type": "stdio",
      "command": "python3",
      "args": ["${workspaceFolder}/ai-projects/llm-maker/llm_maker_mcp_server.py"],
      "env": {
        "PYTHONPATH": "${workspaceFolder}/ai-projects/llm-maker:${workspaceFolder}"
      }
    },
    "task-complete": {
      "type": "stdio",
      "command": "python3",
      "args": ["${workspaceFolder}/scripts/task_complete_mcp_server.py"]
    }
  }
}
```

## Communicating with MCP Servers

### Using Agents

Reference servers directly in Copilot Chat:

```
@quantum-ai Create a Bell state circuit
@llm-maker Generate a Python email validator
@task-complete Mark this training as complete
```

### Agent-to-Server Routing

When you use a specialized agent, Copilot Chat automatically:

1. Receives your request
2. Routes to the appropriate MCP server
3. Invokes the relevant tool
4. Returns results with context

### Tool Discovery

Copilot Chat automatically discovers available tools from each server:

- **Quantum AI** tools: Circuit creation, simulation, Azure Quantum submission
- **LLM Maker** tools: Function generation, website generation, validation
- **Task Complete** tools: Task status, completion tracking, artifact management

## Quantum AI Server

**Location**: `ai-projects/quantum-ml/quantum_mcp_server.py`

**Purpose**: Quantum circuit design, simulation, and Azure Quantum job management

### Available Tools

#### 1. Create Quantum Circuit

Create a quantum circuit with specified parameters:

```
Request:
@quantum-ai Create a 3-qubit GHZ state circuit

Server Response:
{
  "circuit": "OPENQASM 2.0;...",
  "qubit_count": 3,
  "description": "GHZ state preparation"
}
```

#### 2. Simulate Circuit

Run local simulation using Qiskit Aer:

```
Request:
@quantum-ai Simulate a Bell state with 1024 shots

Server Response:
{
  "results": {
    "00": 512,
    "11": 512
  },
  "execution_time": 0.234,
  "backend": "qasm_simulator"
}
```

#### 3. Submit to Azure Quantum

Submit job to real quantum hardware or simulator:

```
Request:
@quantum-ai Submit this circuit to IonQ simulator

Server Response:
{
  "job_id": "abc123...",
  "status": "submitted",
  "estimated_cost": "$0.50",
  "backend": "azure_ionq_simulator"
}
```

#### 4. Check Job Status

Monitor quantum job execution:

```
Request:
@quantum-ai Check the status of job abc123

Server Response:
{
  "job_id": "abc123",
  "status": "completed",
  "results": {...},
  "execution_time": 1.234
}
```

### Best Practices

1. **Start with simulation** — Always test circuits locally first
2. **Use Azure simulator** — Test Azure Quantum before real QPU
3. **Check costs** — Review cost estimates before QPU submission
4. **Monitor jobs** — Use status checks to track execution

### Cost Gating

Quantum AI server includes safety features:

- **Simulator-first policy** — Tests run locally by default
- **Cost estimation** — Estimates before Azure Quantum submission
- **Confirmation gates** — User confirmation for paid QPU access
- **Timeout protection** — Prevents long-running jobs

### Example Workflow

```bash
# 1. Design circuit locally
@quantum-ai Create a variational ansatz circuit

# 2. Simulate locally
@quantum-ai Simulate the circuit with 10000 shots

# 3. Optimize (if needed)
@quantum-ai Improve the circuit for IonQ backend

# 4. Submit to simulator
@quantum-ai Submit to Azure IonQ simulator

# 5. Monitor execution
@quantum-ai Check job status: [job-id]
```

## LLM Maker Server

**Location**: `ai-projects/llm-maker/llm_maker_mcp_server.py`

**Purpose**: Safe LLM-powered code and website generation with validation

### Available Tools

#### 1. Generate Python Function

Create validated Python functions:

```
Request:
@llm-maker Generate a function that validates email addresses

Server Response:
{
  "code": "def validate_email(email: str) -> bool:\n    ...",
  "validation": "passed",
  "imports": ["re"],
  "safety_checks": "safe (no dangerous imports)"
}
```

#### 2. Generate Website

Create complete HTML/CSS/JS websites:

```
Request:
@llm-maker Build a portfolio website with 3 pages

Server Response:
{
  "files": {
    "index.html": "...",
    "style.css": "...",
    "script.js": "..."
  },
  "validation": "passed",
  "web_framework": "vanilla"
}
```

#### 3. Validate Code

Check code safety and imports:

```
Request:
@llm-maker Validate this Python code for safe imports

Server Response:
{
  "is_safe": true,
  "dangerous_imports": [],
  "issues": [],
  "recommendations": []
}
```

#### 4. Regenerate (Retry)

Regenerate code if validation fails:

```
Request:
@llm-maker The generated function uses os.system. Regenerate without system calls.

Server Response:
{
  "code": "def validate_email(email: str) -> bool:\n    ...",
  "validation": "passed"
}
```

### Safety Features

LLM Maker includes strict safety validation:

- **AST-based analysis** — Parses Python code as abstract syntax tree
- **Dangerous import blocking** — Blocks: os, sys, subprocess, socket, pickle, eval, exec
- **Function validation** — Ensures generated functions are syntactically correct
- **Retry on failure** — Automatically regenerates on validation failure

### Blocked Imports (Security)

The following imports are forbidden:

```
os              # System operations
sys             # System access
subprocess      # Process execution
socket          # Network access
pickle          # Serialization security
eval, exec      # Code execution
__import__      # Dynamic imports
ctypes          # C Library binding
```

### Usage Examples

#### Generate a Data Processor

```
@llm-maker Generate a function to parse CSV files and return a Python list of dictionaries
```

#### Build a React Component

```
@llm-maker Create a React component for a user profile card with name, email, and photo
```

#### Safe API Client

```
@llm-maker Create a Python class to make API requests with retry logic and error handling
```

## Task Complete Server

**Location**: `scripts/task_complete_mcp_server.py`

**Purpose**: Task completion tracking and artifact management

### Available Tools

#### 1. Mark Task Complete

Signal task completion:

```
Request:
@task-complete Mark this training run complete with 95.2% accuracy

Server Response:
{
  "task_id": "train-xyz",
  "status": "completed",
  "summary": "95.2% accuracy achieved",
  "timestamp": "2026-03-29T10:30:00Z"
}
```

#### 2. Create Task Record

Create a new task in tracking system:

```
Request:
@task-complete Create task: Training LoRA model on customer-support dataset

Server Response:
{
  "task_id": "task-123",
  "created_at": "2026-03-29T10:00:00Z",
  "status": "in_progress"
}
```

#### 3. Note Progress

Log progress without completing:

```
Request:
@task-complete Note: 50% complete, evaluating on validation set

Server Response:
{
  "task_id": "train-xyz",
  "status": "in_progress",
  "progress": 50
}
```

#### 4. List Tasks

Show active tasks:

```
Request:
@task-complete List all active tasks

Server Response:
{
  "tasks": [
    {"task_id": "train-xyz", "status": "in_progress"},
    {"task_id": "eval-abc", "status": "pending"}
  ]
}
```

### Usage Examples

```
# Training completion
@task-complete Mark complete: LoRA model trained with final accuracy 0.942

# Evaluation tracking
@task-complete Note: F1-score evaluation complete, reviewing results

# Feature development
@task-complete Mark complete: Implemented auto-execute system for Aria character
```

## Adding New MCP Servers

### Step 1: Create Server Script

Create a new MCP server (Python example):

```python
# scripts/my_mcp_server.py
from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("my-server")

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> TextContent:
    if name == "hello":
        return TextContent(text=f"Hello {arguments['name']}")
    return TextContent(text="Unknown tool")

if __name__ == "__main__":
    server.run()
```

### Step 2: Register in MCP Configuration

Add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "my-server": {
      "type": "stdio",
      "command": "python3",
      "args": ["${workspaceFolder}/scripts/my_mcp_server.py"],
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    }
  }
}
```

### Step 3: Reload VS Code

- Press `Ctrl+Shift+P`
- Type "Reload Window"
- Press Enter

### Step 4: Test

In Copilot Chat:
```
@my-server hello world
```

## Troubleshooting

### MCP Servers Not Appearing

**Symptom**: MCP tools not available in Copilot Chat

**Diagnosis**:
```bash
# Check if MCP configuration is valid JSON
python3 -m json.tool .vscode/mcp.json

# Check if server files exist
ls ai-projects/quantum-ml/quantum_mcp_server.py
ls ai-projects/llm-maker/llm_maker_mcp_server.py
ls scripts/task_complete_mcp_server.py
```

**Solutions**:
1. Verify `.vscode/mcp.json` is valid JSON (no trailing commas)
2. Ensure Python files are executable: `chmod +x *.py`
3. Reload VS Code: `Ctrl+Shift+P` → "Reload Window"
4. Check Python path: Confirm PYTHONPATH is set correctly

### Server Startup Errors

**Symptom**: "Failed to start MCP server"

**Check logs**:
```bash
# Run server manually to see errors
python3 ai-projects/quantum-ml/quantum_mcp_server.py 2>&1 | head -20
```

**Common Issues**:
- Missing dependencies: Install with `pip install -r requirements.txt`
- Wrong Python path: Verify PYTHONPATH in mcp.json
- Port conflict: Check if port is already in use

### Slow Response from MCP Server

**Symptom**: MCP tools take a long time to respond

**Optimizations**:
1. **Enable caching**: Check if server has caching enabled
2. **Reduce scope**: Use specific requests instead of broad ones
3. **Check resources**: Monitor CPU/memory during execution
4. **Reload server**: Stop Copilot Chat and reload window

### MCP Server Crashes

**Symptom**: MCP server crashes mid-execution

**Debugging**:
1. Check stdout/stderr for error messages
2. Review server logs: `cat data_out/mcp_server.log`
3. Test server isolation (run alone without Copilot)
4. Check for unhandled exceptions in tool handlers

## Best Practices

### 1. Use Agents for Server Routing

Instead of:
```
Use the quantum-ai MCP server to create a circuit
```

Do:
```
@quantum-ai Create a Bell state circuit
```

Copilot Chat automatically routes to the correct server.

### 2. Handle Server Failures

MCP servers include fallback behavior:

```
If quantum-ai is unavailable:
1. Copilot Chat disables quantum-specific tools
2. Suggests alternatives
3. Logs the failure for debugging
```

### 3. Monitor Server Health

Before critical tasks:
```bash
# Quick health check
python3 ai-projects/quantum-ml/quantum_mcp_server.py <<< '{}' | head -3

# Full introspection
@quantum-ai List available quantum tools
```

### 4. Version Compatibility

Keep MCP dependencies current:

```bash
pip install --upgrade mcp>=0.9.0
```

## MCP Protocol Resources

- **Official MCP Spec**: https://modelcontextprotocol.io/
- **Python SDK**: https://github.com/modelcontextprotocol/python-sdk
- **Example Servers**: https://github.com/modelcontextprotocol/servers

---

**Happy integrating! For issues, check the troubleshooting section or open an issue with MCP server logs attached.**
