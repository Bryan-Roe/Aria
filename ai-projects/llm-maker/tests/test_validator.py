"""
Tests for Tool Validator
"""

import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tool_validator import ToolValidator


class TestToolValidator:
    """Test tool validator functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.validator = ToolValidator()

    def test_valid_code(self):
        """Test validation of safe code"""
        code = """
def add_numbers(a: int, b: int) -> int:
    return a + b
"""
        is_valid, errors = self.validator.validate(code)
        assert is_valid, f"Expected valid but got errors: {errors}"
        assert len(errors) == 0

    def test_dangerous_import(self):
        """Test detection of dangerous imports"""
        code = """
import os

def bad_function():
    return os.getcwd()
"""
        is_valid, errors = self.validator.validate(code)
        assert not is_valid
        assert any("os" in str(e).lower() for e in errors)

    def test_dangerous_builtin(self):
        """Test detection of dangerous built-in functions"""
        code = """
def bad_function(code_str):
    return eval(code_str)
"""
        is_valid, errors = self.validator.validate(code)
        assert not is_valid
        assert any("eval" in str(e).lower() for e in errors)

    def test_file_operations(self):
        """Test detection of file operations"""
        code = """
def bad_function():
    with open('file.txt', 'r') as f:
        return f.read()
"""
        is_valid, errors = self.validator.validate(code)
        assert not is_valid
        assert any("file" in str(e).lower() or "open" in str(e).lower() for e in errors)

    def test_allowed_imports(self):
        """Test that allowed imports pass validation"""
        code = """
import math
import json

def calculate():
    return math.sqrt(16) + len(json.dumps({}))
"""
        is_valid, errors = self.validator.validate(code)
        assert is_valid, f"Expected valid but got errors: {errors}"

    def test_syntax_error(self):
        """Test detection of syntax errors"""
        code = """
def bad_syntax(
    return "missing closing paren"
"""
        is_valid, errors = self.validator.validate(code)
        assert not is_valid
        assert any("syntax" in str(e).lower() for e in errors)

    def test_function_signature_check(self):
        """Test function signature validation"""
        code = """
def my_function(a: int, b: str) -> int:
    return int(b) + a
"""
        is_valid, errors = self.validator.check_function_signature(
            code, "my_function", ["a", "b"]
        )
        assert is_valid, f"Expected valid but got errors: {errors}"

    def test_function_signature_mismatch(self):
        """Test detection of signature mismatch"""
        code = """
def my_function(x: int) -> int:
    return x * 2
"""
        is_valid, errors = self.validator.check_function_signature(
            code, "my_function", ["a", "b"]
        )
        assert not is_valid
        assert any("parameter" in str(e).lower() for e in errors)

    def test_missing_return(self):
        """Test detection of missing return statement"""
        code = """
def my_function(a: int) -> int:
    x = a * 2
    # Missing return
"""
        is_valid, errors = self.validator.check_function_signature(
            code, "my_function", ["a"]
        )
        assert not is_valid
        assert any("return" in str(e).lower() for e in errors)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
