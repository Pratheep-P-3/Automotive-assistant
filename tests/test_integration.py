"""Integration tests for complete end-to-end workflows."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.app import app
from backend.graph.state import WorkflowState
from backend.graph.workflow import QUERY_ROUTER
from backend.agents.code_agent import CodeAgent
from backend.agents.maintenance_agent import MaintenanceAgent
from backend.agents.symptom_agent import SymptomAgent
from backend.rag.retriever import RAGRetriever
from backend.services.azure_openai_service import AzureOpenAIService

client = TestClient(app)


class TestFullDiagnosisWorkflow:
    """Integration tests for complete diagnostic workflows."""

    def test_workflow_code_only_scenario(self) -> None:
        """Test complete workflow for code-only scenario."""
        # Route detection
        state: WorkflowState = {
            "code": "P0171",
            "symptoms": "",
            "make": "",
            "model": "",
            "year": None,
            "mileage": None,
            "maintenance_query": "",
            "sources": [],
        }
        route = QUERY_ROUTER(state)
        assert route == "code_only"
        
        # Code agent
        code_agent = CodeAgent()
        state = code_agent.run(state)
        
        code_result = state.get("code_result", {})
        assert code_result.get("code") == "P0171"
        assert "System Too Lean" in code_result.get("description", "")
        assert len(code_result.get("common_causes", [])) > 0

    def test_workflow_code_vehicle_scenario(self) -> None:
        """Test complete workflow for code+vehicle scenario."""
        state: WorkflowState = {
            "code": "P0171",
            "symptoms": "",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2020,
            "mileage": None,
            "maintenance_query": "",
            "sources": [],
        }
        
        # Route should be code_vehicle
        route = QUERY_ROUTER(state)
        assert route == "code_vehicle"
        
        # Code agent
        code_agent = CodeAgent()
        state = code_agent.run(state)
        assert state.get("code_result") is not None
        
        # Maintenance agent
        maintenance_agent = MaintenanceAgent()
        state = maintenance_agent.run(state)
        assert state.get("maintenance_result") is not None
        
        # LLM report generation
        llm_service = AzureOpenAIService()
        payload = {
            "code_result": state.get("code_result"),
            "vehicle_info": {
                "make": state.get("make"),
                "model": state.get("model"),
                "year": state.get("year"),
            },
            "maintenance_result": state.get("maintenance_result"),
            "sources": state.get("sources", []),
        }
        report = llm_service.generate_report(payload)
        
        # Should have complete structure
        assert "issue_summary" in report
        assert "api_response" in report
        confidence = report.get("api_response", {}).get("confidence_score", 0)
        assert 0.0 <= confidence <= 1.0

    def test_workflow_full_diagnosis_scenario(self) -> None:
        """Test complete workflow with all diagnostic inputs."""
        state: WorkflowState = {
            "code": "P0171",
            "symptoms": "rough idle and poor fuel economy",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2020,
            "mileage": 60000,
            "maintenance_query": "",
            "sources": [],
        }
        
        # Route should be full_diagnosis
        route = QUERY_ROUTER(state)
        assert route == "full_diagnosis"
        
        # Execute all agents
        code_agent = CodeAgent()
        state = code_agent.run(state)
        
        maintenance_agent = MaintenanceAgent()
        state = maintenance_agent.run(state)
        
        symptom_agent = SymptomAgent()
        state = symptom_agent.run(state)
        
        # Verify all results populated
        assert state.get("code_result") is not None
        assert state.get("maintenance_result") is not None
        assert state.get("symptom_result") is not None
        
        # Generate report
        llm_service = AzureOpenAIService()
        payload = {
            "code_result": state.get("code_result"),
            "symptom_result": state.get("symptom_result"),
            "vehicle_info": {
                "make": state.get("make"),
                "model": state.get("model"),
                "year": state.get("year"),
            },
            "maintenance_result": state.get("maintenance_result"),
            "mileage": state.get("mileage"),
            "sources": state.get("sources", []),
        }
        report = llm_service.generate_report(payload)
        
        assert "issue_summary" in report
        assert len(report.get("repair_recommendations", [])) > 0
        assert len(report.get("maintenance_recommendations", [])) > 0

    def test_workflow_symptom_only_scenario(self) -> None:
        """Test complete workflow for symptom-only scenario."""
        state: WorkflowState = {
            "code": "",
            "symptoms": "engine overheating and coolant loss",
            "make": "",
            "model": "",
            "year": None,
            "mileage": None,
            "maintenance_query": "",
            "sources": [],
        }
        
        route = QUERY_ROUTER(state)
        assert route == "symptom_only"
        
        # Symptom agent
        symptom_agent = SymptomAgent()
        state = symptom_agent.run(state)
        
        symptom_result = state.get("symptom_result", {})
        assert isinstance(symptom_result.get("context", []), list)
        assert isinstance(symptom_result.get("troubleshooting_hints", []), list)

    def test_workflow_maintenance_only_scenario(self) -> None:
        """Test complete workflow for maintenance query."""
        state: WorkflowState = {
            "code": "",
            "symptoms": "",
            "make": "Honda",
            "model": "Accord",
            "year": 2018,
            "mileage": 80000,
            "maintenance_query": "What service is due at 80k miles?",
            "sources": [],
        }
        
        route = QUERY_ROUTER(state)
        assert route == "maintenance_only"
        
        # Maintenance agent
        maintenance_agent = MaintenanceAgent()
        state = maintenance_agent.run(state)
        
        maintenance_result = state.get("maintenance_result", {})
        assert len(maintenance_result.get("maintenance_recommendations", [])) > 0

    def test_workflow_fallback_scenario(self) -> None:
        """Test complete workflow when no sufficient input data."""
        state: WorkflowState = {
            "code": "",
            "symptoms": "",
            "make": "",
            "model": "",
            "year": None,
            "mileage": None,
            "maintenance_query": "",
            "sources": [],
        }
        
        route = QUERY_ROUTER(state)
        assert route == "fallback"
        
        # Should generate default report
        llm_service = AzureOpenAIService()
        llm_service.model = None  # Force fallback
        
        report = llm_service.generate_report({"confidence_score": 0.5})
        assert "issue_summary" in report
        # Fallback confidence should be low
        assert report.get("confidence_score") <= 0.65


class TestAPIEndpointIntegration:
    """Integration tests for API endpoints."""

    def test_api_diagnose_with_code_only(self) -> None:
        """Test /diagnose endpoint with code only."""
        payload = {
            "code": "P0171",
        }
        response = client.post("/diagnose", json=payload)
        
        assert response.status_code == 200
        body = response.json()
        
        assert "diagnosis" in body
        assert body.get("code") == "P0171"
        assert isinstance(body.get("confidence_score"), float)
        assert 0.0 <= body.get("confidence_score", 0) <= 1.0

    def test_api_diagnose_with_vehicle_info(self) -> None:
        """Test /diagnose endpoint with vehicle information."""
        payload = {
            "make": "Toyota",
            "model": "Corolla",
            "year": 2020,
            "code": "P0171",
        }
        response = client.post("/diagnose", json=payload)
        
        assert response.status_code == 200
        body = response.json()
        
        assert "diagnosis" in body
        # Confidence should be higher with vehicle info
        assert body.get("confidence_score", 0) >= 0.65

    def test_api_diagnose_with_full_info(self) -> None:
        """Test /diagnose endpoint with all diagnostic information."""
        payload = {
            "make": "Toyota",
            "model": "Corolla",
            "year": 2020,
            "mileage": 60000,
            "code": "P0171",
            "symptoms": "rough idle and poor fuel economy",
        }
        response = client.post("/diagnose", json=payload)
        
        assert response.status_code == 200
        body = response.json()
        
        expected_keys = {
            "diagnosis",
            "severity",
            "possible_causes",
            "repair_steps",
            "maintenance_recommendations",
            "confidence_score",
            "sources",
        }
        assert expected_keys.issubset(body.keys())

    def test_api_diagnose_with_invalid_code(self) -> None:
        """Test /diagnose endpoint with invalid DTC code."""
        payload = {
            "code": "INVALID999",
        }
        response = client.post("/diagnose", json=payload)
        
        assert response.status_code == 200
        body = response.json()
        
        # Should still return response, but with lower confidence
        assert "diagnosis" in body
        assert body.get("confidence_score", 0) <= 0.65

    def test_api_diagnose_with_symptoms_only(self) -> None:
        """Test /diagnose endpoint with symptoms only."""
        payload = {
            "symptoms": "engine overheating, temperature gauge high",
        }
        response = client.post("/diagnose", json=payload)
        
        assert response.status_code == 200
        body = response.json()
        
        assert "diagnosis" in body

    def test_api_diagnose_empty_payload(self) -> None:
        """Test /diagnose endpoint with empty payload."""
        payload = {}
        response = client.post("/diagnose", json=payload)
        
        # Should either return 200 with fallback or 400 with error message
        # depending on implementation
        assert response.status_code in [200, 400, 422]

    def test_api_health_endpoint(self) -> None:
        """Test /health endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        body = response.json()
        assert body.get("status") == "ok"


class TestMultipleScenarioSequence:
    """Integration tests for running multiple scenarios in sequence."""

    def test_run_multiple_diagnoses(self) -> None:
        """Test running multiple different diagnoses."""
        test_cases = [
            {"code": "P0171", "make": "Toyota", "model": "Corolla"},
            {"code": "P0300", "symptoms": "engine misfire"},
            {"make": "Honda", "model": "Civic", "year": 2018, "mileage": 100000},
            {"symptoms": "brake grinding noise"},
        ]
        
        for test_payload in test_cases:
            response = client.post("/diagnose", json=test_payload)
            assert response.status_code == 200
            body = response.json()
            assert "diagnosis" in body
            assert isinstance(body.get("confidence_score"), float)

    def test_state_isolation_between_runs(self) -> None:
        """Test that state is isolated between different diagnoses."""
        payload1 = {"code": "P0171", "make": "Toyota"}
        payload2 = {"code": "P0300", "make": "Honda"}
        
        response1 = client.post("/diagnose", json=payload1)
        response2 = client.post("/diagnose", json=payload2)
        
        body1 = response1.json()
        body2 = response2.json()
        
        # Results should be different
        # P0171 is lean, P0300 is misfire
        assert body1.get("diagnosis") != body2.get("diagnosis")


class TestDataConsistency:
    """Integration tests for data consistency across workflow."""

    def test_sources_tracked_through_workflow(self) -> None:
        """Test that data sources are properly tracked."""
        state: WorkflowState = {
            "code": "P0171",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2020,
            "mileage": 60000,
            "symptoms": "",
            "maintenance_query": "",
            "sources": [],
        }
        
        code_agent = CodeAgent()
        state = code_agent.run(state)
        sources_after_code = len(state.get("sources", []))
        assert sources_after_code > 0
        
        maintenance_agent = MaintenanceAgent()
        state = maintenance_agent.run(state)
        sources_after_maintenance = len(state.get("sources", []))
        assert sources_after_maintenance > sources_after_code
        
        # All sources should have required fields
        for source in state.get("sources", []):
            assert "source" in source
            assert "type" in source

    def test_result_structure_consistency(self) -> None:
        """Test that result structure is consistent across scenarios."""
        scenarios = [
            {"code": "P0171"},
            {"code": "P0171", "make": "Toyota", "model": "Corolla"},
            {"symptoms": "rough idle"},
            {"make": "Toyota", "model": "Corolla", "mileage": 60000},
        ]
        
        required_api_response_fields = [
            "diagnosis",
            "severity",
            "possible_causes",
            "repair_steps",
            "maintenance_recommendations",
            "confidence_score",
            "sources",
        ]
        
        for scenario in scenarios:
            response = client.post("/diagnose", json=scenario)
            assert response.status_code == 200
            body = response.json()
            
            # Check all required fields present
            for field in required_api_response_fields:
                assert field in body, f"Missing field {field} in scenario {scenario}"

    def test_confidence_score_consistency(self) -> None:
        """Test that confidence scores are consistent in type and range."""
        scenarios = [
            {"code": "P0171"},
            {"symptoms": "overheating"},
            {"code": "P0171", "make": "Toyota", "model": "Corolla", "year": 2020},
        ]
        
        for scenario in scenarios:
            response = client.post("/diagnose", json=scenario)
            body = response.json()
            
            confidence = body.get("confidence_score")
            assert isinstance(confidence, float), f"Confidence not float in {scenario}"
            assert 0.0 <= confidence <= 1.0, f"Confidence out of range in {scenario}"


class TestErrorRecovery:
    """Integration tests for error handling and recovery."""

    def test_recovery_from_invalid_input(self) -> None:
        """Test system recovery after invalid input."""
        # First request with invalid input
        response1 = client.post("/diagnose", json={"code": "INVALID"})
        assert response1.status_code == 200  # Should handle gracefully
        
        # Second request with valid input should work
        response2 = client.post("/diagnose", json={"code": "P0171"})
        assert response2.status_code == 200
        body2 = response2.json()
        assert "P0171" in body2.get("diagnosis", "").upper()

    def test_malformed_json_handling(self) -> None:
        """Test handling of malformed requests."""
        # Send invalid JSON (depends on FastAPI validation)
        response = client.post(
            "/diagnose",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )
        # Should return 400 or 422 error
        assert response.status_code >= 400

    def test_missing_required_headers(self) -> None:
        """Test handling of requests with missing headers."""
        response = client.post("/diagnose", json={"code": "P0171"})
        # Should still work (FastAPI handles this)
        assert response.status_code == 200


class TestPerformanceAndReliability:
    """Integration tests for performance and reliability."""

    def test_response_time_code_only(self) -> None:
        """Test response time for code-only diagnosis."""
        import time
        start = time.time()
        response = client.post("/diagnose", json={"code": "P0171"})
        elapsed = time.time() - start
        
        assert response.status_code == 200
        # Should complete within reasonable time (5 seconds)
        assert elapsed < 5.0

    def test_response_time_full_diagnosis(self) -> None:
        """Test response time for full diagnosis with LLM."""
        import time
        start = time.time()
        response = client.post("/diagnose", json={
            "code": "P0171",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2020,
            "mileage": 60000,
            "symptoms": "rough idle",
        })
        elapsed = time.time() - start
        
        assert response.status_code == 200
        # LLM requests may take longer (10 seconds)
        assert elapsed < 15.0

    def test_large_symptom_string(self) -> None:
        """Test handling of large symptom descriptions."""
        long_symptoms = "Check engine light on. " * 100  # 2400+ chars
        response = client.post("/diagnose", json={"symptoms": long_symptoms})
        
        assert response.status_code == 200
        body = response.json()
        assert "diagnosis" in body
