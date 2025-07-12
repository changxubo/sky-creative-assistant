from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class StepType(str, Enum):
    """
    Enumeration defining the types of steps available in a planning workflow.
    
    This enum categorizes steps into two main types to help organize and
    process different kinds of operations within a plan execution context.
    
    Attributes:
        RESEARCH: Steps that involve gathering information, data collection,
                 or external searches. These steps typically require network
                 operations or database queries.
        PROCESSING: Steps that involve data manipulation, analysis, or
                   transformation of existing information. These steps work
                   with already collected data.
    """

    RESEARCH = "research"
    PROCESSING = "processing"


class Step(BaseModel):
    """
    Represents a single executable step within a planning workflow.
    
    This class encapsulates all the information needed to execute a specific
    step in a plan, including its requirements, description, and execution
    results. Each step is self-contained and can be executed independently.
    
    Attributes:
        need_search (bool): Flag indicating whether this step requires external
                           search or data collection operations.
        title (str): Concise, descriptive title of the step for identification.
        description (str): Detailed description explaining what the step should
                          accomplish and what data it should collect.
        step_type (StepType): Categorization of the step as either research or
                             processing type.
        execution_res (Optional[str]): Results or output from step execution,
                                      populated after the step completes.
    """

    need_search: bool = Field(
        ..., 
        description="Must be explicitly set - indicates if step requires external search operations"
    )
    title: str = Field(
        ..., 
        min_length=1, 
        max_length=200,
        description="Concise, descriptive title of the step"
    )
    description: str = Field(
        ..., 
        min_length=10,
        description="Detailed description specifying exactly what data to collect or process"
    )
    step_type: StepType = Field(
        default=StepType.RESEARCH , 
        description="Type classification indicating the nature of the step operation"
    )
    execution_res: Optional[str] = Field(
        default=None, 
        description="Results or output data from step execution (populated after completion)"
    )

    @validator('title')
    def validate_title(cls, v):
        """
        Validates that the title is meaningful and properly formatted.
        
        Args:
            v (str): The title value to validate
            
        Returns:
            str: The validated and potentially cleaned title
            
        Raises:
            ValueError: If title is empty or contains only whitespace
        """
        if not v or not v.strip():
            raise ValueError("Title cannot be empty or whitespace only")
        return v.strip()


class Plan(BaseModel):
    """
    Represents a comprehensive execution plan consisting of multiple coordinated steps.
    
    This class serves as the main container for planning workflows, organizing
    multiple steps into a coherent execution sequence. It includes metadata
    about the plan's context, completeness, and locale-specific requirements.
    
    The plan supports both research and processing steps, allowing for complex
    workflows that combine data gathering and analysis operations.
    
    Attributes:
        locale (str): Language/region locale code (e.g., 'en-US', 'zh-CN') 
                     determining the language for plan execution and results.
        has_enough_context (bool): Flag indicating whether sufficient context
                                  is available to execute the plan effectively.
        thought (str): Reasoning and thought process behind the plan creation,
                      explaining the strategic approach and considerations.
        title (str): Descriptive title summarizing the plan's main objective.
        steps (List[Step]): Ordered list of steps to be executed sequentially
                           or in parallel, depending on dependencies.
    """

    locale: str = Field(
        ...,
        pattern=r'^[a-z]{2}(-[A-Z]{2})?$',
        description="Language/region code (e.g., 'en-US', 'zh-CN') based on user's language preference"
    )
    has_enough_context: bool = Field(
        ...,
        description="Indicates if sufficient context is available for effective plan execution"
    )
    thought: str = Field(
        ...,
        min_length=20,
        description="Strategic reasoning and thought process behind the plan creation"
    )
    title: str = Field(
        ...,
        min_length=5,
        max_length=200,
        description="Descriptive title summarizing the plan's main objective"
    )
    steps: List[Step] = Field(
        #default_factory=list,
        default=[],
        max_items=10,
        min_items=0,
        description="Ordered list of research and processing steps to gather context and achieve objectives"
    )

    @validator('steps')
    def validate_steps_not_empty(cls, v):
        """
        Validates that the plan contains at least one step.
        
        Args:
            v (List[Step]): The list of steps to validate
            
        Returns:
            List[Step]: The validated list of steps
            
        Raises:
            ValueError: If the steps list is empty
        """
        #if not v:
        #    raise ValueError("Plan must contain at least one step")
        return v

    @validator('locale')
    def validate_locale_format(cls, v):
        """
        Validates that the locale follows standard format conventions.
        
        Args:
            v (str): The locale string to validate
            
        Returns:
            str: The validated locale string
            
        Raises:
            ValueError: If locale format is invalid
        """
        if not v or len(v) < 2:
            raise ValueError("Locale must be at least 2 characters (e.g., 'en' or 'en-US')")
        return v.lower() if '-' not in v else f"{v.split('-')[0].lower()}-{v.split('-')[1].upper()}"

    class Config:
        """Configuration for the Plan model with enhanced examples."""
        
        json_schema_extra = {
            "examples": [
                {
                    "locale": "en-US",
                    "has_enough_context": False,
                    "thought": (
                        "To understand the current market trends in AI, we need to gather "
                        "comprehensive information about market size, key players, recent "
                        "developments, and investment patterns. This multi-step approach "
                        "will ensure we have sufficient data for analysis."
                    ),
                    "title": "AI Market Research Plan",
                    "steps": [
                        {
                            "need_search": True,
                            "title": "Current AI Market Analysis",
                            "description": (
                                "Collect comprehensive data on global AI market size, "
                                "growth rates, major players, recent mergers/acquisitions, "
                                "and investment trends in the AI sector for 2024-2025."
                            ),
                            "step_type": "research",
                        },
                        {
                            "need_search": True,
                            "title": "AI Technology Trends Research",
                            "description": (
                                "Gather information on emerging AI technologies, "
                                "breakthrough developments, and adoption rates across "
                                "different industries and geographical regions."
                            ),
                            "step_type": "research",
                        },
                        {
                            "need_search": False,
                            "title": "Market Data Analysis",
                            "description": (
                                "Process and analyze the collected market data to identify "
                                "key trends, patterns, and insights. Generate summary "
                                "statistics and comparative analysis."
                            ),
                            "step_type": "processing",
                        }
                    ],
                }
            ]
        }
