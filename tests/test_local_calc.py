"""Tests for the offline arithmetic helper used by the local AI fallback."""

import unittest

from shared.local_calc import (
    evaluate_arithmetic,
    looks_like_arithmetic,
    normalize_expression,
)


class LocalCalcTests(unittest.TestCase):
    def test_basic_operations(self) -> None:
        self.assertEqual(evaluate_arithmetic("2 + 2"), "4")
        self.assertEqual(evaluate_arithmetic("12 * 7"), "84")
        self.assertEqual(evaluate_arithmetic("100 / 4"), "25")
        self.assertEqual(evaluate_arithmetic("10 - 3"), "7")
        self.assertEqual(evaluate_arithmetic("17 % 5"), "2")

    def test_natural_language_prefixes_and_words(self) -> None:
        self.assertEqual(evaluate_arithmetic("What is 6 * 9?"), "54")
        self.assertEqual(evaluate_arithmetic("how much is 8 plus 5"), "13")
        self.assertEqual(evaluate_arithmetic("calculate: 9 minus 4"), "5")
        self.assertEqual(evaluate_arithmetic("3 to the power of 4"), "81")

    def test_parentheses_and_precedence(self) -> None:
        self.assertEqual(evaluate_arithmetic("(3 + 4) * 2"), "14")
        self.assertEqual(evaluate_arithmetic("2 + 3 * 4"), "14")

    def test_negative_numbers_are_not_swallowed(self) -> None:
        self.assertEqual(evaluate_arithmetic("-5 + 3"), "-2")
        self.assertEqual(evaluate_arithmetic("what is -5 + 3?"), "-2")

    def test_float_formatting(self) -> None:
        self.assertEqual(evaluate_arithmetic("1 / 8"), "0.125")
        self.assertEqual(evaluate_arithmetic("4 / 2"), "2")

    def test_division_by_zero_is_reported(self) -> None:
        self.assertEqual(
            evaluate_arithmetic("10 / 0"), "undefined (division by zero)"
        )

    def test_non_arithmetic_returns_none(self) -> None:
        self.assertIsNone(evaluate_arithmetic("what is quantum entanglement?"))
        self.assertIsNone(evaluate_arithmetic("move right"))
        self.assertIsNone(evaluate_arithmetic(""))
        self.assertIsNone(evaluate_arithmetic("the answer is 42"))

    def test_unsafe_input_is_rejected(self) -> None:
        # Names, calls and attribute access must never be evaluated.
        self.assertIsNone(evaluate_arithmetic("__import__('os').system('ls')"))
        self.assertIsNone(evaluate_arithmetic("os.getcwd()"))
        self.assertIsNone(evaluate_arithmetic("1 + abc"))

    def test_huge_exponent_is_rejected(self) -> None:
        self.assertIsNone(evaluate_arithmetic("9 ** 9 ** 9"))

    def test_looks_like_arithmetic(self) -> None:
        self.assertTrue(looks_like_arithmetic("2 + 2"))
        self.assertFalse(looks_like_arithmetic("hello there"))
        self.assertFalse(looks_like_arithmetic("42"))

    def test_normalize_expression_strips_prefix(self) -> None:
        self.assertEqual(normalize_expression("What is 12 * 7?"), "12 * 7")


if __name__ == "__main__":
    unittest.main()
