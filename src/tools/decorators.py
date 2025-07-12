import functools
import logging
from typing import Any, Callable, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def log_io(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    A decorator that logs the input parameters and output of a tool function.

    Args:
        func: The tool function to be decorated

    Returns:
        The wrapped function with input/output logging
    """

def log_io(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    A decorator that logs the input parameters and output of a tool function.

    Args:
        func (Callable[..., Any]): The tool function to be decorated

    Returns:
        Callable[..., Any]: The wrapped function with input/output logging
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Log input parameters with safe string conversion
        function_name = func.__name__
        try:
            # Safe parameter formatting to handle complex objects
            args_str = ", ".join(str(arg)[:100] for arg in args)  # Limit length to prevent log spam
            kwargs_str = ", ".join(f"{k}={str(v)[:100]}" for k, v in kwargs.items())
            params = ", ".join(filter(None, [args_str, kwargs_str]))
            logger.info(f"Tool {function_name} called with parameters: {params}")
        except Exception as e:
            logger.warning(f"Tool {function_name} called (parameter logging failed: {e})")

        try:
            # Execute the function
            result = func(*args, **kwargs)

            # Log the output with safe string conversion
            try:
                result_str = str(result)[:200]  # Limit output length
                logger.info(f"Tool {function_name} returned: {result_str}")
            except Exception as e:
                logger.info(f"Tool {function_name} completed successfully (result logging failed: {e})")

            return result
        except Exception as e:
            logger.error(f"Tool {function_name} failed with error: {e}")
            raise  # Re-raise the original exception

    return wrapper


class LoggedToolMixin:
    """
    A mixin class that adds comprehensive logging functionality to any tool.
    
    This class provides logging capabilities for tool operations including
    parameter logging, execution tracking, and result logging. It's designed
    to be used with multiple inheritance alongside existing tool classes.
    """

    def _log_operation(self, method_name: str, *args: Any, **kwargs: Any) -> None:
        """
        Helper method to log tool operations with safe parameter handling.
        
        Args:
            method_name (str): The name of the method being called
            *args: Positional arguments passed to the method
            **kwargs: Keyword arguments passed to the method
        """
        tool_name = self.__class__.__name__.replace("Logged", "")
        try:
            # Safe parameter formatting to prevent logging errors
            args_str = ", ".join(str(arg)[:100] for arg in args)
            kwargs_str = ", ".join(f"{k}={str(v)[:100]}" for k, v in kwargs.items())
            params = ", ".join(filter(None, [args_str, kwargs_str]))
            logger.debug(f"Tool {tool_name}.{method_name} called with parameters: {params}")
        except Exception as e:
            logger.debug(f"Tool {tool_name}.{method_name} called (parameter logging failed: {e})")

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """
        Override _run method to add comprehensive logging.
        
        Args:
            *args: Positional arguments passed to the tool
            **kwargs: Keyword arguments passed to the tool
            
        Returns:
            Any: The result from the parent class's _run method
            
        Raises:
            Exception: Re-raises any exception from the parent _run method
        """
        self._log_operation("_run", *args, **kwargs)
        
        try:
            result = super()._run(*args, **kwargs)
            
            # Log successful execution with safe result formatting
            tool_name = self.__class__.__name__.replace("Logged", "")
            try:
                result_str = str(result)[:200]  # Limit result length
                logger.debug(f"Tool {tool_name} returned: {result_str}")
            except Exception as e:
                logger.debug(f"Tool {tool_name} completed successfully (result logging failed: {e})")
                
            return result
        except Exception as e:
            tool_name = self.__class__.__name__.replace("Logged", "")
            logger.error(f"Tool {tool_name} failed with error: {e}")
            raise  # Re-raise the original exception


def create_logged_tool(base_tool_class: Type[T]) -> Type[T]:
    """
    Factory function to create a logged version of any tool class.
    
    This function creates a new class that combines LoggedToolMixin with any
    existing tool class, providing automatic logging capabilities without
    modifying the original tool implementation.

    Args:
        base_tool_class (Type[T]): The original tool class to be enhanced with logging

    Returns:
        Type[T]: A new class that inherits from both LoggedToolMixin and the base tool class
        
    Example:
        >>> class MyTool:
        ...     def _run(self, query: str) -> str:
        ...         return f"Result for {query}"
        >>> 
        >>> LoggedMyTool = create_logged_tool(MyTool)
        >>> tool_instance = LoggedMyTool()
    """
    # Validate input parameter
    if not isinstance(base_tool_class, type):
        raise TypeError(f"Expected a class type, got {type(base_tool_class)}")

    class LoggedTool(LoggedToolMixin, base_tool_class):
        """Dynamically created logged version of the base tool class."""
        pass

    # Set a descriptive name for the dynamically created class
    logged_class_name = f"Logged{base_tool_class.__name__}"
    LoggedTool.__name__ = logged_class_name
    LoggedTool.__qualname__ = logged_class_name
    
    # Preserve the original class documentation if available
    if hasattr(base_tool_class, "__doc__") and base_tool_class.__doc__:
        LoggedTool.__doc__ = f"Logged version of {base_tool_class.__name__}.\n\n{base_tool_class.__doc__}"
    
    return LoggedTool
