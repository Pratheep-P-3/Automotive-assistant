"""
SymptomAgent for Vehicle Symptom Queries.

Integrated with production RAG pipeline:
- QueryClassifier: Detects symptom queries
- Metadata Filtering: Symptom/Troubleshooting category
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


class SymptomAgent:
    """Processes vehicle symptom queries with production RAG pipeline."""

    def __init__(self) -> None:
        """Initialize SymptomAgent."""
        self.rag_retriever = RAGRetriever()
        self.classifier = QueryClassifier()
        self.reranker = CrossEncoderReranker(top_k=3)

        logger.info(
            "[SymptomAgent] ✓ Initialized with production RAG pipeline "
            "(QueryClassifier + MetadataFiltering + ReRanking)"
        )

    def run(self, state: WorkflowState) -> WorkflowState:
        """
        Process symptom query through production pipeline.

        Pipeline:
        1. Extract symptoms from state
        2. Classify query category (should be symptom)
        3. Retrieve troubleshooting documents (top 10)
        4. Re-rank to top 3
        5. Extract troubleshooting workflow
        6. Link to OBD codes if present
        7. Calculate confidence
        8. Attach sources

        Args:
            state: WorkflowState containing symptoms

        Returns:
            Updated state with symptom_result
        """
        symptoms = (state.get("symptoms") or "").strip()

        if not symptoms:
            logger.debug("[SymptomAgent] No symptoms provided, skipping")
            return state

        logger.info(f"[SymptomAgent] Processing symptoms: '{symptoms[:60]}...'")

        # ===== STEP 1: Query Classification =====
        category = self.classifier.classify(symptoms)
        logger.info(f"[SymptomAgent] Query category: {category.value}")

        # ===== STEP 2: Metadata Filter =====
        # For symptoms, we want to search the symptom/troubleshooting category
        if category == QueryCategory.OBD:
            # Even if detected as OBD, we want symptom-related docs
            metadata_filter = {"category": "symptom"}
        else:
            metadata_filter = self.classifier.get_metadata_filter(category)

        logger.debug(f"[SymptomAgent] Metadata filter: {metadata_filter}")

        # ===== STEP 3: Retrieve Top 10 =====
        logger.info("[SymptomAgent] Retrieving troubleshooting documents...")
        docs = self.rag_retriever.retrieve(
            query=symptoms,
            k=10,
            metadata_filter=metadata_filter,
        )

        if not docs:
            logger.warning("[SymptomAgent] ✗ No troubleshooting documents found")
            state["symptom_result"] = {
                "symptoms": symptoms,
                "troubleshooting_hints": [],
                "related_codes": [],
                "diagnostic_workflow": [],
                "confidence": 0,
                "confidence_level": "Low Confidence",
                "source": "not_found",
            }
            return state

        # ===== STEP 4: Re-rank to Top 3 =====
        logger.info(f"[SymptomAgent] Re-ranking {len(docs)} documents...")
        top_docs, rerank_scores = self.reranker.rerank(symptoms, docs)

        if not top_docs:
            logger.warning("[SymptomAgent] Re-ranking returned no results")
            state["symptom_result"] = {
                "symptoms": symptoms,
                "troubleshooting_hints": [],
                "source": "not_found",
            }
            return state

        # ===== STEP 5: Calculate Confidence =====
        confidence_pct, confidence_level = self.reranker.get_confidence_from_scores(rerank_scores)

        # ===== STEP 6: Extract Troubleshooting Information =====
        logger.info("[SymptomAgent] Extracting troubleshooting data from top results")
        result = self._extract_troubleshooting_data(top_docs, symptoms)

        # ===== STEP 7: Add Confidence & Sources =====
        result["confidence"] = confidence_pct
        result["confidence_level"] = confidence_level
        result["source"] = "rag_txt"
        result["sources"] = [
            {
                "source": doc.metadata.get("source", "unknown"),
                "type": "troubleshooting",
                "symptoms": symptoms[:50],
                "chunk_type": doc.metadata.get("chunk_type", "unknown"),
            }
            for doc in top_docs
        ]

        logger.info(
            f"[SymptomAgent] ✓ Found troubleshooting data with confidence {confidence_pct}% ({confidence_level})"
        )

        state["symptom_result"] = result

        # ===== STEP 8: Add to State Sources =====
        state["sources"] = state.get("sources", [])
        for source in result["sources"]:
            state["sources"].append(source)

        return state

    def _extract_troubleshooting_data(
        self, docs: list[Document], symptoms: str
    ) -> dict[str, Any]:
        """
        Extract troubleshooting workflow from documents.

        Parses:
        - Symptom description
        - Possible causes
        - Diagnostic steps
        - Related OBD codes
        - Repair recommendations

        Args:
            docs: Retrieved documents
            symptoms: Original symptom query

        Returns:
            Dict with troubleshooting information
        """
        result = {
            "symptoms": symptoms,
            "troubleshooting_hints": [],
            "related_codes": [],
            "diagnostic_workflow": [],
            "repair_procedures": [],
        }

        combined_text = " ".join([doc.page_content for doc in docs])
        logger.debug(f"[SymptomAgent] Processing {len(combined_text)} chars of troubleshooting data")

        # ===== Extract Troubleshooting Hints (Causes) =====
        hints_match = re.search(
            r"(?:Common Causes|Possible Causes|Likely Causes):(.+?)(?=Diagnostic|Related|---|\Z)",
            combined_text,
            re.IGNORECASE | re.DOTALL,
        )
        if hints_match:
            hints_text = hints_match.group(1)
            hints_list = re.findall(r"^\s*[-•*]\s+(.+?)$", hints_text, re.MULTILINE)
            result["troubleshooting_hints"] = [h.strip() for h in hints_list if h.strip()][:5]
            logger.debug(f"[SymptomAgent] ✓ Extracted {len(result['troubleshooting_hints'])} causes")

        # ===== Extract Related OBD Codes =====
        codes_match = re.search(
            r"(?:Related Codes|Related OBD|Associated Codes):(.+?)(?=Diagnostic|Repair|---|\Z)",
            combined_text,
            re.IGNORECASE | re.DOTALL,
        )
        if codes_match:
            codes_text = codes_match.group(1)
            codes_list = re.findall(r"\b([PUC]\d{4})\b", codes_text)
            result["related_codes"] = list(dict.fromkeys(codes_list))[:5]  # Remove duplicates
            logger.debug(f"[SymptomAgent] ✓ Found {len(result['related_codes'])} related codes")

        # ===== Extract Diagnostic Workflow =====
        workflow_match = re.search(
            r"(?:Diagnostic Steps|Diagnosis Procedure|Troubleshooting Steps):(.+?)(?=Repair|Related|---|\Z)",
            combined_text,
            re.IGNORECASE | re.DOTALL,
        )
        if workflow_match:
            workflow_text = workflow_match.group(1)
            steps_list = re.findall(r"^\s*\d+\.\s+(.+?)$", workflow_text, re.MULTILINE)
            result["diagnostic_workflow"] = [s.strip() for s in steps_list if s.strip()][:8]
            logger.debug(f"[SymptomAgent] ✓ Extracted {len(result['diagnostic_workflow'])} steps")

        # ===== Extract Repair Procedures =====
        repair_match = re.search(
            r"(?:Repair Recommendation|Solution|Fix):(.+?)(?=Related|---|\Z)",
            combined_text,
            re.IGNORECASE | re.DOTALL,
        )
        if repair_match:
            repair_text = repair_match.group(1)
            repairs_list = re.findall(r"^\s*[-•*]?\s*(.+?)$", repair_text, re.MULTILINE)
            result["repair_procedures"] = [r.strip() for r in repairs_list if r.strip()][:5]
            logger.debug(f"[SymptomAgent] ✓ Extracted {len(result['repair_procedures'])} procedures")

        return result
