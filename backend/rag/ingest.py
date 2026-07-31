from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import List

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.rag.embedding import EmbeddingFactory

logger = logging.getLogger(__name__)


def _load_pdfs(directories: List[Path]) -> List[Document]:
    documents: List[Document] = []
    for directory in directories:
        if not directory.exists():
            logger.warning("Directory not found during ingestion: %s", directory)
            continue
        for pdf_path in directory.glob("*.pdf"):
            try:
                loader = PyPDFLoader(str(pdf_path))
                docs = loader.load()
                documents.extend(docs)
                logger.info("Loaded %d pages from %s", len(docs), pdf_path)
            except Exception as exc:
                logger.exception("Failed to load PDF %s: %s", pdf_path, exc)
    return documents


def ingest_documents() -> int:
    root = Path(__file__).resolve().parents[2]
    manuals_dir = root / "data" / "manuals"
    troubleshooting_dir = root / "data" / "troubleshooting"
    maintenance_dir = root / "data" / "maintenance"
    obd_dir = root / "data" / "obd"
    evaluation_dir = root / "data" / "evaluation"

    persist_dir = Path(
        os.getenv("CHROMA_PERSIST_DIR", str(root / "data" / "chroma"))
    )
    collection_name = os.getenv("CHROMA_COLLECTION_NAME", "automotive_docs")

    raw_documents = _load_pdfs([manuals_dir, troubleshooting_dir, maintenance_dir, obd_dir, evaluation_dir])
    if not raw_documents:
        logger.warning(
            "No PDF documents found. Place PDFs under data/manuals or data/troubleshooting."
        )
        return 0

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    chunks = splitter.split_documents(raw_documents)

    Chroma.from_documents(
        documents=chunks,
        embedding=EmbeddingFactory.get_embeddings(),
        collection_name=collection_name,
        persist_directory=str(persist_dir),
    )

    logger.info("Ingestion complete. Indexed %d chunks into %s", len(chunks), persist_dir)
    return len(chunks)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    indexed = ingest_documents()
    print(f"Indexed chunks: {indexed}")
