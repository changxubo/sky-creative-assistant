import json
from typing import Dict, List, Optional

import aiohttp
import requests
from langchain_community.utilities.tavily_search import TAVILY_API_URL
from langchain_community.utilities.tavily_search import (
    TavilySearchAPIWrapper as OriginalTavilySearchAPIWrapper,
)


class EnhancedTavilySearchAPIWrapper(OriginalTavilySearchAPIWrapper):
    """
    Enhanced wrapper for Tavily Search API with additional functionality.

    Extends the original TavilySearchAPIWrapper to provide raw results access,
    asynchronous search capabilities, and improved result formatting with image support.
    Includes better error handling and validation for robust API interactions.
    """

    def raw_results(
        self,
        query: str,
        max_results: Optional[int] = 5,
        search_depth: Optional[str] = "advanced",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        include_answer: Optional[bool] = False,
        include_raw_content: Optional[bool] = False,
        include_images: Optional[bool] = False,
        include_image_descriptions: Optional[bool] = False,
    ) -> Dict:
        """
        Get raw search results from Tavily Search API.

        Args:
            query: Search query string
            max_results: Maximum number of results to return (default: 5)
            search_depth: Search depth level - 'basic' or 'advanced' (default: 'advanced')
            include_domains: List of domains to include in search results
            exclude_domains: List of domains to exclude from search results
            include_answer: Whether to include AI-generated answer (default: False)
            include_raw_content: Whether to include raw HTML content (default: False)
            include_images: Whether to include image results (default: False)
            include_image_descriptions: Whether to include image descriptions (default: False)

        Returns:
            Dict: Raw JSON response from Tavily API containing search results

        Raises:
            ValueError: If query is empty or None
            requests.HTTPError: If API request fails
        """
        # Validate input parameters
        if not query or not query.strip():
            raise ValueError("Query cannot be empty or None")

        # Set default values for list parameters to avoid mutable defaults
        if include_domains is None:
            include_domains = []
        if exclude_domains is None:
            exclude_domains = []

        # Build API request parameters
        api_params = {
            "api_key": self.tavily_api_key.get_secret_value(),
            "query": query.strip(),
            "max_results": max_results,
            "search_depth": search_depth,
            "include_domains": include_domains,
            "exclude_domains": exclude_domains,
            "include_answer": include_answer,
            "include_raw_content": include_raw_content,
            "include_images": include_images,
            "include_image_descriptions": include_image_descriptions,
        }

        try:
            # Make API request with proper error handling
            response = requests.post(
                f"{TAVILY_API_URL}/search",
                json=api_params,
                timeout=30,  # Add timeout to prevent hanging requests
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Tavily API request failed: {str(e)}") from e

    async def raw_results_async(
        self,
        query: str,
        max_results: Optional[int] = 5,
        search_depth: Optional[str] = "advanced",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        include_answer: Optional[bool] = False,
        include_raw_content: Optional[bool] = False,
        include_images: Optional[bool] = False,
        include_image_descriptions: Optional[bool] = False,
    ) -> Dict:
        """
        Get search results from Tavily Search API asynchronously.

        Args:
            query: Search query string
            max_results: Maximum number of results to return (default: 5)
            search_depth: Search depth level - 'basic' or 'advanced' (default: 'advanced')
            include_domains: List of domains to include in search results
            exclude_domains: List of domains to exclude from search results
            include_answer: Whether to include AI-generated answer (default: False)
            include_raw_content: Whether to include raw HTML content (default: False)
            include_images: Whether to include image results (default: False)
            include_image_descriptions: Whether to include image descriptions (default: False)

        Returns:
            Dict: Raw JSON response from Tavily API containing search results

        Raises:
            ValueError: If query is empty or None
            Exception: If API request fails with detailed error information
        """
        # Validate input parameters
        if not query or not query.strip():
            raise ValueError("Query cannot be empty or None")

        # Set default values for list parameters to avoid mutable defaults
        if include_domains is None:
            include_domains = []
        if exclude_domains is None:
            exclude_domains = []

        async def _fetch_search_results() -> str:
            """
            Internal function to perform the asynchronous API call.

            Returns:
                str: JSON response as string from the API

            Raises:
                Exception: If HTTP request fails with status code and reason
            """
            # Build API request parameters
            api_params = {
                "api_key": self.tavily_api_key.get_secret_value(),
                "query": query.strip(),
                "max_results": max_results,
                "search_depth": search_depth,
                "include_domains": include_domains,
                "exclude_domains": exclude_domains,
                "include_answer": include_answer,
                "include_raw_content": include_raw_content,
                "include_images": include_images,
                "include_image_descriptions": include_image_descriptions,
            }

            # Use connection timeout and read timeout for robustness
            timeout = aiohttp.ClientTimeout(total=30, connect=10)

            async with aiohttp.ClientSession(
                trust_env=True, timeout=timeout
            ) as session:
                async with session.post(
                    f"{TAVILY_API_URL}/search", json=api_params
                ) as response:
                    if response.status == 200:
                        response_text = await response.text()
                        return response_text
                    else:
                        # Provide detailed error information
                        error_text = (
                            await response.text()
                            if response.content_length
                            else "No error details"
                        )
                        raise Exception(
                            f"Tavily API request failed with status {response.status}: "
                            f"{response.reason}. Details: {error_text}"
                        )

        try:
            # Execute the async API call and parse JSON response
            results_json_str = await _fetch_search_results()
            return json.loads(results_json_str)
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse API response as JSON: {str(e)}") from e
        except Exception as e:
            # Re-raise with context if it's already our custom exception
            if "Tavily API request failed" in str(e):
                raise
            raise Exception(f"Unexpected error during async search: {str(e)}") from e

    def clean_results_with_images(
        self, raw_results: Dict[str, List[Dict]]
    ) -> List[Dict]:
        """
        Clean and format search results from Tavily Search API, including images.

        Transforms raw API response into a standardized format with separate
        entries for web pages and images. Each result includes essential metadata
        like title, URL, content, and relevance score.

        Args:
            raw_results: Raw response dictionary from Tavily API containing
                        'results' (web pages) and 'images' (image results) keys

        Returns:
            List[Dict]: Cleaned results list with standardized format:
                       - Web pages: type='page', title, url, content, score, raw_content (optional)
                       - Images: type='image', image_url, image_description

        Raises:
            KeyError: If expected keys ('results', 'images') are missing from raw_results
            TypeError: If raw_results is not a dictionary
        """
        # Validate input parameter
        if not isinstance(raw_results, dict):
            raise TypeError("raw_results must be a dictionary")

        if "results" not in raw_results:
            raise KeyError("'results' key missing from raw_results")

        cleaned_results = []

        # Process web page results
        web_results = raw_results["results"]
        for result in web_results:
            # Build clean result with required fields
            clean_result = {
                "type": "page",
                "title": result.get("title", ""),  # Handle missing title gracefully
                "url": result.get("url", ""),  # Handle missing URL gracefully
                "content": result.get(
                    "content", ""
                ),  # Handle missing content gracefully
                "score": result.get("score", 0.0),  # Default score if missing
            }

            # Add raw content if available (optional field)
            if raw_content := result.get("raw_content"):
                clean_result["raw_content"] = raw_content

            cleaned_results.append(clean_result)

        # Process image results if they exist
        if "images" in raw_results and raw_results["images"]:
            image_results = raw_results["images"]
            for image in image_results:
                clean_image_result = {
                    "type": "image",
                    "image_url": image.get("url", ""),  # Handle missing URL gracefully
                    "image_description": image.get(
                        "description", ""
                    ),  # Handle missing description
                }
                cleaned_results.append(clean_image_result)

        return cleaned_results
