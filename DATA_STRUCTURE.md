# Knowledge Base Structure Guide

## Overview

The automotive knowledge base now supports **brand-specific prioritization**. When a user provides their vehicle make (Toyota, Honda, etc.), the system will prioritize documents specific to that brand while still falling back to generic documents.

## Current Directory Structure

```
data/
├── obd/
│   ├── generic/                 ← Generic OBD code documents
│   │   ├── OBD_Codes_Reference_A.txt
│   │   └── OBD_Codes_Reference_B.txt
│   ├── toyota/                  ← Toyota-specific OBD codes
│   │   └── (add Toyota OBD docs here)
│   └── honda/                   ← Honda-specific OBD codes
│       └── (add Honda OBD docs here)
│
├── maintenance/
│   ├── generic/                 ← Generic maintenance procedures
│   │   ├── Maintenance_Reference_A.txt
│   │   └── Maintenance_Reference_B.txt
│   ├── toyota/                  ← Toyota-specific maintenance
│   │   └── (add Toyota maintenance docs here)
│   └── honda/                   ← Honda-specific maintenance
│       └── (add Honda maintenance docs here)
│
├── troubleshooting/
│   ├── generic/                 ← Generic symptom/troubleshooting
│   │   ├── Troubleshooting_Reference_A.txt
│   │   ├── Vehicle_Symptoms_Reference_Manual.txt
│   │   └── Service_Recommendation_Guide.txt
│   ├── toyota/                  ← Toyota-specific troubleshooting
│   │   └── (add Toyota symptom docs here)
│   └── honda/                   ← Honda-specific troubleshooting
│       └── (add Honda symptom docs here)
│
├── evaluation/                  ← Evaluation documents (unchanged)
└── chroma/                       ← ChromaDB vector database (auto-generated)
```

## How Brand-Specific Prioritization Works

### 1. **Ingestion Phase** (backend/rag/ingest.py)

When documents are loaded, the system detects the directory structure:

```python
# File in: data/obd/generic/OBD_Codes_Reference_A.txt
# Metadata: make=None, model=None

# File in: data/obd/toyota/Toyota_OBD_Codes.txt
# Metadata: make="toyota", model=None

# File in: data/obd/honda/Honda_OBD_Codes.txt
# Metadata: make="honda", model=None
```

### 2. **Chunking Phase** (backend/rag/document_chunker.py)

Make/model metadata is preserved through all chunking operations, so each chunk knows its brand origin.

### 3. **Retrieval Phase** (backend/rag/retriever.py)

When a user provides their vehicle make, the retriever:

1. **Fetches candidates**: Retrieves 2x the requested documents (e.g., 10 instead of 5)
2. **Separates by brand**: Splits results into brand-specific and generic
3. **Prioritizes**: Returns brand-specific docs first, then generic
4. **Logs details**: Shows which docs came from which source

Example:
```
User make=toyota, query="P0300"

Retrieval results:
  - 2 brand-specific (Toyota) docs with vector_scores 0.85, 0.82
  - 8 generic docs with vector_scores 0.80, 0.78, 0.75, ...

Final ranking (top 5):
  1. Toyota doc (0.85)
  2. Toyota doc (0.82)
  3. Generic doc (0.80)
  4. Generic doc (0.78)
  5. Generic doc (0.75)
```

### 4. **Agent Processing**

All three v2 agents now pass vehicle info to the retriever:
- **CodeAgent** (OBD codes)
- **SymptomAgent** (troubleshooting)
- **MaintenanceAgent** (maintenance procedures)

## Adding Brand-Specific Documents

### Step 1: Create Brand Directory

For a new brand (e.g., Ford):

```bash
mkdir -p data/obd/ford
mkdir -p data/maintenance/ford
mkdir -p data/troubleshooting/ford
```

### Step 2: Add Documents

Create text files following the same format as generic documents:

**data/obd/ford/Ford_OBD_Codes.txt**
```
OBD Code: P0300
Multiple Cylinder Misfire (Ford-specific)

Common Causes in Ford Vehicles:
- Spark plug quality issues (Ford uses specific spark plug specifications)
- Coil pack failure (common in Ford F-150, Escape)
- Fuel injector fouling

Ford-Specific Diagnostic Steps:
1. Check Ford diagnostic parameter IDs (DPIDs) using Ford-specific scanner
2. Verify Ford coil pack specifications
3. Test fuel pressure (Ford spec: 55-60 PSI for most models)

Ford-Specific Parts:
- OEM Ford Motorcraft plugs recommended
- Ford part numbers for coils: example codes here
- Fuel injector cleaning kit (Ford approved)
```

**data/maintenance/ford/Ford_Maintenance_Schedules.txt**
```
Ford Scheduled Maintenance

15,000 Miles Service
- Tire rotation
- Visual inspection
- Change engine air filter

30,000 Miles Service
- Tire rotation
- Engine air filter replacement
- Cabin air filter replacement

Ford-Specific Notes:
- Ford F-150: Transmission fluid change at 50k miles (Ford recommendation)
- Ford Escape: Check power steering fluid monthly (known issue)
- Ford Focus: Engine coolant flush at 100k miles (not 60k like other brands)
```

### Step 3: Re-ingest Documents

Run the ingestion pipeline to add new documents to the database:

```bash
cd automotive-assistant
python -m backend.rag.ingest
```

The system will:
- Detect Ford documents in `data/obd/ford/`, `data/maintenance/ford/`, etc.
- Extract make="ford" from directory name
- Create chunks with brand metadata
- Index into ChromaDB
- Preserve all brand-specific metadata for retrieval

## Testing Brand-Specific Retrieval

### Using Frontend

1. Start the application:
   ```bash
   # Terminal 1: Backend
   python -m backend.main
   
   # Terminal 2: Frontend
   streamlit run frontend/streamlit_app.py
   ```

2. Enter vehicle info:
   - Make: "Toyota"
   - Model: "Corolla" (optional)
   - Year: "2020" (optional)

3. Query diagnostics:
   - Code: "P0300"
   - Or Symptoms: "rough idle"
   - Or Maintenance: "What service is needed at 60000 miles?"

### Using Backend API

```bash
curl -X POST http://localhost:8000/diagnose \
  -H "Content-Type: application/json" \
  -d {
    "make": "toyota",
    "code": "P0300",
    "symptoms": null,
    "maintenance_query": null
  }
```

### Checking Logs

Look for brand-specific prioritization in logs:

```
[CHROMA] Applying vehicle-aware ranking for make=toyota
[CHROMA] Ranking: 2 brand-specific + 8 generic, returning top 5

[CodeAgent] Prioritizing Toyota documents
[CodeAgent] Doc 1: source=Toyota_OBD_Codes.txt, make=toyota, vector_score=0.85
[CodeAgent] Doc 2: source=OBD_Codes_Reference_A.txt, make=None, vector_score=0.80
```

## Metadata Fields in Each Chunk

When documents are ingested, each chunk gets these metadata fields:

```python
{
    "source": "Toyota_OBD_Codes.txt",           # Original filename
    "category": "obd",                          # Document category
    "file_path": "data/obd/toyota/...",         # Full file path
    "make": "toyota",                           # Brand (from directory)
    "model": None,                              # Model (future expansion)
    "chunk_type": "obd_entry",                  # Semantic unit type
    "code": "P0300",                            # For OBD: the code
    "procedure": "Oil Change Service",          # For maintenance: the procedure
    "symptom": "Engine Misfire",                # For symptoms: the symptom
    "chunk_size": 1250,                         # Bytes in chunk
    "vector_score": 0.85,                       # Similarity score (0-1)
}
```

## Migration from Flat Structure

If you have existing documents in flat structure (e.g., `data/obd/*.txt`):

1. The ingestion pipeline **automatically supports both structures**
2. Old files in `data/obd/*.txt` will be loaded as generic (make=None)
3. Optionally, move generic files to `data/obd/generic/` for cleanliness

```bash
# Option 1: Keep as-is (system handles both)
# - Leave old files in data/obd/
# - Add brand-specific subdirectories
# - System will auto-detect and merge

# Option 2: Organize cleanly
mkdir -p data/obd/generic
mv data/obd/*.txt data/obd/generic/  # Move generic files
# Then add brand-specific subdirectories
```

## Future Enhancements

### Model-Specific Documents

The system is designed for model-specific documents too:

```
data/obd/toyota/corolla/
  ├── Corolla_2015_2020_OBD_Codes.txt
  └── Corolla_Known_Issues_2015_2020.txt

data/obd/toyota/camry/
  └── Camry_OBD_Codes.txt
```

When model-specific filtering is enabled, the retriever will:
1. Prioritize exact brand+model match
2. Fall back to brand match
3. Fall back to generic

### Year-Based Documents

Documents can be tagged with year ranges for model-year-specific diagnostics:

```
data/obd/honda/Civic_2020_2024_OBD_Codes.txt
Metadata: make="honda", model="civic", year_range="2020-2024"
```

## Performance Considerations

- **Retrieval**: Fetches 2x candidates for brand filtering (~20ms overhead)
- **Re-ranking**: Cross-encoder still ranks within filtered set (no additional cost)
- **Storage**: Brand-specific docs don't increase storage, just organize it
- **Scaling**: System handles 100+ brand-specific documents efficiently

## Troubleshooting

### Documents not being found by brand

1. Check directory name matches vehicle make:
   ```
   User enters: "Toyota" or "toyota" → System looks for data/obd/toyota/
   ```

2. Verify make metadata in chunks:
   ```bash
   python -c "
   from backend.rag.ingest import _load_txt_documents
   from pathlib import Path
   docs = _load_txt_documents({'obd': Path('data/obd')})
   for doc in docs[:3]:
      print(f'Source: {doc.metadata[\"source\"]}, Make: {doc.metadata[\"make\"]}')
   "
   ```

3. Re-ingest documents:
   ```bash
   python -m backend.rag.ingest
   ```

### Generic documents not prioritized without make

- This is expected behavior
- Retriever only applies brand prioritization if make is provided
- Fallback to standard vector similarity ranking

## Summary

✅ **Brand-Specific Prioritization**: Documents are organized by make/model in directory structure
✅ **Automatic Metadata Extraction**: Make/model extracted from directory names
✅ **Backward Compatible**: Flat structure still works
✅ **Smart Ranking**: Brand-specific docs ranked first, generic as fallback
✅ **Easy Expansion**: Add new brands by creating new directories
✅ **Future-Ready**: Model-specific and year-specific filtering can be added

The knowledge base now grows in value as you add more brand-specific documents!
