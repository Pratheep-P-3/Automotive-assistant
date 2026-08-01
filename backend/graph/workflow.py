from __future__ import annotations

from typing import Literal

from langgraph.graph import END, START, StateGraph

from backend.agents.code_agent_v2 import CodeAgent
from backend.agents.maintenance_agent_v2 import MaintenanceAgent
from backend.agents.report_agent import ReportAgent
from backend.agents.symptom_agent_v2 import SymptomAgent
from backend.graph.state import WorkflowState

code_agent = CodeAgent()
symptom_agent = SymptomAgent()
maintenance_agent = MaintenanceAgent()
report_agent = ReportAgent()


def query_router(state: WorkflowState) -> WorkflowState:
    has_code = bool((state.get("code") or "").strip())
    has_symptoms = bool((state.get("symptoms") or "").strip())
    has_vehicle_or_mileage = bool(
        (state.get("make") and state.get("model")) or state.get("mileage") is not None
    )
    has_maintenance_query = bool((state.get("maintenance_query") or "").strip())

    state["need_code"] = has_code
    state["need_symptom"] = has_symptoms
    state["need_maintenance"] = has_vehicle_or_mileage or has_maintenance_query

    if has_code and not has_symptoms and not state["need_maintenance"]:
        state["route"] = "code_only"
    elif has_symptoms and not has_code and not state["need_maintenance"]:
        state["route"] = "symptom_only"
    elif has_code and has_symptoms and not state["need_maintenance"]:
        state["route"] = "code_symptom"
    elif has_vehicle_or_mileage and has_code and not has_symptoms:
        state["route"] = "code_vehicle"
    elif has_vehicle_or_mileage and not has_code and not has_symptoms:
        state["route"] = "vehicle_mileage"
    elif has_vehicle_or_mileage and has_symptoms and not has_code:
        state["route"] = "vehicle_symptom"
    elif has_vehicle_or_mileage and has_code and has_symptoms:
        state["route"] = "full_diagnosis"
    elif has_maintenance_query and not has_code and not has_symptoms:
        state["route"] = "maintenance_only"
    else:
        state["route"] = "fallback"

    return state


def route_from_router(state: WorkflowState) -> str:
    return state.get("route", "fallback")


def run_code_agent(state: WorkflowState) -> WorkflowState:
    return code_agent.run(state)


def run_symptom_agent(state: WorkflowState) -> WorkflowState:
    return symptom_agent.run(state)


def run_maintenance_agent(state: WorkflowState) -> WorkflowState:
    return maintenance_agent.run(state)


def run_report_agent(state: WorkflowState) -> WorkflowState:
    return report_agent.run(state)


def route_after_code(state: WorkflowState) -> Literal["symptom_agent", "maintenance_agent", "report_agent"]:
    if state.get("need_symptom"):
        return "symptom_agent"
    if state.get("need_maintenance"):
        return "maintenance_agent"
    return "report_agent"


def route_after_symptom(state: WorkflowState) -> Literal["maintenance_agent", "report_agent"]:
    if state.get("need_maintenance"):
        return "maintenance_agent"
    return "report_agent"


def build_workflow() -> StateGraph:
    graph = StateGraph(WorkflowState)

    graph.add_node("query_router", query_router)
    graph.add_node("code_agent", run_code_agent)
    graph.add_node("symptom_agent", run_symptom_agent)
    graph.add_node("maintenance_agent", run_maintenance_agent)
    graph.add_node("report_agent", run_report_agent)

    graph.add_edge(START, "query_router")

    graph.add_conditional_edges(
        "query_router",
        route_from_router,
        {
            "code_only": "code_agent",
            "symptom_only": "symptom_agent",
            "code_symptom": "code_agent",
            "code_vehicle": "code_agent",
            "vehicle_mileage": "maintenance_agent",
            "vehicle_symptom": "symptom_agent",
            "full_diagnosis": "code_agent",
            "maintenance_only": "maintenance_agent",
            "fallback": "report_agent",
        },
    )

    graph.add_conditional_edges(
        "code_agent",
        route_after_code,
        {
            "symptom_agent": "symptom_agent",
            "maintenance_agent": "maintenance_agent",
            "report_agent": "report_agent",
        },
    )

    graph.add_conditional_edges(
        "symptom_agent",
        route_after_symptom,
        {
            "maintenance_agent": "maintenance_agent",
            "report_agent": "report_agent",
        },
    )

    graph.add_edge("maintenance_agent", "report_agent")
    graph.add_edge("report_agent", END)

    return graph


def get_workflow():
    return build_workflow().compile()
