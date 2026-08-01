"""
RAG Ingestion Validation Utility.

Purpose:
Validate RAG system health after database ingestion or updates.

Checks:
- Total chunk count
- Chunks by category (obd, maintenance, symptom, evaluation)
- Metadata completeness
- Chroma collection contents
- Sample retrieval behavior
- Vector score capture

Run:
    python -m backend.rag.validate_ingestion

Output:
    Detailed validation report with potential issues highlighted
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from langchain_core.documents import Document

from backend.rag.embedding import EmbeddingFactory
from backend.rag.query_classifier import QueryClassifier
from backend.rag.retriever import RAGRetriever

# Configure logging for validation output
logging.basicConfig(
    level=logging.INFO,
    format="[%(name)s] %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def validate_ingestion() -> None:
    """Run complete ingestion validation."""
    logger.info("=" * 70)
    logger.info("RAG INGESTION VALIDATION")
    logger.info("=" * 70)

    # Test 1: Check database existence
    logger.info("\n[TEST 1] Checking ChromaDB Database...")
    test_database_exists()

    # Test 2: Check retriever initialization
    logger.info("\n[TEST 2] Initializing RAG Retriever...")
    retriever = test_retriever_init()

    if not retriever:
        logger.error("✗ Failed to initialize retriever, stopping validation")
        return

    # Test 3: Validate chunk counts
    logger.info("\n[TEST 3] Validating Chunk Counts by Category...")
    test_chunk_distribution(retriever)

    # Test 4: Validate metadata
    logger.info("\n[TEST 4] Validating Metadata Completeness...")
    test_metadata_quality(retriever)

    # Test 5: Test sample retrieval
    logger.info("\n[TEST 5] Testing Sample Retrieval...")
    test_sample_retrieval(retriever)

    # Test 6: Test vector score capture
    logger.info("\n[TEST 6] Testing Vector Score Capture...")
    test_vector_scores(retriever)

    # Test 7: Test configuration
    logger.info("\n[TEST 7] Checking Configuration...")
    test_configuration()

    logger.info("\n" + "=" * 70)
    logger.info("VALIDATION COMPLETE")
    logger.info("=" * 70)


def test_database_exists() -> bool:
    """Test if Chroma database exists and is accessible."""
    root = Path(__file__).resolve().parents[2]
    configured_persist_dir = os.getenv("CHROMA_PERSIST_DIR", str(root / "data" / "chroma"))
    persist_path = Path(configured_persist_dir)
    persist_dir = persist_path if persist_path.is_absolute() else (root / persist_path)

    logger.info(f"[✓] Database path: {persist_dir}")

    if not persist_dir.exists():
        logger.error(f"[✗] Database directory does not exist: {persist_dir}")
        logger.error("[!] Run: python -m backend.rag.ingest")
        return False

    # Check for Chroma files
    chroma_files = list(persist_dir.glob("*"))
    logger.info(f"[✓] Found {len(chroma_files)} files in database directory")

    if len(chroma_files) == 0:
        logger.error("[✗] Database directory is empty")
        return False

    return True


def test_retriever_init() -> RAGRetriever | None:
    """Test retriever initialization."""
    try:
        retriever = RAGRetriever()
        if retriever.vector_store is None:
            logger.error("[✗] Vector store is None after initialization")
            return None

        logger.info("[✓] RAG Retriever initialized successfully")
        return retriever
    except Exception as exc:
        logger.error(f"[✗] Failed to initialize retriever: {exc}")
        return None


def test_chunk_distribution(retriever: RAGRetriever) -> None:
    """Validate chunk distribution by category."""
    try:
        # Query each category to count chunks
        categories = ["obd", "maintenance", "symptom", "evaluation"]
        total_chunks = 0
        distribution = {}

        for category in categories:
            # Use a generic query to retrieve documents in this category
            docs = retriever.retrieve("", k=100, metadata_filter={"category": category})
            count = len(docs)
            distribution[category] = count
            total_chunks += count
            logger.info(f"[✓] Category '{category}': {count} chunks")

        logger.info(f"[✓] TOTAL CHUNKS: {total_chunks}")

        # Validation checks
        if total_chunks == 0:
            logger.error("[✗] No chunks found in database!")
        elif total_chunks < 50:
            logger.warning(f"[!] Low chunk count ({total_chunks}), expected 50+ for robust RAG")
        else:
            logger.info(f"[✓] Healthy chunk count: {total_chunks}")

        # Check for empty categories
        empty_categories = [c for c, count in distribution.items() if count == 0]
        if empty_categories:
            logger.warning(f"[!] Empty categories detected: {empty_categories}")

    except Exception as exc:
        logger.error(f"[✗] Error testing chunk distribution: {exc}")


def test_metadata_quality(retriever: RAGRetriever) -> None:
    """Validate metadata completeness."""
    try:
        # Retrieve sample documents
        docs = retriever.retrieve("", k=10, metadata_filter=None)

        if not docs:
            logger.error("[✗] No documents retrieved for metadata validation")
            return

        logger.info(f"[✓] Retrieved {len(docs)} sample documents")

        # Check metadata fields
        required_metadata = ["source", "category", "chunk_type", "chunk_size"]
        missing_fields = {field: [] for field in required_metadata}

        for i, doc in enumerate(docs):
            for field in required_metadata:
                if field not in doc.metadata:
                    missing_fields[field].append(i)

        # Report missing metadata
        for field, docs_missing in missing_fields.items():
            if docs_missing:
                logger.warning(f"[!] Missing '{field}' in {len(docs_missing)} documents")
            else:
                logger.info(f"[✓] All documents have '{field}'")

        # Show metadata example
        if docs:
            logger.info(f"\n[Sample Metadata from Doc 0]:")
            for key, value in docs[0].metadata.items():
                logger.info(f"  {key}: {value}")

    except Exception as exc:
        logger.error(f"[✗] Error testing metadata: {exc}")


def test_sample_retrieval(retriever: RAGRetriever) -> None:
    """Test retrieval with various queries."""
    sample_queries = [
        ("P0300", {"category": "obd"}),
        ("oil change", {"category": "maintenance"}),
        ("engine misfire", {"category": "symptom"}),
    ]

    for query, metadata_filter in sample_queries:
        try:
            docs = retriever.retrieve(query, k=3, metadata_filter=metadata_filter)
            category = metadata_filter.get("category", "unknown")

            if docs:
                logger.info(f"[✓] Query '{query}' (category={category}): {len(docs)} results")
                # Show first result
                first_doc = docs[0]
                source = first_doc.metadata.get("source", "unknown")
                chunk_type = first_doc.metadata.get("chunk_type", "unknown")
                logger.info(f"    Top result: {source} ({chunk_type})")
            else:
                logger.warning(f"[!] Query '{query}' returned no results")

        except Exception as exc:
            logger.error(f"[✗] Error testing retrieval for '{query}': {exc}")


def test_vector_scores(retriever: RAGRetriever) -> None:
    """Test vector score capture in retrieval results."""
    try:
        docs = retriever.retrieve("P0300", k=3, metadata_filter={"category": "obd"})

        if not docs:
            logger.error("[✗] No documents retrieved for vector score test")
            return

        logger.info(f"[✓] Retrieved {len(docs)} documents")

        # Check vector scores
        has_vector_scores = True
        for i, doc in enumerate(docs):
            vector_score = doc.metadata.get("vector_score", None)
            vector_distance = doc.metadata.get("vector_distance", None)

            if vector_score is None or vector_distance is None:
                has_vector_scores = False
                logger.warning(f"[!] Doc {i} missing vector scores")
            else:
                logger.info(f"[✓] Doc {i}: vector_score={vector_score:.3f}, distance={vector_distance:.3f}")

        if has_vector_scores:
            logger.info("[✓] All documents have vector scores captured")
        else:
            logger.warning("[!] Some documents missing vector scores")

    except Exception as exc:
        logger.error(f"[✗] Error testing vector scores: {exc}")


def test_configuration() -> None:
    """Display current RAG configuration."""
    logger.info("\n[Configuration]")

    # Embedding source
    try:
        embeddings = EmbeddingFactory.get_embeddings()
        source = EmbeddingFactory._embedding_source or "Unknown"
        logger.info(f"[✓] Embedding source: {source}")
    except Exception as exc:
        logger.error(f"[✗] Embedding initialization failed: {exc}")

    # Retrieval parameters
    retrieval_k = os.getenv("RETRIEVAL_K", "5")
    rerank_top_k = os.getenv("RERANK_TOP_K", "3")
    logger.info(f"[✓] Retrieval K: {retrieval_k} (retrieve {retrieval_k}, rerank to {rerank_top_k})")

    # Chroma settings
    collection_name = os.getenv("CHROMA_COLLECTION_NAME", "automotive_docs")
    logger.info(f"[✓] Chroma collection: {collection_name}")

    # Query classifier
    try:
        classifier = QueryClassifier()
        logger.info("[✓] Query classifier initialized")
    except Exception as exc:
        logger.error(f"[✗] Query classifier failed: {exc}")


if __name__ == "__main__":
    validate_ingestion()
