from typing import Optional

# Third-party imports
from readabilipy import simple_json_from_html_string

# Local imports
from .article import Article


class ReadabilityExtractor:
    """
    A class for extracting readable content from HTML using the readabilipy library.
    
    This extractor uses Mozilla's Readability algorithm to extract the main content
    from web pages, filtering out navigation, ads, and other non-essential elements.
    """
    
    def extract_article(self, html_content: str, base_url: Optional[str] = None) -> Article:
        """
        Extract an Article object from raw HTML content using readability parsing.
        
        This method processes HTML content to extract the main article content,
        title, and other relevant information while filtering out boilerplate content.
        
        Args:
            html_content (str): The raw HTML content to extract from
            base_url (Optional[str]): The base URL for resolving relative links.
                                    Defaults to None.
        
        Returns:
            Article: An Article object containing the extracted title and content
            
        Raises:
            ValueError: If html_content is None, empty, or not a string
            RuntimeError: If readability extraction fails or returns invalid data
        """
        # Input validation
        if not html_content or not isinstance(html_content, str):
            raise ValueError("html_content must be a non-empty string")
        
        if html_content.strip() == "":
            raise ValueError("html_content cannot be empty or whitespace only")
        
        try:
            # Extract content using readabilipy with readability algorithm
            extracted_data = simple_json_from_html_string(
                html_content, 
                use_readability=True
            )
            
            # Validate extracted data structure
            if not isinstance(extracted_data, dict):
                raise RuntimeError("Readability extraction returned invalid data format")
            
            # Extract title with fallback handling
            article_title = extracted_data.get("title", "").strip()
            if not article_title:
                article_title = "Untitled Article"  # Fallback for missing titles
            
            # Extract content with validation
            article_content = extracted_data.get("content", "").strip()
            if not article_content:
                raise RuntimeError("No readable content found in HTML")
            
            # Create and return Article object
            return Article(
                title=article_title,
                html_content=article_content,
                url=base_url or ""  # Pass base URL if provided
            )
            
        except Exception as extraction_error:
            # Re-raise ValueError and RuntimeError as-is
            if isinstance(extraction_error, (ValueError, RuntimeError)):
                raise
            
            # Wrap other exceptions in RuntimeError with context
            raise RuntimeError(
                f"Failed to extract article from HTML: {str(extraction_error)}"
            ) from extraction_error
