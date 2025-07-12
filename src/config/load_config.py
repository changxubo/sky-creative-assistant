import os
from typing import Any, Dict, Optional, Union

import yaml


def replace_env_vars(value: str) -> str:
    """
    Replace environment variables in string values.

    Args:
        value (str): String that may contain environment variable references starting with '$'

    Returns:
        str: String with environment variables replaced, or original value if not a string

    Note:
        If environment variable is not found, returns the variable name as fallback
    """
    if not isinstance(value, str):
        return value

    # Check if value starts with '$' indicating an environment variable
    if value.startswith("$"):
        env_var_name = value[1:]  # Remove the '$' prefix
        # Get environment variable value, fallback to variable name if not found
        return os.getenv(env_var_name, env_var_name)

    return value


def process_dict(config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Recursively process dictionary to replace environment variables in string values.

    Args:
        config (Optional[Dict[str, Any]]): Configuration dictionary that may contain
                                         environment variable references

    Returns:
        Dict[str, Any]: Processed dictionary with environment variables replaced
    """
    if not config:
        return {}

    result = {}
    for key, value in config.items():
        if isinstance(value, dict):
            # Recursively process nested dictionaries
            result[key] = process_dict(value)
        elif isinstance(value, str):
            # Replace environment variables in string values
            result[key] = replace_env_vars(value)
        else:
            # Keep other types as-is
            result[key] = value

    return result


# Global cache to store loaded configurations for performance optimization
_config_cache: Dict[str, Dict[str, Any]] = {}


def load_yaml_config(file_path: str) -> Dict[str, Any]:
    """
    Load and process YAML configuration file with caching and environment variable substitution.

    Args:
        file_path (str): Path to the YAML configuration file

    Returns:
        Dict[str, Any]: Processed configuration dictionary with environment variables replaced

    Raises:
        yaml.YAMLError: If YAML file has syntax errors
        IOError: If file cannot be read due to permissions or other I/O issues
    """
    # Validate input parameters
    if not file_path or not file_path.strip():
        return {}

    # Normalize file path for consistent caching
    normalized_path = os.path.normpath(file_path)

    # Return empty dict if file doesn't exist
    if not os.path.exists(normalized_path):
        return {}

    # Check cache first to avoid redundant file operations
    if normalized_path in _config_cache:
        return _config_cache[normalized_path]

    try:
        # Load YAML configuration with explicit UTF-8 encoding
        with open(normalized_path, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)

        # Handle case where YAML file is empty or contains only comments
        if config is None:
            config = {}

        # Process the configuration to replace environment variables
        processed_config = process_dict(config)

        # Cache the processed configuration for future use
        _config_cache[normalized_path] = processed_config
        return processed_config

    except yaml.YAMLError as yaml_error:
        # Log YAML parsing errors and return empty config as fallback
        print(f"Error parsing YAML file {normalized_path}: {yaml_error}")
        return {}
    except IOError as io_error:
        # Log file I/O errors and return empty config as fallback
        print(f"Error reading file {normalized_path}: {io_error}")
        return {}
