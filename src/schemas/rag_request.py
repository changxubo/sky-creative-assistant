from typing import Optional

from pydantic import BaseModel, Field

from src.rag.types import Resource


class RAGConfigResponse(BaseModel):
    """Response model for RAG (Retrieval-Augmented Generation) configuration.

    This model represents the configuration response for RAG operations,
    including provider information and settings.

    Attributes:
        provider: The name of the RAG provider service. Defaults to 'ragflow'
                 if not specified. Can be None if no provider is configured.
    """

    provider: Optional[str] = Field(
        None, description="The provider of the RAG service, defaults to 'ragflow'"
    )


class RAGResourceRequest(BaseModel):
    """Request model for RAG resource queries.

    This model represents a request to search for resources within the RAG system.
    It encapsulates the search query and any associated parameters.

    Attributes:
        query: The search query string used to find relevant resources.
               Can be None if no specific query is provided.
    """

    query: Optional[str] = Field(
        None, description="The search query for resources to be retrieved"
    )


class RAGResourcesResponse(BaseModel):
    """Response model for RAG resource search results.

    This model represents the response containing a collection of resources
    retrieved from the RAG system based on a search query.

    Attributes:
        resources: A list of Resource objects containing the search results.
                  This field is required and must contain at least an empty list.
    """

    resources: list[Resource] = Field(
        ..., description="The list of resources retrieved from the RAG system"
    )
