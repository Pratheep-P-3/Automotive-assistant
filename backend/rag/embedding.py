"""
Embedding Factory for Automotive Diagnostics RAG.

Azure OpenAI Only (text-embedding-3-small) - No fallback.
Requires Azure deployment configured in environment.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class EmbeddingFactory:
    """Factory for creating Azure OpenAI embedding models with singleton caching."""

    AZURE_OPENAI_MODEL = "text-embedding-3-small"
    
    # Singleton cache - store embedding instance to avoid repeated initialization
    _embedding_instance: Any | None = None

    @staticmethod
    def get_embeddings() -> Any:
        """
        Get Azure OpenAI embedding model (singleton-cached).

        Azure OpenAI is REQUIRED. No fallback models.

        Returns:
            AzureOpenAIEmbeddings instance

        Raises:
            ValueError: If Azure is not configured or initialization fails
        """
        # Return cached instance if available
        if EmbeddingFactory._embedding_instance is not None:
            logger.debug("[EmbeddingFactory] Returning cached Azure OpenAI embeddings instance")
            return EmbeddingFactory._embedding_instance

        # Initialize Azure OpenAI (required, no fallback)
        try:
            instance = EmbeddingFactory._get_azure_openai_embeddings()
            EmbeddingFactory._embedding_instance = instance
            logger.info("[EmbeddingFactory] ✓ Cached Azure OpenAI embeddings instance")
            return instance
        except Exception as exc:
            logger.exception("[EmbeddingFactory] ✗ FAILED to initialize Azure OpenAI embeddings (no fallback available)")
            raise ValueError(
                "Azure OpenAI embeddings configuration failed. Ensure AZURE_OPENAI_* environment variables are set correctly."
            ) from exc

    @staticmethod
    def clear_cache() -> None:
        """Clear cached embedding instance (for testing/cleanup)."""
        EmbeddingFactory._embedding_instance = None
        logger.info("[EmbeddingFactory] Cleared cached Azure OpenAI embeddings instance")

    @staticmethod
    def _get_azure_openai_embeddings() -> Any:
        """
        Initialize Azure OpenAI Embeddings.

        Environment variables:
        - AZURE_OPENAI_API_KEY
        - AZURE_OPENAI_ENDPOINT
        - AZURE_OPENAI_API_VERSION (default: 2024-02-15-preview)
        - AZURE_OPENAI_EMBEDDING_DEPLOYMENT (e.g., "text-embedding-3-small")

        Returns:
            AzureOpenAIEmbeddings instance

        Raises:
            ImportError: If langchain-openai not installed
            ValueError: If required environment variables missing
            Exception: If API initialization fails
        """
        try:
            from langchain_openai import AzureOpenAIEmbeddings
        except ImportError as exc:
            raise ImportError(
                "langchain-openai not installed. Install with: pip install langchain-openai"
            ) from exc

        try:
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
            api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

            if not all([api_key, endpoint, deployment]):
                raise ValueError(
                    "Missing required Azure OpenAI environment variables: "
                    "AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
                )

            logger.info(
                f"[EmbeddingFactory] Initializing Azure OpenAI embeddings "
                f"(model={EmbeddingFactory.AZURE_OPENAI_MODEL}, deployment={deployment})"
            )

            embeddings = AzureOpenAIEmbeddings(
                api_key=api_key,
                azure_endpoint=endpoint,
                azure_deployment=deployment,
                api_version=api_version,
                model=EmbeddingFactory.AZURE_OPENAI_MODEL,
            )

            logger.info("[EmbeddingFactory] ✓ Azure OpenAI embeddings initialized successfully")
            return embeddings

        except Exception as exc:
            logger.exception("[EmbeddingFactory] ✗ Failed to initialize Azure OpenAI embeddings")
            raise

