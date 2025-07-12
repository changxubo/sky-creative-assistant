from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from src.config.report_style import ReportStyle
from src.rag.types import Resource


class ContentItem(BaseModel):
    """
    Represents a single content item within a chat message.
    
    Supports multiple content types including text and images,
    following the multi-modal message format.
    """
    
    type: str = Field(..., description="Content type (text, image, etc.)")
    text: Optional[str] = Field(None, description="Text content when type is 'text'")
    image_url: Optional[str] = Field(None, description="Image URL when type is 'image'")
    
    @validator('type')
    def validate_content_type(cls, v):
        """Validate that content type is supported."""
        allowed_types = ['text', 'image']
        if v not in allowed_types:
            raise ValueError(f"Content type must be one of: {allowed_types}")
        return v


class ChatMessage(BaseModel):
    """
    Represents a single message in a chat conversation.
    
    Supports both simple text messages and multi-modal content
    with images and other media types.
    """
    
    role: str = Field(..., description="Message sender role (user, assistant, system)")
    content: Union[str, List[ContentItem]] = Field(
        ...,
        description="Message content - either plain text or list of content items"
    )
    
    @validator('role')
    def validate_role(cls, v):
        """Validate that message role is supported."""
        allowed_roles = ['user', 'assistant', 'system']
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of: {allowed_roles}")
        return v


class ChatRequest(BaseModel):
    """
    Main request model for chat interactions.
    
    Encapsulates all parameters needed for research-based chat,
    including message history, resources, and configuration options.
    """
    
    messages: List[ChatMessage] = Field(
        default_factory=list,
        description="Conversation history between user and assistant"
    )
    resources: List[Resource] = Field(
        default_factory=list,
        description="Research resources for knowledge augmentation"
    )
    debug: bool = Field(False, description="Enable debug logging output")
    thread_id: str = Field(
        "__default__",
        description="Unique conversation thread identifier"
    )
    max_plan_iterations: int = Field(
        1,
        ge=1,
        le=10,
        description="Maximum planning iterations allowed"
    )
    max_step_num: int = Field(
        3,
        ge=1,
        le=20,
        description="Maximum steps per execution plan"
    )
    max_search_results: int = Field(
        3,
        ge=1,
        le=50,
        description="Maximum search results to retrieve"
    )
    auto_accepted_plan: bool = Field(
        False,
        description="Automatically accept generated execution plan"
    )
    interrupt_feedback: Optional[str] = Field(
        None,
        description="User feedback for plan interruption/modification"
    )
    mcp_settings: Optional[Dict] = Field(
        None,
        description="Model Context Protocol configuration settings"
    )
    enable_background_investigation: bool = Field(
        True,
        description="Enable preliminary research before planning"
    )
    report_style: ReportStyle = Field(
        ReportStyle.ACADEMIC,
        description="Output report formatting style"
    )
    enable_deep_thinking: bool = Field(
        False,
        description="Enable enhanced reasoning and analysis"
    )


class TTSRequest(BaseModel):
    """
    Request model for Text-to-Speech conversion.
    
    Configures voice synthesis parameters including voice type,
    encoding format, and audio characteristics.
    """
    
    text: str = Field(..., min_length=1, description="Text content for speech synthesis")
    voice_type: str = Field(
        "BV700_V2_streaming",
        description="Voice model identifier"
    )
    encoding: str = Field("mp3", description="Audio output encoding format")
    speed_ratio: float = Field(
        1.0,
        ge=0.5,
        le=2.0,
        description="Speech speed multiplier (0.5-2.0)"
    )
    volume_ratio: float = Field(
        1.0,
        ge=0.0,
        le=2.0,
        description="Speech volume multiplier (0.0-2.0)"
    )
    pitch_ratio: float = Field(
        1.0,
        ge=0.5,
        le=2.0,
        description="Speech pitch multiplier (0.5-2.0)"
    )
    text_type: str = Field("plain", description="Input text format (plain or ssml)")
    with_frontend: bool = Field(True, description="Enable frontend text processing")
    frontend_type: str = Field("unitTson", description="Frontend processor type")
    
    @validator('encoding')
    def validate_encoding(cls, v):
        """Validate audio encoding format."""
        allowed_encodings = ['mp3', 'wav', 'ogg']
        if v not in allowed_encodings:
            raise ValueError(f"Encoding must be one of: {allowed_encodings}")
        return v
    
    @validator('text_type')
    def validate_text_type(cls, v):
        """Validate text input type."""
        allowed_types = ['plain', 'ssml']
        if v not in allowed_types:
            raise ValueError(f"Text type must be one of: {allowed_types}")
        return v


class GeneratePodcastRequest(BaseModel):
    """
    Request model for podcast generation.
    
    Converts written content into podcast-style audio format
    with appropriate pacing and presentation.
    """
    
    content: str = Field(
        ...,
        min_length=1,
        description="Source content for podcast generation"
    )


class GeneratePPTRequest(BaseModel):
    """
    Request model for PowerPoint presentation generation.
    
    Transforms content into structured slide presentation format
    with appropriate layout and organization.
    """
    
    content: str = Field(
        ...,
        min_length=1,
        description="Source content for presentation generation"
    )


class GenerateProseRequest(BaseModel):
    """
    Request model for prose writing generation.
    
    Creates written content based on prompts and style options,
    with customizable writing parameters.
    """
    
    prompt: str = Field(
        ...,
        min_length=1,
        description="Writing prompt or topic"
    )
    option: str = Field(..., description="Writing style and format option")
    command: str = Field(
        "",
        description="Custom instructions for prose generation"
    )


class EnhancePromptRequest(BaseModel):
    """
    Request model for prompt enhancement and optimization.
    
    Improves user prompts by adding context, clarity,
    and structured formatting for better AI responses.
    """
    
    prompt: str = Field(
        ...,
        min_length=1,
        description="Original prompt text to enhance"
    )
    context: str = Field(
        "",
        description="Additional context for prompt enhancement"
    )
    report_style: str = Field(
        "academic",
        description="Target output style for enhanced prompt"
    )
    
    @validator('report_style')
    def validate_report_style(cls, v):
        """Validate report style option."""
        allowed_styles = ['academic', 'business', 'creative', 'technical']
        if v not in allowed_styles:
            raise ValueError(f"Report style must be one of: {allowed_styles}")
        return v
