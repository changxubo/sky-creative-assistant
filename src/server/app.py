# Standard library imports

import base64
from datetime import datetime
import json
import logging
import os
from typing import (
    Annotated,
    Any,
    AsyncGenerator,
    Dict,
    List,
    Optional,
    cast,
)
from uuid import uuid4

# Third-party imports
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from langchain_core.messages import AIMessageChunk, BaseMessage, ToolMessage
from langgraph.types import Command
from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

# from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.mongodb import AsyncMongoDBSaver
from langfuse.langchain import CallbackHandler

# Local imports
from src.config.report_style import ReportStyle
from src.config.tools import SELECTED_RAG_PROVIDER
from src.agent.graph import build_graph_with_memory
from src.models.chat import get_configured_llm_models
from src.schemas.replay_request import ReplaysRequest, ReplaysResponse
from src.subagent.podcast import build_graph as build_podcast_graph
from src.subagent.ppt import build_graph as build_ppt_graph
from src.subagent.prompt import build_graph as build_prompt_enhancer_graph
from src.subagent.prose import build_graph as build_prose_graph
from src.rag.retriever import build_retriever
from src.rag.types import Resource
from src.schemas.chat_request import (
    ChatRequest,
    EnhancePromptRequest,
    GeneratePodcastRequest,
    GeneratePPTRequest,
    GenerateProseRequest,
    TTSRequest,
)
from src.schemas.config_request import ConfigResponse
from src.schemas.mcp_request import MCPServerMetadataRequest, MCPServerMetadataResponse
from src.schemas.mcp_utils import load_mcp_tools
from src.schemas.rag_request import (
    RAGConfigResponse,
    RAGResourceRequest,
    RAGResourcesResponse,
)
from src.schemas.replay_request import Replay
from src.tools import VolcengineTTS
from src.tools.riva_tts import RivaTTS
from src.agent.checkpoint import chat_stream_message, search_replays, get_replay_by_id,sanitize_args

# Constants
INTERNAL_SERVER_ERROR_DETAIL = "Internal Server Error"
DEFAULT_THREAD_ID = "__default__"
MAX_TEXT_LENGTH = 1024
DEFAULT_MCP_TIMEOUT = 300

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize the Langfuse handler
langfuse_handler = CallbackHandler()

# FastAPI app instance
app = FastAPI(
    title="Deep Research Agent API",
    description="API for Deep Research Agent - An AI-powered research and content generation platform",
    version="0.1.0",
)

# Configure CORS middleware with better security
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure specific origins for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)
in_memory_store = InMemoryStore()

graph = build_graph_with_memory()


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    """
    Stream chat responses from the AI workflow.

    This endpoint processes chat requests and returns streaming responses from the
    AI workflow system. It handles thread management, resource allocation, and
    real-time message streaming.

    Args:
        request: ChatRequest containing messages, configuration, and workflow settings

    Returns:
        StreamingResponse: Server-sent events stream containing chat responses

    Raises:
        HTTPException: If request processing fails
    """
    try:
        # Generate unique thread ID if using default
        thread_id = request.thread_id
        if thread_id == DEFAULT_THREAD_ID:
            thread_id = str(uuid4())

        # Validate request parameters
        if not request.messages:
            raise HTTPException(status_code=400, detail="Messages cannot be empty")

        # initialize checkpointer and store
        pg_db_uri = os.getenv("POSTGRES_URI_test", "")
        mg_db_uri = os.getenv("MONGODB_URI_test", "")
        if pg_db_uri != "":
            logger.info("start async postgres checkpointer")
            connection_kwargs = {
                "autocommit": True,
                "prepare_threshold": 0,
            }
            # async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
            async with AsyncConnectionPool(
                pg_db_uri, kwargs=connection_kwargs
            ) as conn:  # this has been updated
                checkpointer = AsyncPostgresSaver(conn)
                await checkpointer.setup()
                # graph = workflow.compile(checkpointer=checkpointer, store=in_memory_store)
                graph.checkpointer = checkpointer
                graph.store = in_memory_store
                return StreamingResponse(
                    _astream_workflow_generator(
                        request.model_dump()["messages"],
                        thread_id,
                        request.resources,
                        request.max_plan_iterations,
                        request.max_step_num,
                        request.max_search_results,
                        request.auto_accepted_plan,
                        request.interrupt_feedback,
                        request.mcp_settings,
                        request.enable_background_investigation,
                        request.report_style,
                        request.enable_deep_thinking,
                    ),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "X-Accel-Buffering": "no",  # Disable nginx buffering
                    },
                )
        elif mg_db_uri != "":
            logger.info("start async postgres checkpointer.")
            async with AsyncMongoDBSaver.from_conn_string(mg_db_uri) as checkpointer:
                # graph = workflow.compile(checkpointer=checkpointer, store=in_memory_store)
                graph.checkpointer = checkpointer
                graph.store = in_memory_store
                return StreamingResponse(
                    _astream_workflow_generator(
                        request.model_dump()["messages"],
                        thread_id,
                        request.resources,
                        request.max_plan_iterations,
                        request.max_step_num,
                        request.max_search_results,
                        request.auto_accepted_plan,
                        request.interrupt_feedback,
                        request.mcp_settings,
                        request.enable_background_investigation,
                        request.report_style,
                        request.enable_deep_thinking,
                    ),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "X-Accel-Buffering": "no",  # Disable nginx buffering
                    },
                )
        return StreamingResponse(
            _astream_workflow_generator(
                request.model_dump()["messages"],
                thread_id,
                request.resources,
                request.max_plan_iterations,
                request.max_step_num,
                request.max_search_results,
                request.auto_accepted_plan,
                request.interrupt_feedback,
                request.mcp_settings,
                request.enable_background_investigation,
                request.report_style,
                request.enable_deep_thinking,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            },
        )
    except Exception as e:
        logger.exception(f"Error in chat stream endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR_DETAIL)

async def _astream_workflow_generator(
    messages: List[Dict[str, Any]],
    thread_id: str,
    resources: List[Resource],
    max_plan_iterations: int,
    max_step_num: int,
    max_search_results: int,
    auto_accepted_plan: bool,
    interrupt_feedback: str,
    mcp_settings: Dict[str, Any],
    enable_background_investigation: bool,
    report_style: ReportStyle,
    enable_deep_thinking: bool,
) -> AsyncGenerator[str, None]:
    """
    Generate streaming workflow responses.

    This function orchestrates the AI workflow execution and yields streaming
    responses in server-sent events format.

    Args:
        messages: List of chat messages
        thread_id: Unique identifier for the conversation thread
        resources: List of resources to be used in the workflow
        max_plan_iterations: Maximum number of planning iterations
        max_step_num: Maximum number of execution steps
        max_search_results: Maximum number of search results to return
        auto_accepted_plan: Whether to automatically accept the plan
        interrupt_feedback: Feedback for handling interruptions
        mcp_settings: MCP server configuration settings
        enable_background_investigation: Whether to enable background research
        report_style: Style for the final report
        enable_deep_thinking: Whether to enable deep thinking mode

    Yields:
        str: Server-sent events formatted responses
    """
    try:
        # Validate input messages
        if not messages:
            yield _make_event("error", {"error": "No messages provided"})
            return
        for message in messages:
            if isinstance(message, dict) and "content" in message:
                json_data = json.dumps(
                    {
                        "thread_id": thread_id,
                        "id": "run--" + message.get("id", uuid4().hex),
                        "role": "user",
                        "content": message.get("content", ""),
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                chat_stream_message(
                    thread_id, f"event: message_chunk\ndata: {json_data}\n\n", "none"
                )
        # Prepare workflow input
        workflow_input = {
            "messages": messages,
            "plan_iterations": 0,
            "final_report": "",
            "current_plan": None,
            "observations": [],
            "investigations": "",
            "auto_accepted_plan": auto_accepted_plan,
            "enable_background_investigation": enable_background_investigation,
            "research_topic": messages[-1].get("content", "") if messages else "",
            "enable_deep_thinking": enable_deep_thinking,
            "reasoning_content": "",
        }

        # Handle interrupt feedback
        if not auto_accepted_plan and interrupt_feedback:
            resume_message = f"[{interrupt_feedback}]"
            # Add the last message to the resume message
            if messages:
                resume_message += f" {messages[-1].get('content', '')}"
            workflow_input = Command(resume=resume_message)

        # Stream workflow execution
       
        mg_db_uri = os.getenv("MONGODB_URI", "")
        logger.info("start async postgres checkpointer.")
        async with AsyncMongoDBSaver.from_conn_string(mg_db_uri) as checkpointer:
            # graph = workflow.compile(checkpointer=checkpointer, store=in_memory_store)
            graph.checkpointer = checkpointer
            graph.store = in_memory_store
            logger.info(f"Starting workflow with thread_id: {thread_id}")    
            async for agent, _, event_data in graph.astream(
                workflow_input,
                config={
                    "thread_id": thread_id,
                    "resources": resources,
                    "max_plan_iterations": max_plan_iterations,
                    "max_step_num": max_step_num,
                    "max_search_results": max_search_results,
                    "mcp_settings": mcp_settings,
                    "report_style": report_style.value,
                    "enable_deep_thinking": enable_deep_thinking,
                    "callbacks": [langfuse_handler]
                },
                stream_mode=["messages", "updates"],
                subgraphs=True,
                # checkpoint_during= True,
            ):
                # Handle interruption events
                if isinstance(event_data, dict):
                    if "__interrupt__" in event_data:
                        yield _make_event(
                            "interrupt",
                            {
                                "thread_id": thread_id,
                                "id": event_data["__interrupt__"][0].ns[0],
                                "role": "assistant",
                                "content": event_data["__interrupt__"][0].value,
                                "finish_reason": "interrupt",
                                "options": [
                                    {"text": "Edit Plan", "value": "edit_plan"},
                                    {"text": "Start Research", "value": "accepted"},
                                ],
                            },
                        )
                    continue

                if (
                    isinstance(event_data, dict)
                    and "background_investigator_finished" in event_data
                ):
                    # Process message events
                    message_chunk = cast(
                        BaseMessage,
                        event_data["background_investigator"]["messages"][0],
                    )
                    yield _make_event(
                        "message_chunk",
                        {
                            "thread_id": thread_id,
                            "agent": "background_investigator",
                            "id": "run--" + message_chunk.id,
                            "role": "assistant",
                            "content": event_data["background_investigator"][
                                "investigations"
                            ],
                        },
                    )
                    continue

                # Process message events
                message_chunk, message_metadata = cast(
                    tuple[BaseMessage, dict[str, Any]], event_data
                )
                # Handle empty agent tuple gracefully
                agent_name = "unknown"
                if agent and len(agent) > 0:
                    agent_name = agent[0].split(":")[0] if ":" in agent[0] else agent[0]
                else:
                    agent_name = message_metadata.get("langgraph_node", "unknown")
                # Build event stream message
                event_stream_message: Dict[str, Any] = {
                    "thread_id": thread_id,
                    "checkpoint_ns": message_metadata.get("checkpoint_ns", ""),
                    "langgraph_node": message_metadata.get("langgraph_node", ""),
                    "langgraph_path": message_metadata.get("langgraph_path", ""),
                    "langgraph_step": message_metadata.get("langgraph_step", ""),
                    "agent": agent_name,
                    "id": message_chunk.id,
                    "role": "assistant",
                    "content": message_chunk.content,
                }

                # Add reasoning content if available
                if message_chunk.additional_kwargs.get("reasoning_content"):
                    event_stream_message["reasoning_content"] = (
                        message_chunk.additional_kwargs["reasoning_content"]
                    )

                # Add finish reason if available
                if message_chunk.response_metadata.get("finish_reason"):
                    event_stream_message["finish_reason"] = (
                        message_chunk.response_metadata.get("finish_reason")
                    )

                # Handle different message types
                if isinstance(message_chunk, ToolMessage):
                    # Tool Message - Return the result of the tool call
                    event_stream_message["tool_call_id"] = message_chunk.tool_call_id
                    yield _make_event("tool_call_result", event_stream_message)

                elif isinstance(message_chunk, AIMessageChunk):
                    # AI Message - Handle tool calls and content
                    if message_chunk.tool_calls:
                        # AI Message - Tool Call
                        event_stream_message["tool_calls"] = message_chunk.tool_calls
                        chunks = []
                        # Convert special characters in args like [],{},<>,& and etc.
                        for chunk in message_chunk.tool_call_chunks:
                            chunks.append(
                                {
                                    "name": chunk.get("name", ""),
                                    "args": sanitize_args( chunk.get("args", "")),
                                    "id": chunk.get("id", ""),
                                    "index": chunk.get("index", 0),
                                    "type": chunk.get("type", ""),
                                }
                            )
                        event_stream_message["tool_call_chunks"] = chunks
                        yield _make_event("tool_calls", event_stream_message)

                    elif message_chunk.tool_call_chunks:
                        # AI Message - Tool Call Chunks
                        chunks = []
                        # Convert special characters in args like [],{},<>,& and etc.
                        for chunk in message_chunk.tool_call_chunks:
                            chunks.append(
                                {
                                    "name": chunk.get("name", ""),
                                    "args": sanitize_args( chunk.get("args", "")),
                                    "id": chunk.get("id", ""),
                                    "index": chunk.get("index", 0),
                                    "type": chunk.get("type", ""),
                                }
                            )
                        event_stream_message["tool_call_chunks"] =chunks
                        yield _make_event("tool_call_chunks", event_stream_message)

                    else:
                        # AI Message - Raw message tokens
                        message_event = _make_event("message_chunk", event_stream_message)
                        if message_event != "":
                            yield message_event
    except Exception as e:
        logger.exception(f"Error in workflow generator: {str(e)}")
        yield _make_event("error", {"error": str(e)})


def _make_event(event_type: str, data: Dict[str, Any]) -> str:
    """
    Create a server-sent event string from event data.

    Args:
        event_type: Type of the event (e.g., 'message_chunk', 'tool_calls', 'interrupt')
        data: Event data dictionary

    Returns:
        str: Formatted server-sent event string
    """
    # Remove empty content to reduce payload size
    if data.get("content") == "":
        data.pop("content", None)
    # skip empty data: content,reasoning_content,finish_reason
    if event_type == "message_chunk":
        if (
            data.get("content", "") == ""
            and data.get("reasoning_content", "") == ""
            and data.get("finish_reason", "") == ""
        ):
            return ""
    # Ensure JSON serialization with proper encoding
    try:
        json_data = json.dumps(data, ensure_ascii=False)
        finish_reason = data.get("finish_reason", "")
        chat_stream_message(
            data.get("thread_id", ""),
            f"event: {event_type}\ndata: {json_data}\n\n",
            finish_reason,
        )
        return f"event: {event_type}\ndata: {json_data}\n\n"
    except (TypeError, ValueError) as e:
        logger.error(f"Error serializing event data: {e}")
        # Return a safe error event
        error_data = json.dumps({"error": "Serialization failed"}, ensure_ascii=False)
        return f"event: error\ndata: {error_data}\n\n"


def _riva_tts(request: TTSRequest):
    app_id = os.getenv("RIVA_TTS_APPID", "")
    if not app_id:
        raise HTTPException(status_code=400, detail="RIVA_TTS_APPID is not set")
    access_token = os.getenv("RIVA_TTS_ACCESS_TOKEN", "")
    if not access_token:
        raise HTTPException(status_code=400, detail="RIVA_TTS_ACCESS_TOKEN is not set")
    cluster = "Riva_tts"
    voice_type = "Magpie-Multilingual.EN-US.Sofia"
    tts_client = RivaTTS(
        function_id=app_id,
        access_token=access_token,
        cluster=cluster,
        voice_type=voice_type,
    )
    # Call the TTS API
    result = tts_client.text_to_speech(
        text=request.text[:1024],
        encoding=request.encoding,
        speed_ratio=request.speed_ratio,
        volume_ratio=request.volume_ratio,
        pitch_ratio=request.pitch_ratio,
        text_type=request.text_type,
        with_frontend=request.with_frontend,
        frontend_type=request.frontend_type,
        # output_file="output.wav",   # Specify output file for debugging
    )
    return result


def _volcengine_tts(request: TTSRequest):
    app_id = os.getenv("VOLCENGINE_TTS_APPID", "")
    if not app_id:
        raise HTTPException(status_code=400, detail="VOLCENGINE_TTS_APPID is not set")
    access_token = os.getenv("VOLCENGINE_TTS_ACCESS_TOKEN", "")
    if not access_token:
        raise HTTPException(
            status_code=400, detail="VOLCENGINE_TTS_ACCESS_TOKEN is not set"
        )

    # Truncate text to prevent excessive processing
    text_to_convert = request.text[:MAX_TEXT_LENGTH]
    if len(request.text) > MAX_TEXT_LENGTH:
        logger.warning(
            f"Text truncated from {len(request.text)} to {MAX_TEXT_LENGTH} characters"
        )

    # Get TTS configuration with defaults
    cluster = os.getenv("VOLCENGINE_TTS_CLUSTER", "volcano_tts")
    voice_type = os.getenv("VOLCENGINE_TTS_VOICE_TYPE", "BV700_V2_streaming")

    # Initialize TTS client
    tts_client = VolcengineTTS(
        appid=app_id,
        access_token=access_token,
        cluster=cluster,
        voice_type=voice_type,
    )

    # Generate audio
    logger.info(f"Generating TTS for text length: {len(text_to_convert)}")
    result = tts_client.text_to_speech(
        text=text_to_convert,
        encoding=request.encoding,
        speed_ratio=request.speed_ratio,
        volume_ratio=request.volume_ratio,
        pitch_ratio=request.pitch_ratio,
        text_type=request.text_type,
        with_frontend=request.with_frontend,
        frontend_type=request.frontend_type,
    )
    return result


@app.post("/api/tts")
async def text_to_speech(request: TTSRequest) -> Response:
    """
    Convert text to speech using Volcengine TTS API.

    This endpoint converts text to speech using the configured TTS provider.
    It validates input parameters, handles authentication, and returns audio data.

    Args:
        request: TTSRequest containing text and audio generation parameters

    Returns:
        Response: Audio file in the requested format

    Raises:
        HTTPException: If TTS configuration is invalid or processing fails
    """
    # Validate required environment variables
    app_id = os.getenv("VOLCENGINE_TTS_APPID")
    if not app_id:
        logger.error("VOLCENGINE_TTS_APPID environment variable is not set")
        raise HTTPException(
            status_code=400,
            detail="TTS service is not configured. Please check server configuration.",
        )

    access_token = os.getenv("VOLCENGINE_TTS_ACCESS_TOKEN")
    if not access_token:
        logger.error("VOLCENGINE_TTS_ACCESS_TOKEN environment variable is not set")
        raise HTTPException(
            status_code=400,
            detail="TTS service is not configured. Please check server configuration.",
        )

    # Validate request parameters
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:

        tts_type = os.getenv("TTS_TYPE", "VOLCENGINE")
        if tts_type == "RIVA":
            result = _riva_tts(request)
        else:
            result = _volcengine_tts(request)
        # Check TTS result
        if not result.get("success"):
            error_msg = result.get("error", "Unknown TTS error")
            logger.error(f"TTS generation failed: {error_msg}")
            raise HTTPException(
                status_code=500, detail=f"TTS generation failed: {error_msg}"
            )

        # Validate audio data
        audio_data_b64 = result.get("audio_data")
        if not audio_data_b64:
            raise HTTPException(
                status_code=500, detail="No audio data returned from TTS service"
            )

        # Decode base64 audio data
        try:
            audio_data = base64.b64decode(audio_data_b64)
        except Exception as decode_error:
            logger.error(f"Failed to decode audio data: {decode_error}")
            raise HTTPException(status_code=500, detail="Failed to decode audio data")

        # Return audio response
        return Response(
            content=audio_data,
            media_type=f"audio/{request.encoding}",
            headers={
                "Content-Disposition": f"attachment; filename=tts_output.{request.encoding}",
                "Content-Length": str(len(audio_data)),
            },
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in TTS endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR_DETAIL)


@app.post("/api/podcast/generate")
async def generate_podcast(request: GeneratePodcastRequest) -> Response:
    """
    Generate a podcast from text content.

    This endpoint converts text content into a podcast format using AI-powered
    script generation and text-to-speech conversion.

    Args:
        request: GeneratePodcastRequest containing the source content

    Returns:
        Response: MP3 audio file containing the generated podcast

    Raises:
        HTTPException: If podcast generation fails
    """
    try:
        # Validate request content
        if not request.content or not request.content.strip():
            raise HTTPException(status_code=400, detail="Content cannot be empty")

        report_content = request.content.strip()
        logger.info(f"Generating podcast for content length: {len(report_content)}")

        # Build and execute podcast workflow
        podcast_workflow = build_podcast_graph()
        if not podcast_workflow:
            raise HTTPException(
                status_code=500, detail="Podcast workflow is not available"
            )

        # Generate podcast
        final_state = podcast_workflow.invoke({"input": report_content})

        # Validate output
        if not final_state or "output" not in final_state:
            raise HTTPException(
                status_code=500, detail="Podcast generation failed: No output generated"
            )

        audio_bytes = final_state["output"]
        if not audio_bytes:
            raise HTTPException(
                status_code=500, detail="Podcast generation failed: Empty audio output"
            )

        logger.info(f"Podcast generated successfully, size: {len(audio_bytes)} bytes")

        return Response(
            content=audio_bytes,
            media_type="audio/mp3",
            headers={
                "Content-Disposition": "attachment; filename=podcast.mp3",
                "Content-Length": str(len(audio_bytes)),
            },
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error occurred during podcast generation: {str(e)}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR_DETAIL)


@app.post("/api/ppt/generate")
async def generate_ppt(request: GeneratePPTRequest) -> Response:
    """
    Generate a PowerPoint presentation from text content.

    This endpoint converts text content into a PowerPoint presentation using
    AI-powered content structuring and slide generation.

    Args:
        request: GeneratePPTRequest containing the source content

    Returns:
        Response: PPTX file containing the generated presentation

    Raises:
        HTTPException: If PPT generation fails
    """
    try:
        # Validate request content
        if not request.content or not request.content.strip():
            raise HTTPException(status_code=400, detail="Content cannot be empty")

        report_content = request.content.strip()
        logger.info(f"Generating PPT for content length: {len(report_content)}")

        # Build and execute PPT workflow
        ppt_workflow = build_ppt_graph()
        if not ppt_workflow:
            raise HTTPException(status_code=500, detail="PPT workflow is not available")

        # Generate PPT
        final_state = ppt_workflow.invoke({"input": report_content})

        # Validate output
        if not final_state or "generated_file_path" not in final_state:
            raise HTTPException(
                status_code=500,
                detail="PPT generation failed: No output file generated",
            )

        generated_file_path = final_state["generated_file_path"]
        if not generated_file_path or not os.path.exists(generated_file_path):
            raise HTTPException(
                status_code=500, detail="PPT generation failed: Output file not found"
            )

        # Read generated file
        try:
            with open(generated_file_path, "rb") as f:
                ppt_bytes = f.read()
        except (OSError, IOError) as file_error:
            logger.error(f"Failed to read generated PPT file: {file_error}")
            raise HTTPException(
                status_code=500, detail="Failed to read generated PPT file"
            )

        if not ppt_bytes:
            raise HTTPException(
                status_code=500, detail="PPT generation failed: Empty file generated"
            )

        logger.info(f"PPT generated successfully, size: {len(ppt_bytes)} bytes")

        return Response(
            content=ppt_bytes,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={
                "Content-Disposition": "attachment; filename=presentation.pptx",
                "Content-Length": str(len(ppt_bytes)),
            },
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error occurred during PPT generation: {str(e)}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR_DETAIL)


@app.post("/api/prose/generate")
async def generate_prose(request: GenerateProseRequest) -> StreamingResponse:
    """
    Generate prose content using AI workflows.

    This endpoint processes prose generation requests and returns streaming
    responses with AI-generated content based on the specified options.

    Args:
        request: GenerateProseRequest containing prompt and generation options

    Returns:
        StreamingResponse: Server-sent events stream with generated prose

    Raises:
        HTTPException: If prose generation fails
    """
    try:
        # Validate request content
        if not request.prompt or not request.prompt.strip():
            raise HTTPException(status_code=400, detail="Prompt cannot be empty")

        # Sanitize prompt for logging (remove line breaks)
        sanitized_prompt = request.prompt.replace("\r\n", " ").replace("\n", " ")
        logger.info(f"Generating prose for prompt: {sanitized_prompt[:100]}...")

        # Build prose workflow
        prose_workflow = build_prose_graph()
        if not prose_workflow:
            raise HTTPException(
                status_code=500, detail="Prose workflow is not available"
            )

        # Validate generation options
        valid_options = {"continue", "improve", "shorter", "longer", "fix", "zap"}
        if request.option not in valid_options:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid option. Must be one of: {', '.join(valid_options)}",
            )

        # Generate prose stream
        async def prose_stream_generator():
            try:
                events = prose_workflow.astream(
                    {
                        "content": request.prompt,
                        "option": request.option,
                        "command": request.command,
                    },
                    stream_mode="messages",
                    subgraphs=True,
                )

                async for node_info, event in events:
                    if event and len(event) > 0:
                        content = event[0].content
                        if content:  # Only yield non-empty content
                            yield f"data: {content}\n\n"

            except Exception as e:
                logger.exception(f"Error in prose stream generator: {str(e)}")
                yield f"data: Error: {str(e)}\n\n"

        return StreamingResponse(
            prose_stream_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error occurred during prose generation: {str(e)}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR_DETAIL)


@app.post("/api/prompt/enhance")
async def enhance_prompt(request: EnhancePromptRequest) -> Dict[str, str]:
    """
    Enhance a prompt using AI-powered prompt optimization.

    This endpoint processes prompt enhancement requests and returns improved
    versions of the input prompt based on the specified report style.

    Args:
        request: EnhancePromptRequest containing the prompt to enhance

    Returns:
        Dict containing the enhanced prompt result

    Raises:
        HTTPException: If prompt enhancement fails
    """
    try:
        # Validate request content
        if not request.prompt or not request.prompt.strip():
            raise HTTPException(status_code=400, detail="Prompt cannot be empty")

        # Sanitize prompt for logging (remove line breaks)
        sanitized_prompt = request.prompt.replace("\r\n", " ").replace("\n", " ")
        logger.info(f"Enhancing prompt: {sanitized_prompt[:100]}...")

        # Parse and validate report style
        report_style = _parse_report_style(request.report_style)

        # Build prompt enhancer workflow
        prompt_enhancer_workflow = build_prompt_enhancer_graph()
        if not prompt_enhancer_workflow:
            raise HTTPException(
                status_code=500, detail="Prompt enhancer workflow is not available"
            )

        # Enhance prompt
        final_state = prompt_enhancer_workflow.invoke(
            {
                "prompt": request.prompt,
                "context": request.context,
                "report_style": report_style,
            }
        )

        # Validate output
        if not final_state or "output" not in final_state:
            raise HTTPException(
                status_code=500, detail="Prompt enhancement failed: No output generated"
            )

        enhanced_result = final_state["output"]
        if not enhanced_result:
            raise HTTPException(
                status_code=500, detail="Prompt enhancement failed: Empty result"
            )

        logger.info("Prompt enhanced successfully")
        return {"result": enhanced_result}

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error occurred during prompt enhancement: {str(e)}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR_DETAIL)


def _parse_report_style(report_style_str: Optional[str]) -> ReportStyle:
    """
    Parse and validate report style string.

    Args:
        report_style_str: String representation of report style

    Returns:
        ReportStyle: Parsed report style enum
    """
    if not report_style_str:
        return ReportStyle.ACADEMIC

    try:
        # Handle both uppercase and lowercase input
        style_mapping = {
            "ACADEMIC": ReportStyle.ACADEMIC,
            "POPULAR_SCIENCE": ReportStyle.POPULAR_SCIENCE,
            "NEWS": ReportStyle.NEWS,
            "SOCIAL_MEDIA": ReportStyle.SOCIAL_MEDIA,
        }

        normalized_style = report_style_str.upper()
        return style_mapping.get(normalized_style, ReportStyle.ACADEMIC)

    except Exception as e:
        logger.warning(f"Invalid report style '{report_style_str}': {e}")
        return ReportStyle.ACADEMIC


@app.post("/api/mcp/server/metadata", response_model=MCPServerMetadataResponse)
async def mcp_server_metadata(
    request: MCPServerMetadataRequest,
) -> MCPServerMetadataResponse:
    """
    Get metadata and tools information from an MCP server.

    This endpoint connects to an MCP server and retrieves available tools
    and metadata for integration with the AI workflow system.

    Args:
        request: MCPServerMetadataRequest containing server connection details

    Returns:
        MCPServerMetadataResponse: Server metadata and available tools

    Raises:
        HTTPException: If server connection or metadata retrieval fails
    """
    # Check if MCP server configuration is enabled
    if os.getenv("ENABLE_MCP_SERVER_CONFIGURATION", "false").lower() not in [
        "true",
        "1",
        "yes",
    ]:
        raise HTTPException(
            status_code=403,
            detail="MCP server configuration is disabled. Set ENABLE_MCP_SERVER_CONFIGURATION=true to enable MCP features.",
        )
    try:
        # Validate request parameters
        if not request.transport:
            raise HTTPException(status_code=400, detail="Transport type is required")

        if request.transport == "stdio" and not request.command:
            raise HTTPException(
                status_code=400, detail="Command is required for stdio transport"
            )

        if request.transport in ["sse", "websocket"] and not request.url:
            raise HTTPException(
                status_code=400, detail="URL is required for SSE/WebSocket transport"
            )

        # Set timeout with validation
        timeout = DEFAULT_MCP_TIMEOUT
        if request.timeout_seconds is not None:
            if request.timeout_seconds <= 0:
                raise HTTPException(status_code=400, detail="Timeout must be positive")
            timeout = request.timeout_seconds

        logger.info(
            f"Loading MCP tools from {request.transport} server with timeout {timeout}s"
        )

        # Load tools from the MCP server
        tools = await load_mcp_tools(
            server_type=request.transport,
            command=request.command,
            args=request.args,
            url=request.url,
            env=request.env,
            timeout_seconds=timeout,
        )

        # Validate tools response
        if tools is None:
            raise HTTPException(
                status_code=500, detail="Failed to load tools from MCP server"
            )

        logger.info(f"Successfully loaded {len(tools)} tools from MCP server")

        # Create response
        response = MCPServerMetadataResponse(
            transport=request.transport,
            command=request.command,
            args=request.args,
            url=request.url,
            env=request.env,
            tools=tools,
        )

        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error in MCP server metadata endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR_DETAIL)


@app.get("/api/rag/config", response_model=RAGConfigResponse)
async def get_rag_config() -> RAGConfigResponse:
    """
    Get the current RAG (Retrieval-Augmented Generation) configuration.

    Returns:
        RAGConfigResponse: Current RAG provider configuration
    """
    try:
        return RAGConfigResponse(provider=SELECTED_RAG_PROVIDER)
    except Exception as e:
        logger.exception(f"Error getting RAG config: {str(e)}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR_DETAIL)


@app.get("/api/rag/resources", response_model=RAGResourcesResponse)
async def get_rag_resources(
    request: Annotated[RAGResourceRequest, Query()],
) -> RAGResourcesResponse:
    """
    Get available RAG resources based on query parameters.

    Args:
        request: RAGResourceRequest containing query parameters

    Returns:
        RAGResourcesResponse: List of available RAG resources
    """
    try:
        # Build retriever
        retriever = build_retriever()

        # Get resources if retriever is available
        if retriever:
            resources = retriever.list_resources(request.query)
            logger.info(f"Retrieved {len(resources)} RAG resources")
            return RAGResourcesResponse(resources=resources)
        else:
            logger.warning("RAG retriever is not available")
            return RAGResourcesResponse(resources=[])

    except Exception as e:
        logger.exception(f"Error getting RAG resources: {str(e)}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR_DETAIL)


@app.get("/api/config", response_model=ConfigResponse)
async def get_server_config() -> ConfigResponse:
    """
    Get the current server configuration including RAG and LLM settings.

    Returns:
        ConfigResponse: Complete server configuration
    """
    try:
        # Get RAG configuration
        rag_config = RAGConfigResponse(provider=SELECTED_RAG_PROVIDER)

        # Get configured LLM models
        llm_models = get_configured_llm_models()

        logger.info(f"Retrieved configuration with {len(llm_models)} LLM model types")

        return ConfigResponse(
            rag=rag_config,
            models=llm_models,
        )

    except Exception as e:
        logger.exception(f"Error getting server config: {str(e)}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR_DETAIL)


# set response contenttype text/plain
@app.get("/api/replay/{thread_id}", response_model=str)
async def get_replay(thread_id: str) -> Response:
    """
    Get the replay content for a specific thread ID.

    Args:
        thread_id: Unique identifier for the replay thread

    Returns:
        str: Base64 encoded replay content
    """
    try:
        # Search for the replay by thread ID
        content = get_replay_by_id(thread_id)

        if not content:
            raise HTTPException(status_code=404, detail="Replay not found")

        return Response(
            content=content,
            media_type="text/plain",
            headers={"Content-Type": "text/plain; charset=utf-8"},
        )

    except Exception as e:
        logger.exception(f"Error getting replay: {str(e)}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR_DETAIL)


@app.get("/api/replays", response_model=ReplaysResponse)
async def get_replays(request: Annotated[ReplaysRequest, Query()]) -> ReplaysResponse:
    """
    Get replays based on the provided request parameters.

    Args:
        request: ReplaysRequest containing query parameters

    Returns:
        ReplaysResponse: List of replays matching the request criteria
    """
    try:
        replays = search_replays(limit=request.limit, sort=request.sort)
        response = []
        for replay in replays:
            response.append(
                Replay(
                    id=replay.get("thread_id", ""),
                    title=replay.get("research_topic", ""),
                    count=replay.get("messages", 0),
                    date=replay.get("ts", ""),
                    category=replay.get("report_style", ""),
                )
            )
        # Build replay response
        replays_response = ReplaysResponse(data=response)
        return replays_response
    except Exception as e:
        logger.exception(f"Error getting replays: {str(e)}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR_DETAIL)
