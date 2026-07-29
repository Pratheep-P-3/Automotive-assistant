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

        self.vector_store = None
        try:
            self.vector_store = Chroma(
                collection_name=collection_name,
                persist_directory=str(persist_dir),
                embedding_function=EmbeddingFactory.get_embeddings(),
            )
        except Exception as exc:
            logger.exception(
                "Failed to initialize Chroma retriever. RAG lookups will be skipped: %s",
                exc,
            )

    def retrieve(self, query: str, k: int = 4) -> List[Document]:
        if self.vector_store is None:
            return []
        retriever = self.vector_store.as_retriever(search_kwargs={"k": k})
        return retriever.invoke(query)
