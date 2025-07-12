"""Podcast Generation Module

This module provides functionality to generate podcasts from text content
by creating scripts and converting them to audio using text-to-speech.

The workflow consists of three main steps:
1. Script generation from input text using LLM
2. Text-to-speech conversion for each script line
3. Audio mixing to create final podcast output
"""

# Standard library imports
import base64
import logging
import os
from typing import List, Literal, Optional

# Third-party imports
from langchain.schema import HumanMessage, SystemMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from pydantic import BaseModel, Field

# Local imports
from src.config.llm_map import AGENT_LLM_MAP
from src.models.chat import get_llm_by_type
from src.prompts.template import get_prompt_template
from src.tools.volcengine_tts import VolcengineTTS

logger = logging.getLogger(__name__)


class PodcastDialogueLine(BaseModel):
    """Represents a single line in the podcast script with speaker and content.

    This model defines the structure for individual dialogue lines in a podcast,
    including speaker identification and text content to be converted to speech.

    Attributes:
        speaker: Voice type for this line ("male" or "female")
        text_content: Text content to be spoken by the assigned voice
    """

    speaker: Literal["male", "female"] = Field(
        default="male", description="Voice type for this line"
    )
    text_content: str = Field(default="", description="Text content to be spoken")


class PodcastScript(BaseModel):
    """Complete podcast script containing all lines and locale information.

    This model represents the complete structure of a podcast script,
    including language settings and all dialogue lines with speaker assignments.

    Attributes:
        locale: Language locale for the script ("en" or "zh")
        dialogue_lines: List of script lines with speaker assignments
    """

    locale: Literal["en", "zh"] = Field(
        default="en", description="Language locale for the script"
    )
    dialogue_lines: List[PodcastDialogueLine] = Field(
        default=[], description="List of script lines with speaker assignments"
    )


class PodcastState(MessagesState):
    """State management for the podcast generation workflow.

    This class extends MessagesState to track the complete podcast generation process
    from input text to final audio output. It maintains all intermediate states
    and processing results throughout the workflow.

    Attributes:
        input: Input text content for podcast generation
        output: Final audio output as binary data
        script: Generated script with speaker assignments
        audio_chunks: Individual audio segments before final mixing
    """

    # Input data for podcast generation
    input: str = ""

    # Final audio output as binary data
    output: Optional[bytes] = None

    # Intermediate processing assets
    script: Optional[PodcastScript] = None  # Generated script with speaker assignments
    audio_chunks: List[bytes] = []  # Individual audio segments before mixing


# Workflow Node Functions


def combine_audio_chunks(state: PodcastState) -> dict:
    """Combine all audio chunks into a single audio file.

    Takes individual audio segments generated from script lines and concatenates
    them into a single continuous audio stream for the final podcast output.

    Args:
        state: Current podcast state containing audio chunks to be combined

    Returns:
        dict: Dictionary containing the final combined audio output under 'output' key

    Raises:
        ValueError: If no audio chunks are available to combine
    """
    logger.info("Mixing audio chunks for podcast...")
    audio_chunks = state["audio_chunks"]

    # Validate that we have audio chunks to combine
    if not audio_chunks:
        logger.warning("No audio chunks available to combine")
        return {"output": b""}

    # Concatenate all audio chunks into a single binary stream
    combined_audio = b"".join(audio_chunks)

    logger.info(f"Combined {len(audio_chunks)} audio chunks into final podcast")
    return {"output": combined_audio}


def generate_podcast_script(state: PodcastState) -> dict:
    """Generate a podcast script from input text using an LLM.

    Takes the input text and uses a configured language model to create
    a structured script with speaker assignments and dialogue. The LLM
    is configured with structured output to ensure proper formatting.

    Args:
        state: Current podcast state containing input text to be processed

    Returns:
        dict: Dictionary containing generated script and reset audio chunks
              - 'script': PodcastScript object with dialogue lines
              - 'audio_chunks': Empty list reset for new audio generation

    Raises:
        Exception: If LLM fails to generate a valid script
    """
    logger.info("Generating script for podcast...")

    # Validate input text is provided
    if not state["input"].strip():
        logger.warning("Empty input text provided for script generation")
        return {"script": PodcastScript(), "audio_chunks": []}

    # Get the configured LLM for script writing with structured output
    model = get_llm_by_type(
        AGENT_LLM_MAP["podcast_script_writer"]
    ).with_structured_output(PodcastScript, method="json_mode")

    # Generate script using system prompt and user input
    script = model.invoke(
        [
            SystemMessage(content=get_prompt_template("podcast_script_writer")),
            HumanMessage(content=state["input"]),
        ],
    )

    logger.info(f"Generated script with {len(script.dialogue_lines)} dialogue lines")
    print(script)  # Debug output for development
    return {"script": script, "audio_chunks": []}


def create_volcengine_tts_client() -> VolcengineTTS:
    """Create and configure a Volcengine TTS client.

    Initializes the text-to-speech client with credentials from environment variables.
    Uses default voice settings optimized for streaming TTS with proper error handling.

    Returns:
        VolcengineTTS: Configured TTS client instance ready for audio generation

    Raises:
        ValueError: If required environment variables (APPID, ACCESS_TOKEN) are not set
        Exception: If TTS client initialization fails
    """
    # Validate required environment variables
    app_id = os.getenv("VOLCENGINE_TTS_APPID", "").strip()
    if not app_id:
        raise ValueError(
            "VOLCENGINE_TTS_APPID environment variable is required but not set"
        )

    access_token = os.getenv("VOLCENGINE_TTS_ACCESS_TOKEN", "").strip()
    if not access_token:
        raise ValueError(
            "VOLCENGINE_TTS_ACCESS_TOKEN environment variable is required but not set"
        )

    # Set configuration with defaults for optional parameters
    cluster = os.getenv("VOLCENGINE_TTS_CLUSTER", "volcano_tts")
    default_voice_type = "BV001_streaming"  # Default female voice for streaming

    try:
        return VolcengineTTS(
            appid=app_id,
            access_token=access_token,
            cluster=cluster,
            voice_type=default_voice_type,
        )
    except Exception as e:
        logger.error(f"Failed to create Volcengine TTS client: {e}")
        raise


def convert_script_to_audio(state: PodcastState) -> dict:
    """Convert script lines to audio using text-to-speech.

    Processes each line in the podcast script, applies the appropriate voice based
    on speaker gender, and generates audio chunks that will be combined later.
    Uses different voice types for male and female speakers with optimized speed.

    Args:
        state: Current podcast state containing the generated script with dialogue lines

    Returns:
        dict: Dictionary with updated audio chunks list under 'audio_chunks' key

    Raises:
        ValueError: If script is missing or contains no dialogue lines
        Exception: If TTS client creation or audio generation fails
    """
    logger.info("Generating audio chunks for podcast...")

    # Validate script exists and has content
    if not state.get("script") or not state["script"].dialogue_lines:
        logger.warning("No script or dialogue lines available for audio conversion")
        return {"audio_chunks": state.get("audio_chunks", [])}

    try:
        tts_client = create_volcengine_tts_client()
    except Exception as e:
        logger.error(f"Failed to create TTS client: {e}")
        return {"audio_chunks": state.get("audio_chunks", [])}

    audio_chunks = state.get("audio_chunks", [])
    successful_conversions = 0

    # Process each line in the script
    for line_index, dialogue_line in enumerate(state["script"].dialogue_lines):
        # Skip empty text content
        if not dialogue_line.text_content.strip():
            logger.warning(f"Skipping empty dialogue line at index {line_index}")
            continue

        # Select voice type based on speaker gender
        # BV002_streaming: male voice, BV001_streaming: female voice
        voice_type = (
            "BV002_streaming" if dialogue_line.speaker == "male" else "BV001_streaming"
        )
        tts_client.voice_type = voice_type

        try:
            # Generate audio for this line with slight speed increase for better flow
            result = tts_client.text_to_speech(
                dialogue_line.text_content, speed_ratio=1.05
            )

            if result.get("success"):
                # Decode base64 audio data and add to chunks
                audio_data = result["audio_data"]
                audio_chunk = base64.b64decode(audio_data)
                audio_chunks.append(audio_chunk)
                successful_conversions += 1
                logger.debug(f"Successfully converted line {line_index + 1} to audio")
            else:
                error_msg = result.get("error", "Unknown TTS error")
                logger.error(
                    f"TTS conversion failed for line {line_index + 1}: {error_msg}"
                )

        except Exception as e:
            logger.error(
                f"Exception during TTS conversion for line {line_index + 1}: {e}"
            )

    logger.info(
        f"Successfully converted {successful_conversions}/{len(state['script'].dialogue_lines)} lines to audio"
    )

    return {"audio_chunks": audio_chunks}


# Workflow Construction


def build_graph():
    """Build and return the podcast workflow graph.

    Creates a LangGraph workflow that processes text input through a sequential pipeline:
    1. Script generation: Convert input text to structured dialogue script
    2. Text-to-speech conversion: Generate audio for each script line
    3. Audio mixing: Combine all audio chunks into final podcast

    The workflow uses state management to pass data between nodes and ensures
    proper error handling at each stage.

    Returns:
        Compiled LangGraph workflow ready for execution with PodcastState

    Raises:
        Exception: If workflow compilation fails
    """
    # Initialize state graph with PodcastState for type safety
    workflow_builder = StateGraph(PodcastState)

    # Add processing nodes in logical order
    workflow_builder.add_node("script_writer", generate_podcast_script)
    workflow_builder.add_node("tts_converter", convert_script_to_audio)
    workflow_builder.add_node("audio_mixer", combine_audio_chunks)

    # Define workflow edges (execution order) - linear pipeline
    workflow_builder.add_edge(START, "script_writer")  # Start with script generation
    workflow_builder.add_edge(
        "script_writer", "tts_converter"
    )  # Convert script to audio
    workflow_builder.add_edge("tts_converter", "audio_mixer")  # Mix audio chunks
    workflow_builder.add_edge("audio_mixer", END)  # Complete workflow

    logger.info("Podcast workflow built successfully")
    return workflow_builder.compile()


# Global workflow instance - initialized once for efficiency
podcast_graph = build_graph()


def main() -> None:
    """Demo script to test podcast generation functionality.

    This function demonstrates how to use the podcast workflow by:
    1. Loading environment variables for TTS credentials
    2. Reading sample content from a markdown file
    3. Generating a complete podcast from the content
    4. Saving the final audio output to disk

    This serves as both a testing tool and usage example.

    Raises:
        FileNotFoundError: If the sample markdown file is not found
        Exception: If podcast generation fails
    """
    from dotenv import load_dotenv

    # Load environment variables for TTS credentials
    load_dotenv()

    try:
        # Load sample content for podcast generation
        sample_file_path = "examples/nanjing_tangbao.md"
        with open(sample_file_path, "r", encoding="utf-8") as file:
            report_content = file.read()

        logger.info(f"Loaded sample content from {sample_file_path}")

        # Execute the complete podcast workflow
        final_state = podcast_graph.invoke({"input": report_content})

        # Display generated script for debugging and verification
        if final_state.get("script") and final_state["script"].dialogue_lines:
            logger.info("Generated script preview:")
            for line_index, dialogue_line in enumerate(
                final_state["script"].dialogue_lines
            ):
                speaker_prefix = "<M>" if dialogue_line.speaker == "male" else "<F>"
                print(
                    f"{line_index + 1:2d}. {speaker_prefix} {dialogue_line.text_content}"
                )

        # Save the final podcast audio to file
        output_filename = "final_podcast.mp3"
        if final_state.get("output"):
            with open(output_filename, "wb") as audio_file:
                audio_file.write(final_state["output"])
            logger.info(f"Podcast saved successfully to {output_filename}")
        else:
            logger.warning("No audio output generated")

    except FileNotFoundError:
        logger.error(f"Sample file {sample_file_path} not found")
        raise
    except Exception as e:
        logger.error(f"Podcast generation failed: {e}")
        raise


if __name__ == "__main__":
    main()
