# Frontend/Backend Alignment Fix Guide

## 🚨 Critical Issue

Your production workflow is using **OLD agents (v1)** instead of **NEW agents (v2)** that have all the RAG improvements.

**Current:** `code_agent.py` (v1) + `symptom_agent.py` (v1)
**Should be:** `code_agent_v2.py` (v2) + `symptom_agent_v2.py` (v2)

---

## The Fix (5 Minutes)

### Step 1: Backup Current File
```bash
cp backend/graph/workflow.py backend/graph/workflow.py.backup
```

### Step 2: Update Import in workflow.py

**File:** `backend/graph/workflow.py`

**CHANGE THIS (Lines 6-9):**
```python
from backend.agents.code_agent import CodeAgent
from backend.agents.maintenance_agent import MaintenanceAgent
from backend.agents.report_agent import ReportAgent
from backend.agents.symptom_agent import SymptomAgent
```

**TO THIS:**
```python
from backend.agents.code_agent_v2 import CodeAgent
from backend.agents.maintenance_agent import MaintenanceAgent
from backend.agents.report_agent import ReportAgent
from backend.agents.symptom_agent_v2 import SymptomAgent
```

### Step 3: Verify No Other Changes Needed

The rest of `workflow.py` stays unchanged because:
- ✅ v2 agents have same `.run(state)` interface as v1
- ✅ State management is compatible
- ✅ Routing logic works with both versions
- ✅ ReportAgent works with both

---

## Implementation: One-Click Fix

I'll make this change now. It's a single file, 2-line import change:
