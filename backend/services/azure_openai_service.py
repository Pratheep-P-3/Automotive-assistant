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

**CONFIDENCE-AWARE RESPONSES:**
You will receive confidence scores (0-100%) from the RAG re-ranking pipeline:
- 80-100%: High Confidence → Provide definitive diagnosis
- 60-79%:  Medium Confidence → Provide diagnosis with context and caveats
- Below 60%: Low Confidence → Flag limitations and recommend professional verification

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
  "confidence_percentage": 0-100,
  "confidence_level": "High Confidence|Medium Confidence|Low Confidence",
  "confidence_notes": "string - explanation of confidence level and any caveats",
  "references": ["string - which TXT files used"],
  "api_response": {
    "diagnosis": "string - comprehensive diagnosis",
    "severity": "string",
    "possible_causes": ["string"],
    "repair_steps": ["string - numbered procedural steps"],
    "maintenance_recommendations": ["string"],
    "cost_estimate": "string",
    "confidence_score": 0.0,
    "confidence_percentage": 0-100,
    "confidence_level": "string",
    "sources": ["string"]
  }
}

RESPONSE GUIDELINES:

1) **Confidence-Based Messaging:**
   - HIGH (80-100%): "Based on the knowledge base, [definitive statement]..."
   - MEDIUM (60-79%): "The knowledge base suggests [statement] based on [reasoning]..."
   - LOW (Below 60%): "The knowledge base has limited information. [statement]. Professional verification recommended."

2) **Comprehensive Detail:** Use ALL relevant information from the TXT files
   - Include full diagnostic procedures (not just summaries)
   - List ALL common causes with likelihoods/rankings
   - Provide detailed repair steps and procedures
   - Include cost estimates and time requirements
   - Add safety warnings when relevant

3) **Accuracy:** ONLY use information from provided evidence
   - Copy exact descriptions from code_result.description
   - Use common_causes as provided
   - Reference diagnostic steps from reference materials
   - DO NOT add external knowledge or training data

4) **Completeness:** Include these sections when applicable:
   - Detailed issue summary (150-300 words, not 1 sentence)
   - Step-by-step diagnostic checklist (5-10 steps minimum)
   - Ordered list of causes by likelihood
   - Detailed repair procedures
   - Cost estimates and labor time
   - Safety warnings and precautions
   - Preventive maintenance recommendations
   - Confidence-based caveats

5) **Confidence Integration:**
   - Use provided confidence_percentage from RAG pipeline
   - Map to confidence_level (High/Medium/Low)
   - Add confidence_notes explaining reliability
   - For Low Confidence: Add disclaimer about professional consultation

6) **Safety First:**
   - Flag any safety-critical issues (brakes, steering, cooling) with URGENT warnings
   - Include emergency procedures when applicable
   - Recommend professional help for complex repairs
   - Escalate safety concerns regardless of confidence level

7) **Actionable:** 
   - Each repair step must be specific and procedural
   - Include tool requirements
   - Note when professional help is needed
   - Provide cost ranges for planning
   - Reference confidence level in limitations

EXAMPLE OF HIGH CONFIDENCE RESPONSE (P0171, confidence 85%):
- confidence_level: "High Confidence"
- confidence_notes: "Re-ranked semantic match (score 0.85) to multiple knowledge base entries"
- issue_summary: Comprehensive explanation with definitive language
- safety_warnings: Prominently displayed

EXAMPLE OF LOW CONFIDENCE RESPONSE (Unknown code, confidence 45%):
- confidence_level: "Low Confidence"
- confidence_notes: "Limited knowledge base coverage for this query. Recommend OEM service manual consultation."
- issue_summary: Cautious explanation with caveats
- maintenance_recommendations: Professional inspection recommended

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
        """
        Generate comprehensive fallback report when LLM unavailable.

        Uses RAG pipeline confidence scores for accurate representation.
        """
        code_result = payload.get("code_result", {})
        symptom_result = payload.get("symptom_result", {})
        maintenance_result = payload.get("maintenance_result", {})

        # ===== Extract Confidence from RAG Pipeline =====
        confidence_pct = code_result.get("confidence", 0)
        confidence_level = code_result.get("confidence_level", "Low Confidence")

        # Map confidence to appropriate messaging
        if confidence_pct >= 80:
            confidence_guidance = "HIGH CONFIDENCE"
        elif confidence_pct >= 60:
            confidence_guidance = "MEDIUM CONFIDENCE"
        else:
            confidence_guidance = "LOW CONFIDENCE"

        # Build comprehensive diagnosis from all available sources
        diagnosis_parts = []
        if code_result.get("description"):
            diagnosis_parts.append(f"DTC Code: {code_result.get('description')}")
        if symptom_result.get("symptoms"):
            diagnosis_parts.append(f"Reported Symptoms: {', '.join(symptom_result.get('symptoms', []))}")
        if code_result.get("severity"):
            diagnosis_parts.append(f"Severity Level: {code_result.get('severity')}")

        issue_summary = (
            " | ".join(diagnosis_parts)
            if diagnosis_parts
            else "Insufficient fault-code evidence; rely on symptoms and inspection."
        )

        # Get causes (comprehensive)
        likely_causes = code_result.get("common_causes", [])
        if not likely_causes and symptom_result.get("troubleshooting_hints"):
            likely_causes = symptom_result.get("troubleshooting_hints", [])[:5]

        # Get comprehensive repair steps
        repair_steps = code_result.get("repair_steps", [])
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
                safety_warnings.append(
                    "SAFETY CRITICAL: Brake system failure - Do not drive, arrange towing."
                )
            elif "steering" in str(code_result).lower():
                safety_warnings.append(
                    "SAFETY CRITICAL: Steering system issue - Do not drive, arrange towing."
                )
            elif "overheating" in str(code_result).lower():
                safety_warnings.append(
                    "ENGINE OVERHEATING: Stop immediately, turn off engine, check coolant after cooling."
                )

        # Add confidence disclaimer if low
        if confidence_pct < 60:
            safety_warnings.insert(
                0,
                f"LOW CONFIDENCE ({confidence_pct}%): Knowledge base has limited information. "
                "Professional verification strongly recommended.",
            )

        references = [src.get("source", "unknown") for src in payload.get("sources", [])]
        confidence_score = confidence_pct / 100.0  # Convert to 0-1 scale

        # Generate confidence notes
        if confidence_pct >= 80:
            confidence_notes = (
                f"High confidence in this diagnosis ({confidence_pct}%). "
                "The knowledge base contains matching entries with strong relevance scores."
            )
        elif confidence_pct >= 60:
            confidence_notes = (
                f"Moderate confidence ({confidence_pct}%). The knowledge base provides relevant information, "
                "but may lack specific details. Verify with additional resources if needed."
            )
        else:
            confidence_notes = (
                f"Low confidence ({confidence_pct}%). The knowledge base has limited specific information. "
                "Professional verification strongly recommended."
            )

        logger.info(f"[Fallback] Generating report with {confidence_guidance} (score: {confidence_pct}%)")

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
            "confidence_score": confidence_score,
            "confidence_percentage": confidence_pct,
            "confidence_level": confidence_level,
            "confidence_notes": confidence_notes,
            "references": references,
            "api_response": {
                "diagnosis": issue_summary,
                "severity": severity,
                "possible_causes": likely_causes[:5],
                "repair_steps": repair_steps[:8],
                "maintenance_recommendations": maintenance_recommendations[:3],
                "cost_estimate": cost_estimate,
                "confidence_score": confidence_score,
                "confidence_percentage": confidence_pct,
                "confidence_level": confidence_level,
                "sources": references,
            },
        }

    def generate_report(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive diagnostic report using LLM.

        Integrates RAG pipeline confidence scores for confidence-aware responses.

        Args:
            payload: Evidence dict with code_result, symptom_result, maintenance_result,
                    confidence scores, and sources

        Returns:
            Comprehensive diagnostic report with confidence levels
        """
        if self.model is None:
            return self._fallback_report(payload)

        # ===== Extract Confidence Information from RAG Pipeline =====
        code_result = payload.get("code_result", {})
        confidence_pct = code_result.get("confidence", 0)
        confidence_level = code_result.get("confidence_level", "Low Confidence")

        # Map confidence percentage to level for LLM
        if confidence_pct >= 80:
            confidence_guidance = "HIGH CONFIDENCE"
        elif confidence_pct >= 60:
            confidence_guidance = "MEDIUM CONFIDENCE"
        else:
            confidence_guidance = "LOW CONFIDENCE"

        # ===== Build Enhanced Prompt with Confidence Context =====
        human_prompt = (
            "Analyze the automotive diagnostic evidence and produce JSON only.\n\n"
            f"CONFIDENCE CONTEXT: {confidence_guidance} (Score: {confidence_pct}%)\n"
            f"- This indicates the relevance of the retrieved knowledge base entries.\n"
            f"- Adjust response certainty and caveats based on this confidence level.\n\n"
            f"Evidence:\n{json.dumps(payload, indent=2)}"
        )

        try:
            logger.info(
                f"[LLM] Generating report with {confidence_guidance} "
                f"(confidence: {confidence_pct}%, level: {confidence_level})"
            )

            response = self.model.invoke(
                [
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=human_prompt),
                ]
            )

            raw = response.content if isinstance(response.content, str) else str(response.content)
            parsed = json.loads(self._strip_fences(raw))

            # ===== OVERRIDE WITH RAG Confidence Scores (NOT LLM-generated) =====
            # Use the reranker's actual confidence, not the LLM's inflated scores
            parsed["confidence_score"] = confidence_pct / 100.0  # Convert % to 0-1 scale
            parsed["confidence_percentage"] = confidence_pct
            parsed["confidence_level"] = confidence_level

            # Add confidence notes if not already present
            if "confidence_notes" not in parsed:
                if confidence_pct >= 80:
                    parsed["confidence_notes"] = (
                        f"High confidence in this diagnosis. "
                        f"The knowledge base contains matching entries "
                        f"(re-ranking score: {confidence_pct}%)."
                    )
                elif confidence_pct >= 60:
                    parsed["confidence_notes"] = (
                        f"Moderate confidence. The knowledge base provides relevant information, "
                        f"but may lack specific details for this vehicle/situation (score: {confidence_pct}%). "
                        f"Verify with additional resources if needed."
                    )
                else:
                    parsed["confidence_notes"] = (
                        f"Low confidence. The knowledge base has limited specific information for this query "
                        f"(score: {confidence_pct}%). Professional verification strongly recommended."
                    )

            # ===== Build Structured API Response =====
            if "api_response" not in parsed:
                parsed["api_response"] = {
                    "diagnosis": parsed.get("issue_summary", "No diagnosis generated."),
                    "severity": parsed.get("severity", "Unknown"),
                    "possible_causes": parsed.get("likely_causes", []),
                    "repair_steps": parsed.get("repair_recommendations", []),
                    "maintenance_recommendations": parsed.get(
                        "maintenance_recommendations", []
                    ),
                    "confidence_score": confidence_pct / 100.0,  # Use RAG score, not LLM
                    "confidence_percentage": confidence_pct,
                    "confidence_level": confidence_level,
                    "sources": parsed.get("references", []),
                }

            logger.info(
                f"[LLM] ✓ Report generated successfully "
                f"(confidence: {confidence_level}, score: {confidence_pct}%)"
            )

            return parsed

        except json.JSONDecodeError as exc:
            logger.exception(f"[LLM] ✗ Failed to parse JSON response: {exc}")
            return self._fallback_report(payload)
        except Exception as exc:
            logger.exception(f"[LLM] ✗ Report generation failed: {exc}")
            return self._fallback_report(payload)
