# Standard library imports
import logging
from typing import Any, Dict, Optional

# Local module imports
from src.agent import build_graph

# Configure logging with structured format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def enable_debug_logging() -> None:
    """Enable debug level logging for more detailed execution information.

    This function sets the logging level to DEBUG for the 'src' package,
    allowing detailed trace information during workflow execution.
    """
    logging.getLogger("src").setLevel(logging.DEBUG)


# Initialize logger for this module
logger = logging.getLogger(__name__)

# Create the workflow graph instance
research_graph = build_graph()


async def run_agent_workflow_async(
    user_input: str,
    debug: bool = False,
    max_plan_iterations: int = 1,
    max_step_num: int = 3,
    enable_background_investigation: bool = True,
) -> Optional[Dict[str, Any]]:
    """Run the agent workflow asynchronously with the given user input.

    This function executes a multi-agent workflow that can perform research,
    planning, and execution based on user queries. It supports configurable
    parameters for controlling the workflow behavior.

    Args:
        user_input (str): The user's query or request. Must be non-empty.
        debug (bool, optional): If True, enables debug level logging for detailed
            execution traces. Defaults to False.
        max_plan_iterations (int, optional): Maximum number of plan iterations
            allowed during workflow execution. Defaults to 1.
        max_step_num (int, optional): Maximum number of steps allowed in a single
            plan execution. Defaults to 3.
        enable_background_investigation (bool, optional): If True, performs web
            search before planning to enhance context and information gathering.
            Defaults to True.

    Returns:
        Optional[Dict[str, Any]]: The final state dictionary after the workflow
            completes, or None if an error occurs.

    Raises:
        ValueError: If user_input is empty, None, or contains only whitespace.
        RuntimeError: If workflow execution fails due to configuration issues.
    """
    # Input validation with comprehensive checks
    if not user_input or not user_input.strip():
        error_message = "User input cannot be empty or contain only whitespace"
        logger.error(error_message)
        raise ValueError(error_message)

    # Enable debug logging if requested
    if debug:
        enable_debug_logging()
        logger.debug("Debug logging enabled for workflow execution")

    logger.info(f"Starting async workflow with user input: {user_input[:100]}...")

    # Initialize workflow state with user message
    initial_workflow_state = {
        "messages": [{"role": "user", "content": user_input}],
        "auto_accepted_plan": True,
        "enable_background_investigation": enable_background_investigation,
    }

    # Configure workflow parameters and MCP settings
    workflow_config = {
        "configurable": {
            "thread_id": "default",
            "max_plan_iterations": max_plan_iterations,
            "max_step_num": max_step_num,
            "mcp_settings": {
                "servers": {
                    "mcp-github-trending": {
                        "transport": "stdio",
                        "command": "uvx",
                        "args": ["mcp-github-trending"],
                        "enabled_tools": ["get_github_trending_repositories"],
                        "add_to_agents": ["researcher"],
                    },
                    "mcp-rednote-search": {
                        "url": "http://127.0.0.1:19999/mcp",
                        "transport": "sse",
                        "enabled_tools": ["search_notes", "get_note_details"],
                        "add_to_agents": ["researcher"],
                    },
                }
            },
        },
        "recursion_limit": 100,
    }

    # Track message count to avoid duplicate processing
    last_processed_message_count = 0
    final_state = None

    try:
        # Stream workflow execution results
        async for workflow_state in research_graph.astream(
            input=initial_workflow_state, config=workflow_config, stream_mode="values"
        ):
            try:
                # Process workflow state updates
                if isinstance(workflow_state, dict) and "messages" in workflow_state:
                    current_message_count = len(workflow_state["messages"])

                    # Skip if no new messages to process
                    if current_message_count <= last_processed_message_count:
                        continue

                    last_processed_message_count = current_message_count
                    latest_message = workflow_state["messages"][-1]

                    # Handle different message formats
                    if isinstance(latest_message, tuple):
                        print(latest_message)
                    elif hasattr(latest_message, "pretty_print"):
                        latest_message.pretty_print()
                    else:
                        print(f"Message: {latest_message}")
                else:
                    # Handle non-standard output formats
                    print(f"Workflow Output: {workflow_state}")

                # Store the final state for return
                final_state = workflow_state

            except Exception as stream_error:
                error_message = f"Error processing stream output: {stream_error}"
                logger.error(error_message)
                print(f"Stream processing error: {str(stream_error)}")
                continue  # Continue processing other stream items

    except Exception as workflow_error:
        error_message = f"Workflow execution failed: {workflow_error}"
        logger.error(error_message)
        raise RuntimeError(error_message) from workflow_error

    logger.info("Async workflow completed successfully")
    return final_state


if __name__ == "__main__":
    """Main execution block for generating workflow graph visualization."""
    try:
        # Generate and display workflow graph in Mermaid format
        mermaid_graph = research_graph.get_graph(xray=True).draw_mermaid()
        print("Workflow Graph Structure:")
        print(mermaid_graph)
    except Exception as graph_error:
        logger.error(f"Failed to generate workflow graph: {graph_error}")
        print(f"Error generating graph visualization: {str(graph_error)}")
