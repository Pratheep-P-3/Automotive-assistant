from __future__ import annotations

import os
from typing import Any, Dict, List

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Automotive Diagnostics Assistant",
    page_icon="⚙️",
    layout="wide",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    .stApp {
        background: #0f172a;
        min-height: 100vh;
        color: #e2e8f0;
    }

    [data-testid="stAppViewContainer"] > section:first-child {
        max-width: 900px;
        margin-left: auto;
        margin-right: auto;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
    }

    [data-testid="stMainBlockContainer"] {
        max-width: 900px;
        margin-left: auto;
        margin-right: auto;
    }

    .stApp > [data-testid="stAppViewContainer"] {
        width: 100% !important;
    }

    .stApp > [data-testid="stAppViewContainer"] > section {
        max-width: 900px !important;
        margin-left: auto !important;
        margin-right: auto !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }

    /* ============= HERO CARD ============= */
    .hero-card {
        background: linear-gradient(135deg, #1e3a8a 0%, #0369a1 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        margin-bottom: 2rem;
        margin-left: -1.5rem;
        margin-right: -1.5rem;
        border: 1px solid #1e40af30;
        width: calc(100% + 3rem);
        animation: slideDown 0.6s ease-out;
    }

    .hero-card h2 {
        font-size: 1.8rem;
        font-weight: 700;
        letter-spacing: -0.5px;
        margin: 0 !important;
    }

    [data-testid="stSidebar"] {
        background: #1a2332;
        border-right: 1px solid #2d3e52;
    }

    [data-testid="stSidebar"] [data-testid="stHeader"] {
        font-weight: 700;
        color: #06b6d4;
        font-size: 0.9rem;
        margin-bottom: 1.5rem !important;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        padding: 0.8rem 0;
        border-bottom: 1px solid #2d3e52;
    }

    /* ============= INPUT FIELDS ============= */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        background: #1a2332 !important;
        border: 1px solid #2d3e52 !important;
        border-radius: 8px !important;
        padding: 0.75rem 1rem !important;
        font-size: 0.95rem !important;
        color: #e2e8f0 !important;
        transition: all 0.2s ease !important;
    }

    .stTextInput > div > div > input::placeholder,
    .stNumberInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: #64748b !important;
    }

    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus {
        border: 1px solid #06b6d4 !important;
        box-shadow: 0 0 0 2px #0369a130 !important;
        background: #0f172a !important;
        outline: none !important;
    }

    .stTextInput > label,
    .stNumberInput > label,
    .stTextArea > label,
    .stSelectbox > label {
        font-weight: 600 !important;
        color: #cbd5e1 !important;
        font-size: 0.85rem !important;
        text-transform: uppercase;
        letter-spacing: 0.3px;
        margin-bottom: 0.5rem !important;
    }

    /* ============= BUTTONS ============= */
    .stButton > button {
        background: linear-gradient(135deg, #1e3a8a 0%, #0369a1 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        padding: 0.8rem 2rem !important;
        border: 1px solid #0369a180 !important;
        border-radius: 8px !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        box-shadow: 0 4px 12px rgba(3, 105, 161, 0.2) !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(3, 105, 161, 0.3) !important;
    }

    .stButton > button:active {
        transform: translateY(0) !important;
    }

    /* ============= TYPOGRAPHY ============= */
    .stSubheader {
        color: #06b6d4 !important;
        font-weight: 700 !important;
        font-size: 1.2rem !important;
        margin-top: 1.5rem !important;
        margin-bottom: 1rem !important;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #2d3e52;
    }

    /* ============= RESULT CARDS ============= */
    .result-card {
        background: #1a2332;
        border: 1px solid #2d3e52;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        margin-bottom: 1.2rem;
        transition: all 0.3s ease;
    }

    .result-card:hover {
        border-color: #06b6d4;
        box-shadow: 0 6px 16px rgba(6, 182, 212, 0.15);
    }

    /* ============= SECTION TITLES ============= */
    .section-title {
        font-weight: 700;
        color: #06b6d4;
        font-size: 1rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* ============= SEVERITY BADGES ============= */
    .severity-critical {
        color: #fca5a5;
        background: #7f1d1d;
        padding: 0.6rem 1rem;
        border-radius: 6px;
        display: inline-block;
        border: 1px solid #ef444480;
        font-weight: 600;
        font-size: 0.9rem;
    }

    .severity-high {
        color: #fdba74;
        background: #7c2d12;
        padding: 0.6rem 1rem;
        border-radius: 6px;
        display: inline-block;
        border: 1px solid #f9732280;
        font-weight: 600;
        font-size: 0.9rem;
    }

    .severity-medium {
        color: #fcd34d;
        background: #78350f;
        padding: 0.6rem 1rem;
        border-radius: 6px;
        display: inline-block;
        border: 1px solid #f59e0b80;
        font-weight: 600;
        font-size: 0.9rem;
    }

    .severity-low {
        color: #86efac;
        background: #166534;
        padding: 0.6rem 1rem;
        border-radius: 6px;
        display: inline-block;
        border: 1px solid #22c55e80;
        font-weight: 600;
        font-size: 0.9rem;
    }

    /* ============= LISTS ============= */
    .result-card ul {
        list-style: none;
        padding: 0;
    }

    .result-card ul li {
        margin-bottom: 0.8rem;
        line-height: 1.6;
        color: #cbd5e1;
        padding-left: 1.2rem;
        position: relative;
    }

    .result-card ul li::before {
        content: '→';
        color: #06b6d4;
        font-weight: 600;
        margin-right: 0.6rem;
        position: absolute;
        left: 0;
    }

    /* ============= PROGRESS BAR ============= */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #06b6d4 0%, #0369a1 100%) !important;
        border-radius: 8px !important;
    }

    /* ============= MESSAGES ============= */
    .stSuccess {
        background: #0f392f !important;
        border-left: 3px solid #10b981 !important;
        border-radius: 8px !important;
        color: #86efac !important;
        padding: 1rem !important;
    }

    .stError {
        background: #3f0f0f !important;
        border-left: 3px solid #ef4444 !important;
        border-radius: 8px !important;
        color: #fca5a5 !important;
        padding: 1rem !important;
    }

    .stInfo {
        background: #082f49 !important;
        border-left: 3px solid #06b6d4 !important;
        border-radius: 8px !important;
        color: #cffafe !important;
        padding: 1rem !important;
    }

    /* ============= METRICS ============= */
    .stMetric {
        background: #1a2332;
        border: 1px solid #2d3e52;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }

    .stMetric [data-testid="stMetricValue"] {
        color: #06b6d4 !important;
        font-weight: 700 !important;
        font-size: 1.6rem !important;
    }

    .stMetric [data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
    }

    /* ============= ANIMATIONS ============= */
    @keyframes slideDown {
        from {
            opacity: 0;
            transform: translateY(-15px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .stSpinner > div > div {
        border-top-color: #06b6d4 !important;
        border-right-color: #06b6d430 !important;
        border-bottom-color: #06b6d430 !important;
        border-left-color: #06b6d430 !important;
    }

    ::-webkit-scrollbar {
        width: 6px;
    }

    ::-webkit-scrollbar-track {
        background: #1a2332;
    }

    ::-webkit-scrollbar-thumb {
        background: #3b82f6;
        border-radius: 3px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #06b6d4;
    }

    @media (max-width: 768px) {
        .hero-card {
            padding: 1rem;
            width: calc(100% + 2.4rem);
            margin-left: -1.2rem;
            margin-right: -1.2rem;
        }

        .hero-card h2 {
            font-size: 1.4rem;
        }

        .stButton > button {
            padding: 0.7rem 1.5rem !important;
            font-size: 0.9rem !important;
        }

        .stSubheader {
            font-size: 1.1rem !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero-card">
      <h2 style="margin:0;">Vehicle Diagnostics Assistant</h2>
      <p style="margin:0.4rem 0 0 0;">Advanced AI-powered diagnostic system. Enter vehicle details, OBD codes, and symptoms for comprehensive analysis and repair recommendations.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Sidebar - Vehicle Profile (OPTIONAL, for brand-specific prioritization)
with st.sidebar:
    st.header("Vehicle Profile")
    st.caption("Optional - Prioritizes brand-specific diagnostic information")
    make = st.text_input(
        "Make",
        placeholder="e.g., Toyota",
        help="Vehicle manufacturer - helps prioritize brand-specific documents"
    )
    model = st.text_input(
        "Model",
        placeholder="e.g., Corolla",
        help="Vehicle model (optional)"
    )
    year_input = st.text_input(
        "Year",
        placeholder="e.g., 2020",
        help="Vehicle year (optional)"
    )
    mileage_input = st.text_input(
        "Mileage",
        placeholder="e.g., 60000",
        help="Current vehicle mileage (optional)"
    )

st.subheader("Diagnostic Inputs")
st.caption("Enter at least one: OBD Code, Symptoms, or Maintenance Query")

# Main diagnostic input area with better organization
col1, col2 = st.columns([1, 1], gap="medium")
with col1:
    code = st.text_input(
        "Diagnostic Code (DTC)", 
        placeholder="e.g., P0171, P0300, B1234",
        help="Enter OBD-II diagnostic trouble code (optional)"
    )
with col2:
    maintenance_query = st.text_input(
        "Maintenance Query", 
        placeholder="e.g., What should I service?",
        help="Ask about maintenance based on mileage or time (optional)"
    )

symptoms = st.text_area(
    "Describe Vehicle Symptoms",
    placeholder="E.g., rough idle, check engine light, poor fuel economy, burning smell...",
    height=140,
    help="Be as detailed as possible for better diagnosis (optional)"
)

def _format_source(source: Dict[str, Any]) -> str:
    # Handle both old and new source formats
    filename = source.get("source_filename") or source.get("source", "Unknown Source")
    category = source.get("category", "")
    chunk_type = source.get("chunk_type", "")
    vector_score = source.get("vector_score", 0)
    rerank_score = source.get("rerank_score", 0)
    
    # Build the display string
    display = f"📄 {filename}"
    if category:
        display += f" | Category: {category}"
    if chunk_type:
        display += f" | Type: {chunk_type}"
    if vector_score > 0:
        display += f" | Similarity: {vector_score:.2%}"
    if rerank_score > 0:
        display += f" | Relevance: {rerank_score:.2f}"
    
    return display


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
        f'<div class="{css_class}">{severity.upper()}</div>',
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
    """Send diagnostic query to backend API with vehicle prioritization."""
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


if st.button("Run Full Diagnostics", type="primary", use_container_width=True):
    with st.spinner("Running advanced diagnostic workflow..."):
        try:
            result = diagnose()
            
            # Store result in session state and navigate to diagnosis page
            st.session_state.diagnostic_result = result
            st.success("Diagnostic report generated! Navigating to results...")
            st.switch_page("pages/1_🔍_Diagnosis.py")
            
        except requests.HTTPError as exc:
            st.error(f"Backend Error: {exc}")
        except Exception as exc:
            st.error(f"Diagnosis Failed: {exc}")
