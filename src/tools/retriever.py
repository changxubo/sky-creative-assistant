"""
Retriever tool module for local knowledge base search functionality.

This module provides a LangChain-compatible tool for searching and retrieving
documents from local RAG (Retrieval-Augmented Generation) providers. The tool
enables AI agents to search through indexed documents using natural language
queries.
"""

import logging
from typing import List, Optional, Type, Union

from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, validator

from src.config.tools import SELECTED_RAG_PROVIDER
from src.rag import Document, Retriever, Resource, build_retriever

logger = logging.getLogger(__name__)


class RetrieverInput(BaseModel):
    """
    Input schema for the retriever tool.
    
    Defines the expected input structure for document retrieval queries.
    """
    
    keywords: str = Field(
        description="Search keywords to look up in the local knowledge base. "
                   "Should be descriptive terms related to the information needed."
    )
    
    @validator('keywords')
    def validate_keywords(cls, value: str) -> str:
        """
        Validate that keywords are not empty or just whitespace.
        
        Args:
            value: The keywords string to validate
            
        Returns:
            str: The validated keywords string
            
        Raises:
            ValueError: If keywords are empty or just whitespace
        """
        if not value or not value.strip():
            raise ValueError("Keywords cannot be empty or just whitespace")
        return value.strip()


class RetrieverTool(BaseTool):
    """
    LangChain tool for retrieving information from local knowledge base.
    
    This tool searches through indexed documents using RAG providers and returns
    relevant document chunks. It prioritizes local search over web search or
    code generation for document-based queries.
    """
    
    name: str = "local_search_tool"
    description: str = (
        "Searches for information in the local knowledge base using RAG providers. "
        "Useful for retrieving information from files with 'rag://' URI prefix. "
        "This tool should have higher priority than web search or code generation "
        "when dealing with document-based queries. Input should be descriptive "
        "search keywords related to the information needed."
    )
    args_schema: Type[BaseModel] = RetrieverInput

    retriever: Retriever = Field(default_factory=Retriever)
    resources: List[Resource] = Field(default_factory=list)

    def _run(
        self,
        keywords: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Union[List[dict], str]:
        """
        Execute synchronous document retrieval.
        
        Args:
            keywords: Search terms to query against the knowledge base
            run_manager: Optional callback manager for monitoring tool execution
            
        Returns:
            Union[List[dict], str]: List of document dictionaries if found,
                                   or error message string if no results
        """
        if not keywords or not keywords.strip():
            logger.warning("Empty keywords provided to retriever tool")
            return "No keywords provided for search."
            
        logger.info(
            f"Executing retriever tool query with keywords: '{keywords}'",
            extra={
                "resources_count": len(self.resources),
                "rag_provider": SELECTED_RAG_PROVIDER
            }
        )
        
        try:
            documents = self.retriever.query_relevant_documents(keywords, self.resources)
            
            if not documents:
                logger.info(f"No documents found for query: '{keywords}'")
                return "No results found from the local knowledge base."
                
            logger.info(f"Found {len(documents)} documents for query: '{keywords}'")
            return [doc.to_dict() for doc in documents]
            
        except Exception as e:
            logger.error(f"Error during document retrieval: {str(e)}", exc_info=True)
            return f"Error occurred during search: {str(e)}"

    async def _arun(
        self,
        keywords: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> Union[List[dict], str]:
        """
        Execute asynchronous document retrieval.
        
        Args:
            keywords: Search terms to query against the knowledge base
            run_manager: Optional async callback manager for monitoring tool execution
            
        Returns:
            Union[List[dict], str]: List of document dictionaries if found,
                                   or error message string if no results
        """
        # Convert async callback manager to sync if available, otherwise pass None
        sync_manager = run_manager.get_sync() if run_manager else None
        return self._run(keywords, sync_manager)


def get_retriever_tool(resources: List[Resource]) -> Optional[RetrieverTool]:
    """
    Factory function to create a configured RetrieverTool instance.
    
    Args:
        resources: List of Resource objects to search through. If empty,
                  returns None as the tool would have nothing to search.
                  
    Returns:
        Optional[RetrieverTool]: Configured retriever tool instance if resources
                                are provided and retriever can be built, None otherwise
    """
    if not resources:
        logger.warning("No resources provided, cannot create retriever tool")
        return None
        
    logger.info(
        f"Creating retriever tool with {len(resources)} resources using provider: {SELECTED_RAG_PROVIDER}"
    )
    
    try:
        retriever = build_retriever()
        
        if not retriever:
            logger.error("Failed to build retriever instance")
            return None
            
        return RetrieverTool(retriever=retriever, resources=resources)
        
    except Exception as e:
        logger.error(f"Error creating retriever tool: {str(e)}", exc_info=True)
        return None
