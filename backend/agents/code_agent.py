from __future__ import annotations

import logging
import re
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
        Uses flexible parsing to handle chunked text from RAG retrieval.
        """
        try:
            # Try multiple query variations to improve retrieval
            query_variations = [
                f"OBD code {dtc_code}",  # Most direct
                f"{dtc_code} trouble code definition",
                f"{dtc_code} diagnostic",
                f"OBD {dtc_code} description severity causes",
            ]
            
            combined_text = ""
            docs = []
            
            # Try each query variation until we get results
            for query in query_variations:
                logger.info(f"[RAG] Querying ChromaDB for {dtc_code} with: {query}")
                retrieved = self.rag_retriever.retrieve(query, k=8)
                if retrieved:
                    docs.extend(retrieved)
                    combined_text = " ".join([doc.page_content for doc in retrieved])
                    logger.info(f"[RAG] Retrieved {len(retrieved)} documents (total: {len(combined_text)} chars)")
                    break
            
            if not docs or not combined_text:
                logger.warning(f"[RAG] No documents found for {dtc_code} with any query variation")
                return None
            
            logger.info(f"[RAG] ✓ Found data for {dtc_code} (text length: {len(combined_text)} chars)")
            
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
            
            # Use regex-based extraction to handle chunked text robustly
            # Extract description (after "Description:" until next field header or end)
            desc_match = re.search(r'Description:\s*([^\n:]+(?:\n(?!\s*\w+:)[^\n]*)*)', combined_text, re.IGNORECASE)
            if desc_match:
                result["description"] = desc_match.group(1).strip().replace('\n', ' ')[:500]
            
            # Extract severity
            sev_match = re.search(r'Severity:\s*(\w+(?:\s+\w+)?)', combined_text, re.IGNORECASE)
            if sev_match:
                result["severity"] = sev_match.group(1).strip()
            
            # Extract system affected
            sys_match = re.search(r'(?:System\s+Affected|System):\s*([^\n]+)', combined_text, re.IGNORECASE)
            if sys_match:
                result["system_affected"] = sys_match.group(1).strip()
            
            # Extract common causes (lines starting with -, •, or * after "Common Causes:")
            causes_match = re.search(r'Common Causes:(.+?)(?=Diagnostic|Repair|Typical|---|\Z)', combined_text, re.IGNORECASE | re.DOTALL)
            if causes_match:
                causes_text = causes_match.group(1)
                # Find all bullet points
                causes_list = re.findall(r'^\s*[-•*]\s+(.+?)$', causes_text, re.MULTILINE)
                result["common_causes"] = [c.strip() for c in causes_list if c.strip()][:8]
            
            # Extract diagnostic steps (numbered items after "Diagnostic Steps:")
            steps_match = re.search(r'Diagnostic Steps:(.+?)(?=Repair|Typical|---|\Z)', combined_text, re.IGNORECASE | re.DOTALL)
            if steps_match:
                steps_text = steps_match.group(1)
                # Find all numbered steps
                steps_list = re.findall(r'^\s*\d+\.\s+(.+?)$', steps_text, re.MULTILINE)
                result["diagnostic_steps"] = [s.strip() for s in steps_list if s.strip()][:10]
            
            # Extract repair recommendation
            repair_match = re.search(r'Repair Recommendation:\s*([^\n]+)', combined_text, re.IGNORECASE)
            if repair_match:
                result["repair_recommendation"] = repair_match.group(1).strip()
            
            # Extract cost
            cost_match = re.search(r'(?:Typical )?Repair Cost:\s*([^\n]+)', combined_text, re.IGNORECASE)
            if cost_match:
                result["estimated_cost"] = cost_match.group(1).strip()
            
            # If we got a description, we found the code
            if result.get("description"):
                logger.info(f"[RAG] ✓ Extracted data for {dtc_code}: desc_len={len(result['description'])}, causes={len(result['common_causes'])}, steps={len(result['diagnostic_steps'])}")
                return result
            else:
                # Fallback: if no structured data found, still try to extract something
                logger.warning(f"[RAG] Code {dtc_code} not found with structured parsing, using full text extraction")
                result["description"] = combined_text[:500].strip()
                result["severity"] = self._extract_severity(combined_text)
                result["common_causes"] = self._extract_causes(combined_text)
                return result
            
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
