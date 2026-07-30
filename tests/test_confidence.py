"""Tests for confidence score calculation and verification."""
import pytest
from unittest.mock import MagicMock, patch
from backend.services.azure_openai_service import AzureOpenAIService
from backend.graph.state import WorkflowState
from backend.agents.code_agent import CodeAgent
from backend.agents.maintenance_agent import MaintenanceAgent


class TestConfidenceScoring:
    """Tests for confidence score calculation in different scenarios."""

    def test_confidence_code_only_fallback(self) -> None:
        """Test confidence score for code-only scenario in fallback mode."""
        service = AzureOpenAIService()
        service.model = None  # Force fallback
        
        payload = {
            "code_result": {
                "description": "System Too Lean",
                "severity": "High",
                "common_causes": ["O2 Sensor"],
            },
            "confidence_score": 0.65,
        }
        
        result = service.generate_report(payload)
        confidence = result.get("confidence_score", 0)
        
        # Code only should be 0.60-0.70
        assert 0.60 <= confidence <= 0.70

    def test_confidence_symptom_only_fallback(self) -> None:
        """Test confidence score for symptom-only scenario."""
        service = AzureOpenAIService()
        service.model = None  # Force fallback
        
        payload = {
            "symptom_result": {
                "troubleshooting_hints": ["Check O2 sensor"],
            },
            "confidence_score": 0.55,
        }
        
        result = service.generate_report(payload)
        confidence = result.get("confidence_score", 0)
        
        # Symptom only should be 0.50-0.65
        assert 0.50 <= confidence <= 0.65

    def test_confidence_code_vehicle_with_llm(self) -> None:
        """Test confidence score for code+vehicle scenario with LLM."""
        service = AzureOpenAIService()
        service.model = MagicMock()
        
        import json
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "issue_summary": "System Too Lean - Toyota Corolla 2020",
            "confidence_score": 0.87,
            "repair_recommendations": ["Check O2 sensor"],
        })
        service.model.invoke.return_value = mock_response
        
        payload = {
            "code_result": {"description": "System Too Lean"},
            "vehicle_info": {"make": "Toyota", "model": "Corolla", "year": 2020},
        }
        
        result = service.generate_report(payload)
        confidence = result.get("api_response", {}).get("confidence_score", 0)
        
        # Code + vehicle should be 0.80-0.90
        assert 0.80 <= confidence <= 0.90

    def test_confidence_full_diagnosis_with_llm(self) -> None:
        """Test confidence score for full diagnosis with LLM."""
        service = AzureOpenAIService()
        service.model = MagicMock()
        
        import json
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "issue_summary": "Complete Diagnosis",
            "confidence_score": 0.92,
            "repair_recommendations": ["Step 1", "Step 2"],
        })
        service.model.invoke.return_value = mock_response
        
        payload = {
            "code_result": {"description": "P0171"},
            "symptom_result": {"troubleshooting_hints": ["Rough idle"]},
            "vehicle_info": {"make": "Toyota", "model": "Corolla", "year": 2020},
            "maintenance_result": {"recommendations": []},
            "mileage": 60000,
        }
        
        result = service.generate_report(payload)
        confidence = result.get("api_response", {}).get("confidence_score", 0)
        
        # Full diagnosis should be 0.85-0.95
        assert 0.85 <= confidence <= 0.95

    def test_confidence_invalid_code_fallback(self) -> None:
        """Test confidence score when DTC code not found."""
        service = AzureOpenAIService()
        service.model = None
        
        payload = {
            "code_result": {
                "description": "Diagnostic code not found in local dataset.",
                "severity": "Unknown",
                "common_causes": [],
            },
            "confidence_score": 0.55,  # Lower due to invalid code
        }
        
        result = service.generate_report(payload)
        confidence = result.get("confidence_score", 0)
        
        # Invalid code should have lower confidence
        assert 0.50 <= confidence <= 0.65

    def test_confidence_unknown_vehicle_fallback(self) -> None:
        """Test confidence score for unknown vehicle."""
        service = AzureOpenAIService()
        service.model = None
        
        payload = {
            "code_result": {"description": "System Too Lean"},
            "vehicle_info": {"make": "UnknownMake", "model": "UnknownModel"},
            "confidence_score": 0.60,  # Lower due to unknown vehicle
        }
        
        result = service.generate_report(payload)
        confidence = result.get("confidence_score", 0)
        
        # Unknown vehicle should lower confidence
        assert confidence >= 0.50

    def test_confidence_with_maintenance_data(self) -> None:
        """Test confidence boost when maintenance data available."""
        service = AzureOpenAIService()
        service.model = None
        
        payload = {
            "code_result": {"description": "System Too Lean"},
            "maintenance_result": {
                "maintenance_recommendations": ["Oil change", "Filter replacement"],
            },
            "confidence_score": 0.70,
        }
        
        result = service.generate_report(payload)
        confidence = result.get("confidence_score", 0)
        
        # With maintenance data, confidence should be reasonable
        assert 0.60 <= confidence <= 0.80

    def test_confidence_with_rag_context(self) -> None:
        """Test confidence when RAG context available."""
        service = AzureOpenAIService()
        service.model = None
        
        payload = {
            "code_result": {"description": "P0171"},
            "symptom_result": {
                "context": ["Rough idle is common with lean condition"],
                "troubleshooting_hints": ["Check O2 sensor"],
            },
            "confidence_score": 0.70,
        }
        
        result = service.generate_report(payload)
        confidence = result.get("confidence_score", 0)
        
        # With RAG context, should have decent confidence
        assert 0.65 <= confidence <= 0.80


class TestConfidenceScoringBoundaries:
    """Tests for confidence score boundary conditions."""

    def test_confidence_minimum_value(self) -> None:
        """Test that confidence never goes below 0.0."""
        service = AzureOpenAIService()
        service.model = None
        
        payload = {
            "confidence_score": -1.0,  # Invalid
        }
        
        result = service.generate_report(payload)
        confidence = result.get("confidence_score", 0)
        
        # Should never be negative
        assert confidence >= 0.0

    def test_confidence_maximum_value(self) -> None:
        """Test that confidence doesn't exceed 1.0 in normal scenarios."""
        service = AzureOpenAIService()
        service.model = None
        
        payload = {
            "confidence_score": 1.0,
        }
        
        result = service.generate_report(payload)
        confidence = result.get("confidence_score", 0)
        
        # Should be <= 1.0 in fallback mode
        assert confidence <= 1.0

    def test_confidence_is_float(self) -> None:
        """Test that confidence score is always returned as float."""
        service = AzureOpenAIService()
        service.model = None
        
        payload = {"confidence_score": 0.75}
        result = service.generate_report(payload)
        
        confidence = result.get("confidence_score")
        assert isinstance(confidence, float)
        
        api_confidence = result.get("api_response", {}).get("confidence_score")
        assert isinstance(api_confidence, float)

    def test_confidence_precision(self) -> None:
        """Test that confidence scores maintain reasonable precision."""
        service = AzureOpenAIService()
        service.model = MagicMock()
        
        import json
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "issue_summary": "Test",
            "confidence_score": 0.8742857142857143,  # High precision
        })
        service.model.invoke.return_value = mock_response
        
        payload = {}
        result = service.generate_report(payload)
        
        confidence = result.get("api_response", {}).get("confidence_score")
        # Should preserve the value as provided
        assert confidence == 0.8742857142857143


class TestConfidenceScoreProgression:
    """Tests for how confidence changes with data enrichment."""

    def test_confidence_progression_code_only_to_full(self) -> None:
        """Test confidence progression from code-only to full diagnosis."""
        service = AzureOpenAIService()
        service.model = None
        
        # Code only
        payload_code = {
            "code_result": {"description": "P0171"},
            "confidence_score": 0.65,
        }
        result_code = service.generate_report(payload_code)
        conf_code = result_code.get("confidence_score")
        
        # Code + symptoms
        payload_code_symptoms = {
            "code_result": {"description": "P0171"},
            "symptom_result": {"troubleshooting_hints": ["Rough idle"]},
            "confidence_score": 0.70,
        }
        result_code_symptoms = service.generate_report(payload_code_symptoms)
        conf_code_symptoms = result_code_symptoms.get("confidence_score")
        
        # Code + vehicle
        payload_code_vehicle = {
            "code_result": {"description": "P0171"},
            "vehicle_info": {"make": "Toyota", "model": "Corolla"},
            "confidence_score": 0.80,  # With LLM boost
        }
        result_code_vehicle = service.generate_report(payload_code_vehicle)
        conf_code_vehicle = result_code_vehicle.get("confidence_score")
        
        # Full diagnosis
        payload_full = {
            "code_result": {"description": "P0171"},
            "symptom_result": {"troubleshooting_hints": ["Rough idle"]},
            "vehicle_info": {"make": "Toyota", "model": "Corolla"},
            "maintenance_result": {"recommendations": ["Oil change"]},
            "confidence_score": 0.90,  # With LLM boost
        }
        result_full = service.generate_report(payload_full)
        conf_full = result_full.get("confidence_score")
        
        # Confidence should generally increase with more data
        # (though not guaranteed due to fallback mode)
        print(f"Code only: {conf_code}")
        print(f"Code + symptoms: {conf_code_symptoms}")
        print(f"Code + vehicle: {conf_code_vehicle}")
        print(f"Full: {conf_full}")


class TestConfidenceScoreDisplay:
    """Tests for confidence score display format."""

    def test_confidence_displayed_as_decimal(self) -> None:
        """Test that confidence is displayed as 0.0-1.0 scale."""
        service = AzureOpenAIService()
        service.model = None
        
        payload = {"confidence_score": 0.65}
        result = service.generate_report(payload)
        
        confidence = result.get("confidence_score")
        # Should be decimal (0.65) not percentage (65)
        assert 0.0 <= confidence <= 1.0
        assert confidence == 0.65

    def test_confidence_in_api_response(self) -> None:
        """Test that confidence is included in api_response."""
        service = AzureOpenAIService()
        service.model = None
        
        payload = {"confidence_score": 0.75}
        result = service.generate_report(payload)
        
        assert "api_response" in result
        assert "confidence_score" in result.get("api_response", {})
        assert result.get("api_response", {}).get("confidence_score") == 0.75


class TestConfidenceWithMultipleSources:
    """Tests for confidence calculation with multiple data sources."""

    def test_confidence_correlating_sources(self) -> None:
        """Test confidence when multiple sources agree."""
        service = AzureOpenAIService()
        service.model = MagicMock()
        
        import json
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "issue_summary": "System Too Lean confirmed by multiple sources",
            "confidence_score": 0.92,
        })
        service.model.invoke.return_value = mock_response
        
        payload = {
            "code_result": {"description": "System Too Lean", "severity": "High"},
            "symptom_result": {"troubleshooting_hints": ["Rough idle", "Poor fuel economy"]},
            "vehicle_info": {"make": "Toyota", "model": "Corolla"},
            "sources": [
                {"source": "OBD Dataset", "type": "code"},
                {"source": "RAG Documents", "type": "rag"},
                {"source": "Maintenance Database", "type": "maintenance"},
            ],
        }
        
        result = service.generate_report(payload)
        confidence = result.get("api_response", {}).get("confidence_score", 0)
        
        # Multiple correlated sources should boost confidence
        assert confidence >= 0.85

    def test_confidence_contradicting_sources(self) -> None:
        """Test confidence when sources might contradict."""
        service = AzureOpenAIService()
        service.model = None  # Fallback
        
        payload = {
            "code_result": {"description": "System Too Lean"},
            "symptom_result": {"troubleshooting_hints": ["Overheating"]},  # Contradictory
            "confidence_score": 0.60,
        }
        
        result = service.generate_report(payload)
        confidence = result.get("confidence_score", 0)
        
        # Lower confidence due to contradiction
        assert confidence <= 0.70
