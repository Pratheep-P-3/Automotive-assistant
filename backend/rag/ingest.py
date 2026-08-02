"""
Ingestion pipeline for Automotive Diagnostics RAG.

Loads TXT documents, adds metadata, applies document-aware chunking,
and indexes into ChromaDB with Azure OpenAI embeddings.
"""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import Any

from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document

from backend.rag.document_chunker import DocumentAwareChunker
from backend.rag.embedding import EmbeddingFactory

logger = logging.getLogger(__name__)


def _load_txt_documents(data_dirs: dict[str, Path]) -> list[Document]:
    """
    Load TXT documents with metadata from categorized directories.

    Supports both flat structure (data/obd/*.txt) and brand-specific structure:
    - data/obd/generic/*.txt → make=None, model=None
    - data/obd/toyota/*.txt → make=toyota, model=None
    - data/obd/honda/*.txt → make=honda, model=None

    Args:
        data_dirs: Dict of {category: directory_path}
                  e.g., {"obd": Path("data/obd"), "maintenance": Path("data/maintenance")}

    Returns:
        List of Document objects with metadata including make/model
    """
    documents: list[Document] = []
    total_files = 0

    for category, directory in data_dirs.items():
        if not directory.exists():
            logger.warning(f"[INGESTION] Directory not found: {directory}")
            continue

        # Check for brand-specific subdirectories first
        subdirs = list(directory.iterdir())
        
        # Try to load from subdirectories (brand-specific structure)
        brand_dirs = [d for d in subdirs if d.is_dir() and d.name not in ["__pycache__", ".git"]]
        txt_in_root = list(directory.glob("*.txt"))
        
        if brand_dirs:
            # Brand-specific structure exists
            for brand_dir in sorted(brand_dirs):
                make = brand_dir.name.lower() if brand_dir.name != "generic" else None
                txt_files = sorted(brand_dir.glob("*.txt"))
                
                for txt_path in txt_files:
                    try:
                        loader = TextLoader(str(txt_path), encoding="utf-8")
                        docs = loader.load()

                        # Add metadata including make/model
                        for doc in docs:
                            doc.metadata = {
                                "source": txt_path.name,
                                "category": category,
                                "file_path": str(txt_path),
                                "make": make,
                                "model": None,  # Can be extended for model-specific docs later
                            }
                            documents.append(doc)

                        total_files += 1
                        make_label = f" (make: {make})" if make else " (generic)"
                        logger.info(f"[INGESTION] ✓ Loaded {txt_path.name} (category: {category}){make_label}")
                    except Exception as exc:
                        logger.exception(f"[INGESTION] ✗ FAILED to load {txt_path}: {exc}")
        
        elif txt_in_root:
            # Flat structure (backward compatibility)
            logger.info(f"[INGESTION] Using flat structure for {category} (no brand subdirs detected)")
            for txt_path in txt_in_root:
                try:
                    loader = TextLoader(str(txt_path), encoding="utf-8")
                    docs = loader.load()

                    # Add metadata without make/model (generic)
                    for doc in docs:
                        doc.metadata = {
                            "source": txt_path.name,
                            "category": category,
                            "file_path": str(txt_path),
                            "make": None,
                            "model": None,
                        }
                        documents.append(doc)

                    total_files += 1
                    logger.info(f"[INGESTION] ✓ Loaded {txt_path.name} (category: {category}, generic)")
                except Exception as exc:
                    logger.exception(f"[INGESTION] ✗ FAILED to load {txt_path}: {exc}")
        else:
            logger.warning(f"[INGESTION] No TXT files found in {directory}")

    logger.info(f"[INGESTION] Total files loaded: {total_files}")
    return documents


def ingest_documents() -> int:
    """
    Main ingestion pipeline.

    Steps:
    1. Load TXT documents with metadata
    2. Apply document-aware chunking
    3. Index into ChromaDB

    Returns:
        Number of chunks indexed
    """
    root = Path(__file__).resolve().parents[2]

    # Define categorized data directories
    data_dirs = {
        "obd": root / "data" / "obd",
        "maintenance": root / "data" / "maintenance",
        "symptom": root / "data" / "troubleshooting",
        "evaluation": root / "data" / "evaluation",
    }

    persist_dir = Path(os.getenv("CHROMA_PERSIST_DIR", str(root / "data" / "chroma")))
    collection_name = os.getenv("CHROMA_COLLECTION_NAME", "automotive_docs")

    # ===== STEP 1: Clear old database =====
    logger.info("[INGESTION] ===== Clearing old database =====")
    if persist_dir.exists():
        try:
            shutil.rmtree(persist_dir)
            logger.info("[INGESTION] ✓ Old ChromaDB cleared")
        except Exception as exc:
            logger.warning(f"[INGESTION] Could not remove old database: {exc}")

    # ===== STEP 2: Load documents with metadata =====
    logger.info("[INGESTION] ===== Loading TXT documents =====")
    raw_documents = _load_txt_documents(data_dirs)

    if not raw_documents:
        logger.error("[INGESTION] ✗ NO TXT DOCUMENTS FOUND!")
        logger.error("[INGESTION] Place TXT reference files in:")
        for cat, path in data_dirs.items():
            logger.error(f"  - {path} (category: {cat})")
        return 0

    logger.info(f"[INGESTION] Total documents loaded: {len(raw_documents)}")

    # ===== STEP 3: Apply document-aware chunking =====
    logger.info("[INGESTION] ===== Document-Aware Chunking =====")
    chunker = DocumentAwareChunker()
    chunks = chunker.chunk_documents(raw_documents)

    logger.info(f"[INGESTION] Chunks created: {len(chunks)}")

    # Log chunk distribution by category
    chunk_counts_by_category = {}
    for chunk in chunks:
        category = chunk.metadata.get("category", "unknown")
        chunk_counts_by_category[category] = chunk_counts_by_category.get(category, 0) + 1

    logger.info("[INGESTION] Chunk distribution by category:")
    for category, count in sorted(chunk_counts_by_category.items()):
        logger.info(f"  - {category}: {count} chunks")

    # ===== STEP 4: Index into ChromaDB with Azure OpenAI embeddings =====
    logger.info("[INGESTION] ===== Indexing into ChromaDB =====")
    logger.info(f"[INGESTION] Creating Chroma database at {persist_dir}")

    try:
        embeddings = EmbeddingFactory.get_embeddings()
        logger.info("[INGESTION] ✓ Embeddings initialized")

        Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            collection_name=collection_name,
            persist_directory=str(persist_dir),
        )

        logger.info(f"[INGESTION] ✓✓✓ COMPLETE - Indexed {len(chunks)} chunks into Chroma database")
        logger.info(f"[INGESTION] Collection name: {collection_name}")
        logger.info("[INGESTION] Using TXT files ONLY with document-aware chunking")

        return len(chunks)

    except Exception as exc:
        logger.exception(f"[INGESTION] ✗ FAILED to index documents: {exc}")
        return 0


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    )
    indexed = ingest_documents()
    print(f"\nIndexed chunks: {indexed}")

