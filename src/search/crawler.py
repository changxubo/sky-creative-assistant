import logging
from typing import Optional

from .article import Article
from .jina_client import JinaClient
from .extractor import ReadabilityExtractor

logger = logging.getLogger(__name__)


class WebCrawler:
    """
    A web crawler that extracts clean, readable articles from web pages.

    This crawler uses Jina AI's reader service to fetch HTML content and
    the readability library to extract clean article content. The extracted
    content is optimized for LLM consumption by providing structured,
    markdown-formatted text.
    """

    def __init__(self) -> None:
        """
        Initialize the WebCrawler with required clients.
        """
        self._jina_client = JinaClient()
        self._readability_extractor = ReadabilityExtractor()

    def crawl(self, url: str) -> Optional[Article]:
        """
        Crawl a web page and extract its article content.

        This method fetches the HTML content from the given URL using Jina's
        reader service, then extracts clean article content using readability
        algorithms. The result is optimized for LLM processing.

        Args:
            url (str): The URL of the web page to crawl. Must be a valid HTTP/HTTPS URL.

        Returns:
            Optional[Article]: An Article object containing the extracted content,
                             or None if crawling fails.

        Raises:
            ValueError: If the URL is empty or invalid.
            Exception: If crawling or content extraction fails.
        """
        # Validate input URL
        if not url or not isinstance(url, str):
            raise ValueError("URL must be a non-empty string")

        if not url.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")

        try:
            logger.info(f"Starting crawl for URL: {url}")

            # Fetch HTML content using Jina's reader service
            # Jina provides a simple API but may not have the best readability
            # extraction, so we use our own readability processing afterwards
            html_content = self._jina_client.crawl(url, return_format="html")

            if not html_content:
                logger.warning(f"No HTML content received for URL: {url}")
                return None

            # Extract clean article content using readability algorithms
            # This step removes navigation, ads, and other non-content elements
            extracted_article = self._readability_extractor.extract_article(
                html_content
            )

            if not extracted_article:
                logger.warning(f"Failed to extract article content from URL: {url}")
                return None

            # Set the source URL for reference
            extracted_article.url = url

            logger.info(f"Successfully crawled and extracted article from: {url}")
            return extracted_article

        except Exception as crawl_error:
            logger.error(f"Failed to crawl URL {url}: {str(crawl_error)}")
            raise Exception(
                f"Crawling failed for {url}: {str(crawl_error)}"
            ) from crawl_error
