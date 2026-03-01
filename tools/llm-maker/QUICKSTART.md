# LLM Maker - Quick Start Guide

## What is LLM Maker?

LLM Maker is an autonomous tool creation system that allows Large Language Models to:
- Generate Python functions from natural language descriptions
- Validate generated code for safety
- Execute tools in a sandboxed environment
- Manage and reuse tools

## Installation

```bash
cd llm-maker
pip install -r requirements.txt
```

## Basic Usage

### 1. Create a Tool Programmatically

```python
from llm_maker import ToolMaker, ToolRegistry

# Initialize
maker = ToolMaker()
registry = ToolRegistry()

# Create a tool from description
tool = maker.create_tool(
    name="calculate_factorial",
    description="Calculate the factorial of a number",
    parameters={"n": "int"},
    return_type="int"
)

# Register it
tool_id = registry.register(tool)
```

### 2. Execute a Tool

```python
from llm_maker import ToolExecutor

executor = ToolExecutor()

# Execute the tool
result = executor.execute(
    code=tool.code,
    function_name="calculate_factorial",
    args={"n": 5}
)

if result['success']:
    print(f"Result: {result['result']}")
else:
    print(f"Error: {result['error']}")
```

### 3. Use the MCP Server

Start the MCP server:

```bash
python llm_maker_mcp_server.py
```

Then connect with an MCP client to use these tools:
- `create_tool` - Generate tools
- `execute_tool` - Run tools
- `list_registered_tools` - Browse tools
- `get_tool` - Get tool details
- `delete_tool` - Remove tools
- `validate_tool` - Check safety
- `registry_stats` - Usage statistics

## Examples

### Example 1: Fibonacci Calculator

```python
tool = maker.create_tool(
    name="fibonacci",
    description="Calculate the nth Fibonacci number",
    parameters={"n": "int"},
    return_type="int",
    examples=[
        {"input": {"n": 0}, "output": 0},
        {"input": {"n": 1}, "output": 1},
        {"input": {"n": 10}, "output": 55}
    ]
)
```

### Example 2: Text Processor

```python
tool = maker.create_tool(
    name="word_count",
    description="Count words in a text string",
    parameters={"text": "str"},
    return_type="int"
)
```

### Example 3: Data Processor

```python
tool = maker.create_tool(
    name="filter_dict",
    description="Filter dictionary by list of keys",
    parameters={"data": "dict", "keys": "list"},
    return_type="dict"
)
```

## Security

LLM Maker enforces strict security:

### ✅ Allowed
- Safe built-in functions (len, max, min, sum, etc.)
- Safe imports (math, json, re, datetime, collections)
- Pure computation
- Type hints and docstrings

### ❌ Blocked
- Dangerous imports (os, sys, subprocess)
- File operations (open, read, write)
- Network access (socket, urllib, requests)
- Code execution (eval, exec, compile)
- System access (__import__, breakpoint)

## Configuration

Edit `llm_maker_config.yaml`:

```yaml
tool_maker:
  provider: azure  # or openai, local
  temperature: 0.7
  max_tokens: 2000

validation:
  strict_mode: true
  allowed_imports:
    - math
    - json
    - re

execution:
  timeout_seconds: 5
  max_memory_mb: 512
```

## Testing

Run the test suite:

```bash
# All tests
./test_llm_maker.sh

# Or manually
python examples/quick_start.py
```

## Troubleshooting

### "No AI provider available"

Set up Azure OpenAI or OpenAI credentials:

```bash
export AZURE_OPENAI_API_KEY="your-key"
export AZURE_OPENAI_ENDPOINT="https://your-endpoint.openai.azure.com/"
export AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini"
export AZURE_OPENAI_API_VERSION="2024-02-15-preview"
```

### "RestrictedPython not available"

Install optional dependencies:

```bash
pip install RestrictedPython
```

Or continue with basic sandboxing (less secure but functional).

### Tool execution fails

Check the error message:
- **Syntax error**: Code generation failed, try again
- **Validation error**: Code violates security rules
- **Runtime error**: Bug in generated code
- **Timeout**: Execution took too long

## Next Steps

1. Explore examples in `examples/`
2. Read the full documentation in `README.md`
3. Try creating your own tools
4. Integrate with your applications via the MCP server

## Learn More

- [Full README](README.md)
- [Example Tools](examples/)
- [Test Suite](tests/)
- [Configuration](llm_maker_config.yaml)
