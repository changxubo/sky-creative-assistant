import logging
from typing import Annotated, Optional

# Third-party imports
from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL

# Local imports
from .decorators import log_io

# Initialize REPL instance and configure logger
_python_repl_instance = PythonREPL()
_logger = logging.getLogger(__name__)


@tool
@log_io
def python_repl_tool(
    code: Annotated[
        str, "The python code to execute to do further analysis or calculation."
    ],
) -> str:
    """
    Execute Python code using a persistent REPL environment for data analysis and calculations.
    
    This tool provides a sandboxed Python environment where code can be executed
    and results can be captured. Variables and imports persist across calls within
    the same session.
    
    Args:
        code (str): The Python code to execute. Must be a non-empty string.
                   To see output values, use print() statements as they will be
                   visible to the user.
    
    Returns:
        str: A formatted string containing either:
             - Success message with executed code and stdout output
             - Error message with code snippet and error details
    
    Raises:
        No exceptions are raised directly; all errors are caught and returned
        as formatted error messages.
    """
    # Validate input type
    if not isinstance(code, str):
        error_message = f"Invalid input: code must be a string, got {type(code).__name__}"
        _logger.error("Type validation failed: %s", error_message)
        return _format_error_response(code, error_message)
    
    # Validate input content - check for empty or whitespace-only strings
    if not code.strip():
        error_message = "Invalid input: code cannot be empty or contain only whitespace"
        _logger.error("Content validation failed: %s", error_message)
        return _format_error_response(code, error_message)
    
    _logger.info("Executing Python code (length: %d characters)", len(code))
    
    try:
        # Execute the code in the persistent REPL environment
        execution_result = _python_repl_instance.run(code)
        
        # Validate execution result and check for error patterns
        if _contains_error_indicators(execution_result):
            _logger.error("Code execution failed with error indicators in result")
            return _format_error_response(code, execution_result)
        
        _logger.info("Code execution completed successfully")
        return _format_success_response(code, execution_result)
        
    except (SyntaxError, NameError, TypeError, ValueError) as specific_error:
        # Handle common Python execution errors
        error_message = f"{type(specific_error).__name__}: {str(specific_error)}"
        _logger.error("Python execution error: %s", error_message)
        return _format_error_response(code, error_message)
        
    except Exception as unexpected_error:
        # Handle any other unexpected errors
        error_message = f"Unexpected error: {type(unexpected_error).__name__}: {str(unexpected_error)}"
        _logger.error("Unexpected execution error: %s", error_message)
        return _format_error_response(code, error_message)


def _contains_error_indicators(result: Optional[str]) -> bool:
    """
    Check if the execution result contains error indicators.
    
    Args:
        result: The result string from code execution
        
    Returns:
        bool: True if error indicators are found, False otherwise
    """
    if not isinstance(result, str):
        return False
    
    # Common error patterns that indicate execution failure
    error_patterns = ["Error", "Exception", "Traceback", "SyntaxError", "NameError"]
    return any(pattern in result for pattern in error_patterns)


def _format_error_response(code: str, error_message: str) -> str:
    """
    Format a standardized error response message.
    
    Args:
        code: The code that caused the error
        error_message: The error message to include
        
    Returns:
        str: Formatted error response
    """
    return f"Error executing code:\n```python\n{code}\n```\nError: {error_message}"


def _format_success_response(code: str, result: Optional[str]) -> str:
    """
    Format a standardized success response message.
    
    Args:
        code: The successfully executed code
        result: The execution result/output
        
    Returns:
        str: Formatted success response
    """
    # Handle None or empty results gracefully
    output = result if result is not None else "(No output)"
    return f"Successfully executed:\n```python\n{code}\n```\nStdout: {output}"
