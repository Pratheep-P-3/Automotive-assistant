from __future__ import annotations

import os
from typing import Any, Dict, List

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Automotive Diagnostics Assistant",
    page_icon="🚗",
    layout="wide",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Space Grotesk', sans-serif;
    }

    .stApp {
        background: radial-gradient(circle at 20% 20%, #f0f7ff, #f8fbff 40%, #e6eef8 100%);
    }

    .hero-card {
        background: linear-gradient(135deg, #12355b 0%, #1d5f87 70%, #2a9d8f 100%);
        padding: 1.4rem;
        border-radius: 16px;
        color: white;
        box-shadow: 0 12px 32px rgba(18, 53, 91, 0.25);
        margin-bottom: 1rem;
    }

    .result-card {
        background: #ffffff;
        border: 1px solid #dbe7f3;
        border-radius: 14px;
        padding: 1rem 1.2rem;
        box-shadow: 0 6px 20px rgba(18, 53, 91, 0.08);
        margin-bottom: 0.9rem;
    }

    .section-title {
        font-weight: 700;
        color: #12355b;
        font-size: 1rem;
        margin-bottom: 0.4rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero-card">
      <h2 style="margin:0;">Vehicle Diagnostics and Service Recommendation Assistant</h2>
      <p style="margin:0.4rem 0 0 0;">Enter any combination of DTC, symptoms, and vehicle profile to generate a structured diagnosis report.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Vehicle Profile")
    make = st.text_input("Vehicle Make", placeholder="Toyota")
    model = st.text_input("Vehicle Model", placeholder="Corolla")
    year = st.number_input("Vehicle Year", min_value=1950, max_value=2100, value=2020)
    mileage_input = st.text_input("Mileage (optional)", placeholder="60000")

st.subheader("Diagnostic Inputs")
col1, col2 = st.columns([1, 1])
with col1:
    code = st.text_input("Diagnostic Code (DTC)", placeholder="P0171")
with col2:
    maintenance_query = st.text_input(
        "Maintenance Query (optional)",
        placeholder="What should I service at 60,000 miles?",
    )

symptoms = st.text_area(
    "Symptoms",
    placeholder="rough idle and poor fuel economy",
    height=120,
)

def _format_source(source: Dict[str, Any]) -> str:
    base = source.get("source", "unknown")
    src_type = source.get("type", "")
    page = source.get("page")
    suffix = f" ({src_type})" if src_type else ""
    if page is not None:
        suffix += f" page={page}"
    return f"- {base}{suffix}"


def _render_list(items: List[str], empty_text: str) -> None:
    if not items:
        st.write(empty_text)
        return
    for item in items:
        st.markdown(f"- {item}")


def diagnose() -> Dict[str, Any]:
    mileage_value = int(mileage_input) if mileage_input.strip() else None
    payload = {
        "make": make or None,
        "model": model or None,
        "year": int(year) if year else None,
        "mileage": mileage_value,
        "code": code or None,
        "symptoms": symptoms or None,
        "maintenance_query": maintenance_query or None,
    }
    response = requests.post(
        f"{BACKEND_URL}/diagnose",
        json=payload,
        timeout=90,
    )
    response.raise_for_status()
    return response.json()


if st.button("Diagnose", type="primary", use_container_width=True):
    with st.spinner("Running diagnostics workflow..."):
        try:
            result = diagnose()
            st.success("Diagnostic report generated")

            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Diagnostic Summary</div>', unsafe_allow_html=True)
            st.write(result.get("diagnosis", "No diagnosis generated."))
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Severity</div>', unsafe_allow_html=True)
            st.write(result.get("severity", "Unknown"))
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Root Cause Analysis</div>', unsafe_allow_html=True)
            _render_list(result.get("possible_causes", []), "No specific causes found.")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Repair Recommendations</div>', unsafe_allow_html=True)
            _render_list(result.get("repair_steps", []), "No repair recommendations available.")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown(
                '<div class="section-title">Maintenance Recommendations</div>',
                unsafe_allow_html=True,
            )
            _render_list(
                result.get("maintenance_recommendations", []),
                "No maintenance recommendations available.",
            )
            st.markdown("</div>", unsafe_allow_html=True)

            confidence = float(result.get("confidence_score", 0.0))
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Confidence Score</div>', unsafe_allow_html=True)
            st.progress(max(0.0, min(confidence, 1.0)))
            st.write(f"{confidence:.2f}")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Sources</div>', unsafe_allow_html=True)
            sources = result.get("sources", [])
            if sources:
                for source in sources:
                    st.markdown(_format_source(source))
            else:
                st.write("No sources available.")
            st.markdown("</div>", unsafe_allow_html=True)

        except requests.HTTPError as exc:
            st.error(f"Backend returned an error: {exc}")
        except Exception as exc:
            st.error(f"Failed to run diagnosis: {exc}")
