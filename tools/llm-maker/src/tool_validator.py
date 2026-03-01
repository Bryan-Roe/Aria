"""
Tool Validator - Validates generated code for safety
"""
import ast
import logging
import re
from typing import Tuple, List, Set, Optional
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)

# Pre-compiled regex patterns for performance (compile once, use many times)
_FILE_OPERATION_PATTERNS = [
    (re.compile(r'\bopen\s*\('), "open() function call"),
    (re.compile(r'\.unlink\s*\('), ".unlink() method (file deletion)"),
    (re.compile(r'\.rmdir\s*\('), ".rmdir() method"),
    (re.compile(r'\.mkdir\s*\('), ".mkdir() method"),
    (re.compile(r'\bwith\s+open\s*\('), "with open() context manager"),
]

_NETWORK_OPERATION_PATTERNS = [
    (re.compile(r'\bsocket\.\w+'), "socket module usage"),
    (re.compile(r'\burllib\.\w+'), "urllib module usage"),
    (re.compile(r'\brequests\.\w+'), "requests module usage"),
    (re.compile(r'\bhttp\.\w+'), "http module usage"),
    (re.compile(r'requests\.(get|post|put|delete|patch)\b'), "requests HTTP method"),
    (re.compile(r'urllib\.request\.urlopen'), "urllib.request.urlopen"),
    (re.compile(r'socket\.(socket|connect|bind|listen)'), "socket operations"),
]

_CODE_EXEC_PATTERNS = [
    (re.compile(r'\beval\s*\('), "eval"),
    (re.compile(r'\bexec\s*\('), "exec"),
    (re.compile(r'\bcompile\s*\('), "compile"),
    (re.compile(r'\b__import__\s*\('), "__import__"),
]


class ToolValidator:
    """Validates generated tools for safety and correctness"""
    
    # Dangerous imports that should never be allowed
    DANGEROUS_IMPORTS = {
        'os', 'sys', 'subprocess', 'shutil', 'pathlib',
        'socket', 'urllib', 'requests', 'http', 'ftplib',
        'pickle', 'shelve', 'dbm', 'sqlite3', 
        'threading', 'multiprocessing', 'asyncio',
        '__builtin__', 'builtins', 'importlib',
        'ctypes', 'cffi', 'pty', 'fcntl'
    }
    
    # Dangerous built-in functions
    DANGEROUS_BUILTINS = {
        '__import__', 'eval', 'exec', 'compile', 
        'open', 'input', 'breakpoint', 'exit', 'quit',
        'help', 'license', 'copyright', 'credits'
    }
    
    # Dangerous attributes and magic methods
    DANGEROUS_ATTRS = {
        '__code__', '__globals__', '__builtins__',
        '__dict__', '__class__', '__bases__',
        '__subclasses__', '__mro__'
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize validator with configuration
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.allowed_imports = set(self.config.get('validation', {}).get('allowed_imports', []))
        self.strict_mode = self.config.get('validation', {}).get('strict_mode', True)
    
    def _load_config(self, config_path: Optional[Path]) -> dict:
        """Load configuration from YAML file"""
        if config_path and config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        
        # Default configuration if file not found
        default_config_path = Path(__file__).parent.parent / "llm_maker_config.yaml"
        if default_config_path.exists():
            with open(default_config_path, 'r') as f:
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
        
        # Run safety checks
        errors.extend(self._check_imports(tree))
        errors.extend(self._check_dangerous_calls(tree))
        errors.extend(self._check_dangerous_attributes(tree))
        errors.extend(self._check_file_operations(code))
        errors.extend(self._check_network_operations(code))
        errors.extend(self._check_code_execution(code))
        
        if self.strict_mode:
            errors.extend(self._check_strict_mode(tree))
        
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.info("Code validation passed")
        else:
            logger.warning(f"Code validation failed with {len(errors)} errors")
            for error in errors:
                logger.warning(f"  - {error}")
        
        return is_valid, errors
    
    def _check_imports(self, tree: ast.AST) -> List[str]:
        """Check for dangerous imports"""
        errors = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name.split('.')[0]
                    if module in self.DANGEROUS_IMPORTS:
                        errors.append(f"Dangerous import: {alias.name}")
                    elif module not in self.allowed_imports and self.strict_mode:
                        errors.append(f"Import not in whitelist: {alias.name}")
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module = node.module.split('.')[0]
                    if module in self.DANGEROUS_IMPORTS:
                        errors.append(f"Dangerous import from: {node.module}")
                    elif module not in self.allowed_imports and self.strict_mode:
                        errors.append(f"Import not in whitelist: {node.module}")
        
        return errors
    
    def _check_dangerous_calls(self, tree: ast.AST) -> List[str]:
        """Check for calls to dangerous built-in functions"""
        errors = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = None
                
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                
                if func_name in self.DANGEROUS_BUILTINS:
                    errors.append(f"Dangerous function call: {func_name}()")
        
        return errors
    
    def _check_dangerous_attributes(self, tree: ast.AST) -> List[str]:
        """Check for access to dangerous attributes"""
        errors = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                if node.attr in self.DANGEROUS_ATTRS:
                    errors.append(f"Access to dangerous attribute: {node.attr}")
        
        return errors
    
    def _check_file_operations(self, code: str) -> List[str]:
        """Check for file system operations"""
        errors = []
        
        # Use pre-compiled patterns for performance
        for compiled_pattern, description in _FILE_OPERATION_PATTERNS:
            if compiled_pattern.search(code):
                errors.append(f"File operation detected: {description}")
        
        return errors
    
    def _check_network_operations(self, code: str) -> List[str]:
        """Check for network operations"""
        errors = []
        
        # Use pre-compiled patterns for performance
        for compiled_pattern, description in _NETWORK_OPERATION_PATTERNS:
            if compiled_pattern.search(code):
                errors.append(f"Network operation detected: {description}")
        
        return errors
    
    def _check_code_execution(self, code: str) -> List[str]:
        """Check for dynamic code execution"""
        errors = []
        
        # Use pre-compiled patterns for performance
        for compiled_pattern, func_name in _CODE_EXEC_PATTERNS:
            if compiled_pattern.search(code):
                errors.append(f"Code execution detected: {func_name}()")
        
        return errors
    
    def _check_strict_mode(self, tree: ast.AST) -> List[str]:
        """Additional checks for strict mode"""
        errors = []
        
        # Check for lambda functions (can be used to bypass restrictions)
        for node in ast.walk(tree):
            if isinstance(node, ast.Lambda):
                errors.append("Lambda functions not allowed in strict mode")
        
        # Check for list/dict comprehensions with complex expressions
        # (can be used for obfuscation)
        for node in ast.walk(tree):
            if isinstance(node, (ast.ListComp, ast.DictComp, ast.SetComp)):
                if len(list(ast.walk(node))) > 10:
                    errors.append("Complex comprehension detected")
        
        return errors
    
    def check_function_signature(
        self, 
        code: str, 
        expected_name: str,
        expected_params: List[str]
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
        has_return = any(
            isinstance(node, ast.Return) 
            for node in ast.walk(func_def)
        )
        if not has_return:
            errors.append("Function must have a return statement")
        
        return len(errors) == 0, errors
