"""
RAG Provider Builder Module.

This module provides functionality to build and configure RAG (Retrieval-Augmented Generation)
providers based on environment configuration. It acts as a factory for creating different
types of retriever instances.
"""

import logging
from typing import Optional

from src.config.tools import SELECTED_RAG_PROVIDER, RAGProvider
from src.rag.ragflow import RAGFlowProvider
from src.rag.types import Retriever
from src.rag.vikingdb_kb import VikingDBKnowledgeBaseProvider

# Configure logging for this module
logger = logging.getLogger(__name__)


def build_retriever() -> Optional[Retriever]:
    """
    Build and return a RAG provider instance based on configuration.

    This function acts as a factory method that creates the appropriate RAG provider
    instance based on the SELECTED_RAG_PROVIDER environment variable. It supports
    multiple RAG providers and handles configuration validation.

    Returns:
        Optional[Retriever]: An instance of the configured RAG provider, or None if
                           no provider is configured.

    Raises:
        ValueError: If an unsupported RAG provider is specified in configuration.

    Examples:
        >>> retriever = build_retriever()
        >>> if retriever:
        ...     documents = retriever.query_relevant_documents("search query")
    """
    # Log the selected RAG provider for debugging
    logger.info(f"Building RAG retriever with provider: {SELECTED_RAG_PROVIDER}")

    # Handle case where no RAG provider is configured
    if not SELECTED_RAG_PROVIDER:
        logger.warning("No RAG provider configured. Returning None.")
        return None

    # Build RAGFlow provider
    if SELECTED_RAG_PROVIDER == RAGProvider.RAGFLOW.value:
        logger.info("Initializing RAGFlow provider")
        try:
            return RAGFlowProvider()
        except Exception as e:
            logger.error(f"Failed to initialize RAGFlow provider: {e}")
            raise

    # Build VikingDB Knowledge Base provider
    elif SELECTED_RAG_PROVIDER == RAGProvider.VIKINGDB_KNOWLEDGE_BASE.value:
        logger.info("Initializing VikingDB Knowledge Base provider")
        try:
            return VikingDBKnowledgeBaseProvider()
        except Exception as e:
            logger.error(f"Failed to initialize VikingDB Knowledge Base provider: {e}")
            raise

    # Handle unsupported RAG provider
    else:
        available_providers = [provider.value for provider in RAGProvider]
        error_msg = (
            f"Unsupported RAG provider: '{SELECTED_RAG_PROVIDER}'. "
            f"Supported providers are: {', '.join(available_providers)}"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
