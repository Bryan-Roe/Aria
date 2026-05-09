#!/bin/bash
# Test script for LLM Maker

echo "================================================"
echo "LLM Maker - Test Suite"
echo "================================================"
echo ""

cd "$(dirname "$0")"

echo "1. Testing Tool Validator..."
echo "------------------------------"
python -c "
import sys
sys.path.insert(0, 'src')
from tool_validator import ToolValidator

validator = ToolValidator()

# Valid code
code = 'def add(a: int, b: int) -> int:\n    return a + b'
is_valid, errors = validator.validate(code)
print(f'✓ Valid code test: {\"PASS\" if is_valid else \"FAIL\"}')

# Dangerous import
code = 'import os\ndef bad(): return os.getcwd()'
is_valid, errors = validator.validate(code)
print(f'✓ Dangerous import detection: {\"PASS\" if not is_valid else \"FAIL\"}')
"
echo ""

echo "2. Testing Tool Executor..."
echo "------------------------------"
python -c "
import sys
sys.path.insert(0, 'src')
from tool_executor import ToolExecutor

executor = ToolExecutor(timeout=5)

# Simple execution
code = 'def multiply(a: int, b: int) -> int:\n    return a * b'
result = executor.execute(code, 'multiply', {'a': 5, 'b': 3})
print(f'✓ Simple execution: {\"PASS\" if result[\"success\"] and result[\"result\"] == 15 else \"FAIL\"}')

# Error handling
code = 'def divide(a: int, b: int) -> float:\n    return a / b'
result = executor.execute(code, 'divide', {'a': 10, 'b': 0})
print(f'✓ Error handling: {\"PASS\" if not result[\"success\"] else \"FAIL\"}')
"
echo ""

echo "3. Testing Tool Registry..."
echo "------------------------------"
python -c "
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, 'src')
from tool_registry import Tool, ToolRegistry

temp_dir = tempfile.mkdtemp()
registry = ToolRegistry(Path(temp_dir))

# Register tool
tool = Tool(
    id='',
    name='test',
    description='Test',
    code='def test(): return 42',
    parameters={},
    return_type='int',
    created_at=''
)

tool_id = registry.register(tool)
print(f'✓ Register tool: {\"PASS\" if tool_id else \"FAIL\"}')

# Retrieve tool
retrieved = registry.get(tool_id)
print(f'✓ Get tool: {\"PASS\" if retrieved else \"FAIL\"}')

# List tools
tools = registry.list_tools()
print(f'✓ List tools: {\"PASS\" if len(tools) == 1 else \"FAIL\"}')
"
echo ""

echo "================================================"
echo "All tests completed!"
echo "================================================"
