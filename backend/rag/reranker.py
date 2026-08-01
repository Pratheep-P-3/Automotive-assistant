"""
Cross-Encoder Re-ranker for Automotive Diagnostics RAG.

Uses cross-encoder model to re-rank retrieved documents for better relevance.
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    """Re-ranks documents using cross-encoder similarity scores."""

    MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    DEFAULT_TOP_K = 3

    def __init__(self, top_k: int = DEFAULT_TOP_K) -> None:
        """
        Initialize CrossEncoderReranker.

        Args:
            top_k: Number of top results to return after re-ranking
        """
        self.top_k = top_k
        self.model = None

        try:
            # Try to lazy-load model only when needed
            logger.info(f"[Reranker] Will use model: {self.MODEL_NAME}")
            logger.info(f"[Reranker] ✓ Initialized (top_k={top_k})")
        except Exception as exc:
            logger.exception(f"[Reranker] ✗ FAILED to initialize: {exc}")
            raise

    def _load_model(self) -> None:
        """Lazy-load the cross-encoder model."""
        if self.model is not None:
            return

        try:
            from sentence_transformers import CrossEncoder

            logger.info(f"[Reranker] Loading model: {self.MODEL_NAME}")
            self.model = CrossEncoder(self.MODEL_NAME)
            logger.info(f"[Reranker] ✓ Model loaded successfully")
        except ImportError:
            logger.error(
                "[Reranker] sentence-transformers not installed. Install with: "
                "pip install sentence-transformers"
            )
            raise
        except Exception as exc:
            logger.exception(f"[Reranker] ✗ FAILED to load model: {exc}")
            raise

    def rerank(self, query: str, documents: list[Document]) -> tuple[list[Document], list[dict]]:
        """
        Re-rank documents by relevance to query.

        Args:
            query: User query
            documents: Retrieved documents to re-rank

        Returns:
            Tuple of (re-ranked documents, scores with metadata)
        """
        if not documents:
            logger.warning("[Reranker] No documents to re-rank")
            return [], []

        if not query or not isinstance(query, str):
            logger.warning("[Reranker] Invalid query, returning documents as-is")
            return documents[: self.top_k], []

        # Lazy-load model
        self._load_model()

        try:
            logger.info(f"[Reranker] Re-ranking {len(documents)} documents for query: '{query[:60]}...'")

            # Prepare pairs for cross-encoder
            pairs = [[query, doc.page_content] for doc in documents]

            # Score all pairs
            scores = self.model.predict(pairs)
            logger.debug(f"[Reranker] Computed {len(scores)} relevance scores")

            # Create ranked list with metadata
            ranked_results = []
            for i, (doc, score) in enumerate(zip(documents, scores)):
                ranked_results.append(
                    {
                        "document": doc,
                        "original_position": i + 1,  # 1-indexed
                        "score": float(score),
                        "source": doc.metadata.get("source", "unknown"),
                        "chunk_type": doc.metadata.get("chunk_type", "unknown"),
                    }
                )

            # Sort by score (descending)
            ranked_results.sort(key=lambda x: x["score"], reverse=True)

            # Log re-ranking results
            for i, result in enumerate(ranked_results[: self.top_k]):
                logger.info(
                    f"[Reranker] Rank {i + 1}: "
                    f"Score={result['score']:.3f} | "
                    f"Orig Pos={result['original_position']} | "
                    f"Source={result['source']}"
                )

            # Extract top K documents
            top_docs = [r["document"] for r in ranked_results[: self.top_k]]
            top_scores = ranked_results[: self.top_k]

            logger.info(
                f"[Reranker] ✓ Re-ranked complete. "
                f"Top score: {top_scores[0]['score']:.3f} "
                f"(was at position {top_scores[0]['original_position']})"
            )

            return top_docs, top_scores

        except Exception as exc:
            logger.exception(f"[Reranker] ✗ Re-ranking FAILED: {exc}")
            # Fallback: return top K documents as-is
            return documents[: self.top_k], []

    def get_confidence_from_scores(self, scores: list[dict]) -> tuple[int, str]:
        """
        Calculate confidence level from re-ranking scores (multi-factor).

        Uses three factors:
        1. Top reranker score (0-1 range)
        2. Average score of Top 3 results (consistency indicator)
        3. Separation between Rank 1 and Rank 2 (confidence gap)

        Rewards:
        - Strong top match
        - Consistent supporting evidence (narrow score distribution)

        Reduces confidence when:
        - Scores are very close together (ambiguous)
        - Relevance scores are weak

        Args:
            scores: List of re-ranking score dictionaries

        Returns:
            Tuple of (confidence_percentage, confidence_level)
        """
        if not scores or not scores[0].get("score"):
            logger.info("[Reranker] No scores available, returning default confidence")
            return 50, "Low Confidence"

        # Factor 1: Top score (0-1 range from cross-encoder)
        top_score = scores[0]["score"]

        # Factor 2: Average of top 3 results (consistency)
        top_3_scores = [s["score"] for s in scores[:3]]
        avg_top_3 = sum(top_3_scores) / len(top_3_scores)

        # Factor 3: Separation between Rank 1 and Rank 2
        score_gap = 0.0
        if len(scores) > 1:
            score_gap = top_score - scores[1]["score"]
        else:
            score_gap = top_score  # If only 1 result, gap is the score itself

        # Calculate combined confidence
        # Weight: 50% top score + 30% average consistency + 20% score gap
        confidence_score = (top_score * 0.5) + (avg_top_3 * 0.3) + (score_gap * 0.2)

        # Map to 0-100 scale
        confidence_pct = min(100, int(confidence_score * 100))

        # Determine confidence level
        if confidence_pct >= 80:
            level = "High Confidence"
        elif confidence_pct >= 60:
            level = "Medium Confidence"
        else:
            level = "Low Confidence"

        logger.info(
            f"[Reranker] Confidence calculation: "
            f"top_score={top_score:.3f}, avg_top_3={avg_top_3:.3f}, gap={score_gap:.3f} -> "
            f"{confidence_pct}% ({level})"
        )

        return confidence_pct, level
