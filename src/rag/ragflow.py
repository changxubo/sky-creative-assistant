import os
from urllib.parse import urlparse
from typing import Optional, List, Dict, Tuple, Any

import requests

from src.rag.types import Chunk, Document, Resource, Retriever


class RAGFlowError(Exception):
    """Custom exception for RAGFlow-related errors."""
    pass


class RAGFlowProvider(Retriever):
    """
    RAGFlowProvider is a document retrieval provider that interfaces with RAGFlow API.
    
    This provider enables querying documents and listing resources from RAGFlow,
    a RAG (Retrieval-Augmented Generation) system for document management and retrieval.
    
    Attributes:
        api_url (str): The base URL for the RAGFlow API
        api_key (str): Authentication key for API access
        page_size (int): Number of results to return per page (default: 10)
    """

    def __init__(self) -> None:
        """
        Initialize the RAGFlowProvider with configuration from environment variables.
        
        Raises:
            ValueError: If required environment variables are not set
        """
        # Validate and set API URL
        api_url = os.getenv("RAGFLOW_API_URL")
        if not api_url:
            raise ValueError("RAGFLOW_API_URL environment variable is not set")
        self.api_url = api_url.rstrip('/')  # Remove trailing slash for consistency

        # Validate and set API key
        api_key = os.getenv("RAGFLOW_API_KEY")
        if not api_key:
            raise ValueError("RAGFLOW_API_KEY environment variable is not set")
        self.api_key = api_key

        # Set page size with validation
        page_size_str = os.getenv("RAGFLOW_PAGE_SIZE")
        if page_size_str:
            try:
                page_size = int(page_size_str)
                if page_size <= 0:
                    raise ValueError("RAGFLOW_PAGE_SIZE must be a positive integer")
                self.page_size = page_size
            except ValueError as e:
                raise ValueError(f"Invalid RAGFLOW_PAGE_SIZE: {e}")
        else:
            self.page_size = 10

    def query_relevant_documents(
        self, query: str, resources: Optional[List[Resource]] = None
    ) -> List[Document]:
        """
        Query relevant documents from RAGFlow based on the provided query and resources.
        
        Args:
            query (str): The search query to find relevant documents
            resources (Optional[List[Resource]]): List of resources to search within.
                                                If None or empty, searches all available resources.
        
        Returns:
            List[Document]: A list of documents with relevant chunks
        
        Raises:
            RAGFlowError: If the API request fails or returns an error
            ValueError: If the query is empty or invalid
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        # Use empty list if resources is None to avoid mutable default argument
        if resources is None:
            resources = []

        # Prepare request headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Extract dataset and document IDs from resources
        dataset_ids: List[str] = []
        document_ids: List[str] = []

        for resource in resources:
            try:
                dataset_id, document_id = _parse_resource_uri(resource.uri)
                dataset_ids.append(dataset_id)
                if document_id:  # Only add non-empty document IDs
                    document_ids.append(document_id)
            except ValueError as e:
                # Log warning but continue processing other resources
                print(f"Warning: Skipping invalid resource URI {resource.uri}: {e}")

        # Prepare API payload
        payload = {
            "question": query.strip(),
            "dataset_ids": dataset_ids,
            "document_ids": document_ids,
            "page_size": self.page_size,
        }

        try:
            # Make API request
            response = requests.post(
                f"{self.api_url}/api/v1/retrieval", 
                headers=headers, 
                json=payload,
                timeout=30  # Add timeout for better error handling
            )

            if response.status_code != 200:
                raise RAGFlowError(
                    f"API request failed with status {response.status_code}: {response.text}"
                )

            result = response.json()
            
        except requests.exceptions.RequestException as e:
            raise RAGFlowError(f"Network error occurred: {e}")
        except ValueError as e:
            raise RAGFlowError(f"Invalid JSON response: {e}")

        # Parse response and build documents
        return self._parse_documents_response(result)

    def list_resources(self, query: Optional[str] = None) -> List[Resource]:
        """
        List available resources (datasets) from RAGFlow.
        
        Args:
            query (Optional[str]): Optional filter query to search for specific resources by name
        
        Returns:
            List[Resource]: A list of available resources
        
        Raises:
            RAGFlowError: If the API request fails or returns an error
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Prepare query parameters
        params: Dict[str, str] = {}
        if query and query.strip():
            params["name"] = query.strip()

        try:
            # Make API request
            response = requests.get(
                f"{self.api_url}/api/v1/datasets", 
                headers=headers, 
                params=params,
                timeout=30  # Add timeout for better error handling
            )

            if response.status_code != 200:
                raise RAGFlowError(
                    f"API request failed with status {response.status_code}: {response.text}"
                )

            result = response.json()
            
        except requests.exceptions.RequestException as e:
            raise RAGFlowError(f"Network error occurred: {e}")
        except ValueError as e:
            raise RAGFlowError(f"Invalid JSON response: {e}")

        # Parse response and build resources
        resources = []
        data_items = result.get("data", [])
        
        for item in data_items:
            if not isinstance(item, dict):
                continue  # Skip invalid items
                
            item_id = item.get("id")
            if not item_id:
                continue  # Skip items without ID
                
            resource = Resource(
                uri=f"rag://dataset/{item_id}",
                title=item.get("name", ""),
                description=item.get("description", ""),
            )
            resources.append(resource)

        return resources

    def _parse_documents_response(self, result: Dict[str, Any]) -> List[Document]:
        """
        Parse the API response and convert it to Document objects.
        
        Args:
            result (Dict[str, Any]): The JSON response from the API
        
        Returns:
            List[Document]: A list of parsed documents
        """
        data = result.get("data", {})
        if not isinstance(data, dict):
            return []

        doc_aggs = data.get("doc_aggs", [])
        if not isinstance(doc_aggs, list):
            return []

        # Build document dictionary from aggregated data
        docs: Dict[str, Document] = {}
        for doc_data in doc_aggs:
            if not isinstance(doc_data, dict):
                continue
                
            doc_id = doc_data.get("doc_id")
            if not doc_id:
                continue
                
            docs[doc_id] = Document(
                id=doc_id,
                title=doc_data.get("doc_name", ""),
                chunks=[],
            )

        # Add chunks to documents
        chunks_data = data.get("chunks", [])
        if isinstance(chunks_data, list):
            for chunk_data in chunks_data:
                if not isinstance(chunk_data, dict):
                    continue
                    
                document_id = chunk_data.get("document_id")
                if not document_id or document_id not in docs:
                    continue
                    
                content = chunk_data.get("content", "")
                similarity = chunk_data.get("similarity", 0.0)
                
                # Validate chunk data
                if isinstance(content, str) and isinstance(similarity, (int, float)):
                    chunk = Chunk(content=content, similarity=float(similarity))
                    docs[document_id].chunks.append(chunk)

        return list(docs.values())


def _parse_resource_uri(uri: str) -> Tuple[str, str]:
    """
    Parse a resource URI to extract dataset ID and document ID.
    
    Args:
        uri (str): The resource URI in format "rag://dataset/{dataset_id}#{document_id}"
    
    Returns:
        Tuple[str, str]: A tuple containing (dataset_id, document_id)
                        document_id may be empty string if not specified
    
    Raises:
        ValueError: If the URI format is invalid
    """
    if not uri:
        raise ValueError("URI cannot be empty")
    
    try:
        parsed = urlparse(uri)
    except Exception as e:
        raise ValueError(f"Failed to parse URI: {e}")
    
    if parsed.scheme != "rag":
        raise ValueError(f"Invalid URI scheme: expected 'rag', got '{parsed.scheme}'")
    
    if not parsed.path:
        raise ValueError("URI path cannot be empty")
    
    # Split path and extract dataset ID
    path_parts = parsed.path.strip('/').split('/')
    if len(path_parts) < 2 or path_parts[0] != "dataset":
        raise ValueError("Invalid URI format: expected 'rag://dataset/{dataset_id}'")
    
    dataset_id = path_parts[1]
    if not dataset_id:
        raise ValueError("Dataset ID cannot be empty")
    
    # Extract document ID from fragment (optional)
    document_id = parsed.fragment or ""
    
    return dataset_id, document_id
