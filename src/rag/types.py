import abc
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Chunk:
    """
    Represents a chunk of text content with similarity score.
    
    Used to store extracted text segments along with their relevance scores
    for retrieval-augmented generation (RAG) applications.
    """
    
    def __init__(self, content: str, similarity: float) -> None:
        """
        Initialize a text chunk with content and similarity score.
        
        Args:
            content: The text content of the chunk
            similarity: Similarity score indicating relevance (0.0 to 1.0)
        
        Raises:
            ValueError: If similarity is not between 0.0 and 1.0
        """
        if not 0.0 <= similarity <= 1.0:
            raise ValueError("Similarity score must be between 0.0 and 1.0")
        
        self.content = content
        self.similarity = similarity


class Document:
    """
    Represents a document containing multiple text chunks.
    
    A document aggregates related text chunks and maintains metadata
    such as URL, title, and unique identifier for retrieval purposes.
    """
    
    def __init__(
        self,
        document_id: str,
        url: Optional[str] = None,
        title: Optional[str] = None,
        chunks: Optional[List[Chunk]] = None,
    ) -> None:
        """
        Initialize a document with metadata and text chunks.
        
        Args:
            document_id: Unique identifier for the document
            url: Optional URL source of the document
            title: Optional title of the document
            chunks: Optional list of text chunks (defaults to empty list)
        
        Raises:
            ValueError: If document_id is empty or None
        """
        if not document_id:
            raise ValueError("Document ID cannot be empty or None")
        
        self.id = document_id
        self.url = url
        self.title = title
        self.chunks = chunks or []  # Fix: avoid mutable default argument

    def to_dict(self) -> Dict[str, str]:
        """
        Convert document to dictionary representation.
        
        Returns:
            Dictionary containing document metadata and concatenated content
            
        Note:
            Chunks are joined with double newlines for readability
        """
        document_dict = {
            "id": self.id,
            "content": "\n\n".join([chunk.content for chunk in self.chunks]),
        }
        
        # Add optional fields only if they exist and are not empty
        if self.url:
            document_dict["url"] = self.url
        if self.title:
            document_dict["title"] = self.title
            
        return document_dict


class Resource(BaseModel):
    """
    Represents a resource available for retrieval and querying.
    
    Resources define the available data sources that can be queried
    for document retrieval in RAG applications.
    """

    uri: str = Field(..., description="The URI of the resource")
    title: str = Field(..., description="The title of the resource")
    description: Optional[str] = Field(
        default="", 
        description="The description of the resource"
    )


class Retriever(abc.ABC):
    """
    Abstract base class for Retrieval-Augmented Generation (RAG) providers.
    
    Defines the interface for querying documents and listing available resources.
    Implementations should handle the specifics of connecting to and querying
    different knowledge bases or document stores.
    """

    @abc.abstractmethod
    def list_resources(self, query: Optional[str] = None) -> List[Resource]:
        """
        List available resources from the RAG provider.
        
        Args:
            query: Optional query string to filter resources
            
        Returns:
            List of Resource objects representing available data sources
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        pass

    @abc.abstractmethod
    def query_relevant_documents(
        self, 
        query: str, 
        resources: Optional[List[Resource]] = None
    ) -> List[Document]:
        """
        Query and retrieve relevant documents from specified resources.
        
        Args:
            query: Search query string for document retrieval
            resources: Optional list of resources to search within.
                      If None, searches all available resources.
                      
        Returns:
            List of Document objects ranked by relevance to the query
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
            ValueError: If query is empty or None
        """
        pass
