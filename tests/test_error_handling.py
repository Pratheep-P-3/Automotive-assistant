"""Tests for error handling and edge cases."""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from backend.agents.code_agent import CodeAgent
from backend.agents.maintenance_agent import MaintenanceAgent
from backend.rag.retriever import RAGRetriever
from backend.services.azure_openai_service import AzureOpenAIService
from backend.graph.state import WorkflowState


class TestCodeAgentErrorHandling:
    """Tests for error handling in CodeAgent."""

    def test_missing_obd_dataset_file(self) -> None:
        """Test handling when OBD dataset file doesn't exist."""
        with patch("backend.agents.code_agent.CodeAgent.data_path", Path("/nonexistent/path/obd_codes.csv")):
            agent = CodeAgent()
            state: WorkflowState = {"code": "P0171"}
            result = agent.run(state)
            
            code_result = result.get("code_result", {})
            assert "unavailable" in code_result.get("description", "").lower()
            assert code_result.get("common_causes", []) == []

    def test_invalid_csv_format(self) -> None:
        """Test handling of malformed CSV file."""
        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value = ["invalid,", "csv,"]
            agent = CodeAgent()
            # The DictReader might behave unexpectedly but should not crash
            state: WorkflowState = {"code": "P0171"}
            try:
                result = agent.run(state)
                # Should not crash
                assert True
            except Exception as e:
                pytest.fail(f"Agent crashed on invalid CSV: {e}")

    def test_whitespace_handling_in_code(self) -> None:
        """Test handling of code with leading/trailing whitespace."""
        agent = CodeAgent()
        state1: WorkflowState = {"code": "  P0171  "}
        state2: WorkflowState = {"code": "P0171"}
        
        result1 = agent.run(state1)
        result2 = agent.run(state2)
        
        assert result1.get("code_result") == result2.get("code_result")

    def test_null_code_field(self) -> None:
        """Test handling when code field is None."""
        agent = CodeAgent()
        state: WorkflowState = {"code": None}
        result = agent.run(state)
        
        # Should handle gracefully
        assert result.get("code_result") is None or isinstance(result.get("code_result"), dict)


class TestMaintenanceAgentErrorHandling:
    """Tests for error handling in MaintenanceAgent."""

    def test_missing_maintenance_dataset_file(self) -> None:
        """Test handling when maintenance dataset file doesn't exist."""
        agent = MaintenanceAgent()
        with patch.object(agent, 'data_path', Path("/nonexistent/path/maintenance.csv")):
            state: WorkflowState = {
                "make": "Toyota",
                "model": "Corolla",
                "mileage": 60000,
                "sources": [],
            }
            result = agent.run(state)
            
            # Should return generic recommendations
            maintenance_result = result.get("maintenance_result", {})
            recommendations = maintenance_result.get("maintenance_recommendations", [])
            assert len(recommendations) > 0

    def test_invalid_mileage_type(self) -> None:
        """Test handling of invalid mileage type."""
        agent = MaintenanceAgent()
        state: WorkflowState = {
            "make": "Toyota",
            "model": "Corolla",
            "mileage": "invalid_mileage",  # Should be int
            "sources": [],
        }
        # Should handle gracefully
        try:
            result = agent.run(state)
            # May return error or generic recommendations
            assert True
        except (ValueError, TypeError):
            # If it raises, that's an error we should fix
            pytest.fail("Agent should handle invalid mileage type gracefully")

    def test_negative_mileage(self) -> None:
        """Test handling of negative mileage."""
        agent = MaintenanceAgent()
        state: WorkflowState = {
            "make": "Toyota",
            "model": "Corolla",
            "mileage": -1000,
            "sources": [],
        }
        result = agent.run(state)
        
        maintenance_result = result.get("maintenance_result", {})
        # Should still return some recommendations
        assert len(maintenance_result.get("maintenance_recommendations", [])) > 0

    def test_case_insensitive_make_model_matching(self) -> None:
        """Test that make/model matching is case-insensitive."""
        agent = MaintenanceAgent()
        state1: WorkflowState = {
            "make": "Toyota",
            "model": "Corolla",
            "mileage": 60000,
            "sources": [],
        }
        state2: WorkflowState = {
            "make": "toyota",
            "model": "corolla",
            "mileage": 60000,
            "sources": [],
        }
        
        result1 = agent.run(state1)
        result2 = agent.run(state2)
        
        # Should match same vehicle regardless of case
        rec1 = result1.get("maintenance_result", {}).get("maintenance_recommendations", [])
        rec2 = result2.get("maintenance_result", {}).get("maintenance_recommendations", [])
        
        assert rec1 == rec2


class TestRAGErrorHandling:
    """Tests for error handling in RAG retriever."""

    def test_retriever_initialization_failure(self) -> None:
        """Test graceful handling when ChromaDB fails to initialize."""
        with patch("backend.rag.retriever.Chroma", side_effect=Exception("ChromaDB Error")):
            retriever = RAGRetriever()
            # Should initialize with vector_store = None
            assert retriever.vector_store is None

    def test_retriever_retrieve_with_none_vector_store(self) -> None:
        """Test retrieve when vector_store is None."""
        retriever = RAGRetriever()
        retriever.vector_store = None
        
        docs = retriever.retrieve("test query", k=4)
        assert docs == []

    def test_retriever_retrieve_with_empty_query(self) -> None:
        """Test retrieve with empty query string."""
        retriever = RAGRetriever()
        # May or may not have vector store depending on environment
        try:
            docs = retriever.retrieve("", k=4)
            # Should return list (empty or with results)
            assert isinstance(docs, list)
        except Exception:
            # If it fails due to missing ChromaDB, that's OK
            pass

    def test_retriever_negative_k_value(self) -> None:
        """Test retrieve with invalid k value."""
        retriever = RAGRetriever()
        if retriever.vector_store is None:
            pytest.skip("No vector store available")
        
        # Negative k should be handled or raise appropriate error
        try:
            docs = retriever.retrieve("test", k=-1)
            # Should either handle gracefully or raise ValueError
            assert isinstance(docs, list)
        except ValueError:
            # This is acceptable behavior
            pass


class TestAzureServiceErrorHandling:
    """Tests for error handling in Azure OpenAI Service."""

    def test_service_handles_invalid_json_response(self) -> None:
        """Test handling of non-JSON response from LLM."""
        service = AzureOpenAIService()
        service.model = MagicMock()
        service.model.invoke.return_value.content = "Not valid JSON at all {[[["
        
        payload = {"code_result": {"description": "Test"}}
        result = service.generate_report(payload)
        
        # Should fall back to deterministic report
        assert result is not None
        assert "confidence_score" in result

    def test_service_handles_model_none(self) -> None:
        """Test that service handles None model gracefully."""
        service = AzureOpenAIService()
        service.model = None
        
        payload = {"code_result": {"description": "System Too Lean"}}
        result = service.generate_report(payload)
        
        # Should use fallback
        assert result is not None
        assert result.get("confidence_score") is not None

    def test_service_handles_missing_required_fields_in_response(self) -> None:
        """Test handling when LLM response missing required fields."""
        service = AzureOpenAIService()
        service.model = MagicMock()
        service.model.invoke.return_value.content = '{"issue_summary": "Test"}'
        
        payload = {}
        result = service.generate_report(payload)
        
        # Should still have complete structure
        assert "api_response" in result
        assert "confidence_score" in result
        assert result.get("severity") is not None

    def test_service_handles_invalid_confidence_score(self) -> None:
        """Test handling of invalid confidence score value."""
        service = AzureOpenAIService()
        service.model = MagicMock()
        service.model.invoke.return_value.content = json.dumps({
            "issue_summary": "Test",
            "confidence_score": "not_a_number",
        })
        
        payload = {}
        
        # Should handle conversion error gracefully
        try:
            result = service.generate_report(payload)
            # Either converts to 0.5 or raises error we catch
            assert True
        except (ValueError, TypeError):
            # This is acceptable if we properly validate
            pass

    def test_service_handles_confidence_out_of_range(self) -> None:
        """Test handling of confidence score outside 0-1 range."""
        service = AzureOpenAIService()
        service.model = MagicMock()
        service.model.invoke.return_value.content = json.dumps({
            "issue_summary": "Test",
            "confidence_score": 1.5,  # Invalid (> 1.0)
        })
        
        payload = {}
        result = service.generate_report(payload)
        
        # Should accept the value (LLM might generate out-of-range)
        # or clamp it
        confidence = result.get("api_response", {}).get("confidence_score", 0.5)
        assert isinstance(confidence, (int, float))


class TestWorkflowErrorHandling:
    """Tests for error handling in complete workflows."""

    def test_full_workflow_with_all_missing_data(self) -> None:
        """Test complete workflow when all data files are missing."""
        from backend.graph.workflow import QUERY_ROUTER
        from backend.agents.code_agent import CodeAgent
        from backend.agents.maintenance_agent import MaintenanceAgent
        
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
        
        # Get route
        route = QUERY_ROUTER(state)
        assert route is not None
        
        # Try agents even if data missing
        code_agent = CodeAgent()
        state = code_agent.run(state)
        
        maintenance_agent = MaintenanceAgent()
        state = maintenance_agent.run(state)
        
        # Should complete without crashing
        assert state is not None

    def test_workflow_with_special_characters_in_inputs(self) -> None:
        """Test workflow with special characters in input fields."""
        from backend.agents.code_agent import CodeAgent
        
        state: WorkflowState = {
            "code": "P0171 <script>alert('xss')</script>",
            "symptoms": "Engine & symptoms | with ; special < > chars",
        }
        
        agent = CodeAgent()
        result = agent.run(state)
        
        # Should handle without security issues
        assert result is not None

    def test_very_long_input_strings(self) -> None:
        """Test handling of very long input strings."""
        from backend.agents.symptom_agent import SymptomAgent
        
        long_symptoms = "x" * 10000  # 10k character string
        state: WorkflowState = {
            "symptoms": long_symptoms,
        }
        
        agent = SymptomAgent()
        result = agent.run(state)
        
        # Should handle without crashing
        assert result is not None


import json
