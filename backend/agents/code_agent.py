from __future__ import annotations

import csv
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

from backend.graph.state import WorkflowState
from backend.rag.retriever import RAGRetriever

logger = logging.getLogger(__name__)


class CodeAgent:
    def __init__(self, data_path: str | None = None) -> None:
        root = Path(__file__).resolve().parents[2]
        configured_path = data_path or os.getenv(
            "OBD_DATA_PATH", str(root / "data" / "obd" / "obd_codes.csv")
        )
        path_obj = Path(configured_path)
        self.data_path = path_obj if path_obj.is_absolute() else (root / path_obj)
        self.rag_retriever = RAGRetriever()  # Initialize RAG for PDF lookups

    @staticmethod
    def _parse_causes(raw: str) -> List[str]:
        for sep in ["|", ";"]:
            if sep in raw:
                return [item.strip() for item in raw.split(sep) if item.strip()]
        return [item.strip() for item in raw.split(",") if item.strip()]

    def _retrieve_from_rag(self, dtc_code: str) -> Dict[str, Any] | None:
        """Retrieve OBD code definition from RAG (PDFs in vector DB). This is the authoritative source."""
        try:
            # Query specifically for this OBD code
            query = f"OBD code {dtc_code} definition description severity causes"
            docs = self.rag_retriever.retrieve(query, k=5)  # Get more docs for better context
            
            if docs:
                # Found relevant documents from PDFs
                combined_text = " ".join([doc.page_content for doc in docs])
                logger.info(f"✓ RAG retrieved data for {dtc_code} from PDFs")
                
                # Extract structured information from retrieved content
                # Look for the code definition in the text
                lines = combined_text.split('\n')
                description = ""
                severity = "Unknown"
                causes = []
                
                # Find the line with this code and extract information
                for i, line in enumerate(lines):
                    if dtc_code.upper() in line.upper():
                        # This line mentions the code, extract description
                        if ':' in line:
                            description = line.split(':', 1)[1].strip()
                        elif '=' in line:
                            description = line.split('=', 1)[1].strip()
                        else:
                            description = line.replace(dtc_code, '').strip()
                        
                        # Look for severity indicators nearby
                        context = '\n'.join(lines[max(0, i-2):min(len(lines), i+3)])
                        severity = self._extract_severity(context)
                        causes = self._extract_causes(context)
                        break
                
                # If we didn't find specific details, use the whole text
                if not description:
                    description = combined_text[:400]
                    severity = self._extract_severity(combined_text)
                    causes = self._extract_causes(combined_text)
                
                return {
                    "code": dtc_code.upper(),
                    "description": description.strip() if description else "Definition from company PDFs",
                    "severity": severity,
                    "common_causes": causes,
                    "source": "rag_pdf"
                }
            else:
                logger.warning(f"✗ RAG found no data for {dtc_code}")
                return None
                
        except Exception as exc:
            logger.exception(f"RAG retrieval failed for {dtc_code}: {exc}")
            return None

    def _extract_severity(self, text: str) -> str:
        """Extract severity level from text."""
        text_lower = text.lower()
        if "critical" in text_lower or "severe" in text_lower:
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
        lines = text.split(".")
        for line in lines:
            line_clean = line.strip()
            if len(line_clean) > 20 and len(line_clean) < 200:
                causes.append(line_clean)
        return causes[:5]  # Return top 5 causes

    def _lookup_code(self, dtc_code: str) -> Dict[str, Any]:
        if not self.data_path.exists():
            logger.warning("OBD dataset not found at %s", self.data_path)
            return {
                "code": dtc_code,
                "description": "OBD dataset unavailable.",
                "severity": "Unknown",
                "common_causes": [],
            }

        with self.data_path.open("r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                code = (row.get("code") or "").strip().upper()
                if code == dtc_code.upper().strip():
                    return {
                        "code": code,
                        "description": (row.get("description") or "").strip(),
                        "severity": (row.get("severity") or "Unknown").strip() or "Unknown",
                        "common_causes": self._parse_causes(
                            (row.get("common_causes") or "").strip()
                        ),
                    }

        return {
            "code": dtc_code,
            "description": "Diagnostic code not found in local dataset.",
            "severity": "Unknown",
            "common_causes": [],
        }

    def run(self, state: WorkflowState) -> WorkflowState:
        code = (state.get("code") or "").strip()
        if not code:
            return state

        # Try RAG retrieval FIRST (from PDFs in vector DB) - this is the authoritative source
        logger.info(f"Looking up {code} in RAG vector database...")
        rag_result = self._retrieve_from_rag(code)
        
        if rag_result:
            # SUCCESS: Found in PDFs
            result = rag_result
            source_type = "RAG Knowledge Base (PDFs)"
            logger.info(f"✓ Using RAG data for {code}")
        else:
            # FALLBACK ONLY: CSV lookup (for codes not yet in PDFs)
            logger.warning(f"No RAG data for {code}, falling back to CSV...")
            result = self._lookup_code(code)
            source_type = "CSV Fallback"
            logger.warning(f"⚠ Using CSV fallback for {code}")

        state["code_result"] = result

        sources = state.get("sources", [])
        sources.append(
            {
                "source": source_type,
                "type": "obd_code",
                "code": result.get("code", code),
            }
        )
        state["sources"] = sources
        return state
