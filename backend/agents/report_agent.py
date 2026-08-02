from __future__ import annotations

import logging
from typing import Any, Dict

from backend.graph.state import WorkflowState
from backend.services.azure_openai_service import AzureOpenAIService

logger = logging.getLogger(__name__)


class ReportAgent:
    def __init__(self, llm_service: AzureOpenAIService | None = None) -> None:
        self.llm_service = llm_service or AzureOpenAIService()

    @staticmethod
    def _estimate_confidence(state: WorkflowState) -> float:
        """
        Estimate confidence based on input quality and retrieval results.
        
        With brand-specific documents now available:
        - Vehicle make/model DOES improve confidence if brand-specific docs retrieved
        - Generic docs: lower confidence (applies to any vehicle)
        - Brand-specific docs: higher confidence (tailored to user's vehicle)
        """
        score = 0.2  # Base confidence
        
        # Core inputs that affect retrieval quality
        if state.get("code"):
            score += 0.25  # Direct OBD lookup
        if state.get("symptoms"):
            score += 0.25  # Semantic symptom search
        if state.get("code_result"):
            score += 0.15  # Successful code retrieval
        if state.get("symptom_result", {}).get("context"):
            score += 0.1   # Symptom context found
        if state.get("maintenance_result"):
            score += 0.1   # Maintenance data found
        
        # Vehicle-specific document boost
        # If user provided make AND retrieved docs are from that make, boost confidence
        user_make = state.get("make")
        if user_make:
            user_make_lower = user_make.lower().strip()
            
            # Check if any retrieved docs are brand-specific matches
            is_brand_match = False
            matched_make = None
            
            # Check all result types for brand-specific documents
            results_to_check = [
                state.get("code_result", {}),
                state.get("symptom_result", {}),
                state.get("maintenance_result", {}),
            ]
            
            for result in results_to_check:
                if not result or not result.get("sources"):
                    continue
                
                for source in result.get("sources", []):
                    if not source or not isinstance(source, dict):
                        continue
                    
                    doc_make = source.get("make")
                    if doc_make:
                        doc_make_lower = str(doc_make).lower().strip()
                        if doc_make_lower == user_make_lower:
                            is_brand_match = True
                            matched_make = doc_make_lower
                            break
                
                if is_brand_match:
                    break
            
            # Boost confidence if brand-specific docs were used
            if is_brand_match:
                score += 0.15  # +15% for brand-specific match
                logger.info(
                    f"[ReportAgent] Brand-specific document match ({matched_make}) - confidence boosted by +15%"
                )
            
        return max(0.0, min(score, 0.95))

    def run(self, state: WorkflowState) -> WorkflowState:
        payload: Dict[str, Any] = {
            "vehicle": {
                "make": state.get("make"),
                "model": state.get("model"),
                "year": state.get("year"),
                "mileage": state.get("mileage"),
            },
            "inputs": {
                "code": state.get("code"),
                "symptoms": state.get("symptoms"),
                "maintenance_query": state.get("maintenance_query"),
            },
            "code_result": state.get("code_result", {}),
            "symptom_result": state.get("symptom_result", {}),
            "maintenance_result": state.get("maintenance_result", {}),
            "sources": state.get("sources", []),
            "confidence_score": self._estimate_confidence(state),
        }

        llm_output = self.llm_service.generate_report(payload)
        api_response = llm_output.get("api_response", {})

        state["diagnosis"] = api_response.get("diagnosis", "No diagnosis generated.")
        state["severity"] = api_response.get("severity", "Unknown")
        state["possible_causes"] = api_response.get("possible_causes", [])
        state["repair_steps"] = api_response.get("repair_steps", [])
        state["maintenance_recommendations"] = api_response.get(
            "maintenance_recommendations", []
        )
        # USE RAG CONFIDENCE, NOT LLM'S INFLATED SCORE
        state["confidence_score"] = float(api_response.get("confidence_percentage", 50)) / 100.0

        source_objects = state.get("sources", [])
        state["sources"] = source_objects
        state["llm_sections"] = llm_output

        return state
