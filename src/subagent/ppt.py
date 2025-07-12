"""
PowerPoint presentation generation workflow using LangGraph and Marp CLI.

This module provides a comprehensive workflow for generating PowerPoint presentations
from text input using LLM-powered content composition and Marp CLI for file generation.
The workflow consists of two main stages:
1. Content composition using a specialized LLM agent
2. File generation using Marp CLI tool

Example:
    workflow = build_presentation_workflow()
    result = workflow.invoke({"input": "Your content here"})
    print(f"Generated presentation: {result['generated_file_path']}")
"""

# Standard library imports
import logging
import os
import subprocess
import uuid
from typing import Dict, Any

# Third-party imports
from langchain.schema import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph, MessagesState

# Local imports
from src.config.llm_map import AGENT_LLM_MAP
from src.models.chat import get_llm_by_type
from src.prompts.template import get_prompt_template


logger = logging.getLogger(__name__)


class PowerPointWorkflowState(MessagesState):
    """
    State management class for the PowerPoint generation workflow.

    This class extends MessagesState to maintain comprehensive state information
    throughout the presentation generation process. It tracks input content,
    intermediate processing files, generated content, and final output paths.

    The state progression follows this pattern:
    1. Input content is provided
    2. LLM generates presentation content in markdown format
    3. Content is saved to temporary file
    4. Marp CLI converts to PowerPoint format
    5. Final file path is stored

    Attributes:
        input (str): The source content to be converted into a presentation.
                    Should contain the raw text or markdown that will be
                    transformed into presentation slides.
        generated_file_path (str): Absolute path to the final generated PowerPoint file.
                                  Set after successful file generation.
        ppt_content (str): The LLM-generated presentation content in markdown format.
                          Contains Marp-compatible markdown with slide separators.
        ppt_file_path (str): Absolute path to the temporary markdown file used
                           during generation. Cleaned up after conversion.
    """

    # Input
    input: str = ""

    # Output
    generated_file_path: str = ""

    # Assets
    ppt_content: str = ""
    ppt_file_path: str = ""


def generate_presentation_file(state: PowerPointWorkflowState) -> Dict[str, Any]:
    """
    Generate a PowerPoint file from markdown content using Marp CLI.

    This function converts the markdown content stored in a temporary file into
    a PowerPoint presentation using the Marp CLI tool. It handles file generation,
    cleanup of temporary files, and comprehensive error handling for various
    failure scenarios.

    Args:
        state (PowerPointWorkflowState): Current workflow state containing:
            - ppt_file_path: Path to the temporary markdown file to convert
            - Other state attributes are preserved and passed through

    Returns:
        Dict[str, Any]: Dictionary containing the updated state with:
            - generated_file_path (str): Absolute path to the generated PowerPoint file

    Raises:
        subprocess.CalledProcessError: If Marp CLI execution fails
        OSError: If file operations (creation, deletion) fail
        ValueError: If required state attributes are missing or invalid

    Note:
        Requires Marp CLI to be installed and available in the system PATH.
        Installation: npm install -g @marp-team/marp-cli
        Documentation: https://github.com/marp-team/marp-cli
    """
    logger.info("Starting PowerPoint file generation using Marp CLI...")

    # Validate required state attributes
    if not state.get("ppt_file_path"):
        raise ValueError("ppt_file_path is required but not found in state")

    if not os.path.exists(state["ppt_file_path"]):
        raise FileNotFoundError(f"Markdown file not found: {state['ppt_file_path']}")

    # Generate unique output file path with proper extension
    generated_file_path = os.path.join(
        os.getcwd(), f"generated_presentation_{uuid.uuid4().hex}.pptx"
    )

    temp_file_path = state["ppt_file_path"]

    try:
        logger.info(f"Converting markdown file: {temp_file_path}")
        logger.info(f"Output PowerPoint file: {generated_file_path}")

        # Convert markdown to PowerPoint using Marp CLI
        result = subprocess.run(
            ["marp", temp_file_path, "-o", generated_file_path, "--theme", "default"],
            check=True,
            capture_output=True,
            text=True,
        )

        logger.info(f"Marp CLI execution completed successfully")

        # Verify the output file was created
        if not os.path.exists(generated_file_path):
            raise FileNotFoundError(
                f"Expected output file was not created: {generated_file_path}"
            )

        file_size = os.path.getsize(generated_file_path)
        logger.info(f"Generated PowerPoint file size: {file_size} bytes")

        return {"generated_file_path": generated_file_path}

    except subprocess.CalledProcessError as e:
        logger.error(f"Marp CLI execution failed with return code {e.returncode}")
        logger.error(f"Command: {' '.join(e.cmd)}")
        logger.error(f"Error output: {e.stderr}")
        raise RuntimeError(f"PowerPoint generation failed: {e.stderr}") from e

    except (OSError, IOError) as e:
        logger.error(f"File operation failed during PowerPoint generation: {e}")
        raise

    finally:
        # Clean up temporary markdown file (even if generation failed)
        try:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                logger.info(f"Cleaned up temporary file: {temp_file_path}")
        except OSError as cleanup_error:
            logger.warning(
                f"Failed to clean up temporary file {temp_file_path}: {cleanup_error}"
            )


def compose_presentation_content(state: PowerPointWorkflowState) -> Dict[str, Any]:
    """
    Generate presentation content using a specialized LLM agent.

    This function leverages a Large Language Model to transform raw input content
    into structured presentation content formatted as Marp-compatible markdown.
    The generated content includes proper slide separators, formatting, and
    presentation structure suitable for professional presentations.

    Args:
        state (PowerPointWorkflowState): Current workflow state containing:
            - input (str): The source content to be transformed into presentation format
            - Other state attributes are preserved and passed through

    Returns:
        Dict[str, Any]: Dictionary containing the updated state with:
            - ppt_content (str): Generated presentation content in markdown format
            - ppt_file_path (str): Absolute path to the temporary markdown file

    Raises:
        ValueError: If input content is missing or empty
        RuntimeError: If LLM invocation fails
        OSError: If temporary file creation fails

    Note:
        The function uses the configured LLM model specified in AGENT_LLM_MAP
        and applies the presentation composition prompt template.
    """
    logger.info("Generating presentation content using LLM agent...")

    # Validate input content
    input_content = state.get("input", "").strip()
    if not input_content:
        raise ValueError("Input content is required but was empty or missing")

    logger.info(f"Processing input content (length: {len(input_content)} characters)")

    try:
        # Get the configured LLM model for presentation composition
        model = get_llm_by_type(AGENT_LLM_MAP["ppt_composer"])
        logger.info(f"Using LLM model: {AGENT_LLM_MAP['ppt_composer']}")

        # Prepare messages for LLM invocation
        system_prompt = get_prompt_template("ppt_composer")
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=input_content),
        ]

        # Generate presentation content using the LLM
        logger.info("Invoking LLM for content generation...")
        ppt_response = model.invoke(messages)

        if not ppt_response or not hasattr(ppt_response, "content"):
            raise RuntimeError("LLM returned invalid response")

        ppt_content = ppt_response.content.strip()

        if not ppt_content:
            raise RuntimeError("LLM generated empty content")

        logger.info(f"Generated content length: {len(ppt_content)} characters")
        logger.info("Presentation content generated successfully")

        # Create temporary markdown file with unique name
        temp_file_path = os.path.join(os.getcwd(), f"ppt_content_{uuid.uuid4().hex}.md")

        # Write content to temporary file with proper encoding
        try:
            with open(temp_file_path, "w", encoding="utf-8") as f:
                f.write(ppt_content)

            # Verify file was written correctly
            if not os.path.exists(temp_file_path):
                raise OSError(f"Failed to create temporary file: {temp_file_path}")

            file_size = os.path.getsize(temp_file_path)
            logger.info(
                f"Content saved to temporary file: {temp_file_path} ({file_size} bytes)"
            )

        except (OSError, IOError) as e:
            logger.error(f"Failed to write temporary file: {e}")
            raise

        return {"ppt_content": ppt_content, "ppt_file_path": temp_file_path}

    except Exception as e:
        logger.error(f"Failed to generate presentation content: {e}")
        # Log additional context for debugging
        logger.error(f"Input content preview: {input_content[:200]}...")
        raise RuntimeError(f"Content generation failed: {str(e)}") from e


def build_graph():
    """
    Build and compile the PowerPoint generation workflow graph.

    This function constructs a comprehensive LangGraph workflow that orchestrates
    the presentation generation process through a two-stage pipeline:

    1. Content Composition Stage:
       - Takes raw input content
       - Uses specialized LLM agent to generate structured presentation content
       - Saves content to temporary markdown file

    2. File Generation Stage:
       - Converts markdown content to PowerPoint using Marp CLI
       - Handles file operations and cleanup
       - Returns path to generated presentation

    The workflow uses a linear execution model with proper error propagation
    and state management throughout the process.

    Returns:
        CompiledGraph: A compiled LangGraph workflow ready for execution.
                      Can be invoked with {"input": "content"} to generate presentations.

    Raises:
        RuntimeError: If workflow compilation fails

    Example:
        workflow = build_presentation_workflow()
        result = workflow.invoke({"input": "Your presentation content here"})
        presentation_path = result["generated_file_path"]
    """
    logger.info("Building PowerPoint generation workflow...")

    try:
        # Initialize the state graph with our custom state class
        builder = StateGraph(PowerPointWorkflowState)

        # Add workflow nodes with descriptive names
        builder.add_node("content_composer", compose_presentation_content)
        builder.add_node("file_generator", generate_presentation_file)

        # Define workflow edges (execution flow)
        # START -> Content Composition -> File Generation -> END
        builder.add_edge(START, "content_composer")
        builder.add_edge("content_composer", "file_generator")
        builder.add_edge("file_generator", END)

        # Compile the workflow graph
        compiled_workflow = builder.compile()

        logger.info("PowerPoint workflow graph built and compiled successfully")
        return compiled_workflow

    except Exception as e:
        logger.error(f"Failed to build workflow: {e}")
        raise RuntimeError(f"Workflow compilation failed: {str(e)}") from e


# Create the default workflow instance
ppt_graph = build_graph()


def main() -> None:
    """
    Main function for testing and demonstrating the PowerPoint generation workflow.

    This function serves as both a testing utility and usage example. It demonstrates
    the complete workflow execution by:
    1. Loading environment variables for LLM configuration
    2. Reading example content from a markdown file
    3. Executing the workflow with the example content
    4. Reporting the results and generated file location

    The function includes comprehensive error handling for common failure scenarios
    such as missing files, environment configuration issues, and workflow execution errors.

    Returns:
        None

    Raises:
        SystemExit: If critical errors occur that prevent execution

    Example:
        python -m src.ppt.builder
        # This will generate a presentation from the example content
    """
    from dotenv import load_dotenv

    # Load environment variables for LLM configuration
    load_dotenv()
    logger.info("Environment variables loaded")

    try:
        # Define example file path
        example_file_path = "examples/nanjing_tangbao.md"

        # Validate example file exists
        if not os.path.exists(example_file_path):
            logger.error(f"Example file not found: {example_file_path}")
            logger.info("Available examples:")
            if os.path.exists("examples"):
                for file in os.listdir("examples"):
                    if file.endswith(".md"):
                        logger.info(f"  - {file}")
            return

        # Load example content
        logger.info(f"Loading example content from: {example_file_path}")
        with open(example_file_path, "r", encoding="utf-8") as f:
            report_content = f.read()

        if not report_content.strip():
            logger.error("Example file is empty")
            return

        logger.info(f"Loaded content length: {len(report_content)} characters")

        # Execute the workflow
        logger.info("Starting presentation generation workflow...")
        initial_state = {"input": report_content}

        final_state = ppt_graph.invoke(initial_state)

        # Validate and report results
        generated_file = final_state.get("generated_file_path")
        if generated_file and os.path.exists(generated_file):
            file_size = os.path.getsize(generated_file)
            logger.info("Workflow completed successfully!")
            logger.info(f"Generated file: {generated_file}")
            logger.info(f"File size: {file_size} bytes")
            print(f"\n✅ Presentation generated successfully!")
            print(f"📁 File location: {generated_file}")
        else:
            logger.error("Workflow completed but no file was generated")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        print(f"❌ Error: Required file not found - {e}")

    except PermissionError as e:
        logger.error(f"Permission denied: {e}")
        print(f"❌ Error: Permission denied - {e}")

    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        print(f"❌ Error: Workflow execution failed - {e}")
        # Log additional context for debugging
        logger.exception("Full error traceback:")


if __name__ == "__main__":
    main()
