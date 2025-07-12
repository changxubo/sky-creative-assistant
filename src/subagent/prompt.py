"""
Prompt Enhancer Graph Builder Module

This module provides functionality to build and execute a LangGraph workflow
for enhancing user prompts using AI analysis. The workflow takes raw user
prompts and improves them for better AI model performance.

Classes:
    PromptEnhancementState: TypedDict defining the workflow state schema
    
Functions:
    build_prompt_enhancement_graph: Main function to create the enhancement workflow
    enhance_prompt_node: Core node that performs prompt enhancement
    build_graph: Legacy compatibility function
"""

import logging
from typing import Dict, List, Optional, TypedDict

from langchain.schema import HumanMessage
from langgraph.graph import StateGraph

from src.config.llm_map import AGENT_LLM_MAP
from src.config.report_style import ReportStyle
from src.models.chat import get_llm_by_type
from src.prompts.template import apply_prompt_template

logger = logging.getLogger(__name__)

# Constants for better maintainability
ENHANCEMENT_TEMPLATE_PATH = "prompt_enhancer/prompt_enhancer"
ENHANCER_NODE_NAME = "enhancer"

# Common response prefixes that should be removed from enhanced prompts
RESPONSE_PREFIXES_TO_CLEAN: List[str] = [
    "Enhanced Prompt:",
    "Enhanced prompt:",
    "Here's the enhanced prompt:",
    "Here is the enhanced prompt:",
    "**Enhanced Prompt**:",
    "**Enhanced prompt**:",
]


class PromptEnhancementState(TypedDict):
    """
    State schema for the prompt enhancement workflow.
    
    This TypedDict defines the structure of data passed between nodes
    in the prompt enhancement graph.
    
    Attributes:
        prompt: Original user prompt that needs enhancement
        context: Additional context to inform the enhancement process
        report_style: Preferred style for the enhanced prompt output
        output: Final enhanced prompt result after processing
    """
    
    prompt: str
    context: Optional[str]
    report_style: Optional[ReportStyle]
    output: Optional[str]


def _clean_enhanced_prompt_response(response_content: str) -> str:
    """
    Clean the AI model response by removing common formatting prefixes.
    
    This function removes standardized prefixes that AI models commonly add
    to their responses, ensuring clean prompt output.
    
    Args:
        response_content: Raw response content from the AI model
        
    Returns:
        str: Cleaned enhanced prompt without formatting prefixes
        
    Raises:
        None: Function handles all edge cases gracefully
    """
    if not response_content:  # Handle empty or None responses
        return ""
        
    enhanced_prompt = response_content.strip()
    
    # Remove common prefixes that might be added by the model
    for prefix in RESPONSE_PREFIXES_TO_CLEAN:
        if enhanced_prompt.startswith(prefix):
            enhanced_prompt = enhanced_prompt[len(prefix):].strip()
            break
            
    return enhanced_prompt


def _build_context_message(prompt: str, context: Optional[str]) -> str:
    """
    Build the message content for prompt enhancement including context.
    
    Constructs a formatted message that combines the original prompt with
    optional context information for better AI model understanding.
    
    Args:
        prompt: Original user prompt to be enhanced
        context: Optional additional context to inform enhancement
        
    Returns:
        str: Formatted message content ready for AI model processing
        
    Raises:
        None: Function handles all input combinations gracefully
    """
    if not prompt:  # Validate prompt is not empty
        raise ValueError("Prompt cannot be empty or None")
    
    # Build context section if provided
    context_section = ""
    if context and context.strip():  # Ensure context is not just whitespace
        context_section = f"\n\nAdditional context: {context.strip()}"
    
    return f"Please enhance this prompt:{context_section}\n\nOriginal prompt: {prompt}"


def enhance_prompt_node(state: PromptEnhancementState) -> Dict[str, str]:
    """
    Core node that enhances user prompts using AI analysis.
    
    This function takes a user's original prompt and uses an AI model to
    enhance it for better performance and clarity. It handles context
    integration, response cleaning, and robust error recovery.
    
    Args:
        state: Current state containing prompt and optional context/style information
        
    Returns:
        Dict[str, str]: Dictionary with the enhanced prompt in the 'output' key
        
    Raises:
        Exception: Logs errors but doesn't propagate to ensure workflow stability
    """
    logger.info("Starting prompt enhancement process...")
    
    # Validate input state has required prompt
    if not state.get("prompt"):
        logger.error("No prompt provided in state")
        return {"output": ""}
    
    # Get the configured AI model for prompt enhancement
    try:
        model = get_llm_by_type(AGENT_LLM_MAP["prompt_enhancer"])
    except KeyError as e:
        logger.error(f"Prompt enhancer model not configured: {e}")
        return {"output": state["prompt"]}  # Fallback to original
    
    try:
        # Build the message content with context validation
        message_content = _build_context_message(
            state["prompt"], 
            state.get("context")
        )
        
        # Create the human message for the AI model
        original_prompt_message = HumanMessage(content=message_content)

        # Apply the prompt enhancement template with error handling
        messages = apply_prompt_template(
            ENHANCEMENT_TEMPLATE_PATH,
            {
                "messages": [original_prompt_message],
                "report_style": state.get("report_style"),
            },
        )

        # Invoke the AI model to get the enhanced prompt
        response = model.invoke(messages)

        # Validate response exists and has content
        if not response or not hasattr(response, 'content') or not response.content:
            logger.warning("Empty response from AI model")
            return {"output": state["prompt"]}

        # Clean up the response content
        enhanced_prompt = _clean_enhanced_prompt_response(response.content)

        # Final validation of enhanced prompt
        if not enhanced_prompt:
            logger.warning("Enhanced prompt is empty after cleaning")
            return {"output": state["prompt"]}

        logger.info("Prompt enhancement completed successfully")
        logger.debug(f"Original prompt: {state['prompt']}")
        logger.debug(f"Enhanced prompt: {enhanced_prompt}")
        
        return {"output": enhanced_prompt}
        
    except ValueError as e:
        logger.error(f"Input validation error during prompt enhancement: {str(e)}")
        return {"output": state["prompt"]}
    except Exception as e:
        logger.error(f"Unexpected error during prompt enhancement: {str(e)}")
        logger.warning("Falling back to original prompt due to enhancement failure")
        # Return the original prompt as fallback
        return {"output": state["prompt"]}

def build_prompt_enhancement_graph() -> StateGraph:
    """
    Build and compile the prompt enhancement workflow graph.
    
    Creates a LangGraph StateGraph with a single node that handles
    prompt enhancement. The graph takes user prompts as input and
    outputs enhanced versions optimized for AI model performance.
    
    Returns:
        StateGraph: Compiled LangGraph that can be invoked with PromptEnhancementState
        
    Raises:
        Exception: May raise compilation errors if graph structure is invalid
    """
    logger.info("Building prompt enhancement workflow graph...")
    
    # Initialize the state graph with our state schema
    builder = StateGraph(PromptEnhancementState)

    # Add the core enhancement node to the graph
    builder.add_node(ENHANCER_NODE_NAME, enhance_prompt_node)

    # Set the entry point - where the workflow begins
    builder.set_entry_point(ENHANCER_NODE_NAME)

    # Set the finish point - where the workflow ends
    builder.set_finish_point(ENHANCER_NODE_NAME)

    # Compile the graph for execution
    compiled_graph = builder.compile()
    
    logger.info("Prompt enhancement graph built successfully")
    return compiled_graph


def build_graph() -> StateGraph:
    """
    Legacy function name for backward compatibility.
    
    Maintains compatibility with existing code that uses the original
    function name while delegating to the more descriptive function.
    
    Returns:
        StateGraph: Compiled prompt enhancement graph
        
    Deprecated:
        Use build_prompt_enhancement_graph() instead for better clarity
    """
    return build_prompt_enhancement_graph()
