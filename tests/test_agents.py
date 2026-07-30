"""Unit tests for diagnostic agents."""
import pytest
from backend.agents.code_agent import CodeAgent
from backend.agents.maintenance_agent import MaintenanceAgent
from backend.agents.symptom_agent import SymptomAgent
from backend.graph.state import WorkflowState
from backend.rag.retriever import RAGRetriever


class TestCodeAgent:
    """Tests for CodeAgent DTC lookup."""

    def test_lookup_valid_dtc_p0171(self) -> None:
        """Test lookup of valid DTC code P0171."""
        agent = CodeAgent()
        state: WorkflowState = {"code": "P0171"}
        result = agent.run(state)
        
        code_result = result.get("code_result", {})
        assert code_result.get("code") == "P0171"
        assert "System Too Lean" in code_result.get("description", "")
        assert code_result.get("severity") in ["High", "Medium", "Low"]
        assert isinstance(code_result.get("common_causes", []), list)

    def test_lookup_valid_dtc_p0300(self) -> None:
        """Test lookup of valid DTC code P0300."""
        agent = CodeAgent()
        state: WorkflowState = {"code": "P0300"}
        result = agent.run(state)
        
        code_result = result.get("code_result", {})
        assert code_result.get("code") == "P0300"
        assert "Misfire" in code_result.get("description", "")
        assert isinstance(code_result.get("common_causes", []), list)
        assert len(code_result.get("common_causes", [])) > 0

    def test_lookup_invalid_dtc(self) -> None:
        """Test lookup of invalid/non-existent DTC code."""
        agent = CodeAgent()
        state: WorkflowState = {"code": "INVALID999"}
        result = agent.run(state)
        
        code_result = result.get("code_result", {})
        assert code_result.get("code") == "INVALID999"
        assert "not found" in code_result.get("description", "").lower()
        assert code_result.get("severity") == "Unknown"
        assert code_result.get("common_causes", []) == []

    def test_lookup_empty_code(self) -> None:
        """Test that empty code is handled gracefully."""
        agent = CodeAgent()
        state: WorkflowState = {"code": ""}
        result = agent.run(state)
        
        # State should remain unchanged
        assert result.get("code_result") is None

    def test_lookup_case_insensitive(self) -> None:
        """Test that DTC lookup is case-insensitive."""
        agent = CodeAgent()
        state1: WorkflowState = {"code": "P0171"}
        state2: WorkflowState = {"code": "p0171"}
        
        result1 = agent.run(state1)
        result2 = agent.run(state2)
        
        assert result1.get("code_result") == result2.get("code_result")

    def test_source_tracking(self) -> None:
        """Test that source is tracked in state."""
        agent = CodeAgent()
        state: WorkflowState = {"code": "P0171", "sources": []}
        result = agent.run(state)
        
        sources = result.get("sources", [])
        assert len(sources) > 0
        assert any(s.get("type") == "obd_dataset" for s in sources)


class TestMaintenanceAgent:
    """Tests for MaintenanceAgent."""

    def test_maintenance_toyota_corolla_60k(self) -> None:
        """Test maintenance recommendations for Toyota Corolla at 60k miles."""
        agent = MaintenanceAgent()
        state: WorkflowState = {
            "make": "Toyota",
            "model": "Corolla",
            "mileage": 60000,
        }
        result = agent.run(state)
        
        maintenance_result = result.get("maintenance_result", {})
        assert isinstance(maintenance_result.get("maintenance_recommendations", []), list)
        assert len(maintenance_result.get("maintenance_recommendations", [])) > 0
        assert isinstance(maintenance_result.get("preventive_actions", []), list)

    def test_maintenance_honda_civic_100k(self) -> None:
        """Test maintenance recommendations for Honda Civic at 100k miles."""
        agent = MaintenanceAgent()
        state: WorkflowState = {
            "make": "Honda",
            "model": "Civic",
            "mileage": 100000,
        }
        result = agent.run(state)
        
        maintenance_result = result.get("maintenance_result", {})
        assert len(maintenance_result.get("maintenance_recommendations", [])) > 0

    def test_maintenance_unknown_vehicle(self) -> None:
        """Test maintenance for unknown make/model returns generic recommendations."""
        agent = MaintenanceAgent()
        state: WorkflowState = {
            "make": "UnknownMake",
            "model": "UnknownModel",
            "mileage": 50000,
        }
        result = agent.run(state)
        
        maintenance_result = result.get("maintenance_result", {})
        recommendations = maintenance_result.get("maintenance_recommendations", [])
        # Should return generic recommendations
        assert len(recommendations) > 0
        assert any("multi-point" in r.lower() or "oem" in r.lower() for r in recommendations)

    def test_maintenance_no_mileage(self) -> None:
        """Test maintenance without mileage provided."""
        agent = MaintenanceAgent()
        state: WorkflowState = {
            "make": "Toyota",
            "model": "Corolla",
            "mileage": None,
        }
        result = agent.run(state)
        
        maintenance_result = result.get("maintenance_result", {})
        preventive = maintenance_result.get("preventive_actions", [])
        # Should have generic preventive actions
        assert any("oem" in action.lower() or "manual" in action.lower() for action in preventive)

    def test_maintenance_low_mileage(self) -> None:
        """Test preventive actions for low mileage (< 30k)."""
        agent = MaintenanceAgent()
        state: WorkflowState = {
            "make": "Toyota",
            "model": "Corolla",
            "mileage": 15000,
        }
        result = agent.run(state)
        
        maintenance_result = result.get("maintenance_result", {})
        preventive = maintenance_result.get("preventive_actions", [])
        assert any("rotate" in p.lower() or "tire" in p.lower() for p in preventive)

    def test_maintenance_high_mileage(self) -> None:
        """Test preventive actions for high mileage (> 75k)."""
        agent = MaintenanceAgent()
        state: WorkflowState = {
            "make": "Toyota",
            "model": "Corolla",
            "mileage": 150000,
        }
        result = agent.run(state)
        
        maintenance_result = result.get("maintenance_result", {})
        preventive = maintenance_result.get("preventive_actions", [])
        assert any("timing" in p.lower() or "battery" in p.lower() for p in preventive)

    def test_source_tracking(self) -> None:
        """Test that source is tracked in state."""
        agent = MaintenanceAgent()
        state: WorkflowState = {
            "make": "Toyota",
            "model": "Corolla",
            "mileage": 60000,
            "sources": [],
        }
        result = agent.run(state)
        
        sources = result.get("sources", [])
        assert len(sources) > 0
        assert any(s.get("type") == "maintenance_dataset" for s in sources)


class TestSymptomAgent:
    """Tests for SymptomAgent RAG retrieval."""

    def test_symptom_query_empty_symptoms(self) -> None:
        """Test that empty symptoms are handled gracefully."""
        agent = SymptomAgent()
        state: WorkflowState = {"symptoms": ""}
        result = agent.run(state)
        
        # State should remain unchanged
        assert result.get("symptom_result") is None

    def test_symptom_query_with_symptoms(self) -> None:
        """Test symptom query builds correctly."""
        agent = SymptomAgent()
        state: WorkflowState = {
            "symptoms": "rough idle and hesitation",
            "make": "Toyota",
            "model": "Corolla",
            "code": "P0171",
        }
        result = agent.run(state)
        
        symptom_result = result.get("symptom_result", {})
        assert "symptoms" in symptom_result.get("query", "").lower()
        assert isinstance(symptom_result.get("context", []), list)
        assert isinstance(symptom_result.get("troubleshooting_hints", []), list)

    def test_symptom_query_without_vehicle_context(self) -> None:
        """Test symptom query without vehicle info."""
        agent = SymptomAgent()
        state: WorkflowState = {
            "symptoms": "engine overheating",
        }
        result = agent.run(state)
        
        symptom_result = result.get("symptom_result", {})
        assert isinstance(symptom_result.get("context", []), list)

    def test_rag_retriever_graceful_fallback(self) -> None:
        """Test that RAG retriever fails gracefully if no docs indexed."""
        retriever = RAGRetriever()
        # Try to retrieve (may return empty if no docs)
        docs = retriever.retrieve("test query", k=4)
        
        assert isinstance(docs, list)
        # Should return empty list if no docs, not crash


class TestAgentIntegration:
    """Integration tests between agents."""

    def test_full_state_flow(self) -> None:
        """Test agents updating same state sequentially."""
        # This simulates the workflow
        state: WorkflowState = {
            "code": "P0171",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2020,
            "mileage": 60000,
            "symptoms": "rough idle",
            "sources": [],
        }
        
        # Run code agent
        code_agent = CodeAgent()
        state = code_agent.run(state)
        assert state.get("code_result") is not None
        
        # Run maintenance agent
        maintenance_agent = MaintenanceAgent()
        state = maintenance_agent.run(state)
        assert state.get("maintenance_result") is not None
        
        # Run symptom agent
        symptom_agent = SymptomAgent()
        state = symptom_agent.run(state)
        assert state.get("symptom_result") is not None
        
        # All sources should be tracked
        sources = state.get("sources", [])
        assert len(sources) >= 2  # At least code and maintenance sources
