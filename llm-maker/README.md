# LLM Maker - Autonomous Tool Creation for LLMs

LLM Maker is a framework that enables Large Language Models to autonomously create, validate, and use Python tools. It provides a safe, sandboxed environment for dynamic tool generation and execution.

## 🎯 Overview

LLM Maker allows LLMs to:
- **Create Tools**: Generate Python functions from natural language descriptions
- **Validate Tools**: Automatically verify generated code for safety and correctness
- **Execute Tools**: Run tools in a sandboxed environment with resource limits
- **Manage Tools**: Store, retrieve, and version generated tools

## 🚀 Quick Start

### Installation

```bash
cd llm-maker
pip install -r requirements.txt
```

### Basic Usage

```python
from llm_maker import ToolMaker, ToolRegistry

# Initialize tool maker
maker = ToolMaker()
registry = ToolRegistry()

# Create a tool from description
tool = maker.create_tool(
    name="calculate_fibonacci",
    description="Calculate the nth Fibonacci number",
    parameters={"n": "int"},
    return_type="int"
)

# Validate the tool
if maker.validate_tool(tool):
    # Register it
    registry.register(tool)
    
    # Use it
    result = registry.execute("calculate_fibonacci", {"n": 10})
    print(f"Result: {result}")
```

### MCP Server Integration

Start the LLM Maker MCP server:

```bash
python llm_maker_mcp_server.py
```

Available MCP tools:
- `create_tool` - Generate a new tool from description
- `validate_tool` - Check if a tool is safe to use
- `execute_tool` - Run a registered tool
- `list_tools` - Show all available tools
- `delete_tool` - Remove a tool from registry

## 📁 Directory Structure

```
llm-maker/
├── src/
│   ├── tool_maker.py       # Core tool generation
│   ├── tool_validator.py   # Safety validation
│   ├── tool_executor.py    # Sandboxed execution
│   ├── tool_registry.py    # Tool management
│   └── __init__.py
├── tools/                  # Generated tools storage
├── tests/                  # Test suite
├── examples/              # Example tools
├── llm_maker_mcp_server.py # MCP server
├── requirements.txt       # Dependencies
└── README.md
```

## 🔧 Features

### Tool Generation

LLM Maker uses AI providers (Azure OpenAI, OpenAI, or local models) to generate Python functions.

### Safety Validation

All generated tools are validated for:
- **No dangerous imports** (os, subprocess, sys, etc.)
- **No file system access** (open, write, delete)
- **No network access** (requests, urllib, socket)
- **No code execution** (eval, exec, compile)
- **Resource limits** (execution time, memory)

### Sandboxed Execution

Tools run in a restricted environment:
- Limited execution time (default: 5 seconds)
- Memory limits
- No access to system resources
- Exception handling and logging

## 🔒 Security

LLM Maker implements multiple security layers:

1. **Static Analysis**: Code is analyzed before execution
2. **Sandboxing**: Restricted Python environment
3. **Resource Limits**: CPU time, memory, and I/O limits
4. **Whitelist**: Only safe built-in functions allowed
5. **Logging**: All tool executions are logged

---

**Last Updated:** December 8, 2025
