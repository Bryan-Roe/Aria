"""
Tool Validator - Validates generated code for safety
"""

import ast
import logging
from pathlib import Path
from typing import List, Optional, Tuple

import yaml

logger = logging.getLogger(__name__)

# Detection is done via AST; regex fallbacks removed for accuracy and performance.


class ToolValidator:
    """Validates generated tools for safety and correctness"""

    # Dangerous imports that should never be allowed
    DANGEROUS_IMPORTS = {
        "os",
        "sys",
        "subprocess",
        "shutil",
        "pathlib",
        "socket",
        "urllib",
        "requests",
        "http",
        "ftplib",
        "pickle",
        "shelve",
        "dbm",
        "sqlite3",
        "threading",
        "multiprocessing",
        "asyncio",
        "__builtin__",
        "builtins",
        "importlib",
        "ctypes",
        "cffi",
        "pty",
        "fcntl",
    }

    # Dangerous built-in functions
    DANGEROUS_BUILTINS = {
        "__import__",
        "eval",
        "exec",
        "compile",
        "open",
        "input",
        "breakpoint",
        "exit",
        "quit",
        "help",
        "license",
        "copyright",
        "credits",
    }

    # Dangerous attributes and magic methods
    DANGEROUS_ATTRS = {
        "__code__",
        "__globals__",
        "__builtins__",
        "__dict__",
        "__class__",
        "__bases__",
        "__subclasses__",
        "__mro__",
    }

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize validator with configuration

        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.allowed_imports = set(
            self.config.get("validation", {}).get("allowed_imports", [])
        )
        self.strict_mode = self.config.get("validation", {}).get("strict_mode", True)

    def _load_config(self, config_path: Optional[Path]) -> dict:
        """Load configuration from YAML file"""
        if config_path and config_path.exists():
            with open(config_path, "r") as f:
                return yaml.safe_load(f)

        # Default configuration if file not found
        default_config_path = Path(__file__).parent.parent / "llm_maker_config.yaml"
        if default_config_path.exists():
            with open(default_config_path, "r") as f:
                return yaml.safe_load(f)

        return {}

    def validate(self, code: str) -> Tuple[bool, List[str]]:
        """
        Validate tool code for safety

        Args:
            code: Python code to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check if code is parseable
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            errors.append(f"Syntax error: {e}")
            return False, errors

        # One-pass AST traversal to collect nodes and avoid repeated walks
        nodes = list(ast.walk(tree))

        # Run safety checks using the pre-collected nodes to improve performance
        errors.extend(self._check_imports(nodes))
        errors.extend(self._check_dangerous_calls(nodes))
        errors.extend(self._check_dangerous_attributes(nodes))

        # Cheap substring short-circuit: if none of these keywords appear,
        # skip the heavier file/network/code-exec AST checks entirely.
        _quick_keywords = (
            "requests",
            "socket",
            "open",
            "eval",
            "exec",
            "compile",
            "urllib",
            "http",
        )
        has_quick_kw = any(k in code for k in _quick_keywords)

        if has_quick_kw:
            # AST-based checks (primary and accurate)
            errors.extend(self._check_file_operations(nodes, code))
            errors.extend(self._check_network_operations(nodes, code))
            errors.extend(self._check_code_execution(nodes, code))

        if self.strict_mode:
            errors.extend(self._check_strict_mode(nodes))

        is_valid = len(errors) == 0

        if is_valid:
            logger.info("Code validation passed")
        else:
            logger.warning(f"Code validation failed with {len(errors)} errors")
            for error in errors:
                logger.warning(f"  - {error}")

        return is_valid, errors

    def _check_imports(self, tree_or_nodes) -> List[str]:
        """Check for dangerous imports"""
        errors = []
        nodes = (
            tree_or_nodes
            if isinstance(tree_or_nodes, list)
            else list(ast.walk(tree_or_nodes))
        )
        for node in nodes:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name.split(".")[0]
                    if module in self.DANGEROUS_IMPORTS:
                        errors.append(f"Dangerous import: {alias.name}")
                    elif module not in self.allowed_imports and self.strict_mode:
                        errors.append(f"Import not in whitelist: {alias.name}")

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module = node.module.split(".")[0]
                    if module in self.DANGEROUS_IMPORTS:
                        errors.append(f"Dangerous import from: {node.module}")
                    elif module not in self.allowed_imports and self.strict_mode:
                        errors.append(f"Import not in whitelist: {node.module}")

        return errors

    def _check_dangerous_calls(self, tree_or_nodes) -> List[str]:
        """Check for calls to dangerous built-in functions"""
        errors = []
        nodes = (
            tree_or_nodes
            if isinstance(tree_or_nodes, list)
            else list(ast.walk(tree_or_nodes))
        )
        for node in nodes:
            if isinstance(node, ast.Call):
                func_name = None

                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr

                if func_name in self.DANGEROUS_BUILTINS:
                    errors.append(f"Dangerous function call: {func_name}()")

        return errors

    def _check_dangerous_attributes(self, tree_or_nodes) -> List[str]:
        """Check for access to dangerous attributes"""
        errors = []
        nodes = (
            tree_or_nodes
            if isinstance(tree_or_nodes, list)
            else list(ast.walk(tree_or_nodes))
        )
        for node in nodes:
            if isinstance(node, ast.Attribute):
                if node.attr in self.DANGEROUS_ATTRS:
                    errors.append(f"Access to dangerous attribute: {node.attr}")

        return errors

    def _check_file_operations(self, nodes: List[ast.AST], code: str) -> List[str]:
        """AST-based check for file system operations; fallback regex available separately."""
        errors = []

        for node in nodes:
            # direct open() calls
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == "open":
                    errors.append("File operation detected: open() call")

            # attribute calls like Path(...).unlink() or os.remove()
            if isinstance(node, ast.Attribute):
                attr = node.attr
                if attr in ("unlink", "rmdir", "mkdir", "remove"):
                    errors.append(f"File operation detected: .{attr}() method")

            # with open(...) as ...
            if isinstance(node, ast.With):
                for item in node.items:
                    ctx = item.context_expr
                    if (
                        isinstance(ctx, ast.Call)
                        and isinstance(ctx.func, ast.Name)
                        and ctx.func.id == "open"
                    ):
                        errors.append(
                            "File operation detected: with open() context manager"
                        )

        return errors

    def _check_file_operations_regex(self, code: str) -> List[str]:
        """Regex fallback for file ops (kept for broad coverage)."""
        errors = []
        # regex fallbacks were removed; keep this as a stub in case future
        # fuzzy detection is desired.
        return errors

    def _check_network_operations(self, nodes: List[ast.AST], code: str) -> List[str]:
        """AST-based check for network operations; fallback regex available separately."""
        errors = []

        for node in nodes:
            # imports of network modules
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name.split(".")[0]
                    if module in ("socket", "requests", "urllib", "http"):
                        errors.append(f"Network import detected: {alias.name}")

            if isinstance(node, ast.ImportFrom) and node.module:
                module = node.module.split(".")[0]
                if module in ("socket", "requests", "urllib", "http"):
                    errors.append(f"Network import detected: {node.module}")

            # requests.get(...) or socket.connect()
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name):
                    root = node.func.value.id
                    if root in ("requests", "socket", "urllib", "http"):
                        errors.append(
                            f"Network operation detected: {root}.{node.func.attr}()"
                        )

        return errors

    def _check_network_operations_regex(self, code: str) -> List[str]:
        """Regex fallback for network ops."""
        errors = []
        # regex fallbacks were removed; keep this as a stub in case future
        # fuzzy detection is desired.
        return errors

    def _check_code_execution(self, nodes: List[ast.AST], code: str) -> List[str]:
        """AST-based check for direct dynamic code execution calls."""
        errors = []

        for node in nodes:
            if isinstance(node, ast.Call):
                # direct name calls: eval(), exec(), compile(), __import__()
                if isinstance(node.func, ast.Name) and node.func.id in (
                    "eval",
                    "exec",
                    "compile",
                    "__import__",
                ):
                    errors.append(f"Code execution detected: {node.func.id}()")

                # attribute access to builtins or modules (less common for eval/exec)
                if isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name) and node.func.attr in (
                        "eval",
                        "exec",
                        "compile",
                    ):
                        errors.append(
                            f"Code execution detected: {node.func.value.id}.{node.func.attr}()"
                        )

        return errors

    def _check_code_execution_regex(self, code: str) -> List[str]:
        """Regex fallback for dynamic code execution."""
        errors = []
        # regex fallbacks were removed; keep this as a stub in case future
        # fuzzy detection is desired.
        return errors

    def _check_strict_mode(self, tree_or_nodes: ast.AST) -> List[str]:
        """Additional checks for strict mode"""
        errors = []
        nodes = (
            tree_or_nodes
            if isinstance(tree_or_nodes, list)
            else list(ast.walk(tree_or_nodes))
        )

        # Check for lambda functions (can be used to bypass restrictions)
        for node in nodes:
            if isinstance(node, ast.Lambda):
                errors.append("Lambda functions not allowed in strict mode")

        # Check for list/dict comprehensions with complex expressions
        # (can be used for obfuscation)
        for node in nodes:
            if isinstance(node, (ast.ListComp, ast.DictComp, ast.SetComp)):
                if len(list(ast.walk(node))) > 10:
                    errors.append("Complex comprehension detected")

        return errors

    def check_function_signature(
        self, code: str, expected_name: str, expected_params: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Validate function signature matches expected

        Args:
            code: Python code
            expected_name: Expected function name
            expected_params: Expected parameter names

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, [f"Syntax error: {e}"]

        # Find function definition
        func_def = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == expected_name:
                func_def = node
                break

        if not func_def:
            errors.append(f"Function '{expected_name}' not found")
            return False, errors

        # Check parameters
        actual_params = [arg.arg for arg in func_def.args.args]
        if actual_params != expected_params:
            errors.append(
                f"Parameter mismatch: expected {expected_params}, got {actual_params}"
            )

        # Check for return statement
        has_return = any(isinstance(node, ast.Return) for node in ast.walk(func_def))
        if not has_return:
            errors.append("Function must have a return statement")

        return len(errors) == 0, errors
