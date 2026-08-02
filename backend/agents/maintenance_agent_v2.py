"""
MaintenanceAgent for Vehicle Maintenance Queries.

Integrated with production RAG pipeline:
- QueryClassifier: Detects maintenance queries
- Metadata Filtering: Maintenance category
- Retrieval: Top 10 documents
- Re-ranking: Cross-encoder scoring (top 3)
- Confidence Scoring: Relevance-based confidence
"""

from __future__ import annotations

import logging
import re
from typing import Any

from langchain_core.documents import Document

from backend.graph.state import WorkflowState
from backend.rag.query_classifier import QueryClassifier, QueryCategory
from backend.rag.reranker import CrossEncoderReranker
from backend.rag.retriever import RAGRetriever

logger = logging.getLogger(__name__)


class MaintenanceAgent:
    """Processes vehicle maintenance queries with production RAG pipeline."""

    def __init__(self) -> None:
        """Initialize MaintenanceAgent."""
        self.rag_retriever = RAGRetriever()
        self.classifier = QueryClassifier()
        self.reranker = CrossEncoderReranker(top_k=3)

        logger.info(
            "[MaintenanceAgent] ✓ Initialized with production RAG pipeline "
            "(QueryClassifier + MetadataFiltering + ReRanking)"
        )

    def run(self, state: WorkflowState) -> WorkflowState:
        """
        Process maintenance query through production pipeline.

        Pipeline:
        1. Extract maintenance query from state
        2. Classify query category (should be maintenance)
        3. Retrieve maintenance documents (top 10) + vehicle prioritization
        4. Re-rank to top 3
        5. Extract maintenance procedures
        6. Filter by vehicle mileage if provided
        7. Calculate confidence
        8. Attach sources

        Args:
            state: WorkflowState containing maintenance_query and optional vehicle info

        Returns:
            Updated state with maintenance_result
        """
        query = (state.get("maintenance_query") or "").strip()
        mileage = state.get("mileage")

        if not query:
            logger.debug("[MaintenanceAgent] No maintenance query provided, skipping")
            return state

        logger.info(f"[MaintenanceAgent] Processing query: '{query[:60]}...' (mileage: {mileage})")

        # ===== STEP 1: Query Classification =====
        category = self.classifier.classify(query)
        logger.info(f"[MaintenanceAgent] Query category: {category.value}")

        # ===== STEP 2: Metadata Filter =====
        metadata_filter = self.classifier.get_metadata_filter(QueryCategory.MAINTENANCE)
        logger.debug(f"[MaintenanceAgent] Metadata filter: {metadata_filter}")

        # ===== STEP 3: Retrieve Top 10 with Vehicle Prioritization =====
        vehicle_make = (state.get("make") or "").strip().lower() if state.get("make") else None
        vehicle_model = (state.get("model") or "").strip().lower() if state.get("model") else None
        
        logger.info("[MaintenanceAgent] Retrieving maintenance documents...")
        if vehicle_make:
            logger.info(f"[MaintenanceAgent] Prioritizing {vehicle_make.capitalize()} documents")
        
        docs = self.rag_retriever.retrieve(
            query=query,
            k=10,
            metadata_filter=metadata_filter,
            make=vehicle_make,
            model=vehicle_model,
        )

        if not docs:
            logger.warning("[MaintenanceAgent] ✗ No maintenance documents found")
            state["maintenance_result"] = {
                "query": query,
                "maintenance_recommendations": [],
                "preventive_actions": [],
                "confidence": 0,
                "confidence_level": "Low Confidence",
                "source": "not_found",
            }
            return state

        # ===== STEP 4: Re-rank to Top 3 =====
        logger.info(f"[MaintenanceAgent] Re-ranking {len(docs)} documents...")
        top_docs, rerank_scores = self.reranker.rerank(query, docs)

        if not top_docs:
            logger.warning("[MaintenanceAgent] Re-ranking returned no results")
            state["maintenance_result"] = {
                "query": query,
                "maintenance_recommendations": [],
                "source": "not_found",
            }
            return state

        # ===== STEP 5: Calculate Confidence =====
        confidence_pct, confidence_level = self.reranker.get_confidence_from_scores(rerank_scores)

        # ===== STEP 6: Extract Maintenance Information =====
        logger.info("[MaintenanceAgent] Extracting maintenance data from top results")
        result = self._extract_maintenance_data(top_docs, query, mileage)

        # ===== STEP 7: Add Confidence & Sources =====
        result["confidence"] = confidence_pct
        result["confidence_level"] = confidence_level
        result["source"] = "rag_txt"
        result["sources"] = [
            {
                "source_filename": doc.metadata.get("source", "unknown"),
                "category": doc.metadata.get("category", "unknown"),
                "chunk_type": doc.metadata.get("chunk_type", "unknown"),
                "query": query[:50],
                "make": doc.metadata.get("make"),  # Include brand metadata for confidence boost
                "model": doc.metadata.get("model"),
                "procedure": doc.metadata.get("procedure", "unknown"),
                "vector_score": doc.metadata.get("vector_score", 0),
                "rerank_score": rerank_scores[i].get("score", 0) if i < len(rerank_scores) else 0,
            }
            for i, doc in enumerate(top_docs)
        ]

        logger.info(
            f"[MaintenanceAgent] ✓ Found maintenance data with confidence {confidence_pct}% ({confidence_level})"
        )

        state["maintenance_result"] = result

        # ===== STEP 8: Add to State Sources =====
        state["sources"] = state.get("sources", [])
        for source in result["sources"]:
            state["sources"].append(source)

        return state

    def _extract_maintenance_data(
        self, docs: list[Document], query: str, mileage: int | None = None
    ) -> dict[str, Any]:
        """
        Extract maintenance information from documents.

        Parses:
        - Service interval/mileage
        - Maintenance items
        - Procedures
        - Cost estimates
        - Tools required
        - Preventive actions

        Args:
            docs: Retrieved documents
            query: Original query
            mileage: Vehicle mileage (optional filter)

        Returns:
            Dict with maintenance recommendations
        """
        result = {
            "query": query,
            "maintenance_recommendations": [],
            "preventive_actions": [],
            "service_intervals": [],
            "cost_estimates": [],
            "tools_required": [],
        }

        combined_text = " ".join([doc.page_content for doc in docs])
        logger.debug(
            f"[MaintenanceAgent] Processing {len(combined_text)} chars of maintenance data"
        )

        # ===== Extract Service Intervals =====
        intervals_match = re.search(
            r"(?:Service Interval|Schedule|Mileage):\s*([^\n]+)",
            combined_text,
            re.IGNORECASE,
        )
        if intervals_match:
            interval = intervals_match.group(1).strip()
            result["service_intervals"].append(interval)
            logger.debug(f"[MaintenanceAgent] ✓ Found interval: {interval}")

        # ===== Extract Maintenance Recommendations =====
        recom_match = re.search(
            r"(?:Maintenance Items|What to Service|Services Due):(.+?)(?=Cost|Tools|Procedure|---|\Z)",
            combined_text,
            re.IGNORECASE | re.DOTALL,
        )
        if recom_match:
            recom_text = recom_match.group(1)
            recom_list = re.findall(r"^\s*[-•*]\s+(.+?)$", recom_text, re.MULTILINE)
            result["maintenance_recommendations"] = [r.strip() for r in recom_list if r.strip()][:10]
            logger.debug(
                f"[MaintenanceAgent] ✓ Extracted {len(result['maintenance_recommendations'])} items"
            )

        # ===== Extract Cost Estimates =====
        cost_match = re.search(
            r"Cost(?:s)?:\s*([^\n]+(?:\n(?!\s*\w+:)[^\n]*)*)",
            combined_text,
            re.IGNORECASE | re.DOTALL,
        )
        if cost_match:
            cost = cost_match.group(1).strip().replace("\n", " ")
            result["cost_estimates"].append(cost)
            logger.debug(f"[MaintenanceAgent] ✓ Found cost: {cost}")

        # ===== Extract Tools Required =====
        tools_match = re.search(
            r"(?:Tools Required|Tools Needed):(.+?)(?=Cost|Procedure|---|\Z)",
            combined_text,
            re.IGNORECASE | re.DOTALL,
        )
        if tools_match:
            tools_text = tools_match.group(1)
            tools_list = re.findall(r"^\s*[-•*]\s+(.+?)$", tools_text, re.MULTILINE)
            result["tools_required"] = [t.strip() for t in tools_list if t.strip()][:8]
            logger.debug(f"[MaintenanceAgent] ✓ Extracted {len(result['tools_required'])} tools")

        # ===== Extract Procedures =====
        proc_match = re.search(
            r"(?:Procedure|How to|Steps):(.+?)(?=Cost|Tools|---|\Z)",
            combined_text,
            re.IGNORECASE | re.DOTALL,
        )
        if proc_match:
            proc_text = proc_match.group(1)
            steps_list = re.findall(r"^\s*\d+\.\s+(.+?)$", proc_text, re.MULTILINE)
            result["preventive_actions"] = [s.strip() for s in steps_list if s.strip()][:8]
            logger.debug(
                f"[MaintenanceAgent] ✓ Extracted {len(result['preventive_actions'])} steps"
            )

        # ===== Filter by Mileage if Provided =====
        if mileage is not None:
            logger.info(f"[MaintenanceAgent] Filtering results by mileage: {mileage} km")
            result["relevant_for_mileage"] = self._check_mileage_relevance(
                combined_text, mileage
            )

        return result

    def _check_mileage_relevance(self, text: str, mileage: int) -> bool:
        """
        Check if maintenance data is relevant for given mileage.

        Args:
            text: Maintenance document text
            mileage: Vehicle mileage

        Returns:
            True if maintenance is relevant for this mileage
        """
        # Extract mileage intervals from text
        mileage_patterns = re.findall(r"(\d+)\s*(?:km|mile)s?(?:\s+(?:service|maintenance))?", text, re.IGNORECASE)

        if not mileage_patterns:
            logger.debug("[MaintenanceAgent] No mileage intervals found in text")
            return True  # Default to relevant if no specific interval

        intervals = [int(m) for m in mileage_patterns if m.isdigit()]
        if not intervals:
            return True

        # Check if current mileage is close to any service interval (within ±10%)
        for interval in intervals:
            tolerance = interval * 0.1
            if abs(mileage - interval) <= tolerance:
                logger.info(
                    f"[MaintenanceAgent] Mileage {mileage} is relevant for interval {interval}"
                )
                return True

        logger.info(f"[MaintenanceAgent] Mileage {mileage} not matched to common intervals")
        return False
