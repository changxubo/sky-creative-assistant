#  This module provides functionality to build a prompt enhancement workflow
#  using LangGraph, allowing users to enhance and optimize prompts for better
import asyncio
import logging
from typing import Dict, Any, Optional

# Third-party imports
from langchain.schema import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph, MessagesState

# Local imports
from src.config.llm_map import AGENT_LLM_MAP
from src.models.chat import get_llm_by_type
from src.prompts.template import get_prompt_template

logger = logging.getLogger(__name__)


class ProseState(MessagesState):
    """
    State management for prose generation workflow.

    This class extends MessagesState to handle different prose transformation
    operations like continue, improve, shorten, lengthen, fix, and custom zap commands.

    Attributes:
        content (str): The original text content to be processed
        option (str): The prose transformation option (continue, improve, shorter, longer, fix, zap)
        command (str): Custom user command for the 'zap' option
        output (str): The final processed prose content
    """

    content: str = ""
    option: str = ""
    command: str = ""
    output: str = ""


def _get_prose_model():
    """
    Helper function to get the prose writer model.

    Returns:
        The configured LLM model for prose writing operations.

    Raises:
        KeyError: If 'prose_writer' is not found in AGENT_LLM_MAP
    """
    return get_llm_by_type(AGENT_LLM_MAP["prose_writer"])


def _invoke_prose_model(system_prompt_path: str, human_message: str) -> str:
    """
    Helper function to invoke the prose model with consistent error handling.

    Args:
        system_prompt_path (str): Path to the system prompt template
        human_message (str): The human message content

    Returns:
        str: The generated prose content

    Raises:
        Exception: If model invocation fails
    """
    try:
        model = _get_prose_model()
        system_prompt = get_prompt_template(system_prompt_path)

        if not system_prompt:
            raise ValueError(f"Could not load prompt template: {system_prompt_path}")

        prose_response = model.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_message),
            ]
        )

        return prose_response.content if prose_response.content else ""
    except Exception as e:
        logger.error(f"Error invoking prose model: {str(e)}")
        raise


def get_prose_option(state: ProseState) -> str:
    """
    Router function to determine which prose operation to execute.

    Args:
        state (ProseState): Current state containing the prose option

    Returns:
        str: The prose operation option to execute

    Raises:
        ValueError: If option is not provided or is invalid
    """
    option = state.get("option", "").strip()
    if not option:
        raise ValueError("Prose option is required but not provided")

    valid_options = {"continue", "improve", "shorter", "longer", "fix", "zap"}
    if option not in valid_options:
        raise ValueError(
            f"Invalid prose option '{option}'. Must be one of: {valid_options}"
        )

    return option


def prose_zap_node(state: ProseState) -> Dict[str, str]:
    """
    Apply custom user command to the prose content.

    Args:
        state (ProseState): Current state containing content and custom command

    Returns:
        Dict[str, str]: Updated state with generated output

    Raises:
        ValueError: If content or command is missing
    """
    logger.info("Generating prose with custom zap command...")

    content = state.get("content", "").strip()
    command = state.get("command", "").strip()

    if not content:
        raise ValueError("Content is required for zap operation")
    if not command:
        raise ValueError("Custom command is required for zap operation")

    human_message = (
        f"For this text: {content}.\nYou have to respect the command: {command}"
    )
    prose_content = _invoke_prose_model("prose_zap", human_message)

    logger.info("Successfully generated zap prose content")
    return {"output": prose_content}


def prose_shorter_node(state: ProseState) -> Dict[str, str]:
    """
    Make the prose content more concise while preserving meaning.

    Args:
        state (ProseState): Current state containing content to shorten

    Returns:
        Dict[str, str]: Updated state with shortened content

    Raises:
        ValueError: If content is missing
    """
    logger.info("Generating shorter prose content...")

    content = state.get("content", "").strip()
    if not content:
        raise ValueError("Content is required for shortening operation")

    human_message = f"The existing text is: {content}"
    prose_content = _invoke_prose_model("prose_shorter", human_message)

    logger.info("Successfully generated shorter prose content")
    return {"output": prose_content}


def prose_continue_node(state: ProseState) -> Dict[str, str]:
    """
    Continue writing from the existing prose content.

    Args:
        state (ProseState): Current state containing content to continue

    Returns:
        Dict[str, str]: Updated state with continued content

    Raises:
        ValueError: If content is missing
    """
    logger.info("Generating prose continuation...")

    content = state.get("content", "").strip()
    if not content:
        raise ValueError("Content is required for continuation operation")

    prose_content = _invoke_prose_model("prose_continue", content)

    logger.info("Successfully generated prose continuation")
    return {"output": prose_content}


def prose_fix_node(state: ProseState) -> Dict[str, str]:
    """
    Fix grammar, style, and clarity issues in the prose content.

    Args:
        state (ProseState): Current state containing content to fix

    Returns:
        Dict[str, str]: Updated state with fixed content

    Raises:
        ValueError: If content is missing
    """
    logger.info("Generating prose fix content...")

    content = state.get("content", "").strip()
    if not content:
        raise ValueError("Content is required for fix operation")

    human_message = f"The existing text is: {content}"
    prose_content = _invoke_prose_model("prose_fix", human_message)

    logger.info("Successfully generated fixed prose content")
    return {"output": prose_content}


def prose_improve_node(state: ProseState) -> Dict[str, str]:
    """
    Improve the overall quality, flow, and engagement of the prose content.

    Args:
        state (ProseState): Current state containing content to improve

    Returns:
        Dict[str, str]: Updated state with improved content

    Raises:
        ValueError: If content is missing
    """
    logger.info("Generating improved prose content...")

    content = state.get("content", "").strip()
    if not content:
        raise ValueError("Content is required for improvement operation")

    human_message = f"The existing text is: {content}"
    prose_content = _invoke_prose_model("prose_improver", human_message)

    logger.info("Successfully generated improved prose content")
    return {"output": prose_content}


def prose_longer_node(state: ProseState) -> Dict[str, str]:
    """
    Expand the prose content with additional details and elaboration.

    Args:
        state (ProseState): Current state containing content to expand

    Returns:
        Dict[str, str]: Updated state with expanded content

    Raises:
        ValueError: If content is missing
    """
    logger.info("Generating longer prose content...")

    content = state.get("content", "").strip()
    if not content:
        raise ValueError("Content is required for expansion operation")

    human_message = f"The existing text is: {content}"
    prose_content = _invoke_prose_model("prose_longer", human_message)

    logger.info("Successfully generated longer prose content")
    return {"output": prose_content}


def build_graph():
    """
    Build and return the prose transformation workflow graph.

    Creates a StateGraph with all prose transformation nodes and conditional
    routing based on the selected option.

    Returns:
        Compiled StateGraph: The complete prose workflow graph ready for execution

    Raises:
        Exception: If graph construction fails
    """
    try:
        # Initialize the state graph with ProseState
        builder = StateGraph(ProseState)

        # Add all prose transformation nodes
        builder.add_node("prose_continue", prose_continue_node)
        builder.add_node("prose_improve", prose_improve_node)
        builder.add_node("prose_shorter", prose_shorter_node)
        builder.add_node("prose_longer", prose_longer_node)
        builder.add_node("prose_fix", prose_fix_node)
        builder.add_node("prose_zap", prose_zap_node)

        # Add conditional routing from START based on the option
        builder.add_conditional_edges(
            START,
            get_prose_option,
            {
                "continue": "prose_continue",
                "improve": "prose_improve",
                "shorter": "prose_shorter",
                "longer": "prose_longer",
                "fix": "prose_fix",
                "zap": "prose_zap",
            },
        )

        # All nodes lead to END
        for node_name in [
            "prose_continue",
            "prose_improve",
            "prose_shorter",
            "prose_longer",
            "prose_fix",
            "prose_zap",
        ]:
            builder.add_edge(node_name, END)

        return builder.compile()
    except Exception as e:
        logger.error(f"Error building prose workflow graph: {str(e)}")
        raise


async def _test_workflow() -> None:
    """
    Test function to validate the prose workflow functionality.

    This function demonstrates how to use the prose workflow with
    sample input and streams the results.
    """
    try:
        workflow = build_graph()

        # Test data with required fields
        test_input = {
            "content": "The weather in Beijing is sunny",
            "option": "continue",
        }

        # Stream the workflow execution
        events = workflow.astream(
            test_input,
            stream_mode="messages",
            subgraphs=True,
        )

        # Process and display events
        async for node, event in events:
            if event and len(event) > 0:
                event_data = event[0]
                print(
                    {
                        "id": getattr(event_data, "id", "unknown"),
                        "object": "chat.completion.chunk",
                        "content": getattr(event_data, "content", ""),
                    }
                )
    except Exception as e:
        logger.error(f"Error in test workflow: {str(e)}")
        raise


if __name__ == "__main__":
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run the test workflow
    asyncio.run(_test_workflow())
