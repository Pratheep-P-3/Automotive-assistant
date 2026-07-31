from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI, ChatOpenAI

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """
You are an expert automotive diagnostic and service advisor. Your knowledge comes EXCLUSIVELY from the company's proprietary TXT reference materials stored in the vector database (RAG).

**CRITICAL AUTHORITY:** Use ONLY information provided in the evidence. The TXT reference files contain comprehensive diagnostic procedures, common causes, repair steps, and cost estimates. Leverage ALL of this detail.

**RESPONSE EXPECTATIONS:**
You must provide COMPREHENSIVE, DETAILED, and ACTIONABLE diagnostic reports using all available information from the TXT reference materials. This is NOT a summary - it should be thorough.

Return ONLY valid JSON with this exact schema:
{
  "issue_summary": "string - comprehensive explanation of the issue (150-300 words)",
  "diagnostic_code_description": "string - exact description from reference materials",
  "likely_causes": ["string - detailed cause with percentage likelihood or ranking"],
  "severity": "Low|Medium|High|Critical|Urgent",
  "diagnostic_checklist": ["string - specific numbered diagnostic steps from reference materials"],
  "repair_recommendations": ["string - detailed repair steps with procedures"],
  "maintenance_recommendations": ["string - preventive maintenance that applies"],
  "preventive_actions": ["string - actions to prevent recurrence"],
  "estimated_cost_range": "string - repair cost range from reference materials",
  "estimated_time": "string - time estimate in hours",
  "safety_warnings": ["string - any safety concerns"],
  "confidence_score": 0.0-1.0,
  "references": ["string - which TXT files used"],
  "api_response": {
    "diagnosis": "string - comprehensive diagnosis",
    "severity": "string",
    "possible_causes": ["string"],
    "repair_steps": ["string - numbered procedural steps"],
    "maintenance_recommendations": ["string"],
    "cost_estimate": "string",
    "confidence_score": 0.0,
    "sources": ["string"]
  }
}

RESPONSE GUIDELINES:
1) **Comprehensive Detail:** Use ALL relevant information from the TXT files
   - Include full diagnostic procedures (not just summaries)
   - List ALL common causes with likelihoods/rankings
   - Provide detailed repair steps and procedures
   - Include cost estimates and time requirements
   - Add safety warnings when relevant

2) **Accuracy:** ONLY use information from provided evidence
   - Copy exact descriptions from code_result.description
   - Use common_causes as provided
   - Reference diagnostic steps from reference materials
   - DO NOT add external knowledge or training data

3) **Completeness:** Include these sections when applicable:
   - Detailed issue summary (150-300 words, not 1 sentence)
   - Step-by-step diagnostic checklist (5-10 steps minimum)
   - Ordered list of causes by likelihood
   - Detailed repair procedures
   - Cost estimates and labor time
   - Safety warnings and precautions
   - Preventive maintenance recommendations

4) **Structure:** 
   - issue_summary: 150-300 words explaining the problem, impacts, and urgency
   - diagnostic_code_description: Exact text from reference
   - likely_causes: Ranked list with percentages or descriptions
   - diagnostic_checklist: 5-15 specific steps (numbered)
   - repair_recommendations: 3-10 detailed repair procedures
   - maintenance_recommendations: 2-5 relevant maintenance items
   - preventive_actions: 2-5 ways to prevent recurrence

5) **Confidence Scoring:**
   - RAG (TXT) source only: 0.80-0.90 base
   - + Vehicle make/model/year: +0.05
   - + Mileage context: +0.03
   - + Symptoms correlation: +0.05
   - Maximum: 0.95

6) **Safety First:**
   - Flag any safety-critical issues (brakes, steering, cooling) with URGENT warnings
   - Include emergency procedures when applicable
   - Recommend professional help for complex repairs

7) **Actionable:** 
   - Each repair step must be specific and procedural
   - Include tool requirements
   - Note when professional help is needed
   - Provide cost ranges for planning

EXAMPLE OF GOOD RESPONSE (Issue: P0171 Fuel System Too Lean):
- issue_summary: 300 word comprehensive explanation
- diagnostic_code_description: "System Too Lean (Bank 1)"
- likely_causes: [
    "Vacuum leak (most common - 30%)",
    "Dirty MAF sensor (20%)",
    "Low fuel pressure (15%)",
    ...
  ]
- diagnostic_checklist: [
    "1. Check for vacuum leaks using smoke test",
    "2. Measure fuel pressure at fuel rail (40-65 PSI expected)",
    ...10+ steps
  ]
- repair_recommendations: [
    "Replace MAF sensor: Remove air intake tube, unplug sensor, install new sensor, reconnect hoses",
    "Check vacuum system: Inspect all hoses for cracks, use propane smoke test, seal any leaks",
    ...5-10 detailed steps
  ]
- estimated_cost_range: "$80-300 depending on cause"
- estimated_time: "1-3 hours"

DO NOT provide minimal, one-sentence summaries. The reference materials contain comprehensive details - USE ALL OF THEM.
""".strip()


class AzureOpenAIService:
    def __init__(self) -> None:
        self.model: AzureChatOpenAI | ChatOpenAI | None = None
        try:
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
            deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
            api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
            api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")

            if endpoint and deployment and api_key:
                # Detect if this is an Azure Foundry endpoint (OpenAI-compatible format)
                if "openai/v1" in endpoint:
                    # Azure Foundry: Use OpenAI client with base_url
                    logger.info("Detected Azure Foundry endpoint. Using OpenAI-compatible client.")
                    self.model = ChatOpenAI(
                        model=deployment,
                        api_key=api_key,
                        base_url=endpoint,
                        temperature=0.2,
                    )
                else:
                    # Standard Azure OpenAI: Use AzureChatOpenAI
                    logger.info("Detected standard Azure OpenAI endpoint.")
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
        """Generate comprehensive fallback report when LLM unavailable."""
        code_result = payload.get("code_result", {})
        symptom_result = payload.get("symptom_result", {})
        maintenance_result = payload.get("maintenance_result", {})

        # Build comprehensive diagnosis from all available sources
        diagnosis_parts = []
        if code_result.get("description"):
            diagnosis_parts.append(f"DTC Code: {code_result.get('description')}")
        if symptom_result.get("symptoms"):
            diagnosis_parts.append(f"Reported Symptoms: {', '.join(symptom_result.get('symptoms', []))}")
        if code_result.get("severity"):
            diagnosis_parts.append(f"Severity Level: {code_result.get('severity')}")
        
        issue_summary = " | ".join(diagnosis_parts) if diagnosis_parts else "Insufficient fault-code evidence; rely on symptoms and inspection."

        # Get causes (comprehensive)
        likely_causes = code_result.get("common_causes", [])
        if not likely_causes and symptom_result.get("troubleshooting_hints"):
            likely_causes = symptom_result.get("troubleshooting_hints", [])[:5]

        # Get comprehensive repair steps
        repair_steps = code_result.get("repair_procedures", [])
        if not repair_steps:
            repair_steps = [
                "1. Scan and confirm active/pending DTCs with freeze-frame data.",
                "2. Perform visual inspection of affected system and connectors.",
                "3. Run component-level test according to OEM manual.",
                "4. Test each likely cause in order of probability.",
                "5. Repair/replace failed component and clear codes.",
                "6. Road test and re-scan to verify fix.",
                "7. Document repair for service history.",
            ]

        # Get cost estimate if available
        cost_estimate = code_result.get("estimated_cost", "Check with local service center for pricing")
        repair_time = code_result.get("estimated_time", "1-4 hours depending on cause")

        # Comprehensive diagnostic checklist
        diagnostic_checklist = [
            "1. Confirm customer complaint and try to reproduce condition.",
            "2. Check all related fuses, relays, and harness connectors for corrosion.",
            "3. Validate sensor and actuator live data with scan tool.",
            "4. Cross-check with OEM troubleshooting flowchart.",
            "5. Perform component resistance/voltage tests as indicated.",
            "6. Identify root cause (not just symptom).",
        ]

        # Add symptom-specific diagnostic steps
        if symptom_result.get("diagnostic_workflow"):
            diagnostic_checklist.extend(symptom_result.get("diagnostic_workflow", [])[:3])

        maintenance_recommendations = maintenance_result.get("maintenance_recommendations", [])
        preventive_actions = maintenance_result.get("preventive_actions", [])

        # Build safety warnings
        safety_warnings = []
        severity = code_result.get("severity", "Unknown")
        if severity in ["Critical", "Urgent", "High"]:
            if "brake" in str(code_result).lower():
                safety_warnings.append("⚠️ SAFETY CRITICAL: Brake system failure - Do not drive, arrange towing.")
            elif "steering" in str(code_result).lower():
                safety_warnings.append("⚠️ SAFETY CRITICAL: Steering system issue - Do not drive, arrange towing.")
            elif "overheating" in str(code_result).lower():
                safety_warnings.append("⚠️ ENGINE OVERHEATING: Stop immediately, turn off engine, check coolant after cooling.")

        references = [src.get("source", "unknown") for src in payload.get("sources", [])]
        confidence = payload.get("confidence_score", 0.65)

        return {
            "issue_summary": issue_summary,
            "diagnostic_code_description": code_result.get("description", "No DTC description available."),
            "likely_causes": likely_causes,
            "severity": severity,
            "diagnostic_checklist": diagnostic_checklist,
            "repair_recommendations": repair_steps,
            "maintenance_recommendations": maintenance_recommendations[:5],
            "preventive_actions": preventive_actions[:3],
            "estimated_cost_range": cost_estimate,
            "estimated_time": repair_time,
            "safety_warnings": safety_warnings,
            "confidence_score": confidence,
            "references": references,
            "api_response": {
                "diagnosis": issue_summary,
                "severity": severity,
                "possible_causes": likely_causes[:5],
                "repair_steps": repair_steps[:8],
                "maintenance_recommendations": maintenance_recommendations[:3],
                "cost_estimate": cost_estimate,
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
