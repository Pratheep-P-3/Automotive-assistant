from __future__ import annotations

import csv
import logging
import os
from pathlib import Path
from typing import Dict, List

from backend.graph.state import WorkflowState

logger = logging.getLogger(__name__)


class MaintenanceAgent:
    def __init__(self, data_path: str | None = None) -> None:
        root = Path(__file__).resolve().parents[2]
        self.data_path = Path(
            data_path
            or os.getenv(
                "MAINTENANCE_DATA_PATH",
                str(root / "data" / "maintenance" / "maintenance.csv"),
            )
        )

    @staticmethod
    def _preventive_actions(mileage: int | None) -> List[str]:
        if mileage is None:
            return [
                "Follow OEM service intervals in the owner manual.",
                "Check tire pressure and fluid levels monthly.",
            ]
        if mileage < 30000:
            return [
                "Rotate tires every 5,000-7,500 miles.",
                "Inspect engine air filter and cabin filter every service.",
            ]
        if mileage < 75000:
            return [
                "Inspect brake pads/rotors and suspension bushings.",
                "Replace engine coolant and transmission fluid per OEM interval.",
            ]
        return [
            "Perform comprehensive inspection of timing, ignition, and fuel systems.",
            "Monitor battery health, alternator output, and starter current draw.",
        ]

    def _load_rows(self) -> List[Dict[str, str]]:
        if not self.data_path.exists():
            logger.warning("Maintenance dataset not found at %s", self.data_path)
            return []
        with self.data_path.open("r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            return [row for row in reader]

    def run(self, state: WorkflowState) -> WorkflowState:
        make = (state.get("make") or "").strip().lower()
        model = (state.get("model") or "").strip().lower()
        mileage = state.get("mileage")

        rows = self._load_rows()
        filtered = [
            row
            for row in rows
            if (not make or (row.get("make") or "").strip().lower() == make)
            and (not model or (row.get("model") or "").strip().lower() == model)
        ]

        recommendations: List[str] = []
        if mileage is not None and filtered:
            sorted_rows = sorted(
                filtered,
                key=lambda r: abs(int((r.get("mileage") or "0") or "0") - mileage),
            )
            recommendations = [
                (row.get("maintenance_recommendation") or "").strip()
                for row in sorted_rows[:4]
                if (row.get("maintenance_recommendation") or "").strip()
            ]
        elif filtered:
            recommendations = [
                (row.get("maintenance_recommendation") or "").strip()
                for row in filtered[:4]
                if (row.get("maintenance_recommendation") or "").strip()
            ]

        if not recommendations:
            recommendations = [
                "Perform multi-point inspection and follow OEM scheduled maintenance.",
                "Replace engine oil and filter based on service interval and oil life.",
            ]

        state["maintenance_result"] = {
            "maintenance_recommendations": recommendations,
            "preventive_actions": self._preventive_actions(mileage),
        }

        sources = state.get("sources", [])
        sources.append(
            {
                "source": str(self.data_path),
                "type": "maintenance_dataset",
                "make": state.get("make"),
                "model": state.get("model"),
            }
        )
        state["sources"] = sources
        return state
