from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """
You are an expert automotive diagnostic and service advisor.
Always produce automotive-specific guidance tailored to the provided vehicle context.

Return ONLY valid JSON with this exact top-level schema:
{
  "issue_summary": "string",
  "diagnostic_code_description": "string",
  "likely_causes": ["string"],
  "severity": "Low|Medium|High|Critical|Unknown",
  "diagnostic_checklist": ["string"],
  "repair_recommendations": ["string"],
  "maintenance_recommendations": ["string"],
  "preventive_actions": ["string"],
  "confidence_score": 0.0,
  "references": ["string"],
  "api_response": {
    "diagnosis": "string",
    "severity": "string",
    "possible_causes": ["string"],
    "repair_steps": ["string"],
    "maintenance_recommendations": ["string"],
    "confidence_score": 0.0,
    "sources": ["string"]
  }
}

Rules:
1) Base conclusions only on provided evidence; do not invent unsupported facts.
2) Confidence score must be between 0.0 and 1.0.
3) If data is insufficient, explicitly say so and provide safe next diagnostic actions.
4) Keep repair and maintenance steps actionable and workshop-friendly.
""".strip()


class AzureOpenAIService:
    def __init__(self) -> None:
        self.model: AzureChatOpenAI | None = None
        try:
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
            deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
            api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
            api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")

            if endpoint and deployment and api_key:
                self.model = AzureChatOpenAI(
                    azure_endpoint=endpoint,
                    azure_deployment=deployment,
                    api_key=api_key,
                    api_version=api_version,
                    temperature=0.2,
                )
            else:
                logger.warning(
                    "Azure OpenAI not configured. Falling back to deterministic report generation."
                )
        except Exception as exc:
            logger.exception("Failed to initialize Azure OpenAI client: %s", exc)
            self.model = None

    @staticmethod
    def _strip_fences(raw: str) -> str:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:]
        return cleaned.strip()

    def _fallback_report(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        code_result = payload.get("code_result", {})
        symptom_result = payload.get("symptom_result", {})
        maintenance_result = payload.get("maintenance_result", {})

        diagnosis = code_result.get("description") or "Insufficient fault-code evidence; rely on symptoms and inspection."
        likely_causes = code_result.get("common_causes", [])
        if not likely_causes and symptom_result.get("troubleshooting_hints"):
            likely_causes = symptom_result.get("troubleshooting_hints", [])[:3]

        repair_steps = [
            "Scan and confirm active/pending DTCs with freeze-frame data.",
            "Perform visual inspection of affected system and connectors.",
            "Run component-level test according to OEM manual.",
            "Repair/replace failed component and clear codes.",
            "Road test and re-scan to verify fix.",
        ]

        maintenance_recommendations = maintenance_result.get(
            "maintenance_recommendations", []
        )
        preventive_actions = maintenance_result.get("preventive_actions", [])

        references = [src.get("source", "unknown") for src in payload.get("sources", [])]
        confidence = payload.get("confidence_score", 0.5)

        return {
            "issue_summary": diagnosis,
            "diagnostic_code_description": code_result.get("description", "No DTC description available."),
            "likely_causes": likely_causes,
            "severity": code_result.get("severity", "Unknown"),
            "diagnostic_checklist": [
                "Confirm complaint and reproduce condition.",
                "Check related fuses, harness, and connectors.",
                "Validate sensor and actuator live data.",
                "Cross-check with OEM troubleshooting flowchart.",
            ],
            "repair_recommendations": repair_steps,
            "maintenance_recommendations": maintenance_recommendations,
            "preventive_actions": preventive_actions,
            "confidence_score": confidence,
            "references": references,
            "api_response": {
                "diagnosis": diagnosis,
                "severity": code_result.get("severity", "Unknown"),
                "possible_causes": likely_causes,
                "repair_steps": repair_steps,
                "maintenance_recommendations": maintenance_recommendations,
                "confidence_score": confidence,
                "sources": references,
            },
        }

    def generate_report(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if self.model is None:
            return self._fallback_report(payload)

        human_prompt = (
            "Analyze the automotive diagnostic evidence and produce JSON only.\n\n"
            f"Evidence:\n{json.dumps(payload, indent=2)}"
        )

        try:
            response = self.model.invoke(
                [
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=human_prompt),
                ]
            )
            raw = response.content if isinstance(response.content, str) else str(response.content)
            parsed = json.loads(self._strip_fences(raw))

            if "api_response" not in parsed:
                parsed["api_response"] = {
                    "diagnosis": parsed.get("issue_summary", "No diagnosis generated."),
                    "severity": parsed.get("severity", "Unknown"),
                    "possible_causes": parsed.get("likely_causes", []),
                    "repair_steps": parsed.get("repair_recommendations", []),
                    "maintenance_recommendations": parsed.get(
                        "maintenance_recommendations", []
                    ),
                    "confidence_score": float(parsed.get("confidence_score", 0.5)),
                    "sources": parsed.get("references", []),
                }

            return parsed
        except Exception as exc:
            logger.exception("Azure OpenAI report generation failed: %s", exc)
            return self._fallback_report(payload)
