from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import List

from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.rag.embedding import EmbeddingFactory

logger = logging.getLogger(__name__)


def _load_txt_documents(directories: List[Path]) -> List[Document]:
    """Load ONLY TXT documents (structured reference materials) from directories."""
    documents: List[Document] = []
    total_files = 0
    
    for directory in directories:
        if not directory.exists():
            logger.warning("[TXT] Directory not found: %s", directory)
            continue
        
        # Load ONLY TXT files (the authoritative source)
        txt_files = list(directory.glob("*.txt"))
        if txt_files:
            for txt_path in txt_files:
                try:
                    loader = TextLoader(str(txt_path), encoding="utf-8")
                    docs = loader.load()
                    documents.extend(docs)
                    total_files += 1
                    logger.info("[TXT] ✓ Loaded %s", txt_path.name)
                except Exception as exc:
                    logger.exception("[TXT] ✗ FAILED to load %s: %s", txt_path, exc)
        else:
            logger.warning("[TXT] No TXT files found in %s", directory)
    
    logger.info("[TXT] Total files loaded: %d", total_files)
    return documents


def ingest_documents() -> int:
    root = Path(__file__).resolve().parents[2]
    troubleshooting_dir = root / "data" / "troubleshooting"
    maintenance_dir = root / "data" / "maintenance"
    obd_dir = root / "data" / "obd"
    evaluation_dir = root / "data" / "evaluation"

    persist_dir = Path(
        os.getenv("CHROMA_PERSIST_DIR", str(root / "data" / "chroma"))
    )
    collection_name = os.getenv("CHROMA_COLLECTION_NAME", "automotive_docs")

    # CLEAR OLD DATABASE to prevent duplicates
    # Since we switched to TXT-only, start fresh
    if persist_dir.exists():
        import shutil
        logger.info("[CLEANUP] Removing old ChromaDB database...")
        try:
            shutil.rmtree(persist_dir)
            logger.info("[CLEANUP] ✓ Old database removed")
        except Exception as exc:
            logger.warning("[CLEANUP] Could not remove old database: %s", exc)
    
    logger.info("[INGESTION] Loading TXT documents from data directories...")
    raw_documents = _load_txt_documents([troubleshooting_dir, maintenance_dir, obd_dir, evaluation_dir])
    
    if not raw_documents:
        logger.error("[INGESTION] ✗ NO TXT DOCUMENTS FOUND!")
        logger.error("[INGESTION] Place TXT reference files in:")
        logger.error("  - data/troubleshooting/")
        logger.error("  - data/maintenance/")
        logger.error("  - data/obd/")
        logger.error("  - data/evaluation/")
        return 0

    logger.info("[INGESTION] Splitting %d documents into chunks...", len(raw_documents))
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    chunks = splitter.split_documents(raw_documents)
    
    logger.info("[INGESTION] Creating Chroma database at %s", persist_dir)
    Chroma.from_documents(
        documents=chunks,
        embedding=EmbeddingFactory.get_embeddings(),
        collection_name=collection_name,
        persist_directory=str(persist_dir),
    )

    logger.info("[INGESTION] ✓✓✓ COMPLETE - Indexed %d chunks into Chroma database", len(chunks))
    logger.info("[INGESTION] ✓✓✓ Using TXT files ONLY (no PDFs, no CSVs)")
    return len(chunks)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    indexed = ingest_documents()
    print(f"Indexed chunks: {indexed}")
