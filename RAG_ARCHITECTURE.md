# RAG Architecture - Comprehensive Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Components](#components)
3. [Document Ingestion Pipeline](#document-ingestion-pipeline)
4. [Retrieval Pipeline](#retrieval-pipeline)
5. [Reranking & Scoring](#reranking--scoring)
6. [Data Structures](#data-structures)
7. [Configuration Parameters](#configuration-parameters)
8. [Performance Optimization](#performance-optimization)

---

## System Overview

The RAG (Retrieval-Augmented Generation) system enhances LLM responses by retrieving relevant documents from a vector database before generation.

```
Query Input
    ↓
[RETRIEVAL STAGE]
  ├─ Query Classification
  ├─ Query Embedding (Azure)
  ├─ Vector Similarity Search
  └─ Initial Ranking
    ↓
[RERANKING STAGE]
  ├─ Cross-Encoder Scoring
  ├─ Confidence Calculation
  └─ Metadata Enrichment
    ↓
[GENERATION STAGE]
  ├─ LLM Prompt Construction
  ├─ Response Generation
  └─ Source Attribution
    ↓
Final Response with Sources
```

---

## Components

### 1. QueryClassifier (`backend/rag/query_classifier.py`)

**Purpose:** Identify query type to route to appropriate agent

**Supported Types:**
- `OBD`: Vehicle diagnostic trouble codes (P0000-P9999)
- `SYMPTOM`: Vehicle symptoms (engine stalling, misfire, etc.)
- `MAINTENANCE`: Maintenance tasks (oil change, brake inspection)

**Detection Patterns:**

```python
# OBD Detection (6+ formats)
P0300                          # Standard format
Code: P0300                     # Verbose
OBD Code: P0300               # Labeled
P0300 - Description           # With description
Diagnostic Trouble Code P0300 # Full name
DTC P0300                      # Abbreviation

# Maintenance Detection (8+ formats)
5000 km Service
ENGINE OIL CHANGE
Brake Inspection
Coolant Replacement
Air Filter Service
Scheduled Maintenance
Regular Service
Tire Rotation

# Symptom Detection (10+ formats)
Engine Misfire
Vehicle Stalling
Rough Idle
Poor Fuel Economy
Hard Starting
Transmission Slipping
Brake Noise
Battery Drain
Check Engine Light
Engine Overheating
```

**Implementation:**
```python
class QueryClassifier:
    @staticmethod
    def classify(query: str) -> QueryType:
        # Check OBD patterns
        if OBD_PATTERN.search(query):
            return QueryType.OBD
        
        # Check maintenance patterns
        if MAINTENANCE_PATTERN.search(query):
            return QueryType.MAINTENANCE
        
        # Check symptom patterns
        if SYMPTOM_PATTERN.search(query):
            return QueryType.SYMPTOM
        
        # Default
        return QueryType.UNKNOWN
```

---

### 2. EmbeddingFactory (`backend/rag/embedding.py`)

**Purpose:** Generate vector embeddings for documents and queries

**Configuration:**
- **Model**: Azure text-embedding-3-small
- **Dimensions**: 1536
- **Singleton Cache**: Yes (performance optimization)
- **Fallback**: None (Azure-only)

**Process:**
```python
class EmbeddingFactory:
    @staticmethod
    def get_embeddings() -> AzureOpenAIEmbeddings:
        # 1. Check cache
        if _embedding_instance exists:
            return cached instance  # ~10ms
        
        # 2. Initialize Azure OpenAI
        embeddings = AzureOpenAIEmbeddings(
            api_key=AZURE_OPENAI_API_KEY,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            azure_deployment=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
            api_version=2023-05-15,
            model="text-embedding-3-small"
        )
        
        # 3. Cache and return (~800ms first call)
        _embedding_instance = embeddings
        return embeddings
```

**Performance:**
- First call: ~800ms (Azure initialization)
- Cached calls: ~10-50ms (direct return)
- Query embedding: ~100ms per query
- Batch embedding: ~200-500ms for 59 documents

---

### 3. DocumentAwareChunker (`backend/rag/document_chunker.py`)

**Purpose:** Split documents into semantic chunks with pattern detection

**Chunking Strategy:**
```
Document Input
    ↓
[Pattern Detection]
    ├─ OBD codes (P0000-P9999)
    ├─ Maintenance headers
    ├─ Troubleshooting entries
    └─ Evaluation sections
    ↓
[Semantic Splitting]
    ├─ Chunk size: 300-500 tokens
    ├─ No overlap between chunks
    └─ Preserve metadata
    ↓
[Metadata Attachment]
    ├─ source_filename
    ├─ category (obd/maintenance/symptom/evaluation)
    ├─ chunk_type (obd_entry/maintenance_task/etc.)
    └─ chunk_size
    ↓
Indexed Chunks (59 total)
```

**Output Example:**
```python
# Chunk 1 (OBD Entry)
{
    "content": "P0300: Random/Multiple Cylinder Misfire Detected...",
    "metadata": {
        "source_filename": "OBD_Codes_Reference_A.txt",
        "category": "obd",
        "chunk_type": "obd_entry",
        "chunk_size": 356,
        "source": "OBD_Codes_Reference_A.txt"
    }
}

# Chunk 2 (Maintenance Task)
{
    "content": "Oil Change: Change engine oil and oil filter...",
    "metadata": {
        "source_filename": "Maintenance_Reference_A.txt",
        "category": "maintenance",
        "chunk_type": "maintenance_task",
        "chunk_size": 425,
        "source": "Maintenance_Reference_A.txt"
    }
}
```

**Logging:**
```
[DocumentAwareChunker] File=OBD_Codes_Reference_A.txt | Category=obd | OBD Entries Found=12 | Chunks Produced=12
```

---

### 4. RAGRetriever (`backend/rag/retriever.py`)

**Purpose:** Retrieve relevant chunks from vector database

**Retrieval Pipeline:**

```python
class RAGRetriever:
    def retrieve(self, query: str, query_type: QueryType, k: int = 5) -> List[Document]:
        # 1. Embed query
        query_embedding = embeddings.embed_query(query)  # 1536-dim vector
        
        # 2. Build filter (optional)
        if query_type == QueryType.OBD:
            where_filter = {"metadata.category": "obd"}
        elif query_type == QueryType.MAINTENANCE:
            where_filter = {"metadata.category": "maintenance"}
        elif query_type == QueryType.SYMPTOM:
            where_filter = {"metadata.category": "symptom"}
        
        # 3. Search ChromaDB
        results_with_scores = vector_store.similarity_search_with_score(
            query=query,
            k=k,
            where=where_filter
        )
        
        # 4. Convert scores and attach metadata
        for doc, distance in results_with_scores:
            # Convert Chroma distance to similarity (0-1)
            vector_score = max(0, 1 - (distance / 2))
            doc.metadata["vector_score"] = vector_score
            doc.metadata["vector_distance"] = distance
        
        return results_with_scores
```

**Score Calculation:**
```
Chroma uses L2 (Euclidean) distance
Distance range: 0 to 2+ (unbounded)

Conversion to similarity (0-1):
similarity = max(0, 1 - (distance / 2))

Examples:
distance=0.0    → similarity=1.0   (perfect match)
distance=0.5    → similarity=0.75  (very similar)
distance=1.0    → similarity=0.50  (similar)
distance=2.0    → similarity=0.0   (dissimilar)
distance>2.0    → similarity=0.0   (clamped to 0)
```

**Configurable Parameters:**
```
RETRIEVAL_K=5              # Number of chunks to retrieve
RERANK_TOP_K=3            # Number of chunks to rerank
```

---

### 5. CrossEncoderReranker (`backend/rag/reranker.py`)

**Purpose:** Rerank retrieved chunks using semantic relevance scoring

**Reranking Pipeline:**

```python
class CrossEncoderReranker:
    def rerank(self, query: str, documents: List[Document], top_k: int = 3) -> RankerOutput:
        # 1. Load cross-encoder model (MiniLM-L12-v2)
        model = CrossEncoder('cross-encoder/miniLM-L12-v2')
        
        # 2. Score pairs: (query, document)
        sentences = [(query, doc.content) for doc in documents]
        scores = model.predict(sentences)  # Range: -1 to 1
        
        # 3. Normalize to 0-1
        scores = (scores + 1) / 2
        
        # 4. Rank and select top-k
        ranked = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
        top_documents = [doc for doc, score in ranked[:top_k]]
        
        # 5. Calculate multi-factor confidence
        top_score = scores[0]
        avg_top_3 = np.mean(scores[:3])
        score_gap = max(scores) - min(scores)
        
        confidence = (top_score * 0.5) + (avg_top_3 * 0.3) + (score_gap * 0.2)
        
        # 6. Attach rerank scores to documents
        for doc, (orig_doc, score) in enumerate(ranked):
            doc.metadata["rerank_score"] = score
            doc.metadata["original_rank"] = documents.index(orig_doc)
        
        return RankerOutput(
            documents=top_documents,
            confidence=confidence,
            rerank_scores=scores
        )
```

**Confidence Formula:**
```
confidence = (top_score × 0.5) + (avg_top_3 × 0.3) + (score_gap × 0.2)

Factor 1: top_score × 0.5         (50% weight)
  - Relevance of best chunk
  - Most important factor

Factor 2: avg_top_3 × 0.3         (30% weight)
  - Average of 3 best chunks
  - Ensures consistency across top results

Factor 3: score_gap × 0.2         (20% weight)
  - Difference between best and worst
  - Large gap = high confidence
  - Small gap = uncertain

Example Calculation:
  top_score = 0.85
  avg_top_3 = 0.80
  score_gap = 0.85 - 0.65 = 0.20
  
  confidence = (0.85 × 0.5) + (0.80 × 0.3) + (0.20 × 0.2)
             = 0.425 + 0.24 + 0.04
             = 0.705 → 70.5% → MEDIUM confidence
```

**Confidence Levels:**
```
90-100%  → HIGH     ✅ Trust LLM output fully
70-90%   → MEDIUM   ⚠️  Generally reliable
50-70%   → MEDIUM   ⚠️  Use with caution
<50%     → LOW      ❌ Consider fallback
```

---

## Document Ingestion Pipeline

### End-to-End Ingestion Flow

```
[INPUT] TXT Files in data/documents/
    ├─ OBD_Codes_Reference_A.txt
    ├─ OBD_Codes_Reference_B.txt
    ├─ Maintenance_Reference_A.txt
    ├─ Maintenance_Reference_B.txt
    ├─ Service_Recommendation_Guide.txt
    ├─ Troubleshooting_Reference_A.txt
    ├─ Troubleshooting_Reference_B.txt
    ├─ Vehicle_Symptoms_Reference_Manual.txt
    └─ RAG_Evaluation_Reference.txt
         ↓
[LOAD] Read all documents
    └─ 9 files loaded
         ↓
[CATEGORIZE] Assign category based on filename
    ├─ OBD_Codes_* → obd
    ├─ Maintenance_* → maintenance
    ├─ *Troubleshooting_* → symptom
    ├─ *Symptoms_* → symptom
    ├─ Service_* → symptom
    └─ RAG_Evaluation_* → evaluation
         ↓
[CHUNK] DocumentAwareChunker.chunk_documents()
    ├─ Pattern matching for semantic boundaries
    ├─ Split on detected patterns
    ├─ Preserve metadata
    └─ 59 chunks produced
         ↓
[EMBED] EmbeddingFactory.embed_documents()
    ├─ Load/cache Azure embeddings
    ├─ Generate 1536-dim vectors
    └─ Attach to each chunk
         ↓
[STORE] Chroma.from_documents()
    ├─ Create/update collection
    ├─ Add chunks with metadata
    ├─ Build indices
    └─ Persist to disk
         ↓
[OUTPUT] ChromaDB Collection
    ├─ 27 OBD chunks
    ├─ 2 Maintenance chunks
    ├─ 4 Symptom chunks
    └─ 26 Evaluation chunks
```

### Ingestion Command
```bash
python -m backend.rag.ingest
```

### Ingestion Logging
```
[INGESTION] ===== Clearing old database =====
[INGESTION] ===== Loading TXT documents =====
[INGESTION] ✓ Loaded OBD_Codes_Reference_A.txt (category: obd)
[INGESTION] ✓ Loaded OBD_Codes_Reference_B.txt (category: obd)
[INGESTION] Total files loaded: 9
[INGESTION] Total documents loaded: 9
[INGESTION] ===== Document-Aware Chunking =====
[DocumentAwareChunker] File=OBD_Codes_Reference_A.txt | Category=obd | OBD Entries Found=12 | Chunks Produced=12
[DocumentAwareChunker] ✓ Total chunks created: 59
[INGESTION] Chunk distribution by category:
[INGESTION]   - evaluation: 26 chunks
[INGESTION]   - maintenance: 2 chunks
[INGESTION]   - obd: 27 chunks
[INGESTION]   - symptom: 4 chunks
[INGESTION] ===== Indexing into ChromaDB =====
[EmbeddingFactory] Initializing Azure OpenAI embeddings
[EmbeddingFactory] ✓ Azure OpenAI embeddings initialized successfully
[INGESTION] ✓✓✓ COMPLETE - Indexed 59 chunks
```

---

## Retrieval Pipeline

### Query-to-Response Flow

```
User Query: "P0300"
    ↓
[1] CLASSIFICATION
    query_type = QueryClassifier.classify("P0300")
    → QueryType.OBD
    ↓
[2] EMBEDDING
    query_embedding = embeddings.embed_query("P0300")
    → 1536-dimensional vector
    ↓
[3] FILTERING
    category_filter = {"metadata.category": "obd"}
    ↓
[4] RETRIEVAL (K=5)
    results = chroma_collection.query(
        query_embedding=query_embedding,
        where=category_filter,
        n_results=5
    )
    → 5 chunks with distances
    ↓
[5] SCORE CONVERSION
    for each chunk:
        vector_score = max(0, 1 - (distance / 2))
        attach to metadata
    ↓
[6] RERANKING (TOP_K=3)
    top_3 = CrossEncoderReranker.rerank(
        query="P0300",
        documents=5_chunks,
        top_k=3
    )
    → 3 reranked chunks with confidence
    ↓
[7] LLM GENERATION
    prompt = f"""
    Query: P0300
    Context (from retrieved chunks):
    {chunk1_content}
    {chunk2_content}
    {chunk3_content}
    
    Generate diagnosis...
    """
    response = llm.generate(prompt)
    ↓
[8] RESPONSE FORMATTING
    response = {
        "diagnosis": response_text,
        "confidence_score": 75,
        "sources": [
            {
                "source_filename": "OBD_Codes_Reference_A.txt",
                "category": "obd",
                "vector_score": 0.85,
                "rerank_score": 0.82,
                ...
            }
        ]
    }
    ↓
Final Response to User
```

---

## Reranking & Scoring

### Score Composition

Each retrieved chunk carries multiple scores:

```python
chunk.metadata = {
    # FROM RETRIEVAL
    "vector_score": 0.85,              # Similarity (0-1)
    "vector_distance": 0.30,           # L2 distance from query
    
    # FROM RERANKING
    "rerank_score": 0.82,              # Cross-encoder score
    "original_rank": 1,                # Position before reranking
    
    # FROM CLASSIFICATION
    "category": "obd",                 # Type of content
    "chunk_type": "obd_entry",         # Specific format
    
    # FROM INGESTION
    "source_filename": "OBD_Codes_Reference_A.txt",
    "source": "OBD_Codes_Reference_A.txt",
    "chunk_size": 356
}
```

### Confidence Scoring Algorithm

```python
def calculate_confidence(documents: List[Document], scores: List[float]) -> float:
    """Calculate multi-factor confidence score (0-1)"""
    
    # Factor 1: Top chunk relevance (50% weight)
    top_score = scores[0]
    
    # Factor 2: Consistency across top 3 (30% weight)
    avg_top_3 = np.mean(scores[:3])
    
    # Factor 3: Score disparity (20% weight)
    score_gap = max(scores) - min(scores)
    
    # Weighted combination
    confidence = (top_score * 0.5) + (avg_top_3 * 0.3) + (score_gap * 0.2)
    
    # Clamp to 0-1 and convert to percentage
    confidence = max(0, min(1, confidence))
    return confidence * 100  # 0-100%
```

### Logging

```
[Reranker] Confidence calculation: 
  top_score=0.85, 
  avg_top_3=0.80, 
  gap=0.20 
  → 70.5%
```

---

## Data Structures

### ChromaDB Collection Schema

```sql
-- Virtual schema (ChromaDB is document-based)
CREATE TABLE automotive_docs (
    id VARCHAR PRIMARY KEY,                    -- UUID
    content TEXT,                              -- Chunk text
    embedding VECTOR(1536),                    -- Azure embedding
    
    -- Metadata fields (stored as JSON)
    metadata JSONB {
        "source_filename": "string",
        "category": "obd|maintenance|symptom|evaluation",
        "chunk_type": "string",
        "chunk_size": "integer",
        "source": "string"
    }
);
```

### Document Structure (LangChain)

```python
class Document:
    page_content: str          # Chunk text (300-500 tokens)
    metadata: Dict[str, Any]   # Metadata dictionary
    
# Example:
doc = Document(
    page_content="P0300: Random/Multiple Cylinder Misfire...",
    metadata={
        "source_filename": "OBD_Codes_Reference_A.txt",
        "category": "obd",
        "chunk_type": "obd_entry",
        "chunk_size": 356,
        "source": "OBD_Codes_Reference_A.txt",
        "vector_score": 0.85,          # Added during retrieval
        "vector_distance": 0.30,
        "rerank_score": 0.82,          # Added during reranking
        "original_rank": 1
    }
)
```

### Response Structure (API)

```python
class DiagnoseResponse(BaseModel):
    diagnosis: str                          # LLM-generated diagnosis
    severity: Literal["HIGH", "MEDIUM", "LOW"]
    possible_causes: List[str]
    repair_steps: List[str]
    maintenance_recommendations: List[str]
    confidence_score: int                   # 0-100%
    sources: List[SourceAttribution]        # 8 fields each

class SourceAttribution(BaseModel):
    source_filename: str
    category: str
    chunk_type: str
    code: Optional[str]
    vector_score: float
    vector_distance: float
    rerank_score: float
    original_rank: int
```

---

## Configuration Parameters

### Environment Variables

```env
# RETRIEVAL PARAMETERS
RETRIEVAL_K=5              # Number of chunks to retrieve (default: 5)
RERANK_TOP_K=3            # Number of chunks to rerank (default: 3)

# EMBEDDING PARAMETERS
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
AZURE_OPENAI_API_VERSION=2023-05-15

# DATABASE PARAMETERS
CHROMA_PERSIST_DIR=./data/chroma
CHROMA_COLLECTION_NAME=automotive_docs
```

### Fine-tuning Guide

```python
# Higher RETRIEVAL_K = Broader search
RETRIEVAL_K=10  # More chunks, slower but catches edge cases
RETRIEVAL_K=3   # Fewer chunks, faster but might miss context

# Higher RERANK_TOP_K = More precision
RERANK_TOP_K=5  # More reranking, better quality
RERANK_TOP_K=1  # Single best chunk, faster
```

---

## Performance Optimization

### Caching Strategy

```python
# Embedding caching (singleton pattern)
class EmbeddingFactory:
    _embedding_instance = None  # Cached instance
    
    @staticmethod
    def get_embeddings():
        if _embedding_instance is None:
            _embedding_instance = AzureOpenAIEmbeddings(...)
            # First call: ~800ms
        return _embedding_instance
        # Cached call: ~10ms
```

### Batch Processing

```python
# Ingest 59 documents in batch
embeddings = embedding_factory.embed_documents(all_documents)
# Batch: ~1.2s
# vs Individual: 59 × 100ms = 5.9s

# Result: 80% faster
```

### Query Optimization

```python
# Filter before similarity search
where_filter = {"metadata.category": "obd"}
results = chroma.similarity_search(
    query=query_embedding,
    where=where_filter,  # Reduces search space
    k=5
)
# With filter: ~150ms
# Without filter: ~300ms
# Result: 2x faster
```

---

## Monitoring & Debugging

### Validation Suite

```bash
python -m backend.rag.validate_ingestion
```

Output:
```
✅ database_exists
✅ retriever_init
✅ chunk_distribution
✅ metadata_quality
✅ sample_retrieval
✅ vector_scores
✅ configuration
```

### Debug Logging

```python
# Enable detailed logging
LOG_LEVEL=DEBUG python -m backend.rag.ingest

# Output includes:
[RAGRetriever] Retrieved chunk 1: score=0.85, type=obd
[CrossEncoderReranker] Reranked chunk 1: score=0.82
[EmbeddingFactory] Using cached embeddings (10ms)
```

### Performance Profiling

```bash
# Time individual components
import time

start = time.time()
results = retriever.retrieve(query)
print(f"Retrieval: {time.time() - start:.2f}s")

start = time.time()
reranked = reranker.rerank(query, results)
print(f"Reranking: {time.time() - start:.2f}s")
```

---

## Best Practices

1. **Always ingest before querying** - ChromaDB must have data
2. **Use category filtering** - Faster and more relevant results
3. **Monitor confidence scores** - <60% = consider fallback
4. **Cache embeddings** - Dramatically improves performance
5. **Test with multiple queries** - Validate all 3 query types (OBD, Symptom, Maintenance)
6. **Review source attribution** - Ensures traceability
7. **Monitor Azure API usage** - Embeddings consume tokens
