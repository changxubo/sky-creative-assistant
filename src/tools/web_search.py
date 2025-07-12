"""
Search engine integration module.

This module provides a unified interface for different search engines including
Tavily, DuckDuckGo, Brave Search, and ArXiv. It creates logged versions of
search tools and provides a factory function to get the appropriate search tool
based on configuration.
"""

# Standard library imports
import logging
import os
from typing import Any, Union

# Third-party imports
from langchain_community.tools import BraveSearch, DuckDuckGoSearchResults
from langchain_community.tools.arxiv import ArxivQueryRun
from langchain_community.utilities import ArxivAPIWrapper, BraveSearchWrapper

# Local imports
from src.config import SearchEngine, SELECTED_SEARCH_ENGINE
from src.tools.decorators import create_logged_tool
from src.tools.search_with_images import (
    TavilySearchResultsWithImages,
)

# Constants
DEFAULT_SEARCH_NAME = "web_search"
MIN_SEARCH_RESULTS = 1
MAX_SEARCH_RESULTS = 6

# Configure logger
logger = logging.getLogger(__name__)

# Create logged versions of the search tools with proper naming
LoggedTavilySearchTool = create_logged_tool(TavilySearchResultsWithImages)
LoggedDuckDuckGoSearchTool = create_logged_tool(DuckDuckGoSearchResults)
LoggedBraveSearchTool = create_logged_tool(BraveSearch)
LoggedArxivSearchTool = create_logged_tool(ArxivQueryRun)


def get_web_search_tool(max_search_results: int) -> Any:
    """
    Get the appropriate search tool based on the selected search engine configuration.
    
    This function acts as a factory method that returns the configured search tool
    with logging capabilities. It validates input parameters and handles different
    search engine configurations.
    
    Args:
        max_search_results (int): Maximum number of search results to return.
                                Must be between 1 and 100 (inclusive).
    
    Returns:
        Union[LoggedTavilySearchTool, LoggedDuckDuckGoSearchTool, 
              LoggedBraveSearchTool, LoggedArxivSearchTool]: 
            A logged search tool instance configured for the selected search engine.
    
    Raises:
        ValueError: If max_search_results is outside valid range or if the 
                   selected search engine is not supported.
        EnvironmentError: If required API keys are missing for Brave Search.
    """
    # Input validation
    if not isinstance(max_search_results, int):
        raise ValueError(
            f"max_search_results must be an integer, got {type(max_search_results)}"
        )
    
    if not (MIN_SEARCH_RESULTS <= max_search_results <= MAX_SEARCH_RESULTS):
        raise ValueError(
            f"max_search_results must be between {MIN_SEARCH_RESULTS} and "
            f"{MAX_SEARCH_RESULTS}, got {max_search_results}"
        )
    
    logger.debug(
        f"Creating search tool for engine: {SELECTED_SEARCH_ENGINE}, "
        f"max_results: {max_search_results}"
    )
    
    # Tavily search engine configuration
    if SELECTED_SEARCH_ENGINE == SearchEngine.TAVILY.value:
        return LoggedTavilySearchTool(
            name=DEFAULT_SEARCH_NAME,
            max_results=max_search_results,
            include_raw_content=False,
            include_images=True,
            include_image_descriptions=True,
        )
    
    # DuckDuckGo search engine configuration
    elif SELECTED_SEARCH_ENGINE == SearchEngine.DUCKDUCKGO.value:
        return LoggedDuckDuckGoSearchTool(
            name=DEFAULT_SEARCH_NAME,
            num_results=max_search_results,
        )
    
    # Brave search engine configuration
    elif SELECTED_SEARCH_ENGINE == SearchEngine.BRAVE_SEARCH.value:
        brave_api_key = os.getenv("BRAVE_SEARCH_API_KEY")
        if not brave_api_key:
            raise EnvironmentError(
                "BRAVE_SEARCH_API_KEY environment variable is required for Brave Search"
            )
        
        return LoggedBraveSearchTool(
            name=DEFAULT_SEARCH_NAME,
            search_wrapper=BraveSearchWrapper(
                api_key=brave_api_key,
                search_kwargs={"count": max_search_results},
            ),
        )
    
    # ArXiv search engine configuration
    elif SELECTED_SEARCH_ENGINE == SearchEngine.ARXIV.value:
        return LoggedArxivSearchTool(
            name=DEFAULT_SEARCH_NAME,
            api_wrapper=ArxivAPIWrapper(
                top_k_results=max_search_results,
                load_max_docs=max_search_results,
                load_all_available_meta=True,
            ),
        )
    
    # Unsupported search engine
    else:
        available_engines = [engine.value for engine in SearchEngine]
        raise ValueError(
            f"Unsupported search engine: '{SELECTED_SEARCH_ENGINE}'. "
            f"Available engines: {available_engines}"
        )
