"""
This module provides functionality for creating, caching, and managing Large Language Model (LLM)
instances. It supports different LLM types (reasoning, basic, vision) and handles configuration
loading from both YAML files and environment variables.

Changes:
• Optimized imports (grouped and alphabetized: standard library → third-party → local modules)
• Enhanced docstrings with Args and Returns documentation
• Added type hints for better code clarity
• Added None checks and error handling improvements
• Improved variable naming for better readability
• Added inline comments for complex logic
• Enhanced exception handling with specific error messages
"""

# Standard library imports
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union, get_args

# Third-party imports
import httpx
from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langfuse.langchain import CallbackHandler

# Local imports
from src.config import load_yaml_config
from src.config.llm_map import LLMType
from .chat_openai_reasoning import ChatOpenAIReasoning

# Global cache for LLM instances to avoid recreation and improve performance
_llm_instance_cache: Dict[LLMType, Union[ChatOpenAI, ChatDeepSeek, ChatNVIDIA]] = {}

# Initialize the Langfuse handler
langfuse_handler = CallbackHandler()

def _get_config_file_path() -> str:
    """
    Get the absolute path to the configuration file.

    Returns:
        str: Absolute path to the conf.yaml configuration file

    Raises:
        FileNotFoundError: If the configuration file doesn't exist
    """
    config_path = Path(__file__).parent.parent.parent / "conf.yaml"
    config_path_resolved = config_path.resolve()

    # Ensure the configuration file exists
    if not config_path_resolved.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path_resolved}")

    return str(config_path_resolved)


def _get_llm_type_config_keys() -> Dict[str, str]:
    """
    Get mapping of LLM types to their configuration keys in the YAML file.

    This mapping defines how different LLM types correspond to configuration
    sections in the conf.yaml file.

    Returns:
        Dict[str, str]: Dictionary mapping LLM type names to configuration keys
                       - "reasoning": For complex reasoning tasks
                       - "basic": For general purpose tasks
                       - "vision": For vision-related tasks
    """
    return {
        "reasoning": "REASONING_MODEL",  # For complex reasoning tasks
        "basic": "BASIC_MODEL",  # For general purpose tasks
        "vision": "VISION_MODEL",  # For vision-related tasks
    }


def _get_environment_config(llm_type: str) -> Dict[str, Any]:
    """
    Extract LLM configuration from environment variables.

    Searches for environment variables with the pattern:
    {LLM_TYPE}_MODEL__{CONFIG_KEY} and extracts the configuration.

    Args:
        llm_type (str): Type of LLM ("reasoning", "basic", "vision")

    Returns:
        Dict[str, Any]: Dictionary containing configuration extracted from environment variables

    Example:
        For llm_type="basic" and env var "BASIC_MODEL__API_KEY=abc123",
        returns {"api_key": "abc123"}
    """
    if not llm_type:
        return {}

    environment_variable_prefix = f"{llm_type.upper()}_MODEL__"
    extracted_config = {}

    for env_key, env_value in os.environ.items():
        if env_key.startswith(environment_variable_prefix):
            # Extract the configuration key by removing the prefix
            config_key = env_key[len(environment_variable_prefix) :].lower()
            extracted_config[config_key] = env_value

    return extracted_config


def _create_llm_from_config(
    llm_type: LLMType, config: Dict[str, Any]
) -> Union[ChatOpenAI, ChatDeepSeek, ChatNVIDIA]:
    """
    Create an LLM instance using the provided configuration.

    This function handles the creation of different LLM types with their specific
    configurations, including SSL settings and provider-specific parameters.

    Args:
        llm_type (LLMType): Type of LLM to create ("reasoning", "basic", "vision")
        config (Dict[str, Any]): Configuration dictionary containing model settings

    Returns:
        Union[ChatOpenAI, ChatDeepSeek]: Configured LLM instance

    Raises:
        ValueError: If llm_type is unknown or configuration is invalid
        TypeError: If configuration is not a dictionary
    """
    llm_type_config_mapping = _get_llm_type_config_keys()
    configuration_key = llm_type_config_mapping.get(llm_type)

    if not configuration_key:
        supported_types = list(llm_type_config_mapping.keys())
        raise ValueError(
            f"Unknown LLM type: {llm_type}. Supported types: {supported_types}"
        )

    # Extract configuration for this specific LLM type
    llm_specific_config = config.get(configuration_key, {})
    if not isinstance(llm_specific_config, dict):
        raise TypeError(
            f"Invalid LLM configuration for {llm_type}: expected dict, got {type(llm_specific_config)}"
        )

    # Get configuration from environment variables (these take precedence)
    environment_config = _get_environment_config(llm_type)

    # Merge configurations with environment variables taking precedence
    merged_config = {**llm_specific_config, **environment_config}

    if not merged_config:
        raise ValueError(f"No configuration found for LLM type: {llm_type}")

    # Handle SSL verification settings
    ssl_verification_enabled = merged_config.pop("verify_ssl", True)

    # Create custom HTTP client if SSL verification is disabled
    if not ssl_verification_enabled:
        http_client = httpx.Client(verify=False)
        async_http_client = httpx.AsyncClient(verify=False)
        merged_config["http_client"] = http_client
        merged_config["http_async_client"] = async_http_client

    # Create and return the appropriate LLM instance
    if llm_type == "reasoning":
        # return ChatOpenAI(**merged_config, extra_body={"enable_thinking": True})
        # return ChatDeepSeek(**merged_config)
        # return ChatOpenAI(**merged_config)
        # return ChatNVIDIA(**merged_config,  extra_body={"chat_template_kwargs": {"thinking":True}})
        return ChatOpenAIReasoning(
            **merged_config, callbacks=[langfuse_handler], extra_body={"chat_template_kwargs": {"thinking": True}}
        )
    else:
        # return ChatOpenAI(**merged_config, extra_body={"enable_thinking": False})
        # return ChatOpenAI(**merged_config)
        # return ChatNVIDIA(**merged_config,  extra_body={"chat_template_kwargs": {"thinking":False}})
        return ChatOpenAI(
            **merged_config,callbacks=[langfuse_handler], extra_body={"chat_template_kwargs": {"thinking": False}}
        )


def get_llm_by_type(llm_type: LLMType) -> Union[ChatOpenAI, ChatDeepSeek, ChatNVIDIA]:
    """
    Get LLM instance by type with caching for performance optimization.

    This function implements a caching mechanism to avoid recreating LLM instances
    repeatedly, which improves performance and reduces initialization overhead.

    Args:
        llm_type (LLMType): Type of LLM to retrieve ("reasoning", "basic", "vision")

    Returns:
        Union[ChatOpenAI, ChatDeepSeek]: Cached or newly created LLM instance

    Raises:
        ValueError: If configuration is invalid or LLM type is unsupported
        FileNotFoundError: If configuration file is missing
    """
    # Return cached instance if available
    if llm_type in _llm_instance_cache:
        return _llm_instance_cache[llm_type]

    # Load configuration and create new LLM instance
    configuration_file_path = _get_config_file_path()
    loaded_config = load_yaml_config(configuration_file_path)

    if loaded_config is None:
        raise ValueError(f"Failed to load configuration from {configuration_file_path}")

    llm_instance = _create_llm_from_config(llm_type, loaded_config)

    # Cache the instance for future use
    _llm_instance_cache[llm_type] = llm_instance
    return llm_instance


def get_configured_llm_models() -> Dict[str, list[str]]:
    """
    Get all configured LLM models grouped by type.

    This function scans both YAML configuration and environment variables to
    identify which LLM models are properly configured and available for use.

    Returns:
        Dict[str, list[str]]: Dictionary mapping LLM types to lists of configured model names
                             Example: {"reasoning": ["deepseek-reasoner"], "basic": ["gpt-4"]}

    Note:
        Returns empty dictionary if configuration loading fails to prevent application crashes
    """
    try:
        # Load configuration from YAML file
        configuration_file_path = _get_config_file_path()
        loaded_config = load_yaml_config(configuration_file_path)

        if loaded_config is None:
            print(
                f"Warning: Could not load configuration from {configuration_file_path}"
            )
            return {}

        llm_type_config_mapping = _get_llm_type_config_keys()
        configured_models: Dict[str, list[str]] = {}

        # Check each supported LLM type
        for llm_type in get_args(LLMType):
            # Get configuration from YAML file
            configuration_key = llm_type_config_mapping.get(llm_type, "")
            yaml_configuration = (
                loaded_config.get(configuration_key, {}) if configuration_key else {}
            )

            # Get configuration from environment variables
            environment_config = _get_environment_config(llm_type)

            # Merge configurations with environment variables taking precedence
            merged_config = {**yaml_configuration, **environment_config}

            # Check if model is configured and add to results
            model_name = merged_config.get("model")
            if model_name:
                configured_models.setdefault(llm_type, []).append(model_name)

        return configured_models

    except Exception as error:
        # Log error and return empty dict to prevent application failure
        print(f"Warning: Failed to load LLM configuration: {error}")
        return {}


def clear_llm_instance_cache() -> None:
    """
    Clear the LLM instance cache.

    This function removes all cached LLM instances, forcing them to be recreated
    on the next request. Useful for refreshing configurations or freeing memory.

    Returns:
        None
    """
    global _llm_instance_cache
    _llm_instance_cache.clear()


def is_llm_type_configured(llm_type: LLMType) -> bool:
    """
    Check if a specific LLM type is properly configured.

    Args:
        llm_type (LLMType): Type of LLM to check ("reasoning", "basic", "vision")

    Returns:
        bool: True if the LLM type is configured and available, False otherwise
    """
    try:
        configured_models = get_configured_llm_models()
        return llm_type in configured_models and len(configured_models[llm_type]) > 0
    except Exception:
        return False


def get_llm_cache_status() -> Dict[str, Any]:
    """
    Get information about the current LLM cache state.

    Returns:
        Dict[str, Any]: Dictionary containing:
                       - cached_types: List of currently cached LLM types
                       - cache_size: Number of cached instances
                       - available_types: List of all supported LLM types
    """
    return {
        "cached_types": list(_llm_instance_cache.keys()),
        "cache_size": len(_llm_instance_cache),
        "available_types": list(_get_llm_type_config_keys().keys()),
    }


# Future implementation notes:
# The following LLM instances can be pre-initialized for specific use cases:
# reasoning_llm = get_llm_by_type("reasoning")  # For complex reasoning and analysis tasks
# vl_llm = get_llm_by_type("vision")           # For vision and image processing tasks

# Additional optimization opportunities:
# 1. Implement async LLM loading for better performance
# 2. Add configuration validation with pydantic models
# 3. Implement LLM health checks and automatic failover
# 4. Add metrics and monitoring for LLM usage
# 5. Consider implementing LLM connection pooling for high-load scenarios
