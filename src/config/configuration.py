import os
from dataclasses import dataclass, field, fields
from typing import Any, Dict, Optional

from langchain_core.runnables import RunnableConfig

from src.config.report_style import ReportStyle
from src.rag.types import Resource


@dataclass(kw_only=True)
class Configuration:
    """Configuration class for research workflow parameters.
    
    This class defines all configurable parameters for the research workflow,
    including resource management, execution limits, search parameters, MCP settings,
    and output formatting options. It supports initialization from environment
    variables and RunnableConfig objects.
    
    Attributes:
        resources: List of Resource objects to be used during research
        max_plan_iterations: Maximum number of planning iterations allowed
        max_step_num: Maximum number of steps permitted in a single plan
        max_search_results: Maximum number of search results to retrieve
        mcp_settings: Dictionary containing MCP (Model Context Protocol) settings
                     and dynamically loaded tools configuration
        report_style: Output report formatting style (academic, business, etc.)
        enable_deep_thinking: Flag to enable enhanced reasoning capabilities
    """

    resources: list[Resource] = field(
        default_factory=list
    )  # Resources to be used for the research
    max_plan_iterations: int = 1  # Maximum number of plan iterations
    max_step_num: int = 3  # Maximum number of steps in a plan
    max_search_results: int = 3  # Maximum number of search results
    mcp_settings: Optional[Dict[str, Any]] = None  # MCP settings, including dynamic loaded tools
    report_style: str = ReportStyle.ACADEMIC.value  # Report style
    enable_deep_thinking: bool = False  # Whether to enable deep thinking

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig object.
        
        This method extracts configuration values from environment variables
        and RunnableConfig's configurable section, with environment variables
        taking precedence over config values.
        
        Args:
            config: Optional RunnableConfig object containing configuration data.
                   If None, only environment variables will be used.
        
        Returns:
            Configuration: A new Configuration instance with values populated
                          from environment variables and/or the provided config.
        
        Note:
            - Environment variable names are uppercase versions of field names
            - Only non-None values are included in the final configuration
            - Config values are used as fallback when env vars are not set
        """
        # Extract configurable section, defaulting to empty dict if not present
        configurable = {}
        if config is not None and "configurable" in config:
            configurable = config["configurable"]
        
        # Build values dict from environment variables and config, prioritizing env vars
        values: Dict[str, Any] = {}
        for field_info in fields(cls):
            if field_info.init:  # Only include fields that can be initialized
                env_var_name = field_info.name.upper()
                env_value = os.environ.get(env_var_name)
                config_value = configurable.get(field_info.name)
                
                # Use environment variable if available, otherwise use config value
                final_value = env_value if env_value is not None else config_value
                if final_value is not None:
                    values[field_info.name] = final_value
        
        return cls(**values)
