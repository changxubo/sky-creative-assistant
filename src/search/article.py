import re
from typing import Dict, List
from urllib.parse import urljoin

from markdownify import markdownify as md


class Article:
    """
    A class representing an article with HTML content that can be converted to markdown
    and formatted for message consumption.

    Attributes:
        title (str): The title of the article
        html_content (str): The raw HTML content of the article
        url (str): The source URL of the article (optional)
    """

    def __init__(self, title: str, html_content: str, url: str = "") -> None:
        """
        Initialize an Article instance.

        Args:
            title (str): The title of the article
            html_content (str): The HTML content to be processed
            url (str, optional): The source URL of the article. Defaults to empty string.

        Raises:
            ValueError: If title or html_content is None or empty
        """
        if not title or not html_content:
            raise ValueError("Title and html_content cannot be None or empty")

        self.title = title.strip()
        self.html_content = html_content
        self.url = url

    def to_markdown(self, including_title: bool = True) -> str:
        """
        Convert the article's HTML content to markdown format.

        Args:
            including_title (bool): Whether to include the article title as an H1 header.
                                  Defaults to True.

        Returns:
            str: The article content formatted as markdown

        Raises:
            Exception: If markdown conversion fails
        """
        try:
            markdown_content = ""
            if including_title:
                # Add title as H1 header with proper spacing
                markdown_content += f"# {self.title}\n\n"

            # Convert HTML to markdown using markdownify
            converted_content = md(self.html_content)
            if converted_content:
                markdown_content += converted_content

            return markdown_content
        except Exception as e:
            raise Exception(f"Failed to convert HTML to markdown: {str(e)}")

    def to_message(self) -> List[Dict[str, str]]:
        """
        Convert the article to a message format suitable for chat/API consumption.
        Extracts images and text separately for proper message structuring.

        Returns:
            List[Dict[str, str]]: A list of message parts, each containing either:
                                - {"type": "text", "text": "content"}
                                - {"type": "image_url", "image_url": {"url": "image_url"}}

        Raises:
            Exception: If message conversion fails
        """
        try:
            # Regex pattern to match markdown image syntax: ![alt](url)
            image_pattern = r"!\[.*?\]\((.*?)\)"

            message_content: List[Dict[str, str]] = []
            markdown_text = self.to_markdown()

            # Split text by image patterns to separate text and image URLs
            text_parts = re.split(image_pattern, markdown_text)

            for index, part in enumerate(text_parts):
                # Odd indices contain image URLs (captured groups from regex)
                if index % 2 == 1:
                    image_url = part.strip()
                    if image_url:
                        # Convert relative URLs to absolute URLs if base URL is available
                        if self.url and not image_url.startswith(
                            ("http://", "https://")
                        ):
                            image_url = urljoin(self.url, image_url)

                        message_content.append(
                            {"type": "image_url", "image_url": {"url": image_url}}
                        )
                # Even indices contain text content
                else:
                    text_content = part.strip()
                    if text_content:  # Only add non-empty text parts
                        message_content.append({"type": "text", "text": text_content})

            return message_content

        except Exception as e:
            raise Exception(f"Failed to convert article to message format: {str(e)}")
