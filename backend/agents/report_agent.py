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
        score = 0.2
        if state.get("code"):
            score += 0.25
        if state.get("symptoms"):
            score += 0.2
        if state.get("make") and state.get("model"):
            score += 0.15
        if state.get("mileage") is not None:
            score += 0.1
        if state.get("code_result"):
            score += 0.05
        if state.get("symptom_result", {}).get("context"):
            score += 0.05
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
