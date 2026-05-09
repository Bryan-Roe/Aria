"""
Tests for Tool Executor
"""

import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from tool_executor import ToolExecutor
except ImportError:
    from ..src.tool_executor import ToolExecutor


class TestToolExecutor:
    """Test tool executor functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.executor = ToolExecutor(timeout=5)

    def test_execute_simple_function(self):
        """Test executing a simple function"""
        code = """
def add_numbers(a: int, b: int) -> int:
    return a + b
"""
        result = self.executor.execute(code, "add_numbers", {"a": 5, "b": 3})

        assert result["success"]
        assert result["result"] == 8
        assert result["result_type"] == "int"

    def test_execute_with_imports(self):
        """Test executing function with allowed imports"""
        code = """
import math

def calculate_sqrt(n: float) -> float:
    return math.sqrt(n)
"""
        result = self.executor.execute(code, "calculate_sqrt", {"n": 16.0})

        assert result["success"]
        assert abs(result["result"] - 4.0) < 1e-9

    def test_invalid_arguments(self):
        """Test handling of invalid arguments"""
        code = """
def my_func(a: int) -> int:
    return a * 2
"""
        result = self.executor.execute(code, "my_func", {"wrong_arg": 5})

        assert not result["success"]
        assert "TypeError" in result["error_type"]

    def test_runtime_error(self):
        """Test handling of runtime errors"""
        code = """
def divide(a: int, b: int) -> float:
    return a / b
"""
        result = self.executor.execute(code, "divide", {"a": 10, "b": 0})

        assert not result["success"]
        assert "error" in result

    def test_function_not_found(self):
        """Test error when function doesn't exist"""
        code = """
def some_func():
    return 42
"""
        result = self.executor.execute(code, "other_func", {})

        assert not result["success"]
        assert "not defined" in result["error"].lower()

    def test_compilation_check(self):
        """Test code compilation check"""
        good_code = "def func(): return 42"
        bad_code = "def func( return 42"

        assert self.executor.test_execution(good_code)
        assert not self.executor.test_execution(bad_code)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
