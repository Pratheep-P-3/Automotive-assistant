"""
RAG Retriever for Automotive Diagnostics.

Retrieves documents from ChromaDB with:
- Metadata filtering by category
- Top K semantic search
- Detailed logging
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document

from backend.rag.embedding import EmbeddingFactory

logger = logging.getLogger(__name__)


class RAGRetriever:
    """Retrieves documents from ChromaDB with metadata filtering."""

    def __init__(self) -> None:
        """Initialize RAG Retriever and connect to ChromaDB."""
        root = Path(__file__).resolve().parents[2]
        configured_persist_dir = os.getenv("CHROMA_PERSIST_DIR", str(root / "data" / "chroma"))
        persist_path = Path(configured_persist_dir)
        persist_dir = persist_path if persist_path.is_absolute() else (root / persist_path)
        collection_name = os.getenv("CHROMA_COLLECTION_NAME", "automotive_docs")

        logger.info("[CHROMA] Initializing RAGRetriever")
        logger.info(f"[CHROMA] Persist directory: {persist_dir}")
        logger.info(f"[CHROMA] Collection name: {collection_name}")

        self.vector_store = None
        try:
            embeddings = EmbeddingFactory.get_embeddings()
            self.vector_store = Chroma(
                collection_name=collection_name,
                persist_directory=str(persist_dir),
                embedding_function=embeddings,
            )
            logger.info("[CHROMA] ✓ Successfully initialized Chroma database")

            # Try to get collection info
            if hasattr(self.vector_store, "_collection"):
                count = self.vector_store._collection.count()
                logger.info(f"[CHROMA] Database contains {count} documents")
        except Exception as exc:
            logger.exception("[CHROMA] ✗ FAILED to initialize Chroma retriever: %s", exc)

    def retrieve(self, query: str, k: int = 10, metadata_filter: dict[str, Any] | None = None) -> list[Document]:
        """
        Retrieve documents from ChromaDB.

        Workflow:
        1. Apply metadata filter (if provided)
        2. Semantic search with top K
        3. Return ranked results with scores

        Args:
            query: User query
            k: Number of documents to retrieve (default: 10 for re-ranking)
            metadata_filter: Metadata filter dict (e.g., {"category": "obd"})

        Returns:
            List of Document objects with metadata
        """
        if self.vector_store is None:
            logger.error("[CHROMA] Cannot retrieve - vector_store is None (initialization failed)")
            return []

        if not query or not isinstance(query, str):
            logger.warning("[CHROMA] Invalid query provided")
            return []

        try:
            logger.info(f"[CHROMA] Retrieving {k} documents for query: '{query[:60]}...'")
            if metadata_filter:
                logger.info(f"[CHROMA] Using metadata filter: {metadata_filter}")

            # Create retriever with metadata filter
            retriever = self.vector_store.as_retriever(
                search_kwargs={
                    "k": k,
                    "filter": metadata_filter,  # Metadata filtering
                    "fetch_k": k * 2,  # Fetch more candidates for better relevance
                }
            )

            results = retriever.invoke(query)

            logger.info(f"[CHROMA] Retrieved {len(results)} documents")

            # Log retrieval results
            if results:
                for i, doc in enumerate(results):
                    source = doc.metadata.get("source", "unknown")
                    category = doc.metadata.get("category", "unknown")
                    chunk_type = doc.metadata.get("chunk_type", "unknown")
                    logger.debug(
                        f"[CHROMA]   Doc {i+1}: source={source}, category={category}, type={chunk_type}"
                    )
            else:
                logger.warning(f"[CHROMA] No documents found for query with filter: {metadata_filter}")

            return results

        except Exception as exc:
            logger.exception(f"[CHROMA] Error during retrieval: {exc}")
            return []

