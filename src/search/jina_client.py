import logging
import os
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class JinaClient:
    """
    A client for interacting with the Jina AI Reader API.
    
    This class provides functionality to crawl web content using Jina's API,
    with support for different return formats and optional API key authentication.
    """
    
    def __init__(self) -> None:
        """Initialize the JinaClient with default configuration."""
        self.base_url = "https://r.jina.ai/"
        self.api_key = os.getenv("JINA_API_KEY")
        
        if not self.api_key:
            logger.warning(
                "Jina API key is not set. Provide your own key to access a higher rate limit. "
                "See https://jina.ai/reader for more information."
            )
    
    def crawl(self, url: str, return_format: str = "html") -> str:
        """
        Crawl a web page using the Jina AI Reader API.
        
        Args:
            url (str): The URL to crawl. Must be a valid HTTP/HTTPS URL.
            return_format (str, optional): The format for the returned content.
                                         Defaults to "html". Other options may include
                                         "markdown", "text", etc.
        
        Returns:
            str: The crawled content in the specified format.
            
        Raises:
            ValueError: If the URL is empty or invalid.
            requests.RequestException: If the API request fails.
            requests.HTTPError: If the API returns an error status code.
        """
        # Input validation
        if not url or not isinstance(url, str):
            raise ValueError("URL must be a non-empty string")
        
        if not url.strip():
            raise ValueError("URL cannot be empty or whitespace")
        
        # Validate URL format (basic check)
        if not (url.startswith("http://") or url.startswith("https://")):
            logger.warning(f"URL '{url}' does not start with http:// or https://")
        
        # Prepare request headers
        headers = {
            "Content-Type": "application/json",
            "X-Return-Format": return_format,
        }
        
        # Add authentication if API key is available
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            logger.debug("Using API key for authentication")
        
        # Prepare request payload
        request_data = {"url": url}
        
        try:
            logger.info(f"Crawling URL: {url} with format: {return_format}")
            
            # Make the API request
            response = requests.post(
                self.base_url, 
                headers=headers, 
                json=request_data,
                timeout=30  # Add timeout to prevent hanging requests
            )
            
            # Check for HTTP errors
            response.raise_for_status()
            
            logger.info(f"Successfully crawled URL: {url}")
            return response.text
            
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout while crawling URL: {url}")
            raise requests.RequestException(f"Request timeout for URL: {url}")
            
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error while crawling URL: {url}")
            raise requests.RequestException(f"Connection error for URL: {url}")
            
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error {response.status_code} while crawling URL: {url}")
            raise requests.HTTPError(f"HTTP {response.status_code} error for URL: {url}") from http_err
            
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Request error while crawling URL: {url} - {str(req_err)}")
            raise requests.RequestException(f"Request failed for URL: {url}") from req_err
