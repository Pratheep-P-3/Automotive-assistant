"""
PRODUCTION RAG UPGRADE INTEGRATION GUIDE
========================================

This document provides step-by-step instructions for integrating the
production-grade RAG pipeline into your Automotive Diagnostics Assistant.

VERSION: 2.0.0
DATE: 2026-08-01
SCOPE: Complete RAG pipeline upgrade with confidence scoring
"""

# ============================================================================
# PART 1: NEW FILES CREATED
# ============================================================================

"""
1. backend/rag/query_classifier.py
   - QueryClassifier class
   - Detects OBD codes, maintenance keywords, symptom queries
   - Returns QueryCategory enum (OBD, MAINTENANCE, SYMPTOM)
   - Provides metadata filter for Chroma filtering

2. backend/rag/document_chunker.py
   - DocumentAwareChunker class
   - Semantic-aware chunking preserving complete knowledge units
   - OBD entry chunking (complete code + definition)
   - Maintenance procedure chunking (one per procedure)
   - Troubleshooting workflow chunking (one per symptom)
   - Handles large chunks (>2000 chars) with recursive splitting

3. backend/rag/reranker.py
   - CrossEncoderReranker class
   - Uses cross-encoder/ms-marco-MiniLM-L-6-v2 model
   - Re-ranks top 10 to top 3 documents
   - Calculates confidence scores (0-100%)
   - Maps to confidence levels (High/Medium/Low)

4. backend/agents/code_agent_v2.py
   - UPDATED CodeAgent with production pipeline
   - Integrates QueryClassifier + MetadataFiltering + Reranker
   - Extracts structured OBD data using regex
   - Returns confidence scores with results
   - Complete logging of pipeline steps

5. backend/agents/symptom_agent_v2.py
   - UPDATED SymptomAgent with production pipeline
   - Extracts troubleshooting workflows
   - Links related OBD codes
   - Confidence-aware responses

6. backend/agents/maintenance_agent_v2.py
   - UPDATED MaintenanceAgent with production pipeline
   - Extracts maintenance procedures
   - Filters by mileage relevance
   - Cost and time estimates
"""

# ============================================================================
# PART 2: UPDATED FILES
# ============================================================================

"""
1. backend/rag/embedding.py
   - REPLACED EmbeddingFactory with Azure OpenAI support
   - Priority: Azure OpenAI (text-embedding-3-small) > HuggingFace fallback
   - Environment variable driven configuration
   - Graceful fallback if Azure unavailable
   - Full type hints and logging

2. backend/rag/ingest.py
   - UPDATED ingestion pipeline
   - Uses DocumentAwareChunker instead of RecursiveCharacterTextSplitter
   - Adds category metadata during loading
   - Logs chunk distribution by category
   - Better organization and error handling

3. backend/rag/retriever.py
   - UPDATED RAGRetriever with metadata filtering
   - Retrieves top K with metadata filter
   - Improved logging of retrieval process
   - Type hints and documentation

4. backend/services/azure_openai_service.py
   - UPDATED SYSTEM_PROMPT with confidence-aware guidance
   - UPDATED generate_report() to inject confidence scores
   - UPDATED _fallback_report() with confidence levels
   - Proper JSON structure for confidence data
   - Confidence-based messaging patterns
"""

# ============================================================================
# PART 3: ENVIRONMENT VARIABLES
# ============================================================================

"""
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
AZURE_OPENAI_DEPLOYMENT=gpt-5.1

CHROMA_PERSIST_DIR=./data/chroma
CHROMA_COLLECTION_NAME=automotive_docs

BACKEND_URL=http://localhost:8000
"""

# ============================================================================
# PART 4: INTEGRATION STEPS ON UBUNTU
# ============================================================================

"""
STEP 1: Install New Dependencies
---------------------------------
pip install sentence-transformers langchain-openai

# Verify installations
python -c "from sentence_transformers import CrossEncoder; print('✓ Cross-encoder OK')"
python -c "from langchain_openai import AzureOpenAIEmbeddings; print('✓ Azure OpenAI OK')"


STEP 2: Test New Components
---------------------------
# Test QueryClassifier
python -c "
from backend.rag.query_classifier import QueryClassifier
qc = QueryClassifier()
print('OBD:', qc.classify('P0300'))
print('Maintenance:', qc.classify('oil change at 5000 km'))
print('Symptom:', qc.classify('vehicle vibrates'))
"

# Test DocumentAwareChunker
python -c "
from backend.rag.document_chunker import DocumentAwareChunker
dac = DocumentAwareChunker()
print('✓ DocumentAwareChunker initialized')
"

# Test CrossEncoderReranker
python -c "
from backend.rag.reranker import CrossEncoderReranker
reranker = CrossEncoderReranker()
print('✓ CrossEncoderReranker initialized (model will load on first use)')
"


STEP 3: Re-ingest Data with New Pipeline
-----------------------------------------
rm -rf data/chroma
python -m backend.rag.ingest

Expected output:
[INGESTION] ===== Loading TXT documents =====
[INGESTION] Total documents loaded: 9
[INGESTION] ===== Document-Aware Chunking =====
[INGESTION] Chunks created: XXX
[INGESTION] Chunk distribution by category:
  - evaluation: XX chunks
  - maintenance: XX chunks
  - obd: XX chunks
  - symptom: XX chunks
[INGESTION] ===== Indexing into ChromaDB =====
[INGESTION] ✓✓✓ COMPLETE - Indexed XXX chunks into Chroma database


STEP 4: Update Workflow Graph
-----------------------------
Edit backend/graph/workflow.py to use updated agents:

from backend.agents.code_agent_v2 import CodeAgent as CodeAgentV2
from backend.agents.symptom_agent_v2 import SymptomAgent as SymptomAgentV2
from backend.agents.maintenance_agent_v2 import MaintenanceAgent as MaintenanceAgentV2

def create_diagnostic_workflow():
    workflow = StateGraph(WorkflowState)
    
    # Use v2 agents instead of v1
    code_agent = CodeAgentV2()
    symptom_agent = SymptomAgentV2()
    maintenance_agent = MaintenanceAgentV2()
    
    workflow.add_node("code_lookup", code_agent.run)
    workflow.add_node("symptom_analysis", symptom_agent.run)
    workflow.add_node("maintenance_check", maintenance_agent.run)
    # ... rest of workflow setup


STEP 5: Restart Backend
-----------------------
pkill -f "uvicorn"
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000

Expected startup messages:
[EmbeddingFactory] Azure OpenAI is configured
[EmbeddingFactory] ✓ Azure OpenAI embeddings initialized successfully
[CHROMA] ✓ Successfully initialized Chroma database
[CHROMA] Database contains XXX documents


STEP 6: Test P0750 Query in Streamlit
--------------------------------------
1. Browser: http://localhost:8501
2. Enter DTC: P0750
3. Click Diagnose

Expected output:
✓ High Confidence (85%)
✓ Shift Solenoid A (Solenoid 1) Circuit
✓ System Affected: Automatic Transmission Shifting
✓ Common Causes: [Faulty shift solenoid coil, ...]
✓ Diagnostic Steps: [1. Scan for transmission mode, 2. Test solenoid coil resistance, ...]
✓ Repair Recommendation: Replace shift solenoid or repair wiring
✓ Estimated Cost: $300-800 per solenoid
✓ Sources: [OBD_Codes_Reference_B.txt, ...]
"""

# ============================================================================
# PART 5: FILE STRUCTURE AFTER UPGRADE
# ============================================================================

"""
automotive-assistant/
├── backend/
│   ├── agents/
│   │   ├── code_agent.py (KEEP - legacy, not used)
│   │   ├── code_agent_v2.py (NEW - with production RAG pipeline)
│   │   ├── symptom_agent.py (KEEP - legacy)
│   │   ├── symptom_agent_v2.py (NEW - with production RAG pipeline)
│   │   ├── maintenance_agent.py (KEEP - legacy)
│   │   ├── maintenance_agent_v2.py (NEW - with production RAG pipeline)
│   │   └── __init__.py
│   ├── rag/
│   │   ├── embedding.py (UPDATED - Azure OpenAI support)
│   │   ├── ingest.py (UPDATED - document-aware chunking)
│   │   ├── retriever.py (UPDATED - metadata filtering)
│   │   ├── query_classifier.py (NEW)
│   │   ├── document_chunker.py (NEW)
│   │   ├── reranker.py (NEW)
│   │   └── __init__.py
│   ├── graph/
│   │   ├── workflow.py (UPDATE - use v2 agents)
│   │   └── state.py
│   ├── services/
│   │   └── azure_openai_service.py (UPDATED - confidence scoring)
│   └── app.py
├── data/
│   ├── obd/
│   ├── maintenance/
│   ├── troubleshooting/
│   ├── evaluation/
│   └── chroma/ (RECREATED after re-ingestion)
└── frontend/
    └── streamlit_app.py (Already has UI for confidence)
"""

# ============================================================================
# PART 6: CONFIDENCE SCORE FLOW
# ============================================================================

"""
Query → QueryClassifier → Metadata Filter → Retriever (Top 10)
                                                      ↓
                                              CrossEncoderReranker
                                                      ↓
                                              Top 3 + Scores
                                                      ↓
                                          Extract Confidence %
                                                      ↓
                                          Add to Code/Symptom/Maintenance Result
                                                      ↓
                                          Azure OpenAI LLM (confidence-aware)
                                                      ↓
                                          Report with Confidence Level
                                                      ↓
                                          Streamlit UI Display
                                                      ↓
                                          User sees: "High Confidence (85%)"
"""

# ============================================================================
# PART 7: BACKWARD COMPATIBILITY
# ============================================================================

"""
BACKWARD COMPATIBLE CHANGES:
✓ v2 agents have same interface as v1 agents
✓ Workflow.run(state) → returns updated state with results
✓ Existing API endpoints unchanged
✓ Streamlit UI works with new confidence data
✓ Old v1 agents left in place (not used by default)

BREAKING CHANGES:
✗ Must re-ingest database (uses new chunking strategy)
✗ Workflow.py must be updated to import v2 agents
✗ Must install new dependencies (sentence-transformers, langchain-openai)
✗ Azure OpenAI API key now optional (but highly recommended)
"""

# ============================================================================
# PART 8: VALIDATION CHECKLIST
# ============================================================================

"""
After deployment, validate these points:

[ ] Dependencies installed: pip list | grep -E "sentence-transformers|langchain-openai"
[ ] Database re-ingested: ls -lah data/chroma/ | grep -E ".parquet|sqlite3"
[ ] QueryClassifier working: Python import test passes
[ ] DocumentAwareChunker working: Python import test passes
[ ] CrossEncoderReranker working: Python import test passes
[ ] Embeddings initialized: Backend logs show "[EmbeddingFactory] ✓"
[ ] Chroma connected: Backend logs show "[CHROMA] Database contains XXX"
[ ] Agents initialized: Backend logs show "[CodeAgent] ✓ Initialized"
[ ] P0750 query returns full data with confidence
[ ] P0750 confidence >= 80% (high confidence)
[ ] Streamlit displays confidence badge
[ ] LLM generates confidence-aware response
[ ] Sources properly attributed to files
"""

# ============================================================================
# PART 9: TROUBLESHOOTING
# ============================================================================

"""
ISSUE: "Cross-encoder not loading"
SOLUTION: pip install sentence-transformers

ISSUE: "Azure OpenAI embeddings fail, falling back to HuggingFace"
SOLUTION: Check AZURE_OPENAI_* environment variables are set correctly

ISSUE: "Database shows 0 chunks"
SOLUTION: Verify data/obd/, data/maintenance/, data/troubleshooting/ have .txt files
          Re-run: rm -rf data/chroma && python -m backend.rag.ingest

ISSUE: "P0750 still showing 'not found'"
SOLUTION: Wait 30s for backend to reload, browser cache clear (Ctrl+Shift+R)
          Check logs for "[CodeAgent] Re-ranking FAILED"

ISSUE: "Confidence always 0%"
SOLUTION: Verify CodeAgent is using v2 from code_agent_v2.py
          Check logs for "[Reranker] Confidence:" message
"""

# ============================================================================
# PART 10: MONITORING & LOGS
# ============================================================================

"""
Key log messages to watch:

[QueryClassifier] ✓ Classified as OBD: 'P0750'
[CHROMA] Retrieved X documents
[Reranker] Re-ranking X documents...
[Reranker] Rank 1: Score=0.xxx | Orig Pos=X
[Reranker] Confidence: XX% (High/Medium/Low Confidence)
[CodeAgent] ✓ Found P0750 with confidence XX%
[LLM] Generating report with HIGH CONFIDENCE (score: XX%)
[LLM] ✓ Report generated successfully

If any of these are missing, the pipeline is not fully integrated.
"""

# ============================================================================
# PART 11: NEXT STEPS FOR CAPSTONE
# ============================================================================

"""
OPTIONAL ENHANCEMENTS (Not included in this upgrade):

1. Evaluation Framework
   - Create benchmark dataset
   - Measure retrieval@K metrics
   - Track confidence calibration (confidence % vs actual accuracy)
   - NDCG, MRR, Precision@K metrics

2. Feedback Loop
   - User ratings on answer quality
   - Correlation with confidence scores
   - Retrain on feedback

3. Multi-hop Reasoning
   - Link OBD codes → symptoms → maintenance procedures
   - Cross-domain query understanding

4. Cost Estimation
   - Machine learning model for repair cost prediction
   - Regional price adjustments

5. Safety Critical Escalation
   - Automatic routing to human expert for brake/steering issues
   - Integration with SMS/email alerts

These can be added incrementally without breaking the current pipeline.
"""

# ============================================================================
# PART 12: SUPPORT & DOCUMENTATION
# ============================================================================

"""
DOCUMENTATION FILES:
- backend/rag/query_classifier.py (docstrings + type hints)
- backend/rag/document_chunker.py (comprehensive documentation)
- backend/rag/reranker.py (method documentation)
- backend/agents/code_agent_v2.py (pipeline explanation)
- backend/services/azure_openai_service.py (SYSTEM_PROMPT with guidance)

CODE QUALITY:
- Full type hints (Python 3.9+)
- Comprehensive logging (10+ log points per agent)
- Exception handling with fallback
- Backward compatible design
- Production-ready error messages
"""
