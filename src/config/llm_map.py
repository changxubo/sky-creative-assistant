"""Agent-LLM mapping configuration module.

This module defines the mapping between different agent types and their corresponding
LLM capabilities, ensuring appropriate model selection for each agent's specific tasks.
"""

from typing import Dict, Literal, Optional, Set


# Type alias for available LLM capability types
LLMCapabilityType = Literal["basic", "reasoning", "vision"]


def get_available_llm_types() -> Set[LLMCapabilityType]:
    """Get all available LLM capability types.

    Returns:
        Set[LLMCapabilityType]: Set of all available LLM capability types.
    """
    return {"basic", "reasoning", "vision"}


def get_agent_llm_type(agent_name: str) -> Optional[LLMCapabilityType]:
    """Get the LLM capability type for a specific agent.

    Args:
        agent_name (str): Name of the agent to look up.

    Returns:
        Optional[LLMCapabilityType]: The LLM capability type for the agent,
            or None if agent is not found.
    """
    return AGENT_LLM_CAPABILITY_MAP.get(agent_name)


def is_valid_agent(agent_name: str) -> bool:
    """Check if an agent name is valid and exists in the mapping.

    Args:
        agent_name (str): Name of the agent to validate.

    Returns:
        bool: True if agent exists in the mapping, False otherwise.
    """
    return agent_name in AGENT_LLM_CAPABILITY_MAP


# Mapping of agent types to their required LLM capabilities
# Each agent is assigned a capability type based on its functional requirements:
# - "basic": Standard language processing tasks
# - "reasoning": Complex logical reasoning and analysis
# - "vision": Visual content processing and analysis
AGENT_LLM_CAPABILITY_MAP: Dict[str, LLMCapabilityType] = {
    "coordinator": "basic",  # Orchestrates workflow between agents
    "planner": "reasoning",  # Requires strategic planning and reasoning
    "researcher": "basic",  # Information gathering and synthesis
    "coder": "reasoning",  # Code analysis and generation requires logic
    "reporter": "basic",  # Document generation and formatting
    "podcast_script_writer": "basic",  # Creative writing and script generation
    "ppt_composer": "vision",  # Presentation creation with visual elements
    "prose_writer": "basic",  # Creative and technical writing
    "prompt_enhancer": "reasoning",  # Optimization requires analytical thinking
}


# Backward compatibility aliases - DEPRECATED: Use new names above
# TODO: Update all imports to use new names and remove these aliases
LLMType = LLMCapabilityType  # Deprecated: Use LLMCapabilityType instead
AGENT_LLM_MAP = (
    AGENT_LLM_CAPABILITY_MAP  # Deprecated: Use AGENT_LLM_CAPABILITY_MAP instead
)
