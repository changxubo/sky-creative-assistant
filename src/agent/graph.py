# Third-party imports
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END

# Local imports
from src.prompts.planner_model import StepType

from .nodes import (
    background_investigation_node,
    coder_node,
    coordinator_node,
    human_feedback_node,
    planner_node,
    reporter_node,
    research_team_node,
    researcher_node,
)
from .state import State


def continue_to_running_research_team(state: State) -> str:
    """
    Determine the next node to route to based on the current plan's execution state.

    This function analyzes the current plan and routes the workflow to the appropriate
    next node based on the execution status of plan steps and their types.

    Args:
        state (State): The current state containing the plan and execution information.
                      Expected to have a 'current_plan' key with a Plan object.

    Returns:
        str: The name of the next node to route to. Can be:
             - "planner": When no plan exists, all steps are complete, or fallback
             - "researcher": When the current step is a RESEARCH type
             - "coder": When the current step is a PROCESSING type

    Raises:
        AttributeError: If state doesn't contain expected structure (handled gracefully)
    """
    current_plan = state.get("current_plan")

    # Handle case where no plan exists or plan has no steps
    if not current_plan or not current_plan.steps:
        return "planner"

    # Check if all steps are completed - if so, return to planner for next phase
    if all(step.execution_res for step in current_plan.steps):
        return "planner"

    # Find the first incomplete step
    incomplete_step = None
    for step in current_plan.steps:
        if not step.execution_res:
            incomplete_step = step
            break

    # Route based on the type of the incomplete step
    if incomplete_step and incomplete_step.step_type:
        if incomplete_step.step_type == StepType.RESEARCH:
            return "researcher"
        elif incomplete_step.step_type == StepType.PROCESSING:
            return "coder"

    # Default fallback to planner if step type is unknown or missing
    return "planner"


def _build_base_graph() -> StateGraph:
    """
    Build and return the base state graph with all nodes and edges.

    This function creates the core workflow graph structure by:
    1. Creating nodes for each agent/component in the system
    2. Setting up edges to define the flow between nodes
    3. Configuring conditional routing based on execution state

    The graph represents a research workflow where:
    - Coordinator initiates the process
    - Background investigator gathers initial context
    - Planner creates execution plans
    - Research team coordinates between researcher and coder
    - Reporter generates final output

    Returns:
        StateGraph: A configured StateGraph instance with all nodes and edges,
                   ready for compilation into an executable workflow.

    Note:
        This is a private function used internally by the public build functions.
        The graph is not compiled here - compilation happens in the public functions.
    """
    # Initialize the state graph builder with the State schema
    builder = StateGraph(State)

    # Set up the entry point
    builder.add_edge(START, "coordinator")

    # Add all workflow nodes
    builder.add_node("coordinator", coordinator_node)
    builder.add_node("background_investigator", background_investigation_node)
    builder.add_node("planner", planner_node)
    builder.add_node("reporter", reporter_node)
    builder.add_node("research_team", research_team_node)
    builder.add_node("researcher", researcher_node)
    builder.add_node("coder", coder_node)
    builder.add_node("human_feedback", human_feedback_node)

    # Set up direct edges (unconditional flow)
    builder.add_edge("background_investigator", "planner")
    builder.add_edge("reporter", END)

    # Set up conditional edges for dynamic routing
    # The research_team node uses conditional logic to determine next step
    builder.add_conditional_edges(
        "research_team",
        continue_to_running_research_team,
        ["planner", "researcher", "coder"],
    )

    return builder


def build_graph_with_memory():
    """
    Build and return the agent workflow graph with persistent memory capabilities.

    This function creates a compiled workflow graph that includes memory persistence
    for maintaining conversation history and state across multiple executions.
    The memory system allows the workflow to:
    - Remember previous interactions and decisions
    - Maintain context across session boundaries
    - Support complex multi-turn conversations

    Returns:
        CompiledGraph: A compiled StateGraph with MemorySaver checkpointer
                      that can be executed with persistent state management.

    Note:
        Currently uses in-memory storage. Future versions should support
        SQLite and PostgreSQL for production deployments.

    See Also:
        build_graph(): For stateless execution without memory persistence
    """
    # Initialize persistent memory for conversation history
    # TODO: Implement compatibility with SQLite and PostgreSQL backends
    # for production-grade persistence and scalability
    memory_saver = MemorySaver()

    # Build the base graph structure
    base_graph_builder = _build_base_graph()

    # Compile with memory checkpointer for state persistence
    return base_graph_builder.compile(checkpointer=memory_saver)


def build_graph():
    """
    Build and return the agent workflow graph without memory persistence.

    This function creates a compiled workflow graph for stateless execution.
    Each run starts with a fresh state and doesn't persist information
    between executions. This is suitable for:
    - Single-shot research tasks
    - Testing and development
    - Scenarios where memory persistence is not required

    Returns:
        CompiledGraph: A compiled StateGraph without checkpointer
                      that can be executed with stateless behavior.

    Note:
        For applications requiring conversation history or state persistence
        across multiple executions, use build_graph_with_memory() instead.

    See Also:
        build_graph_with_memory(): For persistent state management
    """
    # Build the base graph structure
    base_graph_builder = _build_base_graph()

    # Compile without checkpointer for stateless execution
    return base_graph_builder.compile()


# Create a default graph instance for immediate use
# This provides a ready-to-use workflow for applications that don't need
# to customize the graph building process
graph = build_graph()
