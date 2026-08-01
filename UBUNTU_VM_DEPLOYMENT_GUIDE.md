# Ubuntu VM Deployment Guide - Complete Setup

## Prerequisites Checklist

Before deployment, ensure your Ubuntu VM has:

- ✅ Ubuntu 20.04 LTS or later
- ✅ Python 3.10+ installed
- ✅ 4GB+ RAM (8GB recommended)
- ✅ 2GB+ disk space
- ✅ Internet connectivity
- ✅ Azure OpenAI credentials (endpoint, key, deployment)
- ✅ Git installed

---

## Step 1: System Setup

### 1.1 Update System Packages
```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### 1.2 Install Python and Dependencies
```bash
# Install Python 3.11 (recommended)
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev
sudo apt-get install -y build-essential libssl-dev libffi-dev

# Install git
sudo apt-get install -y git

# Verify installation
python3.11 --version
git --version
```

### 1.3 Clone Repository
```bash
cd ~/
git clone https://github.com/Pratheep-P-3/Automotive-assistant.git
cd Automotive-assistant
```

---

## Step 2: Python Environment Setup

### 2.1 Create Virtual Environment
```bash
# Create venv
python3.11 -m venv .venv

# Activate venv
source .venv/bin/activate

# Verify activation (should show (.venv) prefix)
echo $VIRTUAL_ENV
```

### 2.2 Upgrade pip
```bash
pip install --upgrade pip setuptools wheel
```

---

## Step 3: Install Dependencies

### 3.1 Install All Requirements
```bash
# Install from requirements.txt
pip install -r requirements.txt

# This installs:
# - FastAPI & Uvicorn (backend)
# - Streamlit (frontend)
# - LangChain & LangGraph (orchestration)
# - ChromaDB (vector store)
# - sentence-transformers (reranking)
# - langchain-openai (Azure integration)
# - python-dotenv (config)
# - And 50+ other dependencies
```

**Expected time:** 3-5 minutes

### 3.2 Verify Core Installations
```bash
# Test key packages
python -c "
import fastapi; print(f'✓ FastAPI {fastapi.__version__}')
import streamlit; print(f'✓ Streamlit {streamlit.__version__}')
import langgraph; print(f'✓ LangGraph installed')
import chromadb; print(f'✓ ChromaDB installed')
import sentence_transformers; print(f'✓ Sentence Transformers installed')
"
```

---

## Step 4: Configuration

### 4.1 Create Environment File
```bash
# Copy example to .env
cp .env.example .env

# Edit .env with your Azure credentials
nano .env
```

### 4.2 Required Environment Variables

**IMPORTANT:** Update these in `.env`:

```bash
# ===== AZURE OpenAI Configuration =====
AZURE_OPENAI_ENDPOINT=https://your-instance.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
AZURE_OPENAI_API_VERSION=2024-10-21

# ===== Azure Foundry Alternative (if using Foundry) =====
# Instead of above, use:
AZURE_OPENAI_ENDPOINT=https://your-foundry-instance.openai.azure.com/openai/v1
AZURE_OPENAI_DEPLOYMENT=gpt-5-1 (or your model)
AZURE_OPENAI_API_KEY=your-foundry-key

# ===== Optional: Fine-tuning =====
LOG_LEVEL=INFO
RETRIEVAL_K=5
RERANK_TOP_K=3
CHROMA_COLLECTION_NAME=automotive_docs
CHROMA_PERSIST_DIR=./data/chroma
```

### 4.3 Verify Configuration
```bash
# Check if .env is readable
cat .env | grep -E "AZURE_OPENAI"

# Should show your credentials (mask them in screenshots!)
```

---

## Step 5: Database Initialization

### 5.1 Prepare Document Data
```bash
# Ensure document structure exists
mkdir -p data/chroma
mkdir -p data/manuals
mkdir -p data/maintenance

# Add your TXT files to:
# data/manuals/          (OBD reference files)
# data/maintenance/      (Maintenance procedures)

# Verify files are in place
ls -lah data/
```

**Note:** System uses TXT files only (no PDFs). See `data/manuals/example.txt` format.

### 5.2 Ingest Documents into ChromaDB
```bash
# Activate venv first
source .venv/bin/activate

# Run ingestion
python -m backend.rag.ingest

# Expected output:
# [DocumentAwareChunker] File=obd_reference.txt | Category=obd | Entries Found=50 | Chunks Produced=50
# [INGESTION] ✓✓✓ COMPLETE - Indexed 150 chunks
```

**Time estimate:** 1-2 minutes (depending on document size)

### 5.3 Validate Ingestion
```bash
# Run validation suite
python -m backend.rag.validate_ingestion

# Expected output:
# [TEST 1] Checking ChromaDB Database... ✓
# [TEST 2] Initializing RAG Retriever... ✓
# [TEST 3] Validating Chunk Counts... ✓
# [TEST 4] Validating Metadata... ✓
# [TEST 5] Testing Sample Retrieval... ✓
# [TEST 6] Testing Vector Scores... ✓
# [TEST 7] Checking Configuration... ✓
```

---

## Step 6: Start Backend Service

### 6.1 Run Backend in Foreground (Testing)
```bash
# Activate venv
source .venv/bin/activate

# Start backend
python -m uvicorn backend.app:app \
  --host 0.0.0.0 \
  --port 8000 \
  --reload

# Expected output:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete
```

**Test API health:**
```bash
# In another terminal
curl http://localhost:8000/health

# Expected response:
# {"status":"ok"}
```

### 6.2 Run Backend in Background (Production)
```bash
# Option 1: Using nohup
nohup python -m uvicorn backend.app:app \
  --host 0.0.0.0 \
  --port 8000 > backend.log 2>&1 &

# Option 2: Using screen
screen -S backend
source .venv/bin/activate
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
# Detach with Ctrl+A then D

# Option 3: Using tmux
tmux new-session -d -s backend
tmux send-keys -t backend "cd ~/Automotive-assistant && source .venv/bin/activate && python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000" Enter
```

### 6.3 Monitor Backend
```bash
# Check logs
tail -f backend.log

# Check if process running
ps aux | grep uvicorn

# Stop backend
pkill -f uvicorn
```

---

## Step 7: Start Frontend Service

### 7.1 Run Frontend in New Terminal
```bash
# Activate venv
source .venv/bin/activate

# Start Streamlit
streamlit run frontend/streamlit_app.py \
  --server.port=8501 \
  --server.address=0.0.0.0

# Expected output:
# You can now view your Streamlit app in your browser.
# Network URL: http://<your-vm-ip>:8501
# Local URL: http://localhost:8501
```

### 7.2 Access Streamlit

**From VM:**
```bash
# Open in browser (if X11 available)
firefox http://localhost:8501
```

**From Windows/Mac (accessing Ubuntu VM):**
```
# Use the Network URL from Streamlit output
http://<ubuntu-vm-ip>:8501

# Example:
http://192.168.1.100:8501
```

### 7.3 Run Streamlit in Background
```bash
# Option 1: nohup
nohup streamlit run frontend/streamlit_app.py \
  --server.port=8501 \
  --server.address=0.0.0.0 > streamlit.log 2>&1 &

# Option 2: screen
screen -S streamlit
source .venv/bin/activate
streamlit run frontend/streamlit_app.py --server.port=8501 --server.address=0.0.0.0

# Option 3: tmux
tmux new-session -d -s streamlit
tmux send-keys -t streamlit "cd ~/Automotive-assistant && source .venv/bin/activate && streamlit run frontend/streamlit_app.py --server.port=8501 --server.address=0.0.0.0" Enter
```

---

## Step 8: Full System Integration Test

### 8.1 Verify Both Services Running
```bash
# Check backend
curl http://localhost:8000/health
# Should return: {"status":"ok"}

# Check frontend
curl http://localhost:8501 2>&1 | head -20
# Should show HTML response
```

### 8.2 End-to-End Test
```bash
# Query backend directly
curl -X POST http://localhost:8000/diagnose \
  -H "Content-Type: application/json" \
  -d '{
    "code": "P0300",
    "make": "Toyota",
    "model": "Corolla",
    "year": 2020,
    "mileage": 60000,
    "symptoms": null,
    "maintenance_query": null
  }'

# Expected response:
# {
#   "diagnosis": "...",
#   "severity": "...",
#   "possible_causes": [...],
#   "repair_steps": [...],
#   "maintenance_recommendations": [...],
#   "confidence_score": 0.85,
#   "sources": [...]
# }
```

### 8.3 Test via Browser
1. Open: `http://<ubuntu-vm-ip>:8501`
2. Enter query: `P0300`
3. Click "Diagnose"
4. Verify output displays correctly

---

## Step 9: Firewall Configuration (If Required)

### 9.1 Ubuntu Firewall Setup
```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow 22/tcp

# Allow Backend (port 8000)
sudo ufw allow 8000/tcp

# Allow Frontend (port 8501)
sudo ufw allow 8501/tcp

# Verify rules
sudo ufw status
```

### 9.2 From External Machine
```bash
# Test connectivity
nc -zv <ubuntu-vm-ip> 8000
nc -zv <ubuntu-vm-ip> 8501
```

---

## Step 10: Production Deployment (Optional)

### 10.1 Using Systemd Services

**Create backend service** (`/etc/systemd/system/automotive-backend.service`):
```ini
[Unit]
Description=Automotive Backend Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Automotive-assistant
Environment="PATH=/home/ubuntu/Automotive-assistant/.venv/bin"
ExecStart=/home/ubuntu/Automotive-assistant/.venv/bin/python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Create frontend service** (`/etc/systemd/system/automotive-frontend.service`):
```ini
[Unit]
Description=Automotive Frontend Service
After=network.target automotive-backend.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Automotive-assistant
Environment="PATH=/home/ubuntu/Automotive-assistant/.venv/bin"
ExecStart=/home/ubuntu/Automotive-assistant/.venv/bin/streamlit run frontend/streamlit_app.py --server.port=8501 --server.address=0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start services:**
```bash
# Copy service files
sudo cp automotive-backend.service /etc/systemd/system/
sudo cp automotive-frontend.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable automotive-backend.service
sudo systemctl enable automotive-frontend.service

# Start services
sudo systemctl start automotive-backend.service
sudo systemctl start automotive-frontend.service

# Check status
sudo systemctl status automotive-backend.service
sudo systemctl status automotive-frontend.service

# View logs
sudo journalctl -u automotive-backend.service -f
sudo journalctl -u automotive-frontend.service -f
```

### 10.2 Using Docker (Alternative)

```bash
# Build Docker image
docker build -t automotive-assistant .

# Run with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop services
docker-compose down
```

---

## Troubleshooting

### Issue: "AZURE_OPENAI_ENDPOINT not found"
**Solution:**
```bash
# Check .env file
cat .env | grep AZURE_OPENAI

# Verify it's in the correct format
# AZURE_OPENAI_ENDPOINT=https://your-instance.openai.azure.com/
```

### Issue: "ChromaDB connection failed"
**Solution:**
```bash
# Verify database was initialized
ls -la data/chroma/

# Re-initialize if empty
python -m backend.rag.ingest
```

### Issue: "Streamlit: Cannot connect to backend"
**Solution:**
```bash
# Check backend is running
curl http://localhost:8000/health

# If not, restart backend
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000

# Check BACKEND_URL in frontend code
cat frontend/streamlit_app.py | grep BACKEND_URL
```

### Issue: "Port 8000/8501 already in use"
**Solution:**
```bash
# Find process using port
lsof -i :8000
lsof -i :8501

# Kill process
kill -9 <PID>

# Or use different ports
python -m uvicorn backend.app:app --port 9000
streamlit run frontend/streamlit_app.py --server.port 9502
```

### Issue: "ModuleNotFoundError: No module named 'backend'"
**Solution:**
```bash
# Ensure you're in the project root
pwd  # Should show: /home/ubuntu/Automotive-assistant

# Ensure venv is activated
source .venv/bin/activate

# Test import
python -c "import backend; print('✓')"
```

---

## Verification Checklist

After deployment, verify:

- [ ] Python 3.10+ installed
- [ ] Virtual environment activated
- [ ] All dependencies installed (pip list shows 60+ packages)
- [ ] .env file configured with Azure credentials
- [ ] Documents ingested (ChromaDB has 50+ chunks)
- [ ] Validation passes all 7 tests
- [ ] Backend running on port 8000
- [ ] Frontend running on port 8501
- [ ] Can access http://localhost:8501 from VM
- [ ] Can access http://<vm-ip>:8501 from other machines
- [ ] API health check returns {"status":"ok"}
- [ ] Sample query (P0300) returns full diagnosis
- [ ] Logs show no errors (check error.log)

---

## Quick Reference Commands

```bash
# Activate environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Ingest documents
python -m backend.rag.ingest

# Validate system
python -m backend.rag.validate_ingestion

# Start backend
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000

# Start frontend
streamlit run frontend/streamlit_app.py --server.port 8501 --server.address 0.0.0.0

# Check logs
tail -f error.log
tail -f backend.log

# Test API
curl http://localhost:8000/health

# Find processes
ps aux | grep uvicorn
ps aux | grep streamlit

# Stop services
pkill -f uvicorn
pkill -f streamlit
```

---

## Support

If issues occur:

1. Check logs: `tail -f error.log`
2. Verify configuration: `cat .env`
3. Test backend: `curl http://localhost:8000/health`
4. Review system output for specific error messages
5. Check file permissions: `ls -la backend/`

For Azure-specific issues, verify:
- ✅ Endpoint URL format is correct
- ✅ API key is valid
- ✅ Deployment name matches
- ✅ API version is 2024-10-21 or later
- ✅ Network access to Azure is allowed
