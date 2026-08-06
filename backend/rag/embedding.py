"""
Embedding Factory for Automotive Diagnostics RAG.

Primary: Azure OpenAI (text-embedding-3-small)
Fallback: AllMiniLM-L6-v2 (local, no API key needed)
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
        Get embedding model (singleton-cached).

        Primary: Azure OpenAI (text-embedding-3-small)
        Fallback: AllMiniLM-L6-v2 if Azure unavailable

        Returns:
            Embeddings instance (Azure or AllMiniLM)

        Raises:
            ValueError: If both Azure and AllMiniLM fail
        """
        # Return cached instance if available
        if EmbeddingFactory._embedding_instance is not None:
            logger.debug("[EmbeddingFactory] Returning cached embeddings instance")
            return EmbeddingFactory._embedding_instance

        # Try Azure first
        try:
            instance = EmbeddingFactory._get_azure_openai_embeddings()
            EmbeddingFactory._embedding_instance = instance
            logger.info("[EmbeddingFactory] ✓ Cached Azure OpenAI embeddings instance")
            return instance
        except Exception as azure_exc:
            logger.warning(f"[EmbeddingFactory] Azure OpenAI failed: {azure_exc}")
            logger.info("[EmbeddingFactory] Attempting AllMiniLM-L6-v2 fallback...")
            
            # Fallback to AllMiniLM
            try:
                instance = EmbeddingFactory._get_allminilm_embeddings()
                EmbeddingFactory._embedding_instance = instance
                logger.info("[EmbeddingFactory] ✓ Cached AllMiniLM-L6-v2 fallback embeddings instance")
                return instance
            except Exception as fallback_exc:
                logger.exception("[EmbeddingFactory] ✗ FAILED - Both Azure and AllMiniLM failed")
                raise ValueError(
                    f"Embedding initialization failed:\n"
                    f"  Azure error: {azure_exc}\n"
                    f"  AllMiniLM fallback error: {fallback_exc}"
                ) from fallback_exc

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

            # Test the embeddings with a simple call to validate API key
            logger.info("[EmbeddingFactory] Testing Azure OpenAI API credentials...")
            test_embedding = embeddings.embed_query("test")
            if not test_embedding or len(test_embedding) == 0:
                raise ValueError("Azure embedding test returned empty result")
            logger.info(f"[EmbeddingFactory] ✓ Azure OpenAI API test successful (embedding dimension: {len(test_embedding)})")

            logger.info("[EmbeddingFactory] ✓ Azure OpenAI embeddings initialized successfully")
            return embeddings

        except Exception as exc:
            logger.exception("[EmbeddingFactory] ✗ Failed to initialize Azure OpenAI embeddings")
            raise

    @staticmethod
    def _get_allminilm_embeddings() -> Any:
        """
        Initialize AllMiniLM-L6-v2 embeddings (fallback).

        Uses local sentence-transformers model.
        No API key required. Downloads model on first use (~27MB).

        Returns:
            HuggingFaceEmbeddings instance

        Raises:
            ImportError: If sentence-transformers not installed
            Exception: If model initialization fails
        """
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers not installed. Install with: pip install sentence-transformers"
            ) from exc

        try:
            logger.info(
                "[EmbeddingFactory] Initializing AllMiniLM-L6-v2 fallback embeddings "
                "(local, no API key required)"
            )

            embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={"device": "cpu"}
            )

            logger.info("[EmbeddingFactory] ✓ AllMiniLM-L6-v2 embeddings initialized successfully (fallback mode)")
            return embeddings

        except Exception as exc:
            logger.exception("[EmbeddingFactory] ✗ Failed to initialize AllMiniLM embeddings")
            raise


