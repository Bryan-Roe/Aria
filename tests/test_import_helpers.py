"""Test suite for import_helpers module.

This test validates that the defensive import utilities work correctly
and provide proper fallback behavior.
"""

import sys
from pathlib import Path

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.import_helpers import create_stub_function, safe_import


def test_safe_import_module_success():
    """Test that safe_import returns module when import succeeds."""
    # Import a known module
    result = safe_import("json")

    assert result is not None
    assert hasattr(result, "loads")
    assert hasattr(result, "dumps")
    print("✓ safe_import returns module on success")


def test_safe_import_module_failure():
    """Test that safe_import returns None when module doesn't exist."""
    result = safe_import("nonexistent_module_xyz123", log_failure=False)

    assert result is None
    print("✓ safe_import returns None for missing module")


def test_safe_import_with_names_success():
    """Test importing specific names from a module."""
    result = safe_import("json", import_names=("loads", "dumps"))

    assert "loads" in result
    assert "dumps" in result
    assert callable(result["loads"])
    assert callable(result["dumps"])
    print("✓ safe_import extracts specific names successfully")


def test_safe_import_with_names_and_fallback():
    """Test that fallback factory is used when import fails."""

    def my_fallback(name):
        return f"fallback_{name}"

    result = safe_import(
        "nonexistent_module",
        import_names=("func1", "func2"),
        fallback_factory=my_fallback,
        log_failure=False,
    )

    assert result["func1"] == "fallback_func1"
    assert result["func2"] == "fallback_func2"
    print("✓ safe_import uses fallback_factory on failure")


def test_safe_import_partial_failure():
    """Test behavior when some names exist and others don't."""
    # json has 'loads' but not 'nonexistent_func'
    result = safe_import(
        "json",
        import_names=("loads", "nonexistent_func"),
        fallback_factory=lambda name: f"fallback_{name}",
    )

    assert callable(result["loads"])  # Real function
    assert result["nonexistent_func"] == "fallback_nonexistent_func"  # Fallback
    print("✓ safe_import handles partial availability correctly")


def test_create_stub_function():
    """Test that stub function returns proper error dict."""
    stub = create_stub_function("my_func")

    result = stub()

    assert isinstance(result, dict)
    assert not result["enabled"]
    assert result["error"] == "my_func_unavailable"
    assert stub.__name__ == "my_func"
    print("✓ create_stub_function creates proper stub")


def test_create_stub_function_with_args():
    """Test that stub function accepts any arguments."""
    stub = create_stub_function("func_with_args")

    # Should work with any args/kwargs
    result1 = stub(1, 2, 3)
    result2 = stub(x=1, y=2)
    result3 = stub(1, 2, z=3)

    assert all(not r["enabled"] for r in [result1, result2, result3])
    print("✓ Stub function accepts arbitrary arguments")


def test_create_stub_function_custom_error_key():
    """Test creating stub with custom error key."""
    stub = create_stub_function("my_func", error_key="failure_reason")

    result = stub()

    assert "failure_reason" in result
    assert result["failure_reason"] == "my_func_unavailable"
    print("✓ create_stub_function accepts custom error key")


def test_safe_import_real_world_pattern():
    """Test the pattern used in function_app.py."""
    # Simulate importing sql_health and engine_stats with fallbacks
    result = safe_import(
        "nonexistent.sql_engine",
        import_names=("sql_health", "engine_stats"),
        fallback_factory=create_stub_function,
        log_failure=False,
    )

    sql_health = result["sql_health"]
    engine_stats = result["engine_stats"]

    # Both should be callable stubs
    assert callable(sql_health)
    assert callable(engine_stats)

    # Both should return error dicts
    health_result = sql_health()
    stats_result = engine_stats()

    assert not health_result["enabled"]
    assert "sql_health_unavailable" in health_result["error"]
    assert not stats_result["enabled"]
    assert "engine_stats_unavailable" in stats_result["error"]

    print("✓ Real-world pattern from function_app.py works correctly")


if __name__ == "__main__":
    print("Testing import_helpers module...\n")

    test_safe_import_module_success()
    test_safe_import_module_failure()
    test_safe_import_with_names_success()
    test_safe_import_with_names_and_fallback()
    test_safe_import_partial_failure()
    test_create_stub_function()
    test_create_stub_function_with_args()
    test_create_stub_function_custom_error_key()
    test_safe_import_real_world_pattern()

    print("\n✅ All import_helpers tests passed!")
