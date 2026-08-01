"""
Query Classifier for Automotive Diagnostics RAG.

Classifies user queries into categories:
- obd: OBD/DTC code queries
- maintenance: Maintenance service queries
- symptom: Vehicle symptom/problem queries
"""

from __future__ import annotations

import logging
import re
from enum import Enum
from typing import Literal

logger = logging.getLogger(__name__)


class QueryCategory(str, Enum):
    """Query categories for automotive diagnostics."""

    OBD = "obd"
    MAINTENANCE = "maintenance"
    SYMPTOM = "symptom"


class QueryClassifier:
    """Classifies user queries into automotive diagnostic categories."""

    # OBD Code patterns (P/U/C followed by 4 digits)
    OBD_PATTERN = re.compile(r"\b([PUC]\d{4})\b", re.IGNORECASE)

    # Maintenance keywords
    MAINTENANCE_KEYWORDS = {
        "oil change",
        "engine oil",
        "service interval",
        "scheduled service",
        "maintenance",
        "filter replacement",
        "coolant replacement",
        "air filter",
        "cabin filter",
        "spark plug",
        "brake fluid",
        "transmission fluid",
        "5000 km",
        "10000 km",
        "15000 km",
        "20000 km",
        "30000 km",
        "40000 km",
        "50000 km",
        "60000 km",
        "service due",
        "maintenance due",
        "check-up",
        "routine maintenance",
        "preventive maintenance",
        "fluid change",
        "battery replacement",
        "tire rotation",
        "wheel alignment",
        "brake pad",
        "brake inspection",
    }

    def __init__(self) -> None:
        """Initialize QueryClassifier."""
        logger.info("[QueryClassifier] ✓ Initialized")

    def classify(self, query: str) -> QueryCategory:
        """
        Classify a query into one of the automotive categories.

        Args:
            query: User query string

        Returns:
            QueryCategory (obd, maintenance, or symptom)
        """
        if not query or not isinstance(query, str):
            logger.warning("[QueryClassifier] Invalid query, defaulting to symptom")
            return QueryCategory.SYMPTOM

        query_lower = query.lower().strip()

        # Check for OBD codes first (highest priority)
        if self._is_obd_query(query_lower):
            logger.info(f"[QueryClassifier] ✓ Classified as OBD: '{query[:50]}...'")
            return QueryCategory.OBD

        # Check for maintenance keywords
        if self._is_maintenance_query(query_lower):
            logger.info(f"[QueryClassifier] ✓ Classified as MAINTENANCE: '{query[:50]}...'")
            return QueryCategory.MAINTENANCE

        # Default to symptom (catch-all)
        logger.info(f"[QueryClassifier] ✓ Classified as SYMPTOM: '{query[:50]}...'")
        return QueryCategory.SYMPTOM

    def _is_obd_query(self, query: str) -> bool:
        """
        Detect if query contains OBD codes.

        Args:
            query: Lowercase query string

        Returns:
            True if OBD code detected
        """
        obd_matches = self.OBD_PATTERN.findall(query)
        if obd_matches:
            logger.debug(f"[QueryClassifier] OBD codes found: {obd_matches}")
            return True
        return False

    def _is_maintenance_query(self, query: str) -> bool:
        """
        Detect if query is about maintenance.

        Args:
            query: Lowercase query string

        Returns:
            True if maintenance keywords found
        """
        for keyword in self.MAINTENANCE_KEYWORDS:
            if keyword in query:
                logger.debug(f"[QueryClassifier] Maintenance keyword found: '{keyword}'")
                return True

        return False

    def get_metadata_filter(self, category: QueryCategory) -> dict:
        """
        Get Chroma metadata filter for a category.

        Args:
            category: QueryCategory

        Returns:
            Metadata filter dict for Chroma
        """
        return {"category": category.value}
