# System Workflow Explanation

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      STREAMLIT FRONTEND (Port 8501)              │
│  - User input: vehicle code, symptoms, vehicle info             │
│  - Response display: diagnosis, severity, causes, repair steps  │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP POST /diagnose
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND (Port 8000)                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 1. REQUEST VALIDATION (Pydantic)                         │   │
│  │    - Code, symptoms, vehicle_info validation            │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                           ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 2. LANGGRAPH WORKFLOW STATE MACHINE                      │   │
│  │    - Multi-step agent coordination                       │   │
│  │    - State: make, model, year, code, symptoms, etc.     │   │
│  └────────────────────────┬─────────────────────────────────┘   │
└────────────────────────────┼────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
   ┌─────────┐          ┌─────────┐         ┌──────────┐
   │ CODE    │          │SYMPTOM  │         │MAINTENANCE│
   │AGENT_V2 │          │AGENT_V2 │         │AGENT_V2  │
   └────┬────┘          └────┬────┘         └─────┬────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             ▼
        ┌────────────────────────────────────────┐
        │ RAG PIPELINE (for each agent)          │
        │ ┌─────────────────────────────────────┐│
        │ │ 1. QUERY CLASSIFICATION             ││
        │ │    - Detect: OBD/Symptom/Maintenance││
        │ └────────────────────┬────────────────┘│
        │                      ▼                 │
        │ ┌─────────────────────────────────────┐│
        │ │ 2. CATEGORY FILTER                  ││
        │ │    - Filter ChromaDB by category   ││
        │ └────────────────────┬────────────────┘│
        │                      ▼                 │
        │ ┌─────────────────────────────────────┐│
        │ │ 3. SEMANTIC RETRIEVAL (K=5)        ││
        │ │    - Azure embeddings search        ││
        │ │    - Return top 5 similar chunks   ││
        │ │    - Capture vector scores (0-1)   ││
        │ └────────────────────┬────────────────┘│
        │                      ▼                 │
        │ ┌─────────────────────────────────────┐│
        │ │ 4. CROSS-ENCODER RERANKING (K=3)   ││
        │ │    - Reorder top 3 by relevance    ││
        │ │    - Multi-factor confidence       ││
        │ └────────────────────┬────────────────┘│
        │                      ▼                 │
        │ ┌─────────────────────────────────────┐│
        │ │ 5. SOURCE ATTRIBUTION (8 fields)   ││
        │ │    - filename, category, type      ││
        │ │    - code, vector_score, distance  ││
        │ │    - rerank_score, original_rank   ││
        │ └────────────────────┬────────────────┘│
        │                      ▼                 │
        │ ┌─────────────────────────────────────┐│
        │ │ 6. CONFIDENCE SCORING (0-100%)     ││
        │ │    - top_score × 0.5                ││
        │ │    - avg_top_3 × 0.3                ││
        │ │    - score_gap × 0.2                ││
        │ └─────────────────────────────────────┘│
        └────────────────────────────────────────┘
                             ▼
        ┌────────────────────────────────────────┐
        │ AZURE OPENAI LLM SERVICE               │
        │ - Model: gpt-5.1                       │
        │ - Generate: diagnosis + repair steps  │
        │ - Fallback: deterministic report      │
        └────────────────────┬───────────────────┘
                             ▼
        ┌────────────────────────────────────────┐
        │ REPORT AGENT                           │
        │ - Aggregate all agent results          │
        │ - Format response                      │
        │ - Attach sources                       │
        └────────────────────┬───────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RESPONSE (JSON)                              │
│  {                                                              │
│    "diagnosis": "string",                                      │
│    "severity": "HIGH|MEDIUM|LOW",                              │
│    "possible_causes": ["cause1", "cause2", ...],               │
│    "repair_steps": ["step1", "step2", ...],                    │
│    "maintenance_recommendations": ["maint1", ...],             │
│    "confidence_score": 0-100,                                  │
│    "sources": [                                                │
│      {                                                          │
│        "source_filename": "file.txt",                          │
│        "category": "obd|symptom|maintenance",                 │
│        "chunk_type": "...",                                    │
│        "code": "P0300",                                        │
│        "vector_score": 0.85,                                   │
│        "vector_distance": 0.15,                                │
│        "rerank_score": 0.82,                                   │
│        "original_rank": 1                                      │
│      }                                                          │
│    ]                                                            │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Request Flow - Detailed Steps

### Step 1: User Input (Frontend)
```python
# User submits form in Streamlit
{
  "code": "P0300",
  "symptoms": ["Engine misfire"],
  "vehicle_info": {
    "make": "Toyota",
    "model": "Camry",
    "year": 2020,
    "mileage": 120000
  }
}
```

### Step 2: Backend Receives Request
- FastAPI endpoint `/diagnose` receives POST request
- Pydantic validates input schema
- Creates `DiagnoseRequest` object

### Step 3: LangGraph Workflow Initialization
- Creates `WorkflowState` with 40+ fields
- Sets: make, model, year, mileage, code, symptoms
- Initializes: code_result, symptom_result, maintenance_result
- Starts state machine execution

### Step 4: Query Router Decision
```python
# workflow.py - query_router node
if code in P0000-P9999 format:
    route → code_agent_v2
elif symptom matches engine stalling, misfire, etc:
    route → symptom_agent_v2
elif maintenance topic detected:
    route → maintenance_agent_v2
```

### Step 5: Agent Execution (v2 Agents)

**Code Agent V2 Example (P0300):**

```
1. QueryClassifier.classify("P0300")
   └─ Result: QueryType.CODE

2. RAGRetriever.retrieve("P0300", category="obd", k=5)
   ├─ Convert query to embedding (Azure)
   ├─ Search ChromaDB collection
   ├─ Filter by category: obd
   ├─ Return top 5 chunks with vector_scores
   └─ Result: [chunk1, chunk2, chunk3, chunk4, chunk5]

3. CrossEncoderReranker.rerank(chunks, query, top_k=3)
   ├─ Score chunks using cross-encoder
   ├─ Reorder by relevance
   ├─ Calculate confidence = (top×0.5 + avg_top3×0.3 + gap×0.2)
   └─ Result: [chunk1_reranked, chunk2_reranked, chunk3_reranked]

4. Attach 8-field source metadata to each chunk
   └─ Result: chunks with source attribution

5. Pass to LLM: "Generate diagnosis for P0300 with these sources"
```

### Step 6: LLM Processing (Azure OpenAI)
```
Input to gpt-5.1:
- Code: P0300
- Context: Top 3 retrieved chunks with 1536-dim embeddings
- Temperature: 0.7
- Max tokens: 1024

Output:
- Diagnosis paragraph
- 3-5 root causes
- Step-by-step repair process
- Labor time estimates
```

### Step 7: Confidence Scoring
```python
# Multi-factor confidence calculation
vector_score = 0.85         # Semantic similarity
avg_top_3 = 0.82            # Average of 3 scores
score_gap = 0.85 - 0.70     # Confidence gap
confidence = (0.85 * 0.5) + (0.82 * 0.3) + (0.15 * 0.2)
           = 0.425 + 0.246 + 0.03
           = 0.701 → 70% (MEDIUM confidence)
```

### Step 8: Report Generation
- Code agent result aggregated
- Symptom agent result added (if applicable)
- Maintenance agent result added (if applicable)
- All sources compiled into response

### Step 9: Response Serialization
```python
response = DiagnoseResponse(
    diagnosis="...",
    severity="HIGH",
    possible_causes=[...],
    repair_steps=[...],
    maintenance_recommendations=[...],
    confidence_score=70,
    sources=[...]  # 8-field metadata for each source
)
```

### Step 10: Frontend Rendering
- Display diagnosis with color-coded severity
- List causes in order of likelihood
- Show repair steps with labor time
- Display confidence score percentage
- Link sources to original documents

---

## Data Flow - Components

### ChromaDB Vector Store
```
Collection: automotive_docs
├─ 27 OBD chunks (Category: obd)
├─ 2 Maintenance chunks (Category: maintenance)
├─ 4 Symptom chunks (Category: symptom)
└─ 26 Evaluation chunks (Category: evaluation)

Each chunk contains:
- content: chunk text
- metadata:
  - source_filename: OBD_Codes_Reference_A.txt
  - category: obd
  - chunk_type: obd_entry
  - chunk_size: 356
  - source: OBD_Codes_Reference_A.txt
```

### Embedding Pipeline
```
Query: "P0300"
  ↓
Azure OpenAI (text-embedding-3-small)
  ├─ 1536-dimensional vector
  ├─ ~1 second latency
  └─ Singleton cached
  ↓
ChromaDB similarity_search_with_score()
  ├─ Cosine distance → similarity conversion
  ├─ Return (chunk, distance) pairs
  └─ Convert to vector_score (0-1)
```

### Confidence Levels
```
90-100%  → HIGH confidence (trust LLM output)
70-90%   → MEDIUM confidence (generally reliable)
50-70%   → MEDIUM confidence (use with caution)
< 50%    → LOW confidence (consider fallback report)
```

---

## Error Handling

### Level 1: Input Validation
- Invalid vehicle code format → HTTP 400
- Missing required fields → HTTP 422
- Invalid vehicle year → HTTP 400

### Level 2: RAG Pipeline
- No matching chunks found → Use fallback report
- Azure embedding failure → Raise error (no HuggingFace fallback)
- Reranker timeout → Use top chunks from retriever

### Level 3: LLM Service
- Azure API timeout → Fallback deterministic report
- Rate limit exceeded → Return cached response
- No API key → Raise configuration error

### Level 4: Response
- Invalid JSON → HTTP 500
- Missing required fields → HTTP 500

---

## Performance Characteristics

```
Component              Time        Notes
─────────────────────────────────────────────────
Frontend rendering     <100ms      Streamlit
Request validation     <50ms       Pydantic
Query classification   ~10ms       Regex patterns
Azure embedding        ~800ms      Cached on 2nd+ calls
ChromaDB retrieval     ~150ms      5 chunks, 10 metadata fields
Cross-encoder rerank   ~300ms      3 chunks, similarity scoring
LLM generation         ~3-5s       Azure gpt-5.1
Report aggregation     ~50ms       Formatting
──────────────────────────────────────────────────
TOTAL                  ~5-8 sec    Per request
```

---

## State Transitions

```
START
  ↓
query_router
  ├─→ CODE → code_agent_v2
  ├─→ SYMPTOM → symptom_agent_v2
  ├─→ MAINTENANCE → maintenance_agent_v2
  └─→ COMBINATION → multiple agents
  ↓
report_agent (aggregates results)
  ↓
END (return response)
```

---

## Key Design Patterns

1. **Singleton Caching**: Embeddings cached after first init
2. **Multi-factor Scoring**: Confidence uses 3 independent factors
3. **Source Attribution**: Track every chunk's provenance
4. **Category Filtering**: Pre-filter to relevant document types
5. **Graceful Degradation**: Fallback reports when LLM unavailable
6. **Async State Machine**: LangGraph handles workflow coordination
