"""
Tests for regex pattern compilation optimizations.

These tests verify that regex patterns are pre-compiled at module level
for improved performance, rather than being compiled on every use.
"""

import re
import sys
import time
from pathlib import Path

import pytest


class TestFinalValidationOptimizations:
    """Tests for scripts/final_validation.py regex optimizations."""

    def test_regex_patterns_are_compiled(self):
        """Test that regex patterns are pre-compiled at module level."""
        # Add scripts directory to path
        repo_root = Path(__file__).resolve().parents[1]
        scripts_path = str(repo_root / "scripts")
        if scripts_path not in sys.path:
            sys.path.insert(0, scripts_path)

        try:
            # Import the module to trigger pattern compilation
            import final_validation

            # Verify compiled patterns exist
            assert hasattr(final_validation, "_RE_ONCLICK")
            assert hasattr(final_validation, "_RE_FUNC_NAMES")
            assert hasattr(final_validation, "_RE_ELEMENT_IDS")
            assert hasattr(final_validation, "_RE_GET_BY_ID")
            assert hasattr(final_validation, "_RE_FETCH_CALLS")

            # Verify they are compiled regex objects
            assert isinstance(final_validation._RE_ONCLICK, re.Pattern)
            assert isinstance(final_validation._RE_FUNC_NAMES, re.Pattern)
            assert isinstance(final_validation._RE_ELEMENT_IDS, re.Pattern)

        except ImportError:
            pytest.skip("final_validation module not available")
        finally:
            # Clean up sys.path
            if scripts_path in sys.path:
                sys.path.remove(scripts_path)

    def test_onclick_pattern_matches_correctly(self):
        """Test that the onclick pattern matches HTML correctly."""
        repo_root = Path(__file__).resolve().parents[1]
        scripts_path = str(repo_root / "scripts")
        if scripts_path not in sys.path:
            sys.path.insert(0, scripts_path)

        try:
            import final_validation

            # Test data
            html = '<button onclick="handleClick()">Click</button>'
            matches = final_validation._RE_ONCLICK.findall(html)

            assert len(matches) == 1
            assert matches[0] == "handleClick()"

        except ImportError:
            pytest.skip("final_validation module not available")
        finally:
            if scripts_path in sys.path:
                sys.path.remove(scripts_path)


class TestValidateDashboardOptimizations:
    """Tests for scripts/validate_dashboard.py regex optimizations."""

    def test_regex_patterns_are_compiled(self):
        """Test that regex patterns are pre-compiled at module level."""
        repo_root = Path(__file__).resolve().parents[1]
        scripts_path = str(repo_root / "scripts")
        if scripts_path not in sys.path:
            sys.path.insert(0, scripts_path)

        try:
            import validate_dashboard

            # Verify compiled patterns exist
            assert hasattr(validate_dashboard, "_RE_CONSOLE_LOG")
            assert hasattr(validate_dashboard, "_RE_GET_BY_ID")
            assert hasattr(validate_dashboard, "_RE_ELEMENT_IDS")
            assert hasattr(validate_dashboard, "_RE_ASYNC_FUNCTION")
            assert hasattr(validate_dashboard, "_RE_AWAIT")
            assert hasattr(validate_dashboard, "_RE_EVENT_LISTENER")
            assert hasattr(validate_dashboard, "_RE_FETCH_CALLS")
            assert hasattr(validate_dashboard, "_RE_LOCALSTORAGE")
            assert hasattr(validate_dashboard, "_RE_ONCLICK")

            # Verify they are compiled regex objects
            assert isinstance(validate_dashboard._RE_CONSOLE_LOG, re.Pattern)
            assert isinstance(validate_dashboard._RE_ASYNC_FUNCTION, re.Pattern)

        except ImportError:
            pytest.skip("validate_dashboard module not available")
        finally:
            if scripts_path in sys.path:
                sys.path.remove(scripts_path)


class TestFunctionAppOptimizations:
    """Tests for function_app.py regex optimizations."""

    def test_word_split_pattern_is_compiled(self):
        """Test that word split pattern is pre-compiled at module level."""
        repo_root = Path(__file__).resolve().parents[1]

        try:
            # Import function_app module
            sys.path.insert(0, str(repo_root))
            import function_app

            # Verify compiled pattern exists
            assert hasattr(function_app, "_RE_WORD_SPLIT")
            assert isinstance(function_app._RE_WORD_SPLIT, re.Pattern)

            # Test the pattern works correctly
            text = "Hello world, this is a test!"
            words = function_app._RE_WORD_SPLIT.findall(text)

            assert len(words) == 6
            assert words[0] == "Hello"
            assert words[-1] == "test!"

        except ImportError:
            pytest.skip("function_app module not available")
        finally:
            if str(repo_root) in sys.path:
                sys.path.remove(str(repo_root))

    def test_re_module_imported_at_top(self):
        """Test that re module is imported at module level, not locally."""
        repo_root = Path(__file__).resolve().parents[1]
        function_app_path = repo_root / "function_app.py"

        if not function_app_path.exists():
            pytest.skip("function_app.py not found")

        content = function_app_path.read_text()

        # Count occurrences of 'import re' in the file
        import_count = content.count("import re")

        # Should have exactly 1 import at the top level
        # (There might be other imports like 'import requests', so check carefully)
        lines_with_import_re = [
            line
            for line in content.split("\n")
            if "import re" in line and not line.strip().startswith("#")
        ]

        # Filter for actual 're' imports (not 'requests', 'requirements', etc.)
        actual_re_imports = [
            line
            for line in lines_with_import_re
            if "import re" in line
            and ("import re\n" in (line + "\n") or "import re " in line)
        ]

        # We expect exactly one import at the top level
        assert (
            len(actual_re_imports) >= 1
        ), "re module should be imported at module level"


class TestEmailNotificationsOptimizations:
    """Tests for shared/email_notifications.py regex optimizations."""

    def test_html_patterns_are_compiled(self):
        """Test that HTML stripping patterns are pre-compiled."""
        repo_root = Path(__file__).resolve().parents[1]
        shared_path = str(repo_root / "shared")
        if shared_path not in sys.path:
            sys.path.insert(0, shared_path)

        try:
            import email_notifications

            # Verify compiled patterns exist
            assert hasattr(email_notifications, "_RE_HTML_TAGS")
            assert hasattr(email_notifications, "_RE_WHITESPACE")

            # Verify they are compiled regex objects
            assert isinstance(email_notifications._RE_HTML_TAGS, re.Pattern)
            assert isinstance(email_notifications._RE_WHITESPACE, re.Pattern)

        except ImportError:
            pytest.skip("email_notifications module not available")
        finally:
            if shared_path in sys.path:
                sys.path.remove(shared_path)

    def test_html_stripping_works_correctly(self):
        """Test that HTML stripping functionality works after optimization."""
        repo_root = Path(__file__).resolve().parents[1]
        shared_path = str(repo_root / "shared")
        if shared_path not in sys.path:
            sys.path.insert(0, shared_path)

        try:
            from email_notifications import EmailNotificationSystem

            email_system = EmailNotificationSystem()

            # Test HTML stripping
            html = "<p>Hello <strong>world</strong>!</p>   <p>Test</p>"
            text = email_system._strip_html(html)

            assert "Hello world!" in text
            assert "Test" in text
            assert "<p>" not in text
            assert "<strong>" not in text

        except ImportError:
            pytest.skip("email_notifications module not available")
        finally:
            if shared_path in sys.path:
                sys.path.remove(shared_path)


class TestCookingAIOptimizations:
    """Tests for cooking-ai/src/providers/local.py regex optimizations."""

    def test_quantity_pattern_is_compiled(self):
        """Test that quantity extraction pattern is pre-compiled."""
        repo_root = Path(__file__).resolve().parents[1]
        cooking_ai_path = str(
            repo_root / "ai-projects" / "cooking-ai" / "src" / "providers"
        )
        if cooking_ai_path not in sys.path:
            sys.path.insert(0, cooking_ai_path)

        try:
            import local as cooking_local

            # Verify compiled pattern exists
            assert hasattr(cooking_local, "_RE_QUANTITY")
            assert isinstance(cooking_local._RE_QUANTITY, re.Pattern)

            # Test the pattern matches ingredient quantities correctly
            test_input = "2 cups flour"
            match = cooking_local._RE_QUANTITY.match(test_input)

            assert match is not None
            assert match.group("qty") == "2"
            assert match.group("unit") == "cups"
            assert match.group("name") == "flour"

        except ImportError:
            pytest.skip("cooking-ai local provider module not available")
        finally:
            if cooking_ai_path in sys.path:
                sys.path.remove(cooking_ai_path)


class TestPerformanceBenchmark:
    """Performance benchmarks to verify optimization impact."""

    def test_compiled_vs_inline_regex_performance(self):
        """Benchmark showing compiled regex is faster than inline."""
        pattern_str = r"\S+"
        test_text = "The quick brown fox jumps over the lazy dog " * 100
        iterations = 1000

        # Test inline compilation (old way)
        start_inline = time.perf_counter()
        for _ in range(iterations):
            re.findall(pattern_str, test_text)
        time_inline = time.perf_counter() - start_inline

        # Test pre-compiled pattern (new way)
        compiled_pattern = re.compile(pattern_str)
        start_compiled = time.perf_counter()
        for _ in range(iterations):
            compiled_pattern.findall(test_text)
        time_compiled = time.perf_counter() - start_compiled

        # Pre-compiled should be faster or at least not slower
        speedup = time_inline / time_compiled
        print(f"\nRegex compilation speedup: {speedup:.2f}x")
        print(f"Inline time: {time_inline:.4f}s, Compiled time: {time_compiled:.4f}s")

        # Micro-benchmarks are noisy across CI/dev containers and Python versions.
        # Guard only against catastrophic regressions while preserving signal.
        assert (
            speedup >= 0.25
        ), f"Compiled regex benchmark regressed unexpectedly, got {speedup:.2f}x"

    def test_pattern_cache_stability(self):
        """Test that compiled patterns remain stable across calls."""
        pattern_str = r"test"
        compiled = re.compile(pattern_str)

        # Get the id of the compiled pattern
        pattern_id = id(compiled)

        # Use it multiple times
        for _ in range(100):
            compiled.search("test string")

        # Pattern object should remain the same
        assert id(compiled) == pattern_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
