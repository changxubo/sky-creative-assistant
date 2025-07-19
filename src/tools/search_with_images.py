import json
from typing import Any, Dict, List, Optional, Tuple, Union

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain_community.tools.tavily_search.tool import TavilySearchResults
from pydantic import Field

from src.tools.search_wrapper import (
    EnhancedTavilySearchAPIWrapper,
)


class TavilySearchResultsWithImages(TavilySearchResults):  # type: ignore[override, override]
    """Enhanced Tavily Search tool that includes image search capabilities.

    This class extends the base TavilySearchResults to support image search
    functionality, including image descriptions. It provides both synchronous
    and asynchronous search capabilities with comprehensive result formatting.

    Attributes:
        include_image_descriptions (bool): Whether to include image descriptions
            in the search results. Default is False.
        api_wrapper (EnhancedTavilySearchAPIWrapper): The API wrapper instance
            used to interact with the Tavily Search API.

    Example:
        >>> tool = TavilySearchResultsWithImages(
        ...     max_results=5,
        ...     include_answer=True,
        ...     include_raw_content=True,
        ...     include_images=True,
        ...     include_image_descriptions=True
        ... )
        >>> results = tool.invoke({'query': 'latest AI developments'})

    Setup:
        Install ``langchain-openai`` and ``tavily-python``, and set environment variable ``TAVILY_API_KEY``.

        .. code-block:: bash

            pip install -U langchain-community tavily-python
            export TAVILY_API_KEY="your-api-key"

    Instantiate:

        .. code-block:: python

            from langchain_community.tools import TavilySearchResults

            tool = TavilySearchResults(
                max_results=5,
                include_answer=True,
                include_raw_content=True,
                include_images=True,
                include_image_descriptions=True,
                # search_depth="advanced",
                # include_domains = []
                # exclude_domains = []
            )

    Invoke directly with args:

        .. code-block:: python

            tool.invoke({'query': 'who won the last french open'})

        .. code-block:: json

            {
                "url": "https://www.nytimes.com...",
                "content": "Novak Djokovic won the last French Open by beating Casper Ruud ..."
            }

    Invoke with tool call:

        .. code-block:: python

            tool.invoke({"args": {'query': 'who won the last french open'}, "type": "tool_call", "id": "foo", "name": "tavily"})

        .. code-block:: python

            ToolMessage(
                content='{ "url": "https://www.nytimes.com...", "content": "Novak Djokovic won the last French Open by beating Casper Ruud ..." }',
                artifact={
                    'query': 'who won the last french open',
                    'follow_up_questions': None,
                    'answer': 'Novak ...',
                    'images': [
                        'https://www.amny.com/wp-content/uploads/2023/06/AP23162622181176-1200x800.jpg',
                        ...
                        ],
                    'results': [
                        {
                            'title': 'Djokovic ...',
                            'url': 'https://www.nytimes.com...',
                            'content': "Novak...",
                            'score': 0.99505633,
                            'raw_content': 'Tennis\nNovak ...'
                        },
                        ...
                    ],
                    'response_time': 2.92
                },
                tool_call_id='1',
                name='tavily_search_results_json',
            )

    """  # noqa: E501

    include_image_descriptions: bool = False
    """Include image descriptions in the search response.

    When set to True, the API will attempt to provide descriptions for
    images found in search results. Default is False for performance optimization.
    """

    api_wrapper: EnhancedTavilySearchAPIWrapper = Field(
        default_factory=EnhancedTavilySearchAPIWrapper
    )  # type: ignore[arg-type]

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Tuple[Union[List[Dict[str, Any]], str], Dict[str, Any]]:
        """Execute synchronous search query using Tavily API.

        Args:
            query (str): The search query string to execute
            run_manager (Optional[CallbackManagerForToolRun]): Callback manager
                for tool execution monitoring

        Returns:
            Tuple[Union[List[Dict[str, Any]], str], Dict[str, Any]]: A tuple containing:
                - Cleaned search results or error message string
                - Raw API response dictionary

        Raises:
            Exception: Re-raises any exceptions from the API wrapper as string representation
        """
        # Validate input query
        if not query or not query.strip():
            error_msg = "Search query cannot be empty or whitespace only"
            return error_msg, {}

        try:
            # Execute search with all configured parameters
            raw_results = self.api_wrapper.raw_results(
                query,
                self.max_results,
                self.search_depth,
                self.include_domains,
                self.exclude_domains,
                self.include_answer,
                self.include_raw_content,
                self.include_images,
                self.include_image_descriptions,
            )
        except Exception as e:
            # Return string representation of exception for debugging
            return repr(e), {}

        # Process and clean the raw results
        cleaned_results = self.api_wrapper.clean_results_with_images(raw_results)

        # Debug output for synchronous execution
        #print("sync", json.dumps(cleaned_results, indent=2, ensure_ascii=False))

        return cleaned_results, raw_results

    async def _arun(
        self,
        query: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> Tuple[Union[List[Dict[str, Any]], str], Dict[str, Any]]:
        """Execute asynchronous search query using Tavily API.

        Args:
            query (str): The search query string to execute
            run_manager (Optional[AsyncCallbackManagerForToolRun]): Async callback
                manager for tool execution monitoring

        Returns:
            Tuple[Union[List[Dict[str, Any]], str], Dict[str, Any]]: A tuple containing:
                - Cleaned search results or error message string
                - Raw API response dictionary

        Raises:
            Exception: Re-raises any exceptions from the API wrapper as string representation
        """
        # Validate input query
        if not query or not query.strip():
            error_msg = "Search query cannot be empty or whitespace only"
            return error_msg, {}

        try:
            # Execute async search with all configured parameters
            raw_results = await self.api_wrapper.raw_results_async(
                query,
                self.max_results,
                self.search_depth,
                self.include_domains,
                self.exclude_domains,
                self.include_answer,
                self.include_raw_content,
                self.include_images,
                self.include_image_descriptions,
            )
        except Exception as e:
            # Return string representation of exception for debugging
            return repr(e), {}

        # Process and clean the raw results
        cleaned_results = self.api_wrapper.clean_results_with_images(raw_results)

        # Debug output for asynchronous execution
        #print("async", json.dumps(cleaned_results, indent=2, ensure_ascii=False))

        return cleaned_results, raw_results
