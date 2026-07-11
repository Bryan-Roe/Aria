"""Extended tests for shared/local_calc.py.

Covers edge cases not exercised by test_local_calc.py:
- Unicode arithmetic operators (× ÷ ^)
- Full set of word-operator substitutions (times, multiplied by, divided by,
  modulo, to the power of, plus, minus)
- Floor division (//)
- looks_like_arithmetic with word-operator expressions
- normalize_expression idempotence and combined prefixes
- _format_result precision for floats
- evaluate_arithmetic with deeply nested parentheses
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


from shared.local_calc import evaluate_arithmetic, looks_like_arithmetic, normalize_expression

# ---------------------------------------------------------------------------
# Unicode operators
# ---------------------------------------------------------------------------


class TestUnicodeOperators:
    def test_multiplication_sign(self):
        # × (U+00D7) should be substituted with *
        result = evaluate_arithmetic("3 × 4")
        assert result == "12"

    def test_division_sign(self):
        # ÷ (U+00F7) should be substituted with /
        result = evaluate_arithmetic("10 ÷ 2")
        assert result == "5"

    def test_caret_as_power(self):
        # ^ should be substituted with **
        result = evaluate_arithmetic("2^10")
        assert result == "1024"

    def test_combined_unicode_and_ascii(self):
        result = evaluate_arithmetic("6 × 7 ÷ 2")
        assert result == "21"


# ---------------------------------------------------------------------------
# Word operator substitutions
# ---------------------------------------------------------------------------


class TestWordOperators:
    def test_times(self):
        result = evaluate_arithmetic("5 times 6")
        assert result == "30"

    def test_multiplied_by(self):
        result = evaluate_arithmetic("7 multiplied by 3")
        assert result == "21"

    def test_divided_by(self):
        result = evaluate_arithmetic("20 divided by 4")
        assert result == "5"

    def test_modulo(self):
        result = evaluate_arithmetic("17 modulo 5")
        assert result == "2"

    def test_mod_short_form(self):
        result = evaluate_arithmetic("17 mod 5")
        assert result == "2"

    def test_to_the_power_of(self):
        result = evaluate_arithmetic("3 to the power of 3")
        assert result == "27"

    def test_plus_word(self):
        result = evaluate_arithmetic("8 plus 4")
        assert result == "12"

    def test_minus_word(self):
        result = evaluate_arithmetic("15 minus 7")
        assert result == "8"


# ---------------------------------------------------------------------------
# Floor division
# ---------------------------------------------------------------------------


class TestFloorDivision:
    def test_floor_division_positive(self):
        # 10 // 3 = 3
        result = evaluate_arithmetic("10 // 3")
        assert result == "3"

    def test_floor_division_exact(self):
        result = evaluate_arithmetic("12 // 4")
        assert result == "3"

    def test_floor_division_by_zero(self):
        result = evaluate_arithmetic("5 // 0")
        assert result == "undefined (division by zero)"


# ---------------------------------------------------------------------------
# looks_like_arithmetic — word-operator expressions
# ---------------------------------------------------------------------------


class TestLooksLikeArithmeticWords:
    def test_word_plus_detected(self):
        assert looks_like_arithmetic("8 plus 4") is True

    def test_word_minus_detected(self):
        assert looks_like_arithmetic("15 minus 7") is True

    def test_word_times_detected(self):
        assert looks_like_arithmetic("5 times 3") is True

    def test_word_divided_by_detected(self):
        assert looks_like_arithmetic("20 divided by 5") is True

    def test_number_only_returns_false(self):
        # "42" alone is not an arithmetic expression (no operator)
        assert looks_like_arithmetic("42") is False

    def test_empty_string_returns_false(self):
        assert looks_like_arithmetic("") is False

    def test_none_like_empty_is_false(self):
        assert looks_like_arithmetic("   ") is False

    def test_unicode_multiply_detected(self):
        assert looks_like_arithmetic("3 × 4") is True

    def test_caret_power_detected(self):
        assert looks_like_arithmetic("2^8") is True


# ---------------------------------------------------------------------------
# normalize_expression
# ---------------------------------------------------------------------------


class TestNormalizeExpressionExtended:
    def test_strips_trailing_question_mark(self):
        result = normalize_expression("What is 3 + 3?")
        assert result == "3 + 3"

    def test_strips_trailing_period(self):
        result = normalize_expression("Calculate 2 + 2.")
        assert "2 + 2" in result

    def test_please_prefix_stripped(self):
        result = normalize_expression("Please calculate 5 * 5")
        assert result == "5 * 5"

    def test_can_you_prefix_stripped(self):
        result = normalize_expression("Can you compute 3 + 3")
        assert result == "3 + 3"

    def test_tell_me_prefix_stripped(self):
        result = normalize_expression("tell me 4 + 4")
        assert result == "4 + 4"

    def test_the_value_of_prefix_stripped(self):
        result = normalize_expression("the value of 9 - 1")
        assert result == "9 - 1"

    def test_unicode_operators_substituted(self):
        result = normalize_expression("3 × 4")
        assert "*" in result

    def test_caret_substituted(self):
        result = normalize_expression("2^8")
        assert "**" in result

    def test_word_operators_substituted(self):
        result = normalize_expression("5 plus 3")
        assert "+" in result
        result = normalize_expression("10 minus 4")
        assert "-" in result


# ---------------------------------------------------------------------------
# evaluate_arithmetic — additional edge cases
# ---------------------------------------------------------------------------


class TestEvaluateArithmeticEdgeCases:
    def test_nested_parentheses(self):
        result = evaluate_arithmetic("((2 + 3) * (4 - 1))")
        assert result == "15"

    def test_result_with_decimal_precision(self):
        result = evaluate_arithmetic("1 / 3")
        # Should be a non-None string representing a float
        assert result is not None
        val = float(result)
        assert abs(val - 1 / 3) < 1e-9

    def test_large_integer_result(self):
        result = evaluate_arithmetic("999 * 999")
        assert result == "998001"

    def test_unary_positive(self):
        result = evaluate_arithmetic("+5 + 3")
        assert result == "8"

    def test_whitespace_around_operators(self):
        result = evaluate_arithmetic("   10   +   5   ")
        assert result == "15"

    def test_float_result_no_trailing_zero(self):
        # 1 / 4 = 0.25 — should not show trailing zeros
        result = evaluate_arithmetic("1 / 4")
        assert result == "0.25"

    def test_power_of_zero(self):
        result = evaluate_arithmetic("5 ** 0")
        assert result == "1"

    def test_zero_to_power(self):
        result = evaluate_arithmetic("0 ** 5")
        assert result == "0"

    def test_modulo_gives_zero(self):
        result = evaluate_arithmetic("10 % 5")
        assert result == "0"

    def test_chained_operations(self):
        result = evaluate_arithmetic("2 + 3 * 4 - 1")
        # Standard precedence: 2 + 12 - 1 = 13
        assert result == "13"
