"""Unit tests for cleanup_query_metrics security fixes."""

import sys
from pathlib import Path

import pytest

# Import the module under test
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from cleanup_query_metrics import _validate_table_name


class TestValidateTableName:
    """Test the _validate_table_name function for SQL injection prevention."""

    # Valid table names
    def test_simple_valid_name(self):
        """Test simple valid table name."""
        assert _validate_table_name("TableName") == "TableName"

    def test_lowercase_valid_name(self):
        """Test lowercase valid table name."""
        assert _validate_table_name("tablename") == "tablename"

    def test_underscore_prefix_valid(self):
        """Test table name starting with underscore."""
        assert _validate_table_name("_table") == "_table"

    def test_name_with_numbers(self):
        """Test valid table name with numbers."""
        assert _validate_table_name("table_123") == "table_123"

    def test_mixed_case_with_numbers(self):
        """Test mixed case with numbers."""
        assert _validate_table_name("QAI_QueryMetrics") == "QAI_QueryMetrics"

    def test_all_caps(self):
        """Test all caps table name."""
        assert _validate_table_name("METRICS") == "METRICS"

    def test_single_letter(self):
        """Test single letter table name."""
        assert _validate_table_name("A") == "A"

    def test_underscore_only(self):
        """Test underscore only table name."""
        assert _validate_table_name("_") == "_"

    # Invalid table names - SQL injection attempts
    def test_rejects_sql_injection_semicolon(self):
        """Test rejection of SQL injection with semicolon."""
        with pytest.raises(ValueError) as excinfo:
            _validate_table_name("table;DROP TABLE users")
        assert "Invalid table name" in str(excinfo.value)

    def test_rejects_sql_comment_double_dash(self):
        """Test rejection of SQL injection with double dash comment."""
        with pytest.raises(ValueError) as excinfo:
            _validate_table_name("table--")
        assert "Invalid table name" in str(excinfo.value)

    def test_rejects_sql_comment_block(self):
        """Test rejection of SQL injection with block comment."""
        with pytest.raises(ValueError) as excinfo:
            _validate_table_name("table/*")
        assert "Invalid table name" in str(excinfo.value)

    def test_rejects_sql_union(self):
        """Test rejection of SQL injection with UNION."""
        with pytest.raises(ValueError) as excinfo:
            _validate_table_name("table UNION SELECT")
        assert "Invalid table name" in str(excinfo.value)

    def test_rejects_single_quote(self):
        """Test rejection of single quote (common SQL injection char)."""
        with pytest.raises(ValueError) as excinfo:
            _validate_table_name("table'")
        assert "Invalid table name" in str(excinfo.value)

    def test_rejects_double_quote(self):
        """Test rejection of double quote."""
        with pytest.raises(ValueError) as excinfo:
            _validate_table_name('table"')
        assert "Invalid table name" in str(excinfo.value)

    def test_rejects_parentheses(self):
        """Test rejection of parentheses."""
        with pytest.raises(ValueError) as excinfo:
            _validate_table_name("table()")
        assert "Invalid table name" in str(excinfo.value)

    # Edge cases
    def test_rejects_empty_string(self):
        """Test rejection of empty string."""
        with pytest.raises(ValueError) as excinfo:
            _validate_table_name("")
        assert "Invalid table name" in str(excinfo.value)

    def test_rejects_starting_with_number(self):
        """Test rejection of table name starting with number."""
        with pytest.raises(ValueError) as excinfo:
            _validate_table_name("123table")
        assert "Invalid table name" in str(excinfo.value)

    def test_rejects_spaces(self):
        """Test rejection of table name with spaces."""
        with pytest.raises(ValueError) as excinfo:
            _validate_table_name("table name")
        assert "Invalid table name" in str(excinfo.value)

    def test_rejects_hyphen(self):
        """Test rejection of table name with hyphen."""
        with pytest.raises(ValueError) as excinfo:
            _validate_table_name("table-name")
        assert "Invalid table name" in str(excinfo.value)

    def test_rejects_dot(self):
        """Test rejection of table name with dot (schema.table syntax)."""
        with pytest.raises(ValueError) as excinfo:
            _validate_table_name("schema.table")
        assert "Invalid table name" in str(excinfo.value)

    def test_rejects_backtick(self):
        """Test rejection of backtick (MySQL identifier quote)."""
        with pytest.raises(ValueError) as excinfo:
            _validate_table_name("`table`")
        assert "Invalid table name" in str(excinfo.value)

    def test_rejects_brackets(self):
        """Test rejection of square brackets (SQL Server identifier quote)."""
        with pytest.raises(ValueError) as excinfo:
            _validate_table_name("[table]")
        assert "Invalid table name" in str(excinfo.value)

    def test_rejects_newline(self):
        """Test rejection of newline character."""
        with pytest.raises(ValueError) as excinfo:
            _validate_table_name("table\nname")
        assert "Invalid table name" in str(excinfo.value)

    def test_rejects_tab(self):
        """Test rejection of tab character."""
        with pytest.raises(ValueError) as excinfo:
            _validate_table_name("table\tname")
        assert "Invalid table name" in str(excinfo.value)

    # SQL keywords (these are technically valid as table names but good to test)
    def test_accepts_sql_keyword_as_name(self):
        """Test that SQL keywords are accepted (they're valid identifiers)."""
        # Note: Using SQL keywords as table names is generally valid in SQL
        # The regex validation allows them because they're valid identifier syntax
        assert _validate_table_name("SELECT") == "SELECT"
        assert _validate_table_name("DROP") == "DROP"
        assert _validate_table_name("TABLE") == "TABLE"
