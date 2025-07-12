"""
Tool configuration module for DeerFlow application.

This module defines enumerations for search engines and RAG providers,
along with configuration constants loaded from environment variables.
"""

import enum
import os
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class SearchEngine(enum.Enum):
    """
    Enumeration of supported search engines.

    This enum defines the available search engine options that can be
    configured for the application's search functionality.
    """

    TAVILY = "tavily"
    DUCKDUCKGO = "duckduckgo"
    BRAVE_SEARCH = "brave_search"
    ARXIV = "arxiv"


class RAGProvider(enum.Enum):
    """
    Enumeration of supported RAG (Retrieval-Augmented Generation) providers.

    This enum defines the available RAG provider options for the
    application's knowledge retrieval functionality.
    """

    RAGFLOW = "ragflow"
    VIKINGDB_KNOWLEDGE_BASE = "vikingdb_knowledge_base"


# Tool configuration constants
SELECTED_SEARCH_ENGINE: str = os.getenv("SEARCH_API", SearchEngine.TAVILY.value)
SELECTED_RAG_PROVIDER: Optional[str] = os.getenv("RAG_PROVIDER")
