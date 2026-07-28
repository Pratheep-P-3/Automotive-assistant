from __future__ import annotations

import os

from langchain_huggingface import HuggingFaceEmbeddings


class EmbeddingFactory:
    @staticmethod
    def get_embeddings() -> HuggingFaceEmbeddings:
        model_name = os.getenv(
            "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        )
        return HuggingFaceEmbeddings(model_name=model_name)
