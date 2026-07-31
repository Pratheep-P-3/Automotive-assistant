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
    @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css');

    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    html, body, [class*="css"]  {
        font-family: 'Space Grotesk', sans-serif;
    }

    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        min-height: 100vh;
    }

    /* Hero Card */
    .hero-card {
        background: linear-gradient(135deg, #1a4d7a 0%, #2a7fab 40%, #1e9b9e 100%);
        padding: 2rem 1.8rem;
        border-radius: 20px;
        color: white;
        box-shadow: 0 20px 60px rgba(26, 77, 122, 0.3);
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        animation: slideDown 0.6s ease-out;
    }

    .hero-card h2 {
        font-size: 1.8rem;
        font-weight: 700;
        letter-spacing: -0.5px;
        margin-bottom: 0.8rem !important;
    }

    .hero-card p {
        font-size: 0.95rem;
        opacity: 0.95;
        line-height: 1.6;
    }

    /* Sidebar Enhancement */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8fafb 0%, #e8ecf1 100%);
    }

    [data-testid="stSidebar"] [data-testid="stHeader"] {
        font-weight: 700;
        color: #1a4d7a;
        font-size: 1.1rem;
        margin-bottom: 1.5rem !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Input Fields Styling */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: white !important;
        border: 2px solid #e0e7f1 !important;
        border-radius: 12px !important;
        padding: 0.75rem 1rem !important;
        font-size: 0.95rem !important;
        transition: all 0.3s ease !important;
        font-weight: 500 !important;
    }

    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #2a7fab !important;
        box-shadow: 0 0 0 3px rgba(42, 127, 171, 0.1) !important;
        background: linear-gradient(135deg, #ffffff 0%, #f0f8fc 100%) !important;
    }

    /* Label Styling */
    .stTextInput > label,
    .stNumberInput > label,
    .stTextArea > label,
    .stSelectbox > label {
        font-weight: 600 !important;
        color: #1a4d7a !important;
        font-size: 0.95rem !important;
        text-transform: uppercase;
        letter-spacing: 0.3px;
        margin-bottom: 0.6rem !important;
    }

    /* Button Styling */
    .stButton > button {
        background: linear-gradient(135deg, #2a7fab 0%, #1e9b9e 100%) !important;
        color: white !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        padding: 0.85rem 2rem !important;
        border: none !important;
        border-radius: 12px !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        box-shadow: 0 8px 20px rgba(42, 127, 171, 0.25) !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 12px 30px rgba(42, 127, 171, 0.35) !important;
    }

    .stButton > button:active {
        transform: translateY(0) !important;
    }

    /* Subheader Styling */
    .stSubheader {
        color: #1a4d7a !important;
        font-weight: 700 !important;
        font-size: 1.3rem !important;
        margin-top: 2rem !important;
        margin-bottom: 1.5rem !important;
        padding-bottom: 0.8rem;
        border-bottom: 3px solid #2a7fab;
    }

    /* Result Cards */
    .result-card {
        background: white;
        border: 1px solid #e0e7f1;
        border-left: 5px solid #2a7fab;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 8px 24px rgba(26, 77, 122, 0.08);
        margin-bottom: 1.2rem;
        transition: all 0.3s ease;
        animation: fadeInUp 0.5s ease-out;
    }

    .result-card:hover {
        box-shadow: 0 12px 32px rgba(26, 77, 122, 0.12);
        transform: translateY(-2px);
        border-left-color: #1e9b9e;
    }

    /* Section Title */
    .section-title {
        font-weight: 700;
        color: #1a4d7a;
        font-size: 1.1rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .section-title::before {
        content: '';
        display: inline-block;
        width: 4px;
        height: 4px;
        background: #2a7fab;
        border-radius: 50%;
        margin-right: 0.8rem;
    }

    /* Severity Styling */
    .severity-critical {
        color: #d32f2f;
        font-weight: 700;
        background: #ffebee;
        padding: 0.6rem 1rem;
        border-radius: 8px;
        display: inline-block;
    }

    .severity-high {
        color: #f57c00;
        font-weight: 700;
        background: #fff3e0;
        padding: 0.6rem 1rem;
        border-radius: 8px;
        display: inline-block;
    }

    .severity-medium {
        color: #fbc02d;
        font-weight: 700;
        background: #fffde7;
        padding: 0.6rem 1rem;
        border-radius: 8px;
        display: inline-block;
    }

    .severity-low {
        color: #388e3c;
        font-weight: 700;
        background: #e8f5e9;
        padding: 0.6rem 1rem;
        border-radius: 8px;
        display: inline-block;
    }

    /* List Items */
    .result-card ul li {
        margin-bottom: 0.8rem;
        line-height: 1.8;
        color: #334455;
    }

    .result-card ul li:before {
        content: '▸ ';
        color: #2a7fab;
        font-weight: bold;
        margin-right: 0.5rem;
    }

    /* Progress Bar */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #2a7fab 0%, #1e9b9e 100%) !important;
        border-radius: 10px !important;
    }

    /* Success Message */
    .stSuccess {
        background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%) !important;
        border-left: 5px solid #388e3c !important;
        border-radius: 12px !important;
        color: #1b5e20 !important;
    }

    /* Error Message */
    .stError {
        background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%) !important;
        border-left: 5px solid #d32f2f !important;
        border-radius: 12px !important;
        color: #b71c1c !important;
    }

    /* Spinner */
    .stSpinner > div > div {
        border-top-color: #2a7fab !important;
    }

    /* Animations */
    @keyframes slideDown {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* Responsive Design */
    @media (max-width: 768px) {
        .hero-card {
            padding: 1.5rem;
        }

        .hero-card h2 {
            font-size: 1.3rem;
        }

        .result-card {
            padding: 1rem;
        }

        .section-title {
            font-size: 0.95rem;
        }
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
    year_input = st.text_input("Vehicle Year", placeholder="2020")
    mileage_input = st.text_input("Mileage", placeholder="60000")

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


def _get_severity_color(severity: str) -> str:
    """Return CSS class for severity level."""
    severity_lower = severity.lower() if severity else "unknown"
    if "critical" in severity_lower or "urgent" in severity_lower:
        return "severity-critical"
    elif "high" in severity_lower:
        return "severity-high"
    elif "medium" in severity_lower:
        return "severity-medium"
    elif "low" in severity_lower:
        return "severity-low"
    return "severity-medium"


def _render_severity_badge(severity: str) -> None:
    """Render a color-coded severity badge."""
    css_class = _get_severity_color(severity)
    st.markdown(
        f'<div class="{css_class}">⚠️ {severity.upper()}</div>',
        unsafe_allow_html=True
    )


def _render_list(items: List[str], empty_text: str) -> None:
    """Render a formatted list with better styling."""
    if not items:
        st.info(empty_text)
        return
    st.markdown("<ul>", unsafe_allow_html=True)
    for item in items:
        st.markdown(f"<li>{item}</li>", unsafe_allow_html=True)
    st.markdown("</ul>", unsafe_allow_html=True)


def diagnose() -> Dict[str, Any]:
    # Convert year and mileage from text input to int if provided
    try:
        year_val = int(year_input) if year_input.strip() else None
    except ValueError:
        year_val = None
    
    try:
        mileage_val = int(mileage_input) if mileage_input.strip() else None
    except ValueError:
        mileage_val = None
    
    payload = {
        "make": make or None,
        "model": model or None,
        "year": year_val,
        "mileage": mileage_val,
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
            st.success("✅ Diagnostic report generated successfully!")

            # Diagnostic Summary
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">📋 Diagnostic Summary</div>', unsafe_allow_html=True)
            st.markdown(result.get("diagnosis", "No diagnosis generated."))
            st.markdown("</div>", unsafe_allow_html=True)

            # Severity with color coding
            severity = result.get("severity", "Unknown")
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">🚨 Severity Level</div>', unsafe_allow_html=True)
            _render_severity_badge(severity)
            st.markdown("</div>", unsafe_allow_html=True)

            # Root Cause Analysis
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">🔍 Root Cause Analysis</div>', unsafe_allow_html=True)
            _render_list(result.get("possible_causes", []), "No specific causes found.")
            st.markdown("</div>", unsafe_allow_html=True)

            # Repair Recommendations
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">🔧 Repair Recommendations</div>', unsafe_allow_html=True)
            _render_list(result.get("repair_steps", []), "No repair recommendations available.")
            st.markdown("</div>", unsafe_allow_html=True)

            # Maintenance Recommendations
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">🛠️ Maintenance Recommendations</div>', unsafe_allow_html=True)
            _render_list(
                result.get("maintenance_recommendations", []),
                "No maintenance recommendations available.",
            )
            st.markdown("</div>", unsafe_allow_html=True)

            # Confidence Score
            confidence = float(result.get("confidence_score", 0.0))
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">📊 Confidence Score</div>', unsafe_allow_html=True)
            col1, col2 = st.columns([4, 1])
            with col1:
                st.progress(max(0.0, min(confidence, 1.0)))
            with col2:
                st.metric(label="Score", value=f"{confidence:.0%}")
            st.markdown("</div>", unsafe_allow_html=True)

            # Sources
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">📚 Knowledge Sources</div>', unsafe_allow_html=True)
            sources = result.get("sources", [])
            if sources:
                st.markdown("<ul>", unsafe_allow_html=True)
                for source in sources:
                    st.markdown(f"<li>{_format_source(source)}</li>", unsafe_allow_html=True)
                st.markdown("</ul>", unsafe_allow_html=True)
            else:
                st.info("No sources available.")
            st.markdown("</div>", unsafe_allow_html=True)

        except requests.HTTPError as exc:
            st.error(f"❌ Backend Error: {exc}")
        except Exception as exc:
            st.error(f"❌ Diagnosis Failed: {exc}")
