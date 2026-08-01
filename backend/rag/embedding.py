"""
Embedding Factory for Automotive Diagnostics RAG.

Supports both Azure OpenAI and HuggingFace embeddings.
Priority: Azure OpenAI (text-embedding-3-small) > HuggingFace fallback
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class EmbeddingFactory:
    """Factory for creating embedding models."""

    AZURE_OPENAI_MODEL = "text-embedding-3-small"
    HUGGINGFACE_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

    @staticmethod
    def get_embeddings() -> Any:
        """
        Get embedding model.

        Priority:
        1. Azure OpenAI (if configured)
        2. HuggingFace (fallback)

        Returns:
            Embedding model instance (AzureOpenAIEmbeddings or HuggingFaceEmbeddings)

        Raises:
            ValueError: If no valid embedding service is available
        """
        # Try Azure OpenAI first
        if EmbeddingFactory._is_azure_configured():
            try:
                return EmbeddingFactory._get_azure_openai_embeddings()
            except Exception as exc:
                logger.warning(f"[EmbeddingFactory] Azure OpenAI initialization failed: {exc}")
                logger.info("[EmbeddingFactory] Falling back to HuggingFace")

        # Fall back to HuggingFace
        try:
            return EmbeddingFactory._get_huggingface_embeddings()
        except Exception as exc:
            logger.exception(f"[EmbeddingFactory] ✗ FAILED to initialize any embedding model: {exc}")
            raise ValueError(
                "No valid embedding service available. Configure Azure OpenAI or ensure HuggingFace is installed."
            ) from exc

    @staticmethod
    def _is_azure_configured() -> bool:
        """
        Check if Azure OpenAI is configured.

        Required environment variables:
        - AZURE_OPENAI_API_KEY
        - AZURE_OPENAI_ENDPOINT
        - AZURE_OPENAI_EMBEDDING_DEPLOYMENT

        Returns:
            True if all required Azure vars are present
        """
        required_vars = [
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
        ]
        configured = all(os.getenv(var) for var in required_vars)
        if configured:
            logger.info("[EmbeddingFactory] Azure OpenAI is configured")
        return configured

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

    @staticmethod
    def _get_huggingface_embeddings() -> Any:
        """
        Initialize HuggingFace Embeddings.

        Environment variables:
        - EMBEDDING_MODEL (default: sentence-transformers/all-MiniLM-L6-v2)

        Returns:
            HuggingFaceEmbeddings instance

        Raises:
            ImportError: If langchain-huggingface not installed
            Exception: If model initialization fails
        """
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError as exc:
            raise ImportError(
                "langchain-huggingface not installed. Install with: pip install langchain-huggingface"
            ) from exc

        try:
            model_name = os.getenv("EMBEDDING_MODEL", EmbeddingFactory.HUGGINGFACE_MODEL)

            logger.info(f"[EmbeddingFactory] Initializing HuggingFace embeddings (model={model_name})")

            embeddings = HuggingFaceEmbeddings(model_name=model_name)

            logger.info("[EmbeddingFactory] ✓ HuggingFace embeddings initialized successfully")
            return embeddings

        except Exception as exc:
            logger.exception("[EmbeddingFactory] ✗ Failed to initialize HuggingFace embeddings")
            raise

