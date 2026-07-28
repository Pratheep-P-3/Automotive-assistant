from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, TypedDict


ScenarioKey = Literal[
    "code_only",
    "symptom_only",
    "code_symptom",
    "vehicle_mileage",
    "vehicle_symptom",
    "full_diagnosis",
    "maintenance_only",
    "fallback",
]


class WorkflowState(TypedDict, total=False):
    make: Optional[str]
    model: Optional[str]
    year: Optional[int]
    mileage: Optional[int]
    code: Optional[str]
    symptoms: Optional[str]
    maintenance_query: Optional[str]

    route: ScenarioKey
    need_code: bool
    need_symptom: bool
    need_maintenance: bool

    code_result: Dict[str, Any]
    symptom_result: Dict[str, Any]
    maintenance_result: Dict[str, Any]

    diagnosis: str
    severity: str
    possible_causes: List[str]
    repair_steps: List[str]
    maintenance_recommendations: List[str]
    confidence_score: float
    sources: List[Dict[str, Any]]

    llm_sections: Dict[str, Any]
    errors: List[str]
