"""
CodeAgent for OBD Diagnostic Code Queries.

Integrated with production RAG pipeline:
- QueryClassifier: Detects OBD codes
- Metadata Filtering: Category-based retrieval
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


class CodeAgent:
    """Processes OBD/DTC code queries with production RAG pipeline."""

    def __init__(self, data_path: str | None = None) -> None:
        """
        Initialize CodeAgent.

        Args:
            data_path: Legacy parameter (kept for compatibility, not used)
        """
        self.rag_retriever = RAGRetriever()
        self.classifier = QueryClassifier()
        self.reranker = CrossEncoderReranker(top_k=3)

        logger.info(
            "[CodeAgent] ✓ Initialized with production RAG pipeline "
            "(QueryClassifier + MetadataFiltering + ReRanking)"
        )

    def run(self, state: WorkflowState) -> WorkflowState:
        """
        Process OBD code query through production pipeline.

        Pipeline:
        1. Extract code from state
        2. Classify query category
        3. Retrieve documents with metadata filter (top 10) + vehicle prioritization
        4. Re-rank to top 3
        5. Extract structured information
        6. Calculate confidence
        7. Attach sources

        Args:
            state: WorkflowState containing code and optional vehicle info

        Returns:
            Updated state with code_result
        """
        code = (state.get("code") or "").strip().upper()

        if not code:
            logger.debug("[CodeAgent] No code provided, skipping")
            return state

        logger.info(f"[CodeAgent] Processing code: {code}")

        # ===== STEP 1: Query Classification =====
        category = self.classifier.classify(code)
        logger.info(f"[CodeAgent] Query category: {category.value}")

        # Only proceed if classified as OBD
        if category != QueryCategory.OBD:
            logger.warning(f"[CodeAgent] Code {code} not classified as OBD, skipping")
            return state

        # ===== STEP 2: Metadata Filter =====
        metadata_filter = self.classifier.get_metadata_filter(category)
        logger.debug(f"[CodeAgent] Metadata filter: {metadata_filter}")

        # ===== STEP 3: Retrieve Top K with Vehicle Prioritization =====
        vehicle_make = (state.get("make") or "").strip().lower() if state.get("make") else None
        vehicle_model = (state.get("model") or "").strip().lower() if state.get("model") else None
        
        logger.info(f"[CodeAgent] Retrieving documents for {code}...")
        if vehicle_make:
            logger.info(f"[CodeAgent] Prioritizing {vehicle_make.capitalize()} documents")
        
        docs = self.rag_retriever.retrieve(
            query=code,
            k=None,  # Use default retrieval_k from environment (default: 5)
            metadata_filter=metadata_filter,
            make=vehicle_make,
            model=vehicle_model,
        )

        if not docs:
            logger.warning(f"[CodeAgent] ✗ No documents found for {code}")
            state["code_result"] = {
                "code": code,
                "description": f"OBD code {code} not found in knowledge base",
                "severity": "Unknown",
                "common_causes": [],
                "system_affected": "",
                "diagnostic_steps": [],
                "repair_recommendation": "",
                "estimated_cost": "",
                "confidence": 0,
                "confidence_level": "Low Confidence",
                "source": "not_found",
            }
            return state

        # ===== STEP 4: Re-rank to Top 3 =====
        logger.info(f"[CodeAgent] Re-ranking {len(docs)} documents...")
        top_docs, rerank_scores = self.reranker.rerank(code, docs)

        if not top_docs:
            logger.warning(f"[CodeAgent] Re-ranking returned no results")
            state["code_result"] = {
                "code": code,
                "description": f"OBD code {code} not found in knowledge base",
                "severity": "Unknown",
                "common_causes": [],
                "source": "not_found",
            }
            return state

        # ===== STEP 5: Calculate Confidence =====
        confidence_pct, confidence_level = self.reranker.get_confidence_from_scores(rerank_scores)

        # ===== STEP 6: Extract Information from Top Result =====
        logger.info(f"[CodeAgent] Extracting data from top-ranked document")
        result = self._extract_from_document(top_docs[0], code)

        # ===== STEP 7: Add Confidence & Sources (Richer Attribution) =====
        result["confidence"] = confidence_pct
        result["confidence_level"] = confidence_level
        result["source"] = "rag_txt"
        result["sources"] = [
            {
                "source_filename": doc.metadata.get("source", "unknown"),
                "category": doc.metadata.get("category", "unknown"),
                "chunk_type": doc.metadata.get("chunk_type", "unknown"),
                "code": code,
                "make": doc.metadata.get("make"),  # Include brand metadata for confidence boost
                "model": doc.metadata.get("model"),
                "vector_score": doc.metadata.get("vector_score", 0),
                "vector_distance": doc.metadata.get("vector_distance", 0),
                "rerank_score": rerank_scores[i].get("score", 0) if i < len(rerank_scores) else 0,
                "original_rank": rerank_scores[i].get("original_position", i+1) if i < len(rerank_scores) else i+1,
            }
            for i, doc in enumerate(top_docs)
        ]

        logger.info(
            f"[CodeAgent] ✓ Found {code} with confidence {confidence_pct}% ({confidence_level})"
        )

        state["code_result"] = result

        # ===== STEP 8: Add to State Sources =====
        state["sources"] = state.get("sources", [])
        for source in result["sources"]:
            state["sources"].append(source)

        return state

    def _extract_from_document(self, doc: Document, code: str) -> dict[str, Any]:
        """
        Extract structured fields from retrieved document.

        Uses regex patterns to parse OBD entry format:
        - Description
        - Severity
        - System Affected
        - Common Causes
        - Diagnostic Steps
        - Repair Recommendation
        - Estimated Cost

        Args:
            doc: Retrieved Document
            code: OBD code

        Returns:
            Dict with extracted fields
        """
        text = doc.page_content

        logger.debug(f"[CodeAgent] Extracting data from document (length: {len(text)} chars)")

        result = {
            "code": code,
            "description": "",
            "severity": "Unknown",
            "system_affected": "",
            "common_causes": [],
            "diagnostic_steps": [],
            "repair_recommendation": "",
            "estimated_cost": "",
        }

        # ===== Extract Description =====
        desc_match = re.search(
            r"Description:\s*([^\n]+(?:\n(?!\s*\w+:)[^\n]*)*)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if desc_match:
            result["description"] = desc_match.group(1).strip().replace("\n", " ")[:500]
            logger.debug(f"[CodeAgent] ✓ Extracted description: {result['description'][:80]}...")

        # ===== Extract Severity =====
        sev_match = re.search(r"Severity:\s*(\w+(?:\s+\w+)?)", text, re.IGNORECASE)
        if sev_match:
            result["severity"] = sev_match.group(1).strip()
            logger.debug(f"[CodeAgent] ✓ Extracted severity: {result['severity']}")

        # ===== Extract System Affected =====
        sys_match = re.search(
            r"(?:System\s+Affected|System):\s*([^\n]+)",
            text,
            re.IGNORECASE,
        )
        if sys_match:
            result["system_affected"] = sys_match.group(1).strip()
            logger.debug(f"[CodeAgent] ✓ Extracted system: {result['system_affected']}")

        # ===== Extract Common Causes =====
        causes_match = re.search(
            r"Common Causes:(.+?)(?=Diagnostic|Repair|Typical|---|\Z)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if causes_match:
            causes_text = causes_match.group(1)
            causes_list = re.findall(r"^\s*[-•*]\s+(.+?)$", causes_text, re.MULTILINE)
            result["common_causes"] = [c.strip() for c in causes_list if c.strip()][:8]
            logger.debug(f"[CodeAgent] ✓ Extracted {len(result['common_causes'])} causes")

        # ===== Extract Diagnostic Steps =====
        steps_match = re.search(
            r"Diagnostic Steps:(.+?)(?=Repair|Typical|---|\Z)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if steps_match:
            steps_text = steps_match.group(1)
            steps_list = re.findall(r"^\s*\d+\.\s+(.+?)$", steps_text, re.MULTILINE)
            result["diagnostic_steps"] = [s.strip() for s in steps_list if s.strip()][:10]
            logger.debug(f"[CodeAgent] ✓ Extracted {len(result['diagnostic_steps'])} steps")

        # ===== Extract Repair Recommendation =====
        repair_match = re.search(
            r"Repair Recommendation:\s*([^\n]+)",
            text,
            re.IGNORECASE,
        )
        if repair_match:
            result["repair_recommendation"] = repair_match.group(1).strip()
            logger.debug(f"[CodeAgent] ✓ Extracted repair recommendation")

        # ===== Extract Cost =====
        cost_match = re.search(
            r"(?:Typical )?Repair Cost:\s*([^\n]+)",
            text,
            re.IGNORECASE,
        )
        if cost_match:
            result["estimated_cost"] = cost_match.group(1).strip()
            logger.debug(f"[CodeAgent] ✓ Extracted cost: {result['estimated_cost']}")

        return result
