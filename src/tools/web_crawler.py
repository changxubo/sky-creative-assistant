import logging
from typing import Annotated

from langchain_core.tools import tool

from .decorators import log_io
from src.search import WebCrawler

logger = logging.getLogger(__name__)


@tool
@log_io
def crawl_tool(
    url: Annotated[str, "The URL to crawl and extract content from."],
) -> str:
    """
    Crawl a URL and extract readable content in markdown format.
    
    This tool uses a web crawler to fetch and parse content from a given URL,
    returning the extracted text in markdown format for better readability.
    
    Args:
        url (str): The URL to crawl. Must be a valid HTTP/HTTPS URL.
        
    Returns:
        str: JSON string containing the URL and crawled content (truncated to 1000 chars),
             or error message if crawling fails.
             
    Raises:
        Exception: When URL crawling fails due to network issues, invalid URL,
                  or content extraction problems.
    """
    # Validate URL format
    if not url or not isinstance(url, str):
        error_msg = "Invalid URL: URL must be a non-empty string"
        logger.error(error_msg)
        return error_msg
        
    if not (url.startswith('http://') or url.startswith('https://')):
        error_msg = f"Invalid URL format: {url}. URL must start with http:// or https://"
        logger.error(error_msg)
        return error_msg
    
    try:
        logger.info(f"Starting crawl operation for URL: {url}")
        crawler = WebCrawler()
        article = crawler.crawl(url)
        
        # Check if article content exists
        if not article:
            error_msg = f"No content extracted from URL: {url}"
            logger.warning(error_msg)
            return error_msg
            
        # Extract markdown content with safe handling
        markdown_content = article.to_markdown()
        if not markdown_content:
            error_msg = f"Failed to convert content to markdown for URL: {url}"
            logger.warning(error_msg)
            return error_msg
            
        # Truncate content to prevent oversized responses
        max_content_length = 1000
        truncated_content = (
            markdown_content[:max_content_length] 
            if len(markdown_content) > max_content_length 
            else markdown_content
        )
        
        # Create consistent response format
        result = {
            "url": url,
            "crawled_content": truncated_content,
            "content_length": len(markdown_content),
            "truncated": len(markdown_content) > max_content_length
        }
        
        logger.info(f"Successfully crawled URL: {url}, content length: {len(markdown_content)}")
        return str(result)
        
    except (ConnectionError, TimeoutError) as e:
        error_msg = f"Network error while crawling URL {url}: {repr(e)}"
        logger.error(error_msg)
        return error_msg
    except ValueError as e:
        error_msg = f"Invalid content or parsing error for URL {url}: {repr(e)}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error while crawling URL {url}: {repr(e)}"
        logger.error(error_msg)
        return error_msg
