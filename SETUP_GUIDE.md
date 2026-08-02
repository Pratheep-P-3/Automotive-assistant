# Automotive Diagnostics System - Setup Guide

## Prerequisites

- **OS:** Windows 10+ or Ubuntu 20.04+
- **Python:** 3.11+
- **RAM:** 4GB minimum
- **Internet:** Required for Azure OpenAI API

---

## Windows Setup

### 1. Clone Repository
```bash
git clone https://github.com/Pratheep-P-3/Automotive-assistant.git
cd Automotive-assistant/automotive-assistant
```

### 2. Create Virtual Environment
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create `.env` file with:
```env
AZURE_OPENAI_ENDPOINT=https://wp-sl-user-205-9314-resource.services.ai.azure.com
AZURE_OPENAI_API_KEY=<your-azure-key>
AZURE_OPENAI_DEPLOYMENT=gpt-5.1
AZURE_OPENAI_API_VERSION=2025-11-13

AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
AZURE_OPENAI_API_VERSION=2023-05-15
EMBEDDING_MODEL=
HUGGINGFACE_EMBEDDING_MODEL=

BACKEND_URL=http://localhost:8000
CHROMA_PERSIST_DIR=./data/chroma
CHROMA_COLLECTION_NAME=automotive_docs

LOG_LEVEL=INFO
RETRIEVAL_K=5
RERANK_TOP_K=3
```

### 5. Ingest Documents into Database
```bash
python -m backend.rag.ingest
```

Expected output:
```
[EmbeddingFactory] ✓ Azure OpenAI embeddings initialized successfully
[INGESTION] ✓✓✓ COMPLETE - Indexed 59 chunks
```

### 6. Start Backend (Terminal 1)
```bash
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

### 7. Start Frontend (Terminal 2)
```bash
streamlit run frontend/streamlit_app.py --server.port 8501
```

Expected output:
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

### 8. Access Application
Open browser: `http://localhost:8501`

---

## Ubuntu Setup

### 1. Clone Repository
```bash
cd ~/Desktop
git clone https://github.com/Pratheep-P-3/Automotive-assistant.git
cd Automotive-assistant/automotive-assistant
```

### 2. Create Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
```bash
cat > .env << 'EOF'
AZURE_OPENAI_ENDPOINT=https://wp-sl-user-205-9314-resource.services.ai.azure.com
AZURE_OPENAI_API_KEY=<your-azure-key>
AZURE_OPENAI_DEPLOYMENT=gpt-5.1
AZURE_OPENAI_API_VERSION=2025-11-13

AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
AZURE_OPENAI_API_VERSION=2023-05-15
EMBEDDING_MODEL=
HUGGINGFACE_EMBEDDING_MODEL=

BACKEND_URL=http://localhost:8000
CHROMA_PERSIST_DIR=./data/chroma
CHROMA_COLLECTION_NAME=automotive_docs

LOG_LEVEL=INFO
RETRIEVAL_K=5
RERANK_TOP_K=3
EOF
```

### 5. Ingest Documents
```bash
rm -rf data/chroma
python -m backend.rag.ingest
```

### 6. Start Backend (Terminal 1)
```bash
source .venv/bin/activate
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

### 7. Start Frontend (Terminal 2)
```bash
source .venv/bin/activate
streamlit run frontend/streamlit_app.py --server.port 8501 --server.address 0.0.0.0
```

### 8. Access Application
Open browser: `http://your-ubuntu-ip:8501`

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'fastapi'` | Run `pip install -r requirements.txt` |
| `Azure 404 error` | Check AZURE_OPENAI_ENDPOINT (should NOT have `/openai/v1`) |
| `Port 8000/8501 already in use` | Change port: `--port 8002` or kill process using port |
| `Cannot connect to Azure` | Verify API key and endpoint in `.env` |
| `Chroma database error` | Delete `data/chroma/` and re-ingest: `python -m backend.rag.ingest` |

---

## Validation

Run validation suite:
```bash
python -m backend.rag.validate_ingestion
```

Expected output:
```
✅ database_exists
✅ retriever_init
✅ chunk_distribution
✅ metadata_quality
✅ sample_retrieval
✅ vector_scores
✅ configuration
```

---

## API Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "ok"}
```
