from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List

from backend.graph.state import WorkflowState
from backend.rag.retriever import RAGRetriever

logger = logging.getLogger(__name__)


class CodeAgent:
    def __init__(self, data_path: str | None = None) -> None:
        # Data path is kept for compatibility but NOT USED
        # All diagnostic data comes from TXT files via RAG/ChromaDB ONLY
        self.rag_retriever = RAGRetriever()
        logger.info("[CodeAgent] ✓ Initialized - Using TXT files via RAG ONLY (no PDFs, no CSVs)")

    @staticmethod
    def _extract_severity(text: str) -> str:
        """Extract severity level from text."""
        text_lower = text.lower()
        if "critical" in text_lower or "severe" in text_lower or "urgent" in text_lower:
            return "Critical"
        elif "high" in text_lower or "major" in text_lower:
            return "High"
        elif "medium" in text_lower or "moderate" in text_lower:
            return "Medium"
        elif "low" in text_lower or "minor" in text_lower:
            return "Low"
        return "Unknown"

    def _extract_causes(self, text: str) -> List[str]:
        """Extract common causes from RAG text."""
        causes = []
        # Look for structured cause lists
        for line in text.split('\n'):
            line_clean = line.strip()
            # Skip headers and empty lines
            if line_clean and len(line_clean) > 15 and not any(x in line_clean.lower() for x in ['code:', 'severity:', 'system:', 'description:', '=']):
                # Remove bullet points and numbering
                clean = line_clean.lstrip('- •*123456789.) ')
                if len(clean) > 10 and len(clean) < 200:
                    causes.append(clean)
        return causes[:5]  # Return top 5 causes

    def _retrieve_from_rag(self, dtc_code: str) -> Dict[str, Any] | None:
        """Retrieve OBD code definition from RAG (TXT files in ChromaDB). 
        
        THIS IS THE ONLY AUTHORITATIVE SOURCE - No PDFs, No CSVs
        Extracts structured fields: Description, Severity, System Affected, Common Causes, etc.
        """
        try:
            query = f"OBD code {dtc_code} definition description severity causes"
            logger.info(f"[RAG] Querying ChromaDB for {dtc_code}...")
            docs = self.rag_retriever.retrieve(query, k=5)
            logger.info(f"[RAG] Retrieved {len(docs)} documents for {dtc_code}")
            
            if docs:
                combined_text = " ".join([doc.page_content for doc in docs])
                logger.info(f"[RAG] ✓ Found data for {dtc_code} (text length: {len(combined_text)} chars)")
                
                lines = combined_text.split('\n')
                result = {
                    "code": dtc_code.upper(),
                    "description": "",
                    "severity": "Unknown",
                    "system_affected": "",
                    "common_causes": [],
                    "diagnostic_steps": [],
                    "repair_recommendation": "",
                    "estimated_cost": "",
                }
                
                # Find the section for this code
                code_start_idx = -1
                for i, line in enumerate(lines):
                    if dtc_code.upper() in line.upper() and ('OBD Code:' in line or 'OBD-II' in line or line.strip().startswith('P') or line.strip().startswith('U') or line.strip().startswith('C')):
                        code_start_idx = i
                        logger.info(f"[RAG] Code section found at line {i}: {line[:80]}")
                        break
                
                if code_start_idx == -1:
                    logger.warning(f"[RAG] Code {dtc_code} not found in structured format")
                    return None
                
                # Extract fields from this code section until next code or end
                i = code_start_idx
                while i < len(lines):
                    line = lines[i]
                    line_lower = line.lower()
                    
                    # Stop if we hit the next code
                    if i > code_start_idx and ('OBD Code:' in line or 'OBD-II' in line) and dtc_code.upper() not in line.upper():
                        break
                    
                    # Extract Description
                    if 'description:' in line_lower:
                        desc_parts = [lines[i].split(':', 1)[1].strip() if ':' in lines[i] else ""]
                        i += 1
                        # Capture multi-line description
                        while i < len(lines) and lines[i].strip() and not ':' in lines[i]:
                            desc_parts.append(lines[i].strip())
                            i += 1
                        result["description"] = " ".join(desc_parts).strip()
                        continue
                    
                    # Extract Severity
                    if 'severity:' in line_lower:
                        result["severity"] = lines[i].split(':', 1)[1].strip() if ':' in lines[i] else "Unknown"
                    
                    # Extract System Affected
                    if 'system affected:' in line_lower or 'system:' in line_lower:
                        result["system_affected"] = lines[i].split(':', 1)[1].strip() if ':' in lines[i] else ""
                    
                    # Extract Common Causes
                    if 'common causes:' in line_lower:
                        i += 1
                        while i < len(lines) and (lines[i].startswith('  -') or lines[i].startswith('  •') or lines[i].startswith('  *')):
                            cause = lines[i].strip().lstrip('- •*').strip()
                            if cause:
                                result["common_causes"].append(cause)
                            i += 1
                        continue
                    
                    # Extract Diagnostic Steps
                    if 'diagnostic steps:' in line_lower:
                        i += 1
                        while i < len(lines) and (lines[i].strip().startswith(tuple('0123456789')) or lines[i].startswith('  ')):
                            step = lines[i].strip()
                            if step and ':' in step:
                                # Extract numbered step
                                step_text = step.split('.', 1)[-1].strip() if '.' in step else step
                                if step_text:
                                    result["diagnostic_steps"].append(step_text)
                                i += 1
                            elif ':' not in lines[i] and 'diagnostic' not in lines[i].lower() and 'repair' not in lines[i].lower():
                                i += 1
                            else:
                                break
                        continue
                    
                    # Extract Repair Recommendation
                    if 'repair recommendation:' in line_lower:
                        result["repair_recommendation"] = lines[i].split(':', 1)[1].strip() if ':' in lines[i] else ""
                    
                    # Extract Cost
                    if 'typical repair cost:' in line_lower or 'cost:' in line_lower:
                        result["estimated_cost"] = lines[i].split(':', 1)[1].strip() if ':' in lines[i] else ""
                    
                    i += 1
                
                logger.info(f"[RAG] ✓ Extracted complete data for {dtc_code}: desc_len={len(result['description'])}, causes={len(result['common_causes'])}, steps={len(result['diagnostic_steps'])}")
                
                return result
            
            logger.warning(f"[RAG] No documents found for {dtc_code}")
            return None
            
        except Exception as exc:
            logger.exception(f"[RAG] Error retrieving {dtc_code}: {exc}")
            return None

    def run(self, state: WorkflowState) -> WorkflowState:
        code = (state.get("code") or "").strip()
        if not code:
            return state

        # ONLY retrieve from RAG (TXT files in ChromaDB)
        # NO FALLBACK TO CSV OR PDFS
        logger.info(f"[CodeAgent] Looking up {code} in RAG knowledge base (TXT files only)...")
        result = self._retrieve_from_rag(code)
        
        if result and result.get("description"):
            logger.info(f"[CodeAgent] ✓ Found {code} in TXT knowledge base with full data")
            source_type = "RAG Knowledge Base (TXT Files)"
            result["source"] = "rag_txt"
        else:
            logger.warning(f"[CodeAgent] ✗ Code {code} NOT found in TXT knowledge base")
            # Return "not found" result instead of fallback
            result = {
                "code": code.upper(),
                "description": f"OBD code {code} not found in reference materials",
                "severity": "Unknown",
                "common_causes": [],
                "system_affected": "",
                "diagnostic_steps": [],
                "repair_recommendation": "",
                "estimated_cost": "",
                "source": "not_found"
            }
            source_type = "Code Not Found in Knowledge Base"

        state["code_result"] = result

        sources = state.get("sources", [])
        sources.append({
            "source": source_type,
            "type": "obd_code",
            "code": result.get("code", code),
        })
        state["sources"] = sources
        return state
