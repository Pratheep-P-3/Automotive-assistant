# RAG Improvements: Deployment & Testing Guide

## ✅ What Was Improved

| # | Issue | Status | File(s) |
|---|-------|--------|---------|
| 1 | Robust OBD Detection | ✅ FIXED | document_chunker.py |
| 2 | Maintenance Headers | ✅ FIXED | document_chunker.py |
| 3 | Troubleshooting Sections | ✅ FIXED | document_chunker.py |
| 4 | Chunking Logging | ✅ ADDED | document_chunker.py |
| 5 | Embedding Caching | ✅ ADDED | embedding.py |
| 6 | Confidence Scoring | ✅ IMPROVED | reranker.py |
| 7 | Vector Scores | ✅ CAPTURED | retriever.py, code_agent_v2.py |
| 8 | Retrieval Tuning | ✅ ADDED | retriever.py, code_agent_v2.py |
| 9 | Source Attribution | ✅ ENHANCED | code_agent_v2.py |
| 10 | Validation Utility | ✅ CREATED | validate_ingestion.py |

---

## 🚀 Deployment Steps

### Step 1: Review Changes
```bash
# No new dependencies added! All improvements use existing packages
pip list | grep -E "sentence-transformers|langchain-chroma|langchain-core|langchain-openai"
# Should show: sentence-transformers, langchain-chroma, langchain-core, langchain-openai
```

### Step 2: (Optional) Configure Retrieval Parameters
```bash
# Edit .env file - adjust for your dataset size
echo "RETRIEVAL_K=5" >> .env
echo "RERANK_TOP_K=3" >> .env

# For larger datasets, you can adjust:
# RETRIEVAL_K=10
# RERANK_TOP_K=5
```

### Step 3: Re-ingest Database (Important!)
```bash
# Clear old database
rm -rf data/chroma

# Re-ingest with improved patterns
python -m backend.rag.ingest

# Expected output:
# [DocumentAwareChunker] File=... | Category=obd | OBD Entries Found=50 | Chunks Produced=50
# [DocumentAwareChunker] File=... | Category=maintenance | Sections Detected=8 | Chunks Produced=8
# [DocumentAwareChunker] File=... | Category=symptom | Sections Detected=25 | Chunks Produced=25
# [INGESTION] ✓✓✓ COMPLETE - Indexed XXX chunks
```

### Step 4: Validate System Health
```bash
# Run validation utility
python -m backend.rag.validate_ingestion

# Expected output:
# [TEST 1] Checking ChromaDB Database...  ✓
# [TEST 2] Initializing RAG Retriever...  ✓
# [TEST 3] Validating Chunk Counts...     ✓ (should show counts by category)
# [TEST 4] Validating Metadata Quality... ✓ (all required fields present)
# [TEST 5] Testing Sample Retrieval...    ✓ (sample queries work)
# [TEST 6] Testing Vector Scores...       ✓ (scores captured)
# [TEST 7] Checking Configuration...      ✓
```

### Step 5: Restart Backend
```bash
# Kill existing processes
pkill -f "uvicorn"
pkill -f "streamlit"

# Start backend with fresh database
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 &

# In new terminal, start Streamlit
streamlit run frontend/streamlit_app.py
```

---

## 🧪 Testing Guide

### Test 1: OBD Pattern Robustness
```python
from backend.rag.document_chunker import DocumentAwareChunker

chunker = DocumentAwareChunker()

# Test all supported OBD formats
test_formats = """
P0300
Code: P0300
OBD Code: P0300
P0300 - Random Misfire
Diagnostic Trouble Code P0300
DTC P0300
"""

# All should be detected
for line in test_formats.strip().split('\n'):
    matches = list(chunker.OBD_PATTERN.finditer(line))
    print(f"'{line}' -> {'✓ Detected' if matches else '✗ MISSED'}")
```

### Test 2: Maintenance Header Robustness
```python
from backend.rag.document_chunker import DocumentAwareChunker

chunker = DocumentAwareChunker()

# Test maintenance formats
test_headers = [
    "5000 km Service",
    "10000 km Service",
    "ENGINE OIL CHANGE",
    "Brake Inspection",
    "Coolant Replacement",
    "Air Filter Replacement",
    "Scheduled Maintenance",
    "Regular Service"
]

for header in test_headers:
    match = chunker.MAINTENANCE_HEADER_PATTERN.match(header)
    print(f"'{header}' -> {'✓ Detected' if match else '✗ MISSED'}")
```

### Test 3: Troubleshooting Pattern Robustness
```python
from backend.rag.document_chunker import DocumentAwareChunker

chunker = DocumentAwareChunker()

# Test symptom formats
test_symptoms = [
    "Engine Misfire",
    "Vehicle Stalling",
    "Rough Idle",
    "Poor Fuel Economy",
    "Hard Starting",
    "Transmission Slipping",
    "Brake Noise",
    "Battery Drain",
    "Check Engine Light",
    "Engine Overheating"
]

for symptom in test_symptoms:
    match = chunker.TROUBLESHOOTING_PATTERN.match(symptom)
    print(f"'{symptom}' -> {'✓ Detected' if match else '✗ MISSED'}")
```

### Test 4: Embedding Factory Singleton Caching
```python
import time
from backend.rag.embedding import EmbeddingFactory

# Clear cache to start fresh
EmbeddingFactory.clear_cache()

# First call (initializes)
print("First call (initializes embedding model)...")
start = time.time()
emb1 = EmbeddingFactory.get_embeddings()
time1 = time.time() - start
print(f"✓ Initialized in {time1:.2f}s")

# Second call (from cache - should be instant)
print("Second call (from cache)...")
start = time.time()
emb2 = EmbeddingFactory.get_embeddings()
time2 = time.time() - start
print(f"✓ Retrieved from cache in {time2:.2f}s (should be <1ms)")

# Verify same instance
print(f"Same instance: {'✓' if emb1 is emb2 else '✗ Different instances (caching failed)'}")

# Show source
print(f"Embedding source: {EmbeddingFactory._embedding_source}")
```

### Test 5: Vector Score Capture
```python
from backend.rag.retriever import RAGRetriever
from backend.rag.query_classifier import QueryClassifier

retriever = RAGRetriever()
classifier = QueryClassifier()

# Query with OBD code
query = "P0300"
category = classifier.classify(query)
docs = retriever.retrieve(query, metadata_filter={"category": category.value})

if docs:
    print(f"Retrieved {len(docs)} documents for '{query}'")
    for i, doc in enumerate(docs):
        print(f"\nDoc {i+1}:")
        print(f"  Source: {doc.metadata.get('source')}")
        print(f"  Vector Score: {doc.metadata.get('vector_score', 'N/A')}")  # ✓ Should have this
        print(f"  Vector Distance: {doc.metadata.get('vector_distance', 'N/A')}")  # ✓ Should have this
else:
    print(f"✗ No documents found for {query}")
```

### Test 6: Multi-Factor Confidence Scoring
```python
from backend.rag.reranker import CrossEncoderReranker

reranker = CrossEncoderReranker()

# Simulate different score scenarios
# Scenario 1: Strong, consistent scores (high confidence)
scores_strong = [
    {"score": 0.92, "original_position": 1},
    {"score": 0.88, "original_position": 2},
    {"score": 0.85, "original_position": 3},
]

# Scenario 2: Ambiguous, close scores (lower confidence)
scores_ambiguous = [
    {"score": 0.62, "original_position": 1},
    {"score": 0.60, "original_position": 2},
    {"score": 0.59, "original_position": 3},
]

print("Strong, consistent scores:")
conf1, level1 = reranker.get_confidence_from_scores(scores_strong)
print(f"  Confidence: {conf1}% ({level1})")

print("\nAmbiguous, close scores:")
conf2, level2 = reranker.get_confidence_from_scores(scores_ambiguous)
print(f"  Confidence: {conf2}% ({level2})")

print(f"\n✓ Multi-factor scoring is working (ambiguous < strong: {conf2 < conf1})")
```

### Test 7: Enhanced Source Attribution
```python
from backend.agents.code_agent_v2 import CodeAgent
from backend.graph.state import WorkflowState

agent = CodeAgent()

# Query an OBD code
state = WorkflowState(code="P0750")
result_state = agent.run(state)

if result_state.get("code_result"):
    result = result_state["code_result"]
    
    print(f"Code: {result.get('code')}")
    print(f"Confidence: {result.get('confidence')}%")
    
    # Check enhanced source attribution
    if result.get("sources"):
        print(f"\nSources ({len(result['sources'])} documents):")
        for i, source in enumerate(result["sources"][:3]):  # Show top 3
            print(f"\n  Source {i+1}:")
            print(f"    Filename: {source.get('source_filename')}")  # ✓ Rich metadata
            print(f"    Category: {source.get('category')}")
            print(f"    Chunk Type: {source.get('chunk_type')}")
            print(f"    Vector Score: {source.get('vector_score', 'N/A')}")  # ✓ New field
            print(f"    Rerank Score: {source.get('rerank_score', 'N/A')}")  # ✓ New field
            print(f"    Original Rank: {source.get('original_rank', 'N/A')}")  # ✓ New field
```

### Test 8: Full End-to-End Query
```bash
# Open browser: http://localhost:8501
# Query: "P0750"
# Expected improvements:

# 1. ✅ Robust detection: Code found despite format variations
# 2. ✅ Chunking logging: See console output showing chunks detected
# 3. ✅ Vector scores: See similarity scores in logs
# 4. ✅ Confidence: Multi-factor score displayed
# 5. ✅ Source attribution: Rich metadata about where answer came from
# 6. ✅ Validation: Run `python -m backend.rag.validate_ingestion` to verify health
```

---

## 📊 Performance Baseline

Run before and after to measure improvement:

```bash
# Test initialization speed (singleton caching benefit)
python -c "
import time
from backend.rag.embedding import EmbeddingFactory

# Clear cache
EmbeddingFactory.clear_cache()

# First init
start = time.time()
EmbeddingFactory.get_embeddings()
first = time.time() - start

# Second call (should be instant with caching)
start = time.time()
EmbeddingFactory.get_embeddings()
second = time.time() - start

print(f'First init: {first:.2f}s')
print(f'Cached call: {second:.2f}s')
print(f'Speedup: {first/max(second, 0.001):.1f}x faster')
"

# Test retrieval quality
python -c "
import time
from backend.rag.retriever import RAGRetriever
from backend.rag.query_classifier import QueryClassifier

retriever = RAGRetriever()
classifier = QueryClassifier()

query = 'P0300'
category = classifier.classify(query)

start = time.time()
docs = retriever.retrieve(query, metadata_filter={'category': category.value})
elapsed = time.time() - start

print(f'Retrieved {len(docs)} docs in {elapsed:.2f}s')
if docs and 'vector_score' in docs[0].metadata:
    print('✓ Vector scores captured')
else:
    print('✗ Vector scores NOT captured')
"
```

---

## 📝 Validation Checklist

After deployment:

- [ ] Database re-ingested successfully
- [ ] Validation utility runs without errors: `python -m backend.rag.validate_ingestion`
- [ ] Chunk counts reasonable (50+ total chunks)
- [ ] All required metadata fields present
- [ ] Vector scores captured in retrieval
- [ ] Sample queries (P0300, oil change, engine misfire) return results
- [ ] Confidence scores showing (should vary based on relevance)
- [ ] Sources properly attributed with rich metadata
- [ ] Backend logs show new logging statements
- [ ] No errors in error.log

---

## 🆘 Troubleshooting

### Issue: "No OBD pattern matched" in logs
**Solution:** Check source document format. Improved patterns support:
```
P0300
Code: P0300
OBD Code: P0300
P0300 - Description
DTC P0300
```

If still not matching, add specific format to document test.

### Issue: Singleton caching not working (embeddings reinit every call)
**Solution:** Verify no code calls `EmbeddingFactory.clear_cache()`:
```bash
grep -r "clear_cache" backend/
```

Should return no results (except in tests).

### Issue: Vector scores showing 0 or NaN
**Solution:** Check ChromaDB initialization:
```python
from backend.rag.retriever import RAGRetriever
retriever = RAGRetriever()
print(f"Vector store initialized: {retriever.vector_store is not None}")
```

If False, re-ingest database.

### Issue: Validation utility fails
**Solution:** Run in order:
```bash
python -m backend.rag.ingest          # Step 1: Ingest
python -m backend.rag.validate_ingestion  # Step 2: Validate
```

---

## 📚 Reference Docs

- **Technical details:** See `TECHNICAL_REVIEW_RAG_IMPROVEMENTS.md`
- **Complete guide:** See `UPGRADE_GUIDE_RAG_2.0.md`
- **Quick reference:** See `RAG_2.0_QUICK_REFERENCE.md`

---

## ✨ Summary

All 10 improvements are production-ready:

✅ More robust pattern detection
✅ Better visibility into chunking
✅ Faster initialization (caching)
✅ More accurate confidence scoring
✅ Complete score transparency
✅ Configurable for any dataset size
✅ Rich source attribution
✅ Health check utility

**Ready to deploy!** 🚀
