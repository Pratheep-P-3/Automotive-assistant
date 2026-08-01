# ⚡ Ubuntu Deployment: Quick Start (30 min)

## Copy-Paste Ready Commands

```bash
# 1. System Setup (2 min)
sudo apt-get update && sudo apt-get install -y python3.11 python3.11-venv git build-essential libssl-dev libffi-dev

# 2. Clone & Setup (3 min)
cd ~
git clone https://github.com/Pratheep-P-3/Automotive-assistant.git
cd Automotive-assistant
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel

# 3. Install Dependencies (5 min)
pip install -r requirements.txt

# 4. Configure Credentials (1 min)
cp .env.example .env
nano .env  # EDIT: Add your Azure credentials
#    AZURE_OPENAI_ENDPOINT=your-endpoint
#    AZURE_OPENAI_API_KEY=your-key
#    AZURE_OPENAI_DEPLOYMENT=your-deployment

# 5. Initialize Database (2 min)
python -m backend.rag.ingest

# 6. Verify System (2 min)
python verify_deployment.py

# 7. Start Backend (1 min) - Terminal 1
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000

# 8. Start Frontend (1 min) - Terminal 2
source .venv/bin/activate
streamlit run frontend/streamlit_app.py --server.port 8501 --server.address 0.0.0.0

# 9. Access & Test (5 min)
# Open: http://localhost:8501
# Query: P0300
# You should see full LLM response (now Azure is accessible)
```

**Total time: ~30 minutes**

---

## What You'll See (Expected Output)

### Terminal 1 (Backend)
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
[CodeAgent] ✓ Initialized with production RAG pipeline
[RAGRetriever] ✓ Successfully initialized Chroma database
```

### Terminal 2 (Frontend)
```
You can now view your Streamlit app in your browser.
Network URL: http://<your-vm-ip>:8501
Local URL: http://localhost:8501
```

### Browser (http://localhost:8501)
```
Enter: P0300
Click: Diagnose

Expected Response:
✅ Diagnostic Summary
✅ Severity Level (with color)
✅ Root Cause Analysis
✅ Repair Recommendations
✅ Maintenance Recommendations
✅ Confidence Score (80%+)
✅ Knowledge Sources (with 8 metadata fields)
```

---

## Key Differences from Windows

| Aspect | Windows | Ubuntu |
|--------|---------|--------|
| Network | ❌ No Azure access | ✅ Azure APIs work |
| LLM | ⚠️ Fallback reports | ✅ Real LLM responses |
| Performance | ✅ Same | ✅ Same |
| Code | ✅ Same | ✅ Same |
| Database | ✅ Same | ✅ Same |

**The code is IDENTICAL - only Azure network access differs!**

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'backend'"
```bash
# Make sure you're in the right directory
pwd  # Should end with: /Automotive-assistant
# Verify venv activated
which python  # Should show .venv/bin/python
```

### "Port 8000 already in use"
```bash
lsof -i :8000
kill -9 <PID>
```

### "Can't import from backend"
```bash
# Add to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python -c "from backend.app import app; print('✓')"
```

### "Azure credentials not working"
```bash
# Check .env file
cat .env | grep AZURE_OPENAI
# Should show your real credentials (not template values)
```

---

## Verification Checklist

- [ ] Python 3.11 installed
- [ ] Repository cloned
- [ ] Virtual environment activated
- [ ] Dependencies installed (pip list shows 60+ packages)
- [ ] .env configured with Azure credentials
- [ ] Database ingested (python -m backend.rag.ingest completed)
- [ ] Verification passed (python verify_deployment.py shows all ✅)
- [ ] Backend running on 8000 (curl http://localhost:8000/health → {"status":"ok"})
- [ ] Frontend running on 8501 (streamlit output shows Network URL)
- [ ] Can access http://localhost:8501 from browser
- [ ] Query P0300 returns full diagnosis (with LLM response, not just fallback)

---

## Next: Production Setup (Optional)

### Option 1: Systemd Services (Persistent)
```bash
# See UBUNTU_VM_DEPLOYMENT_GUIDE.md Section 10.1
# Services auto-start on reboot, auto-restart on failure
sudo systemctl enable automotive-backend.service
sudo systemctl enable automotive-frontend.service
```

### Option 2: Docker (Containerized)
```bash
docker-compose up -d
docker-compose logs -f backend
```

### Option 3: Screen/Tmux (Simple)
```bash
screen -S backend
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
# Detach: Ctrl+A then D
```

---

## Support Resources

- **Full Ubuntu Guide:** UBUNTU_VM_DEPLOYMENT_GUIDE.md (10 steps, detailed)
- **Deployment Checklist:** DEPLOYMENT_READINESS_CHECKLIST.md (15 sections)
- **Verification Script:** `python verify_deployment.py`
- **Status Report:** DEPLOYMENT_STATUS_REPORT.md (comprehensive)

---

## You're Now Ready! 🎉

**In 30 minutes, you'll have:**
- ✅ Full system running on Ubuntu
- ✅ Azure APIs accessible (P0300 query shows full LLM response)
- ✅ Production-ready deployment
- ✅ All 10 RAG improvements active
- ✅ Ready to scale and monitor

**Report back with results!** 🚀
