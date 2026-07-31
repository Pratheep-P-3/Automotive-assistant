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
                description = ""
                severity = "Unknown"
                causes = []
                
                # Find line with this code and extract info
                code_found = False
                for i, line in enumerate(lines):
                    if dtc_code.upper() in line.upper():
                        logger.info(f"[RAG] Code found in text: {line[:80]}")
                        code_found = True
                        
                        # Extract description from various formats
                        if ':' in line:
                            description = line.split(':', 1)[1].strip()
                        elif '=' in line:
                            description = line.split('=', 1)[1].strip()
                        else:
                            description = line.replace(dtc_code, '').strip()
                        
                        # Extract severity and causes from context
                        context = '\n'.join(lines[max(0, i-2):min(len(lines), i+5)])
                        severity = self._extract_severity(context)
                        causes = self._extract_causes(context)
                        break
                
                # Fallback: use full text if code not found in specific line
                if not code_found:
                    logger.info(f"[RAG] Code not found in specific line, extracting from full text")
                    description = combined_text[:300]
                    severity = self._extract_severity(combined_text)
                    causes = self._extract_causes(combined_text)
                
                logger.info(f"[RAG] ✓ Extracted: severity={severity}, causes={len(causes)}")
                
                return {
                    "code": dtc_code.upper(),
                    "description": description.strip() if description else f"Code {dtc_code} from company TXT reference materials",
                    "severity": severity,
                    "common_causes": causes,
                    "source": "rag_txt"
                }
            else:
                logger.warning(f"[RAG] ✗ No matching documents found for {dtc_code}")
                return None
                
        except Exception as exc:
            logger.exception(f"[RAG] ✗ Retrieval FAILED for {dtc_code}: {exc}")
            return None

    def run(self, state: WorkflowState) -> WorkflowState:
        code = (state.get("code") or "").strip()
        if not code:
            return state

        # ONLY retrieve from RAG (TXT files in ChromaDB)
        # NO FALLBACK TO CSV OR PDFS
        logger.info(f"[CodeAgent] Looking up {code} in RAG knowledge base (TXT files only)...")
        result = self._retrieve_from_rag(code)
        
        if result:
            logger.info(f"[CodeAgent] ✓ Found {code} in TXT knowledge base")
            source_type = "RAG Knowledge Base (TXT Files)"
        else:
            logger.warning(f"[CodeAgent] ✗ Code {code} NOT found in TXT knowledge base")
            # Return "not found" result instead of fallback
            result = {
                "code": code.upper(),
                "description": f"OBD code {code} not found in reference materials",
                "severity": "Unknown",
                "common_causes": [],
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
