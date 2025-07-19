from langgraph.graph import MessagesState
from src.prompts.planner_model import Plan
from src.rag import Resource

class State(MessagesState):
    """State for the agent system, extends MessagesState with next field."""

    # Runtime Variables
    locale: str = "zh-CN"
    step: int = -1
    research_topic: str = ""
    observations: list[str] = []
    resources: list[Resource] = []
    plan_iterations: int = 0
    current_plan: Plan | str = None
    final_report: str = ""
    auto_accepted_plan: bool = False
    enable_background_investigation: bool = True
    background_investigation_results: str = None
    investigations:str = ""
    enable_deep_thinking: bool = True
    reasoning_content: str = ""
