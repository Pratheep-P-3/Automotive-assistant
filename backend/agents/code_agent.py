from __future__ import annotations

import csv
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

from backend.graph.state import WorkflowState

logger = logging.getLogger(__name__)


class CodeAgent:
    def __init__(self, data_path: str | None = None) -> None:
        root = Path(__file__).resolve().parents[2]
        configured_path = data_path or os.getenv(
            "OBD_DATA_PATH", str(root / "data" / "obd" / "obd_codes.csv")
        )
        path_obj = Path(configured_path)
        self.data_path = path_obj if path_obj.is_absolute() else (root / path_obj)

    @staticmethod
    def _parse_causes(raw: str) -> List[str]:
        for sep in ["|", ";"]:
            if sep in raw:
                return [item.strip() for item in raw.split(sep) if item.strip()]
        return [item.strip() for item in raw.split(",") if item.strip()]

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

        result = self._lookup_code(code)
        state["code_result"] = result

        sources = state.get("sources", [])
        sources.append(
            {
                "source": str(self.data_path),
                "type": "obd_dataset",
                "code": result.get("code", code),
            }
        )
        state["sources"] = sources
        return state
