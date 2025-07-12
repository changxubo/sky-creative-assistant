from pydantic import BaseModel, Field

from src.schemas.rag_request import RAGConfigResponse


class ConfigResponse(BaseModel):
    """Response model for server configuration data.
    
    This model represents the complete configuration response structure
    containing both RAG (Retrieval-Augmented Generation) settings and
    available model configurations for the application.
    
    Attributes:
        rag: Configuration settings for the RAG system
        models: Dictionary mapping model categories to available model lists
    """

    rag: RAGConfigResponse = Field(
        ..., 
        description="The RAG (Retrieval-Augmented Generation) configuration settings"
    )
    models: dict[str, list[str]] = Field(
        ..., 
        description="Dictionary of configured models, mapping model types to available model names"
    )
