import json
import os
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import requests
from volcengine.auth.SignerV4 import SignerV4
from volcengine.base.Request import Request
from volcengine.Credentials import Credentials

from src.rag.types import Chunk, Document, Resource, Retriever


class VikingDBKnowledgeBaseProvider(Retriever):
    """
    VikingDB Knowledge Base Provider for document retrieval.
    
    This provider interfaces with VikingDB's Knowledge Base API to retrieve relevant 
    documents based on queries. It handles authentication, request signing, and 
    document parsing from the VikingDB service.
    
    Attributes:
        api_url (str): The VikingDB API base URL
        api_ak (str): Access key for VikingDB authentication
        api_sk (str): Secret key for VikingDB authentication
        retrieval_size (int): Maximum number of documents to retrieve per query
    """

    def __init__(self) -> None:
        """
        Initialize the VikingDB Knowledge Base Provider.
        
        Loads configuration from environment variables and validates required settings.
        
        Raises:
            ValueError: If required environment variables are not set
        """
        # Load and validate API URL
        api_url = os.getenv("VIKINGDB_KNOWLEDGE_BASE_API_URL")
        if not api_url:
            raise ValueError("VIKINGDB_KNOWLEDGE_BASE_API_URL environment variable is not set")
        self.api_url = api_url

        # Load and validate access key
        api_ak = os.getenv("VIKINGDB_KNOWLEDGE_BASE_API_AK")
        if not api_ak:
            raise ValueError("VIKINGDB_KNOWLEDGE_BASE_API_AK environment variable is not set")
        self.api_ak = api_ak

        # Load and validate secret key
        api_sk = os.getenv("VIKINGDB_KNOWLEDGE_BASE_API_SK")
        if not api_sk:
            raise ValueError("VIKINGDB_KNOWLEDGE_BASE_API_SK environment variable is not set")
        self.api_sk = api_sk

        # Load optional retrieval size configuration
        retrieval_size = os.getenv("VIKINGDB_KNOWLEDGE_BASE_RETRIEVAL_SIZE")
        self.retrieval_size = int(retrieval_size) if retrieval_size else 10

    def prepare_request(self, method: str, path: str, params: Optional[dict] = None, 
                       data: Optional[dict] = None, doseq: int = 0) -> Request:
        """
        Prepare a signed request using VikingDB volcengine authentication.
        
        Args:
            method (str): HTTP method (GET, POST, etc.)
            path (str): API endpoint path
            params (Optional[dict]): Query parameters
            data (Optional[dict]): Request body data
            doseq (int): Parameter for handling list serialization
            
        Returns:
            Request: Signed request object ready for execution
        """
        # Process parameters to ensure proper string formatting
        if params:
            for key in params:
                param_value = params[key]
                if isinstance(param_value, (int, float, bool)):
                    params[key] = str(param_value)
                elif isinstance(param_value, list):
                    if not doseq:
                        params[key] = ",".join(param_value)

        # Create and configure the request object
        request = Request()
        request.set_shema("https")  # Use HTTPS for security
        request.set_method(method)
        request.set_connection_timeout(10)
        request.set_socket_timeout(10)
        
        # Set standard headers for JSON communication
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        request.set_headers(headers)
        
        # Add query parameters if provided
        if params:
            request.set_query(params)
        
        request.set_path(path)
        
        # Add request body if provided
        if data is not None:
            request.set_body(json.dumps(data))

        # Sign the request with VikingDB credentials
        credentials = Credentials(self.api_ak, self.api_sk, "air", "cn-north-1")
        SignerV4.sign(request, credentials)
        
        return request

    def query_relevant_documents(self, query: str, resources: List[Resource] = None) -> List[Document]:
        """
        Query relevant documents from the VikingDB knowledge base.
        
        Args:
            query (str): Search query string
            resources (List[Resource], optional): List of resources to search within.
                                                Defaults to empty list if None.
            
        Returns:
            List[Document]: List of relevant documents with their chunks
            
        Raises:
            ValueError: If API response is invalid or contains errors
        """
        # Handle None resources parameter
        if resources is None:
            resources = []
            
        # Return empty list if no resources provided
        if not resources:
            return []

        # Validate query input
        if not query or not query.strip():
            raise ValueError("Query cannot be empty or None")

        all_documents = {}
        
        # Process each resource to retrieve relevant documents
        for resource in resources:
            try:
                resource_id, document_id = parse_uri(resource.uri)
            except ValueError as e:
                # Skip invalid URIs and continue with other resources
                continue
                
            # Build request parameters for VikingDB API
            request_params = {
                "resource_id": resource_id,
                "query": query.strip(),
                "limit": self.retrieval_size,
                "dense_weight": 0.5,
                "pre_processing": {
                    "need_instruction": True,
                    "rewrite": False,
                    "return_token_usage": True,
                },
                "post_processing": {
                    "rerank_switch": True,
                    "chunk_diffusion_count": 0,
                    "chunk_group": True,
                    "get_attachment_link": True,
                },
            }
            
            # Add document filter if specific document ID is provided
            if document_id:
                document_filter = {"op": "must", "field": "doc_id", "conds": [document_id]}
                query_param = {"doc_filter": document_filter}
                request_params["query_param"] = query_param

            # Prepare and execute the API request
            method = "POST"
            path = "/api/knowledge/collection/search_knowledge"
            signed_request = self.prepare_request(method=method, path=path, data=request_params)
            
            # Execute the HTTP request
            response = requests.request(
                method=signed_request.method,
                url=f"https://{self.api_url}{signed_request.path}",  # Use HTTPS
                headers=signed_request.headers,
                data=signed_request.body,
                timeout=30  # Add timeout for reliability
            )

            # Parse and validate JSON response
            try:
                response_data = response.json()
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse JSON response: {e}")

            # Check for API errors
            if response_data.get("code") != 0:
                raise ValueError(f"API error: {response_data.get('message', 'Unknown error')}")

            response_payload = response_data.get("data", {})

            # Skip resources with no results
            if "result_list" not in response_payload:
                continue

            result_list = response_payload["result_list"]

            # Process each result item
            for item in result_list:
                document_info = item.get("doc_info", {})
                document_id = document_info.get("doc_id")

                # Skip items without document ID
                if not document_id:
                    continue

                # Create document if not already exists
                if document_id not in all_documents:
                    all_documents[document_id] = Document(
                        id=document_id, 
                        title=document_info.get("doc_name", "Unknown Document"), 
                        chunks=[]
                    )

                # Create and add chunk to document
                chunk = Chunk(
                    content=item.get("content", ""), 
                    similarity=item.get("score", 0.0)
                )
                all_documents[document_id].chunks.append(chunk)

        return list(all_documents.values())

    def list_resources(self, query: Optional[str] = None) -> List[Resource]:
        """
        List available resources (knowledge bases) from the VikingDB service.
        
        Args:
            query (Optional[str]): Optional filter query to match collection names.
                                 Only collections containing this query will be returned.
                                 Case-insensitive matching.
            
        Returns:
            List[Resource]: List of available resources matching the query filter
            
        Raises:
            ValueError: If API response parsing fails
            RuntimeError: If API returns an error response
        """
        method = "POST"
        path = "/api/knowledge/collection/list"
        
        # Prepare and execute the API request
        signed_request = self.prepare_request(method=method, path=path)
        
        response = requests.request(
            method=signed_request.method,
            url=f"https://{self.api_url}{signed_request.path}",  # Use HTTPS
            headers=signed_request.headers,
            data=signed_request.body,
            timeout=30  # Add timeout for reliability
        )
        
        # Parse and validate JSON response
        try:
            response_data = response.json()
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}")

        # Check for API errors
        if response_data.get("code") != 0:
            error_message = response_data.get("message", "Unknown error")
            raise RuntimeError(f"Failed to list resources: {error_message}")

        resources = []
        response_payload = response_data.get("data", {})
        collection_list = response_payload.get("collection_list", [])
        
        # Process each collection in the response
        for collection_item in collection_list:
            collection_name = collection_item.get("collection_name", "")
            description = collection_item.get("description", "")

            # Apply query filter if provided
            if query and query.strip():
                if query.lower() not in collection_name.lower():
                    continue

            resource_id = collection_item.get("resource_id", "")
            
            # Skip collections without resource ID
            if not resource_id:
                continue
                
            # Create resource object
            resource = Resource(
                uri=f"rag://dataset/{resource_id}",
                title=collection_name,
                description=description,
            )
            resources.append(resource)

        return resources


def parse_uri(uri: str) -> Tuple[str, str]:
    """
    Parse a RAG URI to extract resource ID and document ID.
    
    Args:
        uri (str): URI in format 'rag://dataset/{resource_id}#{document_id}'
                  The document_id part (after #) is optional.
    
    Returns:
        Tuple[str, str]: A tuple containing (resource_id, document_id).
                        document_id will be empty string if not present in URI.
    
    Raises:
        ValueError: If URI format is invalid or scheme is not 'rag'
    """
    if not uri:
        raise ValueError("URI cannot be empty or None")
        
    try:
        parsed_uri = urlparse(uri)
    except Exception as e:
        raise ValueError(f"Invalid URI format: {uri}") from e
        
    if parsed_uri.scheme != "rag":
        raise ValueError(f"Invalid URI scheme. Expected 'rag', got '{parsed_uri.scheme}'")
    
    # Extract resource ID from path (skip the first '/' character)
    path_parts = parsed_uri.path.lstrip('/').split('/')
    if len(path_parts) < 2 or path_parts[0] != "dataset":
        raise ValueError(f"Invalid URI path format. Expected '/dataset/{{resource_id}}', got '{parsed_uri.path}'")
    
    resource_id = path_parts[1]
    document_id = parsed_uri.fragment  # Fragment is the part after '#'
    
    return resource_id, document_id
