from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import List

from langchain_chroma import Chroma
from langchain_core.documents import Document

from backend.rag.embedding import EmbeddingFactory

logger = logging.getLogger(__name__)


class RAGRetriever:
    def __init__(self) -> None:
        root = Path(__file__).resolve().parents[2]
        configured_persist_dir = os.getenv("CHROMA_PERSIST_DIR", str(root / "data" / "chroma"))
        persist_path = Path(configured_persist_dir)
        persist_dir = persist_path if persist_path.is_absolute() else (root / persist_path)
        collection_name = os.getenv("CHROMA_COLLECTION_NAME", "automotive_docs")

        logger.info(f"[CHROMA] Initializing RAGRetriever")
        logger.info(f"[CHROMA] Persist directory: {persist_dir}")
        logger.info(f"[CHROMA] Collection name: {collection_name}")

        self.vector_store = None
        try:
            self.vector_store = Chroma(
                collection_name=collection_name,
                persist_directory=str(persist_dir),
                embedding_function=EmbeddingFactory.get_embeddings(),
            )
            logger.info(f"[CHROMA] ✓ Successfully initialized Chroma database")
            # Try to get collection info
            if hasattr(self.vector_store, '_collection'):
                count = self.vector_store._collection.count()
                logger.info(f"[CHROMA] Database contains {count} documents")
        except Exception as exc:
            logger.exception(
                "[CHROMA] ✗ FAILED to initialize Chroma retriever: %s",
                exc,
            )

    def retrieve(self, query: str, k: int = 4) -> List[Document]:
        if self.vector_store is None:
            logger.error(f"[CHROMA] Cannot retrieve - vector_store is None (initialization failed)")
            return []
        
        logger.info(f"[CHROMA] Retrieving {k} documents for query: {query}")
        retriever = self.vector_store.as_retriever(search_kwargs={"k": k})
        results = retriever.invoke(query)
        logger.info(f"[CHROMA] Retrieved {len(results)} documents")
        for i, doc in enumerate(results):
            logger.debug(f"[CHROMA]   Doc {i+1}: {doc.page_content[:100]}...")
        return results
