"""
RAG Retriever for Automotive Diagnostics.

Retrieves documents from ChromaDB with:
- Metadata filtering by category
- Configurable top K retrieval
- Vector similarity scores (when available)
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
    """Retrieves documents from ChromaDB with metadata filtering and score tracking."""

    def __init__(self) -> None:
        """Initialize RAG Retriever and connect to ChromaDB."""
        root = Path(__file__).resolve().parents[2]
        configured_persist_dir = os.getenv("CHROMA_PERSIST_DIR", str(root / "data" / "chroma"))
        persist_path = Path(configured_persist_dir)
        persist_dir = persist_path if persist_path.is_absolute() else (root / persist_path)
        collection_name = os.getenv("CHROMA_COLLECTION_NAME", "automotive_docs")

        # Configurable retrieval parameters for small dataset
        # Default: retrieve 5, rerank to 3 (appropriate for 9-document dataset)
        self.retrieval_k = int(os.getenv("RETRIEVAL_K", "5"))
        self.rerank_top_k = int(os.getenv("RERANK_TOP_K", "3"))

        logger.info("[CHROMA] Initializing RAGRetriever")
        logger.info(f"[CHROMA] Persist directory: {persist_dir}")
        logger.info(f"[CHROMA] Collection name: {collection_name}")
        logger.info(f"[CHROMA] Retrieval parameters: retrieve_k={self.retrieval_k}, rerank_top_k={self.rerank_top_k}")

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

    def retrieve(self, query: str, k: int | None = None, metadata_filter: dict[str, Any] | None = None) -> list[Document]:
        """
        Retrieve documents from ChromaDB.

        Workflow:
        1. Apply metadata filter (if provided)
        2. Semantic search with configurable top K
        3. Capture vector similarity scores
        4. Return ranked results with scores in metadata

        Args:
            query: User query
            k: Number of documents to retrieve (default: RETRIEVAL_K from env, typically 5)
            metadata_filter: Metadata filter dict (e.g., {"category": "obd"})

        Returns:
            List of Document objects with vector scores in metadata
        """
        if k is None:
            k = self.retrieval_k

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

            # Use Chroma's similarity search which returns scores
            # Note: Chroma returns scores as distances (lower = better), we'll normalize to similarity
            results_with_scores = self.vector_store.similarity_search_with_score(
                query=query,
                k=k,
                filter=metadata_filter,
            )

            # Transform results to include vector scores in metadata
            results = []
            for doc, vector_score in results_with_scores:
                # Chroma returns distance scores, convert to similarity (0-1 scale)
                # Distance range typically 0-2, convert to similarity: similarity = 1 - (distance / 2)
                similarity_score = max(0, 1 - (vector_score / 2)) if vector_score >= 0 else 0.5
                
                # Add vector score to metadata for later use
                doc.metadata["vector_score"] = float(similarity_score)
                doc.metadata["vector_distance"] = float(vector_score)
                results.append(doc)

            logger.info(f"[CHROMA] Retrieved {len(results)} documents")

            # Log retrieval results with vector scores
            if results:
                for i, doc in enumerate(results):
                    source = doc.metadata.get("source", "unknown")
                    category = doc.metadata.get("category", "unknown")
                    chunk_type = doc.metadata.get("chunk_type", "unknown")
                    vector_score = doc.metadata.get("vector_score", 0)
                    logger.debug(
                        f"[CHROMA]   Doc {i+1}: source={source}, category={category}, type={chunk_type}, "
                        f"vector_score={vector_score:.3f}"
                    )
            else:
                logger.warning(f"[CHROMA] No documents found for query with filter: {metadata_filter}")

            return results

        except Exception as exc:
            logger.exception(f"[CHROMA] Error during retrieval: {exc}")
            return []

