from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from backend.graph.state import WorkflowState
from backend.graph.workflow import get_workflow

logger = logging.getLogger(__name__)

router = APIRouter(tags=["diagnostics"])
workflow = get_workflow()


class DiagnoseRequest(BaseModel):
    make: Optional[str] = Field(default=None, description="Vehicle make")
    model: Optional[str] = Field(default=None, description="Vehicle model")
    year: Optional[int] = Field(default=None, ge=1950, le=2100)
    mileage: Optional[int] = Field(default=None, ge=0)
    code: Optional[str] = Field(default=None, description="Diagnostic Trouble Code")
    symptoms: Optional[str] = Field(default=None, description="Vehicle symptoms")
    maintenance_query: Optional[str] = Field(
        default=None,
        description="Maintenance-only question, e.g. 'What service is needed at 60,000 miles?'",
    )

    @model_validator(mode="after")
    def validate_at_least_one_input(self) -> "DiagnoseRequest":
        has_any_input = any(
            [
                self.code,
                self.symptoms,
                self.maintenance_query,
                self.mileage is not None,
                self.make,
                self.model,
            ]
        )
        if not has_any_input:
            raise ValueError(
                "At least one of code, symptoms, vehicle fields, mileage, or maintenance_query is required."
            )
        return self


class DiagnoseResponse(BaseModel):
    diagnosis: str
    severity: str
    possible_causes: List[str]
    repair_steps: List[str]
    maintenance_recommendations: List[str]
    confidence_score: float
    sources: List[Dict[str, Any]]


@router.post("/diagnose", response_model=DiagnoseResponse)
def diagnose(payload: DiagnoseRequest) -> DiagnoseResponse:
    try:
        initial_state: WorkflowState = {
            "make": payload.make,
            "model": payload.model,
            "year": payload.year,
            "mileage": payload.mileage,
            "code": payload.code,
            "symptoms": payload.symptoms,
            "maintenance_query": payload.maintenance_query,
            "sources": [],
            "errors": [],
        }

        result = workflow.invoke(initial_state)

        return DiagnoseResponse(
            diagnosis=result.get("diagnosis", "No diagnosis generated."),
            severity=result.get("severity", "Unknown"),
            possible_causes=result.get("possible_causes", []),
            repair_steps=result.get("repair_steps", []),
            maintenance_recommendations=result.get("maintenance_recommendations", []),
            confidence_score=float(result.get("confidence_score", 0.5)),
            sources=result.get("sources", []),
        )
    except Exception as exc:
        logger.exception("Failed to process diagnostic request: %s", exc)
        raise HTTPException(status_code=500, detail="Diagnosis failed due to internal error.") from exc
