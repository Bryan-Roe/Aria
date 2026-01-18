# Test Developer Quick Reference

## 30-Second Quick Start

```bash
# Install dependencies
pip install pytest pytest-cov pytest-asyncio

# Run all tests
python scripts/test_runner.py --unit

# Run specific test
pytest tests/test_aria_command_parser.py -v

# Run with coverage
pytest --cov=. --cov-report=html
```

## Common Test Commands

### Basic Execution
```bash
# All unit tests (fast)
pytest tests/ -v

# Specific file
pytest tests/test_chat_cli_api.py

# Specific test
pytest tests/test_chat_cli_api.py::TestChatCLI::test_chat_cli_help

# Watch mode (re-run on file change)
pytest-watch tests/
```

### Filtering & Selection
```bash
# Skip slow tests
pytest -m "not slow"

# Skip Azure tests
pytest -m "not azure"

# Only integration tests
pytest -m integration

# Only GPU tests
pytest -m gpu

# Match pattern
pytest -k "command_parser"
```

### Coverage & Reports
```bash
# Basic coverage
pytest --cov=.

# Coverage report in HTML
pytest --cov=. --cov-report=html

# Coverage for specific module
pytest --cov=shared tests/test_shared*.py

# Show uncovered lines
pytest --cov=. --cov-report=term-missing
```

## Writing Tests - Templates

### Simple Unit Test
```python
def test_feature_behavior():
    """Test that feature does X"""
    result = feature_function()
    assert result == expected_value
```

### Test with Mock
```python
from unittest.mock import Mock, patch

@patch("module.external_function")
def test_with_mock(mock_function):
    mock_function.return_value = "expected"
    result = my_function()
    assert result == "expected"
    mock_function.assert_called_once()
```

### Test with Fixture
```python
def test_with_fixture(sample_training_config):
    """Test using provided fixture"""
    assert sample_training_config["model"] is not None
    assert sample_training_config["epochs"] > 0
```

### Parametrized Test
```python
@pytest.mark.parametrize("input,expected", [
    ("move left", "move"),
    ("wave", "gesture"),
    ("jump", "gesture"),
])
def test_multiple_cases(input, expected):
    result = parse(input)
    assert expected in result
```

### Test Class Organization
```python
class TestFeatureName:
    """Test suite for feature X"""
    
    def test_basic_functionality(self):
        """Test basic case"""
        pass
    
    def test_edge_case(self):
        """Test edge case"""
        pass
    
    def test_error_handling(self):
        """Test error scenario"""
        pass
```

### Async Test
```python
@pytest.mark.asyncio
async def test_async_operation():
    result = await async_function()
    assert result is not None
```

## Available Fixtures

### Import in Test File
```python
from tests.conftest import (
    sample_json_data,
    sample_chat_messages,
    sample_training_config,
    mock_openai_client
)
```

### Use in Test
```python
def test_using_fixture(sample_training_config):
    assert sample_training_config["model"] is not None
```

### Common Fixtures
| Fixture | Purpose | Type |
|---------|---------|------|
| `sample_json_data` | JSON structure | dict |
| `sample_chat_messages` | Conversation | list |
| `sample_training_config` | ML config | dict |
| `sample_aria_action` | Game action | dict |
| `mock_openai_client` | API mock | Mock |
| `temp_data_dir` | Temp directory | Path |

## Pytest Markers

### Available Markers
```python
@pytest.mark.slow           # Long-running test
@pytest.mark.azure          # Requires Azure creds
@pytest.mark.integration    # Integration test
@pytest.mark.quantum        # Quantum backend needed
@pytest.mark.gpu            # GPU acceleration needed
```

### Using Markers
```python
@pytest.mark.slow
def test_long_operation():
    # This test takes time
    pass

# Run without slow tests
pytest -m "not slow"

# Run only integration tests
pytest -m integration
```

## Mock Patterns

### Simple Mock
```python
from unittest.mock import Mock

mock_obj = Mock()
mock_obj.method.return_value = "value"
result = mock_obj.method()
assert result == "value"
```

### Mock with Patch
```python
from unittest.mock import patch

@patch("module.function")
def test_function(mock_func):
    mock_func.return_value = 42
    result = call_function_that_uses_it()
    mock_func.assert_called_once()
```

### Context Manager Patch
```python
with patch("module.function") as mock_func:
    mock_func.return_value = "test"
    # test code here
```

### Mock Attribute/Property
```python
mock_obj = Mock()
mock_obj.property = "value"
mock_obj.method.return_value = "result"

# Or chain calls
mock_obj.chain.method.return_value = "value"
```

## Common Assertions

### Basic Assertions
```python
assert value == expected          # Equality
assert value != expected          # Inequality
assert value is None              # None check
assert value is True              # Boolean
assert callable(function)         # Callable check
```

### Collection Assertions
```python
assert item in collection         # Membership
assert len(collection) == 3       # Length
assert collection[0] == value     # Indexing
assert "key" in dictionary        # Dict key
```

### Type Assertions
```python
assert isinstance(value, str)     # Type check
assert isinstance(value, (int, float))  # Multiple types
```

### Exception Assertions
```python
with pytest.raises(ValueError):
    function_that_raises()

with pytest.raises(ValueError, match="error message"):
    function_that_raises()
```

### Mock Assertions
```python
mock.assert_called()              # Was called
mock.assert_called_once()         # Called exactly once
mock.assert_called_with(arg)      # Called with arg
mock.assert_not_called()          # Not called
mock.assert_called_once_with(arg) # Called once with arg
```

## Test File Structure

### Recommended Layout
```python
"""Module docstring describing what's tested"""
import pytest
from unittest.mock import Mock, patch

# Imports at top

class TestFeatureA:
    """Test feature A"""
    
    def test_case_1(self):
        """Description of test"""
        pass
    
    def test_case_2(self):
        """Description of test"""
        pass

class TestFeatureB:
    """Test feature B"""
    
    def test_case_1(self):
        pass

# Standalone test functions
def test_utility_function():
    """Test utility"""
    pass

@pytest.mark.slow
def test_slow_operation():
    """Test slow operation"""
    pass
```

## Debugging Tests

### Print Output
```python
def test_with_debug():
    value = function()
    print(f"Debug: {value}")  # Shows with pytest -s
    assert value == expected
```

### Run with Output
```bash
# Show print statements
pytest -s

# Show local variables on failure
pytest -l

# Verbose output
pytest -v

# Full traceback
pytest --tb=long
```

### Drop to Debugger
```python
def test_with_debugger():
    import pdb; pdb.set_trace()  # Drops to debugger
    # or
    breakpoint()  # Python 3.7+
```

### Run Tests in Order
```bash
# Run tests in reverse order
pytest --reverse

# Run last failed test
pytest --lf

# Run failed tests first
pytest --ff
```

## CI/CD Integration

### GitHub Actions
Tests run automatically on:
- Push to any branch
- Pull request
- Scheduled daily

### Local Pre-commit
```bash
# Run tests before commit
pytest tests/ --maxfail=1

# Fix any failures before committing
```

## Performance Optimization

### Run Only Changed Tests
```bash
# With git
pytest --testmon  # requires pytest-testmon

# With pattern matching
pytest tests/test_aria*.py
```

### Run Tests in Parallel
```bash
pip install pytest-xdist
pytest -n auto  # Use all CPU cores
```

### Skip Slow Tests During Development
```bash
pytest -m "not slow"
```

## Troubleshooting

### Import Error
```python
# Solution: Check PYTHONPATH
import sys
print(sys.path)

# Or use pytest directly in workspace
cd /workspaces/AI
pytest tests/
```

### Fixture Not Found
```bash
# Solution: Verify conftest.py location
ls tests/conftest.py

# Solution: Check fixture name spelling
pytest --fixtures
```

### Mock Not Working
```python
# Solution: Patch where it's used, not where it's defined
@patch("module_using_it.function")  # Not module_defining_it.function

# Solution: Patch before import
with patch("os.path.exists") as mock:
    # os.path.exists is now mocked
    pass
```

### Test Hangs
```bash
# Solution: Add timeout
pip install pytest-timeout
pytest --timeout=300

# Solution: Kill hung processes
pkill -f pytest
```

## Resource Links

- [Pytest Documentation](https://docs.pytest.org/)
- [Unittest.mock Docs](https://docs.python.org/3/library/unittest.mock.html)
- [Python Testing Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)

## Project Test Files

### Main Test Directories
```
/workspaces/AI/tests/          - All test files
/workspaces/AI/tests/conftest.py  - Fixtures & config
```

### Key Test Files
- `tests/test_shared_chat_providers.py` - Provider tests
- `tests/test_aria_command_parser.py` - Aria tests
- `tests/test_orchestrators.py` - Orchestrator tests
- `tests/test_chat_cli_api.py` - Chat/API tests

### Documentation
- `TESTING_GUIDE.md` - Complete testing reference
- `TEST_IMPROVEMENTS.md` - What was improved
- `TEST_COMPLETION_SUMMARY.md` - Summary of changes

## Quick Checklist

Before committing code:
- [ ] Run `pytest tests/ -v`
- [ ] No failures
- [ ] Coverage above 80%
- [ ] Tests added for new features
- [ ] Markers applied (@pytest.mark.*)
- [ ] Documentation updated

## Getting Help

1. Check TESTING_GUIDE.md
2. Look at similar test files
3. Check conftest.py for available fixtures
4. Run with `-v` and `-s` for details
5. Use `pytest --fixtures` to see available fixtures
