import dataclasses
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from jinja2 import Environment, FileSystemLoader, TemplateNotFound, select_autoescape
from langgraph.prebuilt.chat_agent_executor import AgentState

from src.config.configuration import Configuration

# Initialize Jinja2 environment with optimized settings
jinja_env = Environment(
    loader=FileSystemLoader(os.path.dirname(__file__)+"/templates"),
    autoescape=select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True,
)


def get_prompt_template(prompt_name: str) -> str:
    """
    Load and return a prompt template using Jinja2.

    This function loads a Markdown template file and renders it without
    any variable substitution. It's used to get the raw template content.

    Args:
        prompt_name (str): Name of the prompt template file (without .md extension).
                          Must be a non-empty string.

    Returns:
        str: The rendered template string with proper variable substitution syntax.

    Raises:
        ValueError: If prompt_name is empty or None.
        TemplateNotFound: If the specified template file doesn't exist.
        ValueError: If there's an error during template loading or rendering.
    """
    if not prompt_name or not isinstance(prompt_name, str):
        raise ValueError("prompt_name must be a non-empty string")
    
    try:
        template = jinja_env.get_template(f"{prompt_name}.md")
        return template.render()
    except TemplateNotFound as e:
        raise TemplateNotFound(f"Template '{prompt_name}.md' not found: {e}")
    except Exception as e:
        raise ValueError(f"Error loading template '{prompt_name}': {e}")


def apply_prompt_template(
    prompt_name: str, 
    state: AgentState, 
    configurable: Optional[Configuration] = None
) -> List[Dict[str, str]]:
    """
    Apply template variables to a prompt template and return formatted messages.

    This function loads a Jinja2 template, renders it with provided variables,
    and returns a list of messages with the system prompt as the first message.

    Args:
        prompt_name (str): Name of the prompt template to use (without .md extension).
                          Must be a non-empty string.
        state (AgentState): Current agent state containing variables to substitute.
                           Must contain a 'messages' key with a list of messages.
        configurable (Optional[Configuration]): Optional configuration object 
                                               containing additional variables.

    Returns:
        List[Dict[str, str]]: List of messages with the system prompt as the first message.
                             Each message has 'role' and 'content' keys.

    Raises:
        ValueError: If prompt_name is empty/None or state is invalid.
        TemplateNotFound: If the specified template file doesn't exist.
        ValueError: If there's an error during template rendering.
    """
    # Input validation
    if not prompt_name or not isinstance(prompt_name, str):
        raise ValueError("prompt_name must be a non-empty string")
    
    if not isinstance(state, dict):
        raise ValueError("state must be a dictionary")
    
    # Ensure state has messages key with proper fallback
    if "messages" not in state:
        state["messages"] = []
    elif not isinstance(state["messages"], list):
        raise ValueError("state['messages'] must be a list")

    # Convert state to dict for template rendering with current timestamp
    state_vars: Dict[str, Any] = {
        "CURRENT_TIME": datetime.now().strftime("%a %b %d %Y %H:%M:%S %z"),
        **state,
    }

    # Add configurable variables if provided
    if configurable:
        try:
            configurable_dict = dataclasses.asdict(configurable)
            state_vars.update(configurable_dict)
        except Exception as e:
            raise ValueError(f"Error converting configurable to dict: {e}")

    try:
        # Load and render template with state variables
        template = jinja_env.get_template(f"{prompt_name}.md")
        system_prompt = template.render(**state_vars)
        #print(f"System prompt generated: {system_prompt[:100]}...")  # Debug output
        # Return system message followed by existing messages
        return [{"role": "system", "content": system_prompt}] + state["messages"]
    except TemplateNotFound as e:
        raise TemplateNotFound(f"Template '{prompt_name}.md' not found: {e}")
    except Exception as e:
        raise ValueError(f"Error applying template '{prompt_name}': {e}")
