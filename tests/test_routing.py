"""Tests for routing logic and scenario detection."""
import pytest
from backend.graph.workflow import QUERY_ROUTER
from backend.graph.state import WorkflowState


class TestQueryRouter:
    """Tests for the query router that determines diagnostic route."""

    def test_route_code_only(self) -> None:
        """Test routing for code-only scenario."""
        state: WorkflowState = {
            "code": "P0171",
            "symptoms": "",
            "make": "",
            "model": "",
            "year": None,
            "mileage": None,
            "maintenance_query": "",
        }
        result = QUERY_ROUTER(state)
        assert result == "code_only"

    def test_route_symptom_only(self) -> None:
        """Test routing for symptom-only scenario."""
        state: WorkflowState = {
            "code": "",
            "symptoms": "engine overheating and loss of power",
            "make": "",
            "model": "",
            "year": None,
            "mileage": None,
            "maintenance_query": "",
        }
        result = QUERY_ROUTER(state)
        assert result == "symptom_only"

    def test_route_code_and_symptoms(self) -> None:
        """Test routing for code + symptoms scenario."""
        state: WorkflowState = {
            "code": "P0171",
            "symptoms": "rough idle and hesitation",
            "make": "",
            "model": "",
            "year": None,
            "mileage": None,
            "maintenance_query": "",
        }
        result = QUERY_ROUTER(state)
        assert result == "code_symptom"

    def test_route_code_and_vehicle(self) -> None:
        """Test routing for code + vehicle (no symptoms)."""
        state: WorkflowState = {
            "code": "P0171",
            "symptoms": "",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2020,
            "mileage": None,
            "maintenance_query": "",
        }
        result = QUERY_ROUTER(state)
        assert result == "code_vehicle"

    def test_route_code_vehicle_mileage(self) -> None:
        """Test routing with code, vehicle, and mileage (no symptoms)."""
        state: WorkflowState = {
            "code": "P0171",
            "symptoms": "",
            "make": "Honda",
            "model": "Civic",
            "year": 2018,
            "mileage": 80000,
            "maintenance_query": "",
        }
        result = QUERY_ROUTER(state)
        # Should route to code_vehicle (code takes precedence)
        assert result == "code_vehicle"

    def test_route_vehicle_only(self) -> None:
        """Test routing with vehicle info only (no code/symptoms)."""
        state: WorkflowState = {
            "code": "",
            "symptoms": "",
            "make": "Toyota",
            "model": "Camry",
            "year": 2015,
            "mileage": None,
            "maintenance_query": "",
        }
        result = QUERY_ROUTER(state)
        # Should route to fallback as needs more info
        assert result == "fallback"

    def test_route_vehicle_and_mileage(self) -> None:
        """Test routing with vehicle and mileage (no code/symptoms)."""
        state: WorkflowState = {
            "code": "",
            "symptoms": "",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2020,
            "mileage": 60000,
            "maintenance_query": "",
        }
        result = QUERY_ROUTER(state)
        assert result == "vehicle_mileage"

    def test_route_vehicle_and_symptoms(self) -> None:
        """Test routing with vehicle and symptoms (no code)."""
        state: WorkflowState = {
            "code": "",
            "symptoms": "grinding noise when braking",
            "make": "Ford",
            "model": "F-150",
            "year": 2019,
            "mileage": None,
            "maintenance_query": "",
        }
        result = QUERY_ROUTER(state)
        assert result == "vehicle_symptom"

    def test_route_full_diagnosis(self) -> None:
        """Test routing when all diagnostic info provided."""
        state: WorkflowState = {
            "code": "P0171",
            "symptoms": "rough idle and poor fuel economy",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2020,
            "mileage": 60000,
            "maintenance_query": "",
        }
        result = QUERY_ROUTER(state)
        assert result == "full_diagnosis"

    def test_route_maintenance_only(self) -> None:
        """Test routing for maintenance query only."""
        state: WorkflowState = {
            "code": "",
            "symptoms": "",
            "make": "",
            "model": "",
            "year": None,
            "mileage": None,
            "maintenance_query": "What maintenance is due?",
        }
        result = QUERY_ROUTER(state)
        assert result == "maintenance_only"

    def test_route_maintenance_with_vehicle(self) -> None:
        """Test routing for maintenance query with vehicle info."""
        state: WorkflowState = {
            "code": "",
            "symptoms": "",
            "make": "Honda",
            "model": "Accord",
            "year": 2018,
            "mileage": None,
            "maintenance_query": "Service recommendations?",
        }
        result = QUERY_ROUTER(state)
        # Should route to maintenance_only (maintenance query overrides vehicle)
        assert result == "maintenance_only"

    def test_route_fallback_no_inputs(self) -> None:
        """Test routing fallback when no inputs provided."""
        state: WorkflowState = {
            "code": "",
            "symptoms": "",
            "make": "",
            "model": "",
            "year": None,
            "mileage": None,
            "maintenance_query": "",
        }
        result = QUERY_ROUTER(state)
        assert result == "fallback"

    def test_route_fallback_whitespace_only(self) -> None:
        """Test routing fallback when only whitespace provided."""
        state: WorkflowState = {
            "code": "   ",
            "symptoms": "   ",
            "make": "   ",
            "model": "   ",
            "year": None,
            "mileage": None,
            "maintenance_query": "   ",
        }
        result = QUERY_ROUTER(state)
        assert result == "fallback"

    def test_route_code_takes_precedence_over_mileage(self) -> None:
        """Test that code takes precedence over mileage in routing."""
        state: WorkflowState = {
            "code": "P0300",
            "symptoms": "",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2020,
            "mileage": 100000,
            "maintenance_query": "",
        }
        result = QUERY_ROUTER(state)
        # Should route to code_vehicle, not vehicle_mileage
        assert result == "code_vehicle"

    def test_route_code_takes_precedence_over_symptoms_vehicle_path(self) -> None:
        """Test that code + symptoms routes to code_symptom, not vehicle_symptom."""
        state: WorkflowState = {
            "code": "P0171",
            "symptoms": "rough idle",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2020,
            "mileage": None,
            "maintenance_query": "",
        }
        result = QUERY_ROUTER(state)
        # With code, should prioritize code_symptom (code + symptoms)
        # Full diagnosis requires both code AND vehicle AND symptoms
        assert result in ["code_symptom", "full_diagnosis"]

    def test_route_consistency_with_different_whitespace(self) -> None:
        """Test that routing is consistent regardless of whitespace variations."""
        state1: WorkflowState = {
            "code": "P0171",
            "symptoms": "",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2020,
            "mileage": None,
            "maintenance_query": "",
        }
        
        state2: WorkflowState = {
            "code": "  P0171  ",
            "symptoms": "  ",
            "make": "  Toyota  ",
            "model": "  Corolla  ",
            "year": 2020,
            "mileage": None,
            "maintenance_query": "  ",
        }
        
        result1 = QUERY_ROUTER(state1)
        result2 = QUERY_ROUTER(state2)
        assert result1 == result2


class TestScenarioDetection:
    """Tests for scenario key detection."""

    def test_scenario_detection_has_code_flag(self) -> None:
        """Test detection of has_code flag."""
        state: WorkflowState = {
            "code": "P0171",
            "symptoms": "",
            "make": "",
            "model": "",
            "year": None,
            "mileage": None,
            "maintenance_query": "",
        }
        result = QUERY_ROUTER(state)
        # Should detect code
        assert result != "fallback"

    def test_scenario_detection_has_symptoms_flag(self) -> None:
        """Test detection of has_symptoms flag."""
        state: WorkflowState = {
            "code": "",
            "symptoms": "engine noise",
            "make": "",
            "model": "",
            "year": None,
            "mileage": None,
            "maintenance_query": "",
        }
        result = QUERY_ROUTER(state)
        assert result == "symptom_only"

    def test_scenario_detection_has_vehicle_flag(self) -> None:
        """Test detection of has_vehicle_or_mileage flag."""
        state: WorkflowState = {
            "code": "",
            "symptoms": "",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2020,
            "mileage": None,
            "maintenance_query": "",
        }
        result = QUERY_ROUTER(state)
        # Vehicle alone without other info
        assert result == "fallback"

    def test_scenario_detection_has_maintenance_query(self) -> None:
        """Test detection of maintenance query."""
        state: WorkflowState = {
            "code": "",
            "symptoms": "",
            "make": "",
            "model": "",
            "year": None,
            "mileage": None,
            "maintenance_query": "What service is due?",
        }
        result = QUERY_ROUTER(state)
        assert result == "maintenance_only"


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_year_as_none(self) -> None:
        """Test that None year is handled correctly."""
        state: WorkflowState = {
            "code": "P0171",
            "symptoms": "",
            "make": "Toyota",
            "model": "Corolla",
            "year": None,
            "mileage": None,
            "maintenance_query": "",
        }
        result = QUERY_ROUTER(state)
        assert result == "code_vehicle"

    def test_mileage_zero(self) -> None:
        """Test that zero mileage is treated as valid."""
        state: WorkflowState = {
            "code": "",
            "symptoms": "",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2020,
            "mileage": 0,
            "maintenance_query": "",
        }
        result = QUERY_ROUTER(state)
        assert result == "vehicle_mileage"

    def test_code_case_sensitivity_in_routing(self) -> None:
        """Test that code routing is case-insensitive."""
        state1: WorkflowState = {
            "code": "P0171",
            "symptoms": "",
            "make": "",
            "model": "",
            "year": None,
            "mileage": None,
            "maintenance_query": "",
        }
        
        state2: WorkflowState = {
            "code": "p0171",
            "symptoms": "",
            "make": "",
            "model": "",
            "year": None,
            "mileage": None,
            "maintenance_query": "",
        }
        
        result1 = QUERY_ROUTER(state1)
        result2 = QUERY_ROUTER(state2)
        assert result1 == result2 == "code_only"

    def test_model_without_make(self) -> None:
        """Test vehicle detection when model provided without make."""
        state: WorkflowState = {
            "code": "",
            "symptoms": "",
            "make": "",
            "model": "Corolla",
            "year": 2020,
            "mileage": None,
            "maintenance_query": "",
        }
        result = QUERY_ROUTER(state)
        # Incomplete vehicle info, should likely be fallback
        assert result == "fallback"
