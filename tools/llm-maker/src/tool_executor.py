"""
Tool Executor - Executes tools in a sandboxed environment
"""
import logging
import signal
import sys
from contextlib import contextmanager
from typing import Any, Dict, Optional
import traceback

logger = logging.getLogger(__name__)

# Try to import RestrictedPython if available
try:
    from RestrictedPython import compile_restricted
    from RestrictedPython.Guards import safe_builtins, guarded_iter_unpack_sequence
    HAS_RESTRICTED_PYTHON = True
except ImportError:
    HAS_RESTRICTED_PYTHON = False
    logger.warning("RestrictedPython not available, using basic sandboxing")


class ExecutionTimeout(Exception):
    """Raised when execution exceeds timeout"""
    pass


class ToolExecutor:
    """Executes tools in a restricted environment"""
    
    def __init__(self, timeout: int = 5, max_output_size: int = 10000):
        """
        Initialize executor
        
        Args:
            timeout: Maximum execution time in seconds
            max_output_size: Maximum size of output in bytes
        """
        self.timeout = timeout
        self.max_output_size = max_output_size
        self._setup_safe_globals()
    
    def _setup_safe_globals(self):
        """Setup safe global namespace for execution"""
        # Start with safe builtins
        self.safe_globals = {
            '__builtins__': {
                # Safe built-in functions
                'abs': abs,
                'all': all,
                'any': any,
                'bool': bool,
                'bytes': bytes,
                'chr': chr,
                'dict': dict,
                'enumerate': enumerate,
                'filter': filter,
                'float': float,
                'format': format,
                'frozenset': frozenset,
                'int': int,
                'isinstance': isinstance,
                'issubclass': issubclass,
                'iter': iter,
                'len': len,
                'list': list,
                'map': map,
                'max': max,
                'min': min,
                'next': next,
                'ord': ord,
                'pow': pow,
                'range': range,
                'repr': repr,
                'reversed': reversed,
                'round': round,
                'set': set,
                'slice': slice,
                'sorted': sorted,
                'str': str,
                'sum': sum,
                'tuple': tuple,
                'type': type,
                'zip': zip,
                # Safe modules
                '__name__': '__main__',
                '__doc__': None,
            }
        }
        
        # Add safe iteration support if RestrictedPython is available
        if HAS_RESTRICTED_PYTHON:
            self.safe_globals['_iter_unpack_sequence_'] = guarded_iter_unpack_sequence
    
    @contextmanager
    def _timeout_context(self, seconds: int):
        """Context manager for execution timeout"""
        def timeout_handler(signum, frame):
            raise ExecutionTimeout(f"Execution exceeded {seconds} seconds")
        
        # Use signal on Unix-like systems
        if hasattr(signal, 'SIGALRM'):
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            try:
                yield
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        else:
            # On Windows, use threading-based timeout
            import threading
            timer = None
            timed_out = [False]
            
            def timeout_callback():
                timed_out[0] = True
            
            try:
                timer = threading.Timer(seconds, timeout_callback)
                timer.start()
                yield
                if timed_out[0]:
                    raise ExecutionTimeout(f"Execution exceeded {seconds} seconds")
            finally:
                if timer:
                    timer.cancel()
    
    def execute(
        self, 
        code: str, 
        function_name: str,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute tool code with given arguments
        
        Args:
            code: Python code to execute
            function_name: Name of function to call
            args: Arguments to pass to function
            
        Returns:
            Dictionary with result or error
        """
        try:
            # Compile code
            if HAS_RESTRICTED_PYTHON:
                byte_code = compile_restricted(
                    code,
                    filename='<tool>',
                    mode='exec'
                )
                
                if byte_code.errors:
                    return {
                        'success': False,
                        'error': f"Compilation errors: {byte_code.errors}",
                        'error_type': 'CompilationError'
                    }
                compiled_code = byte_code.code
            else:
                # Fallback to regular compile (less safe but functional)
                try:
                    compiled_code = compile(code, '<tool>', 'exec')
                except SyntaxError as e:
                    return {
                        'success': False,
                        'error': f"Syntax error: {e}",
                        'error_type': 'SyntaxError'
                    }
            
            # Create execution namespace
            exec_globals = self.safe_globals.copy()
            exec_locals = {}
            
            # Execute code to define function
            try:
                with self._timeout_context(self.timeout):
                    exec(compiled_code, exec_globals, exec_locals)
            except ExecutionTimeout as e:
                return {
                    'success': False,
                    'error': str(e),
                    'error_type': 'TimeoutError'
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': f"Execution error: {str(e)}",
                    'error_type': type(e).__name__,
                    'traceback': traceback.format_exc()
                }
            
            # Get the function
            if function_name not in exec_locals:
                return {
                    'success': False,
                    'error': f"Function '{function_name}' not defined",
                    'error_type': 'NameError'
                }
            
            func = exec_locals[function_name]
            
            # Call the function
            try:
                with self._timeout_context(self.timeout):
                    result = func(**args)
            except ExecutionTimeout as e:
                return {
                    'success': False,
                    'error': str(e),
                    'error_type': 'TimeoutError'
                }
            except TypeError as e:
                return {
                    'success': False,
                    'error': f"Invalid arguments: {str(e)}",
                    'error_type': 'TypeError'
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': f"Runtime error: {str(e)}",
                    'error_type': type(e).__name__,
                    'traceback': traceback.format_exc()
                }
            
            # Check output size
            result_str = str(result)
            if len(result_str) > self.max_output_size:
                return {
                    'success': False,
                    'error': f"Output too large (>{self.max_output_size} bytes)",
                    'error_type': 'OutputError'
                }
            
            logger.info(f"Successfully executed {function_name}")
            
            return {
                'success': True,
                'result': result,
                'result_type': type(result).__name__
            }
            
        except Exception as e:
            logger.error(f"Unexpected error executing tool: {e}")
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}",
                'error_type': 'UnexpectedError',
                'traceback': traceback.format_exc()
            }
    
    def test_execution(self, code: str) -> bool:
        """
        Test if code can be compiled and executed
        
        Args:
            code: Python code to test
            
        Returns:
            True if code can be executed
        """
        try:
            if HAS_RESTRICTED_PYTHON:
                byte_code = compile_restricted(code, filename='<test>', mode='exec')
                return len(byte_code.errors) == 0
            else:
                compile(code, '<test>', 'exec')
                return True
        except Exception:
            return False
