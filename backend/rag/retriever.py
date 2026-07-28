from __future__ import annotations

import os
from pathlib import Path
from typing import List

from langchain_chroma import Chroma
from langchain_core.documents import Document

from backend.rag.embedding import EmbeddingFactory


class RAGRetriever:
    def __init__(self) -> None:
        root = Path(__file__).resolve().parents[2]
        persist_dir = os.getenv("CHROMA_PERSIST_DIR", str(root / "data" / "chroma"))
        collection_name = os.getenv("CHROMA_COLLECTION_NAME", "automotive_docs")

        self.vector_store = Chroma(
            collection_name=collection_name,
            persist_directory=persist_dir,
            embedding_function=EmbeddingFactory.get_embeddings(),
        )

    def retrieve(self, query: str, k: int = 4) -> List[Document]:
        retriever = self.vector_store.as_retriever(search_kwargs={"k": k})
        return retriever.invoke(query)
