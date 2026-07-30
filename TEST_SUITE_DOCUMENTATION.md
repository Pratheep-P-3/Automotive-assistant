# Comprehensive Test Suite Documentation

## Overview

Created **6 comprehensive test modules** with **150+ test cases** covering all critical areas of the Automotive Diagnostics Assistant.

---

## Test Files Created

### 1. **test_agents.py** (35+ tests)
**Purpose**: Unit tests for individual diagnostic agents

**Coverage**:
- ✅ CodeAgent: Valid DTC lookups, invalid codes, case sensitivity, whitespace handling
- ✅ MaintenanceAgent: Vehicle-specific recommendations, mileage-based logic, unknown vehicles
- ✅ SymptomAgent: Symptom querying, RAG retrieval, graceful fallback
- ✅ Agent Integration: State flow between agents, source tracking

**Key Test Cases**:
- `test_lookup_valid_dtc_p0171()` - P0171 returns "System Too Lean"
- `test_lookup_invalid_dtc()` - INVALID999 returns "not found" gracefully
- `test_maintenance_toyota_corolla_60k()` - Vehicle-specific recommendations
- `test_maintenance_unknown_vehicle()` - Returns generic recommendations
- `test_full_state_flow()` - All agents work with same state

---

### 2. **test_routing.py** (25+ tests)
**Purpose**: Tests for query router logic and scenario detection

**Coverage**:
- ✅ All 9 routing scenarios:
  - code_only
  - symptom_only
  - code_symptom
  - code_vehicle ⭐
  - vehicle_mileage
  - vehicle_symptom
  - full_diagnosis ⭐⭐
  - maintenance_only
  - fallback
- ✅ Route decision logic and precedence
- ✅ Whitespace and case-insensitive matching
- ✅ Edge cases (None values, zero mileage, incomplete vehicle info)

**Key Test Cases**:
- `test_route_code_vehicle()` - Code + vehicle routes to "code_vehicle"
- `test_route_full_diagnosis()` - All inputs route to "full_diagnosis"
- `test_route_fallback_no_inputs()` - Empty inputs fallback
- `test_route_consistency_with_different_whitespace()` - Handles formatting
- `test_code_takes_precedence_over_mileage()` - Routing priority

---

### 3. **test_llm_service.py** (30+ tests)
**Purpose**: LLM integration, response parsing, and Azure Foundry testing

**Coverage**:
- ✅ Azure OpenAI service initialization
- ✅ Foundry endpoint detection (OpenAI-compatible format)
- ✅ JSON response parsing and extraction
- ✅ Markdown code fence handling
- ✅ Missing/invalid response fields
- ✅ Confidence score extraction
- ✅ API response structure validation
- ✅ Fallback report generation

**Key Test Cases**:
- `test_service_initialization_with_foundry_endpoint()` - Detects Foundry format
- `test_strip_fences_with_markdown_code_block()` - Removes ```json``` fences
- `test_response_parsing_valid_json()` - Parses complete LLM response
- `test_response_parsing_markdown_json()` - Handles markdown-wrapped JSON
- `test_response_parsing_missing_confidence()` - Defaults to 0.5
- `test_response_parsing_invalid_json()` - Falls back gracefully

---

### 4. **test_error_handling.py** (35+ tests)
**Purpose**: Error scenarios, missing data, and edge cases

**Coverage**:
- ✅ Missing data files (OBD, maintenance CSV)
- ✅ Invalid/malformed data formats
- ✅ Invalid input types (negative mileage, string mileage)
- ✅ Whitespace and special characters
- ✅ RAG retriever failures
- ✅ LLM response errors
- ✅ None/null fields
- ✅ Very long input strings
- ✅ Security edge cases (XSS-like inputs)

**Key Test Cases**:
- `test_missing_obd_dataset_file()` - Returns "unavailable" gracefully
- `test_missing_maintenance_dataset_file()` - Returns generic recommendations
- `test_invalid_csv_format()` - Doesn't crash
- `test_retriever_initialization_failure()` - Sets vector_store=None
- `test_service_handles_invalid_json_response()` - Falls back to deterministic
- `test_negative_mileage()` - Handles gracefully
- `test_very_long_input_strings()` - Doesn't crash with 10k+ chars

---

### 5. **test_confidence.py** (25+ tests)
**Purpose**: Confidence score calculation and verification

**Coverage**:
- ✅ Confidence ranges for each scenario
- ✅ Confidence progression (code → vehicle → full → LLM)
- ✅ LLM confidence boost (0.65 fallback vs 0.85+ with LLM)
- ✅ Confidence boundaries (0.0-1.0 range)
- ✅ Type validation (always float)
- ✅ Multiple data sources correlation
- ✅ Missing/contradicting data impact

**Key Test Cases**:
- `test_confidence_code_only_fallback()` - 0.60-0.70 range
- `test_confidence_code_vehicle_with_llm()` - 0.80-0.90 range ⭐
- `test_confidence_full_diagnosis_with_llm()` - 0.85-0.95 range ⭐⭐
- `test_confidence_progression_code_only_to_full()` - Shows escalation
- `test_confidence_unknown_vehicle_fallback()` - Lowers score appropriately
- `test_confidence_with_maintenance_data()` - Boost from additional data
- `test_confidence_correlating_sources()` - Multiple sources increase confidence

**Expected Confidence Ranges**:

| Scenario | Fallback | With LLM |
|----------|----------|----------|
| Code only | 0.60-0.70 | 0.60-0.70 |
| Code + Vehicle | 0.70-0.80 | **0.80-0.90** ✅ |
| Full Diagnosis | 0.75-0.85 | **0.85-0.95** ✅✅ |
| Symptom only | 0.50-0.65 | 0.50-0.65 |
| Unknown Vehicle | 0.50-0.65 | 0.60-0.70 |

---

### 6. **test_integration.py** (40+ tests)
**Purpose**: End-to-end workflow testing and API integration

**Coverage**:
- ✅ Full diagnostic workflows for all 9 scenarios
- ✅ API endpoint integration (/diagnose, /health)
- ✅ Multi-scenario sequences
- ✅ Data consistency and tracking
- ✅ Error recovery
- ✅ Performance benchmarks
- ✅ Response structure consistency
- ✅ State isolation between runs

**Key Test Cases**:
- `test_workflow_code_only_scenario()` - P0171 lookup
- `test_workflow_code_vehicle_scenario()` - P0171 + Toyota Corolla 2020
- `test_workflow_full_diagnosis_scenario()` - All inputs combined
- `test_api_diagnose_with_code_only()` - POST /diagnose endpoint
- `test_api_diagnose_with_vehicle_info()` - Vehicle context
- `test_api_diagnose_with_full_info()` - Complete diagnostic
- `test_api_diagnose_with_invalid_code()` - Graceful fallback
- `test_run_multiple_diagnoses()` - Sequence of requests
- `test_state_isolation_between_runs()` - No cross-contamination
- `test_sources_tracked_through_workflow()` - Source tracking verified
- `test_response_time_code_only()` - Performance benchmark
- `test_response_time_full_diagnosis()` - LLM response time

---

## Running the Tests

### Run All Tests
```bash
cd c:\Automotive_assistant\automotive-assistant
pytest
```

### Run Specific Test Module
```bash
pytest tests/test_agents.py
pytest tests/test_routing.py
pytest tests/test_llm_service.py
pytest tests/test_error_handling.py
pytest tests/test_confidence.py
pytest tests/test_integration.py
```

### Run Specific Test Class
```bash
pytest tests/test_agents.py::TestCodeAgent
pytest tests/test_routing.py::TestQueryRouter
pytest tests/test_confidence.py::TestConfidenceScoring
```

### Run Specific Test Case
```bash
pytest tests/test_agents.py::TestCodeAgent::test_lookup_valid_dtc_p0171
pytest tests/test_routing.py::TestQueryRouter::test_route_code_vehicle
pytest tests/test_confidence.py::TestConfidenceScoring::test_confidence_code_vehicle_with_llm
```

### Run with Verbose Output
```bash
pytest -v
```

### Run with Print Statements
```bash
pytest -s
```

### Run with Coverage Report
```bash
pytest --cov=backend tests/
```

### Run Specific Test Marker
```bash
pytest -m "not slow"  # Skip slow tests
```

---

## Test Statistics

| Module | Test Count | Focus Area |
|--------|-----------|-----------|
| test_agents.py | 35+ | Agent logic & data lookups |
| test_routing.py | 25+ | Scenario detection & routing |
| test_llm_service.py | 30+ | LLM integration & parsing |
| test_error_handling.py | 35+ | Graceful error recovery |
| test_confidence.py | 25+ | Confidence score calculation |
| test_integration.py | 40+ | End-to-end workflows |
| **TOTAL** | **150+** | **Complete system coverage** |

---

## Key Testing Areas

### ✅ Completed
- [x] All 9 routing scenarios
- [x] Code agent (valid/invalid DTC codes)
- [x] Maintenance agent (known/unknown vehicles, mileage logic)
- [x] Symptom agent (RAG retrieval)
- [x] Confidence scoring (0.50-0.95 ranges)
- [x] LLM response parsing (markdown, JSON, errors)
- [x] Error handling (missing files, invalid types)
- [x] API endpoints (/diagnose, /health)
- [x] Full workflow integration (6 complete scenarios)
- [x] State isolation and data consistency

### 🎯 Priority Test Cases

**Essential for LLM Verification**:
1. `test_route_code_vehicle()` - Verifies routing logic
2. `test_confidence_code_vehicle_with_llm()` - Confidence 0.80-0.90
3. `test_confidence_full_diagnosis_with_llm()` - Confidence 0.85-0.95
4. `test_workflow_code_vehicle_scenario()` - Full workflow test
5. `test_api_diagnose_with_vehicle_info()` - API integration

**Azure Foundry Specific**:
1. `test_service_initialization_with_foundry_endpoint()` - Detects /openai/v1
2. `test_response_parsing_valid_json()` - Parses LLM response
3. `test_response_parsing_markdown_json()` - Handles markdown wrappers

**Error Resilience**:
1. `test_missing_obd_dataset_file()` - Graceful degradation
2. `test_retriever_initialization_failure()` - RAG fallback
3. `test_recovery_from_invalid_input()` - Error recovery

---

## Expected Test Results

When running `pytest`:
- ✅ All tests should pass
- ✅ No failures or errors
- ✅ Some tests may skip if RAG not initialized (ChromaDB needs HuggingFace access)
- ✅ Performance tests should complete in <5s for basic, <15s for LLM

---

## Next Steps

1. **Run tests locally**:
   ```bash
   pytest tests/ -v
   ```

2. **Verify Azure Foundry integration**:
   ```bash
   pytest tests/test_llm_service.py::TestAzureOpenAIService -v
   ```

3. **Check confidence scoring**:
   ```bash
   pytest tests/test_confidence.py -v
   ```

4. **Full integration test**:
   ```bash
   pytest tests/test_integration.py::TestFullDiagnosisWorkflow -v
   ```

5. **Generate coverage report**:
   ```bash
   pytest --cov=backend tests/ --cov-report=html
   ```

---

## Continuous Integration

Add this to CI/CD pipeline:
```bash
pytest tests/ -v --cov=backend --cov-report=xml
```

All 150+ tests should pass before deploying to production.
