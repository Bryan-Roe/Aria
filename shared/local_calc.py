"""Safe, deterministic arithmetic evaluation for local/offline fallbacks.

The local echo provider has no real model, so it normally cannot answer even
trivial factual questions. Basic arithmetic, however, can be computed exactly
and offline. This module provides a small, dependency-free evaluator that
parses arithmetic expressions with Python's :mod:`ast` module (never ``eval``)
and only permits a safe subset of numeric operations.
"""

from __future__ import annotations

import ast
import operator
import re
from typing import Optional

# Only allow a small set of binary/unary numeric operators. Anything outside
# this set (names, calls, attribute access, comprehensions, etc.) is rejected.
_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

# Cap exponents so an expression like ``9**9**9`` cannot hang the process.
_MAX_POW_EXPONENT = 1000

# Words people commonly use in place of arithmetic symbols.
_WORD_REPLACEMENTS = (
    (r"\bplus\b", "+"),
    (r"\bminus\b", "-"),
    (r"\btimes\b", "*"),
    (r"\bmultiplied by\b", "*"),
    (r"\bdivided by\b", "/"),
    (r"\bmod(?:ulo)?\b", "%"),
    (r"\bto the power of\b", "**"),
    (r"\^", "**"),
    (r"\u00d7", "*"),  # ×
    (r"\u00f7", "/"),  # ÷
)

# A question is only treated as arithmetic if, after stripping a leading
# natural-language prefix, the remainder consists solely of math characters.
_PREFIX_RE = re.compile(
    r"^\s*(?:please\s+)?(?:can you\s+|could you\s+)?"
    r"(?:tell me\s+|calculate|compute|evaluate|solve|what(?:'s| is| are)|"
    r"how much is|the value of)?\s*:?\s*",
    re.IGNORECASE,
)

_MATH_ONLY_RE = re.compile(r"^[0-9\.\s+\-*/%()]+$")


class _SafeEvaluator(ast.NodeVisitor):
    """Evaluate a restricted arithmetic AST, rejecting anything unsafe."""

    def visit(self, node: ast.AST) -> float:
        method = "visit_" + type(node).__name__
        visitor = getattr(self, method, None)
        if visitor is None:
            raise ValueError(f"Unsupported expression element: {type(node).__name__}")
        return visitor(node)

    def visit_Expression(self, node: ast.Expression) -> float:
        return self.visit(node.body)

    def visit_BinOp(self, node: ast.BinOp) -> float:
        op_type = type(node.op)
        if op_type not in _BIN_OPS:
            raise ValueError("Unsupported operator")
        left = self.visit(node.left)
        right = self.visit(node.right)
        if op_type is ast.Pow and abs(right) > _MAX_POW_EXPONENT:
            raise ValueError("Exponent too large")
        return _BIN_OPS[op_type](left, right)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> float:
        op_type = type(node.op)
        if op_type not in _UNARY_OPS:
            raise ValueError("Unsupported unary operator")
        return _UNARY_OPS[op_type](self.visit(node.operand))

    def visit_Constant(self, node: ast.Constant) -> float:
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise ValueError("Only numeric constants are allowed")
        return node.value


def _normalize_expression(text: str) -> str:
    """Replace word operators with symbols and strip a question prefix."""
    cleaned = text.strip().rstrip("?.! ")
    for pattern, replacement in _WORD_REPLACEMENTS:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
    cleaned = _PREFIX_RE.sub("", cleaned, count=1)
    return cleaned.strip()


def normalize_expression(text: str) -> str:
    """Public wrapper returning the cleaned arithmetic expression for display."""
    return _normalize_expression(text)


def looks_like_arithmetic(text: str) -> bool:
    """Return True if ``text`` looks like a self-contained arithmetic query."""
    if not text:
        return False
    expr = _normalize_expression(text)
    if not expr or not any(ch.isdigit() for ch in expr):
        return False
    if not any(op in expr for op in "+-*/%"):
        return False
    return bool(_MATH_ONLY_RE.match(expr))


def _format_result(value: float) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, float):
        return f"{value:.10g}"
    return str(value)


def evaluate_arithmetic(text: str) -> Optional[str]:
    """Evaluate an arithmetic expression embedded in ``text``.

    Returns the formatted numeric result as a string, or ``None`` if the input
    is not a safe, self-contained arithmetic expression.
    """
    if not looks_like_arithmetic(text):
        return None
    expr = _normalize_expression(text)
    try:
        tree = ast.parse(expr, mode="eval")
        result = _SafeEvaluator().visit(tree)
    except ZeroDivisionError:
        return "undefined (division by zero)"
    except (ValueError, SyntaxError, TypeError, OverflowError):
        return None
    if isinstance(result, bool) or not isinstance(result, (int, float)):
        return None
    return _format_result(result)
