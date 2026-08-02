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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Poppins:wght@600;700;800&display=swap');
    
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f4c75 100%);
        min-height: 100vh;
        color: #e2e8f0;
    }

    /* ============= HEADER HERO CARD ============= */
    .hero-card {
        background: linear-gradient(135deg, #0369a1 0%, #0284c7 50%, #06b6d4 100%);
        padding: 2.5rem 2rem;
        border-radius: 24px;
        color: white;
        box-shadow: 0 25px 50px rgba(3, 105, 161, 0.3), 0 0 1px rgba(255, 255, 255, 0.1);
        margin-bottom: 2.5rem;
        border: 1px solid rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(10px);
        animation: slideDown 0.7s cubic-bezier(0.34, 1.56, 0.64, 1);
        position: relative;
        overflow: hidden;
    }

    .hero-card::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        border-radius: 50%;
        pointer-events: none;
    }

    .hero-card h2 {
        font-size: 2.2rem;
        font-weight: 800;
        font-family: 'Poppins', sans-serif;
        letter-spacing: -1px;
        margin-bottom: 0.8rem !important;
        position: relative;
        z-index: 1;
    }

    .hero-card p {
        font-size: 1rem;
        opacity: 0.95;
        line-height: 1.7;
        font-weight: 400;
        position: relative;
        z-index: 1;
    }

    /* ============= SIDEBAR STYLING ============= */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
        border-right: 1px solid rgba(148, 163, 184, 0.1);
    }

    [data-testid="stSidebar"] [data-testid="stHeader"] {
        font-weight: 700;
        font-family: 'Poppins', sans-serif;
        color: #06b6d4;
        font-size: 1.1rem;
        margin-bottom: 1.8rem !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        padding: 1rem 0.5rem;
        border-bottom: 2px solid rgba(6, 182, 212, 0.3);
    }

    /* ============= INPUT FIELDS ============= */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
        border: 2px solid #334155 !important;
        border-radius: 14px !important;
        padding: 0.85rem 1rem !important;
        font-size: 0.95rem !important;
        transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
        font-weight: 500 !important;
        color: #e2e8f0 !important;
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
        border-color: #06b6d4 !important;
        box-shadow: 0 0 0 4px rgba(6, 182, 212, 0.2), 0 0 20px rgba(6, 182, 212, 0.15) !important;
        background: linear-gradient(135deg, #0f172a 0%, #001f3f 100%) !important;
    }

    /* ============= LABELS ============= */
    .stTextInput > label,
    .stNumberInput > label,
    .stTextArea > label,
    .stSelectbox > label {
        font-weight: 700 !important;
        font-family: 'Poppins', sans-serif;
        color: #06b6d4 !important;
        font-size: 0.9rem !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.7rem !important;
    }

    /* ============= BUTTONS ============= */
    .stButton > button {
        background: linear-gradient(135deg, #0369a1 0%, #0284c7 50%, #06b6d4 100%) !important;
        color: white !important;
        font-weight: 700 !important;
        font-family: 'Poppins', sans-serif;
        font-size: 1.05rem !important;
        padding: 1rem 2.5rem !important;
        border: none !important;
        border-radius: 14px !important;
        cursor: pointer !important;
        transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        box-shadow: 0 10px 25px rgba(3, 105, 161, 0.3) !important;
        position: relative;
        overflow: hidden;
    }

    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: rgba(255, 255, 255, 0.2);
        transition: left 0.5s ease;
    }

    .stButton > button:hover {
        transform: translateY(-4px) !important;
        box-shadow: 0 15px 35px rgba(3, 105, 161, 0.4) !important;
    }

    .stButton > button:hover::before {
        left: 100%;
    }

    .stButton > button:active {
        transform: translateY(-1px) !important;
    }

    /* ============= TYPOGRAPHY ============= */
    .stSubheader {
        color: #06b6d4 !important;
        font-weight: 800 !important;
        font-family: 'Poppins', sans-serif;
        font-size: 1.5rem !important;
        margin-top: 2.5rem !important;
        margin-bottom: 1.8rem !important;
        padding-bottom: 1rem;
        border-bottom: 3px solid #0369a1;
        display: flex;
        align-items: center;
        gap: 0.8rem;
    }

    /* ============= RESULT CARDS ============= */
    .result-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid rgba(6, 182, 212, 0.2);
        border-left: 5px solid #06b6d4;
        border-radius: 18px;
        padding: 1.8rem;
        box-shadow: 0 10px 30px rgba(6, 182, 212, 0.1);
        margin-bottom: 1.5rem;
        transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
        animation: fadeInUp 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
    }

    .result-card:hover {
        box-shadow: 0 15px 40px rgba(6, 182, 212, 0.2);
        transform: translateY(-4px);
        border-left-color: #06b6d4;
        border-color: rgba(6, 182, 212, 0.3);
    }

    /* ============= SECTION TITLES ============= */
    .section-title {
        font-weight: 800;
        font-family: 'Poppins', sans-serif;
        color: #06b6d4;
        font-size: 1.15rem;
        margin-bottom: 1.2rem;
        display: flex;
        align-items: center;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        position: relative;
        padding-left: 1rem;
    }

    .section-title::before {
        content: '';
        position: absolute;
        left: 0;
        width: 4px;
        height: 24px;
        background: linear-gradient(180deg, #06b6d4 0%, #0369a1 100%);
        border-radius: 2px;
    }

    /* ============= SEVERITY BADGES ============= */
    .severity-critical {
        color: #fecaca;
        font-weight: 700;
        font-family: 'Poppins', sans-serif;
        background: linear-gradient(135deg, #7f1d1d 0%, #5f0f0f 100%);
        padding: 0.8rem 1.2rem;
        border-radius: 10px;
        display: inline-block;
        border: 1px solid rgba(252, 165, 165, 0.3);
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);
    }

    .severity-high {
        color: #fed7aa;
        font-weight: 700;
        font-family: 'Poppins', sans-serif;
        background: linear-gradient(135deg, #7c2d12 0%, #5a1f0f 100%);
        padding: 0.8rem 1.2rem;
        border-radius: 10px;
        display: inline-block;
        border: 1px solid rgba(253, 186, 116, 0.3);
        box-shadow: 0 4px 12px rgba(249, 115, 22, 0.2);
    }

    .severity-medium {
        color: #fef08a;
        font-weight: 700;
        font-family: 'Poppins', sans-serif;
        background: linear-gradient(135deg, #713f12 0%, #5a3400 100%);
        padding: 0.8rem 1.2rem;
        border-radius: 10px;
        display: inline-block;
        border: 1px solid rgba(253, 224, 71, 0.3);
        box-shadow: 0 4px 12px rgba(217, 119, 6, 0.2);
    }

    .severity-low {
        color: #bbf7d0;
        font-weight: 700;
        font-family: 'Poppins', sans-serif;
        background: linear-gradient(135deg, #15803d 0%, #166534 100%);
        padding: 0.8rem 1.2rem;
        border-radius: 10px;
        display: inline-block;
        border: 1px solid rgba(167, 243, 208, 0.3);
        box-shadow: 0 4px 12px rgba(34, 197, 94, 0.2);
    }

    /* ============= LISTS ============= */
    .result-card ul {
        list-style: none;
        padding: 0;
    }

    .result-card ul li {
        margin-bottom: 1rem;
        line-height: 1.8;
        color: #cbd5e1;
        padding-left: 1.5rem;
        position: relative;
        transition: all 0.3s ease;
    }

    .result-card ul li:hover {
        color: #06b6d4;
        padding-left: 2rem;
    }

    .result-card ul li::before {
        content: '→';
        color: #06b6d4;
        font-weight: 800;
        margin-right: 0.8rem;
        position: absolute;
        left: 0;
    }

    /* ============= PROGRESS BAR ============= */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #0369a1 0%, #06b6d4 100%) !important;
        border-radius: 12px !important;
        box-shadow: 0 0 10px rgba(6, 182, 212, 0.3);
    }

    /* ============= MESSAGES ============= */
    .stSuccess {
        background: linear-gradient(135deg, #15803d 0%, #166534 100%) !important;
        border-left: 5px solid #22c55e !important;
        border-radius: 14px !important;
        color: #bbf7d0 !important;
        padding: 1rem !important;
    }

    .stError {
        background: linear-gradient(135deg, #7f1d1d 0%, #5f0f0f 100%) !important;
        border-left: 5px solid #ef4444 !important;
        border-radius: 14px !important;
        color: #fecaca !important;
        padding: 1rem !important;
    }

    .stInfo {
        background: linear-gradient(135deg, #0c4a6e 0%, #0369a1 100%) !important;
        border-left: 5px solid #06b6d4 !important;
        border-radius: 14px !important;
        color: #a5f3fc !important;
        padding: 1rem !important;
    }

    /* ============= METRICS ============= */
    .stMetric {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid rgba(6, 182, 212, 0.2);
        border-radius: 14px;
        padding: 1.2rem;
        box-shadow: 0 4px 12px rgba(6, 182, 212, 0.1);
    }

    .stMetric [data-testid="stMetricValue"] {
        color: #06b6d4 !important;
        font-family: 'Poppins', sans-serif;
        font-weight: 800 !important;
        font-size: 1.8rem !important;
    }

    .stMetric [data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-weight: 600 !important;
    }

    /* ============= ANIMATIONS ============= */
    @keyframes slideDown {
        from {
            opacity: 0;
            transform: translateY(-30px);
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

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    /* ============= SPINNER ============= */
    .stSpinner > div > div {
        border-top-color: #06b6d4 !important;
        border-right-color: rgba(6, 182, 212, 0.3) !important;
        border-bottom-color: rgba(6, 182, 212, 0.3) !important;
        border-left-color: rgba(6, 182, 212, 0.3) !important;
    }

    /* ============= RESPONSIVE DESIGN ============= */
    @media (max-width: 768px) {
        .hero-card {
            padding: 2rem 1.5rem;
        }

        .hero-card h2 {
            font-size: 1.8rem;
        }

        .hero-card p {
            font-size: 0.95rem;
        }

        .result-card {
            padding: 1.5rem 1rem;
        }

        .section-title {
            font-size: 1rem;
        }

        .stButton > button {
            padding: 0.9rem 2rem !important;
            font-size: 0.95rem !important;
        }

        .stSubheader {
            font-size: 1.3rem !important;
        }
    }

    /* ============= SCROLLBAR STYLING ============= */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #0f172a;
    }

    ::-webkit-scrollbar-thumb {
        background: #06b6d4;
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #0284c7;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero-card">
      <h2 style="margin:0;">⚡ Vehicle Diagnostics Assistant</h2>
      <p style="margin:0.4rem 0 0 0;">Advanced AI-powered diagnostic system. Enter vehicle details, OBD codes, and symptoms for comprehensive analysis and repair recommendations.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Enhanced sidebar with better organization
with st.sidebar:
    st.header("🚗 Vehicle Profile")
    
    # Create columns for better layout
    col1, col2 = st.columns(2)
    with col1:
        make = st.text_input("Make", placeholder="Toyota", label_visibility="collapsed")
    with col2:
        model = st.text_input("Model", placeholder="Corolla", label_visibility="collapsed")
    
    col3, col4 = st.columns(2)
    with col3:
        year_input = st.text_input("Year", placeholder="2020", label_visibility="collapsed")
    with col4:
        mileage_input = st.text_input("Mileage", placeholder="60000", label_visibility="collapsed")

st.subheader("🔍 Diagnostic Inputs")

# Main diagnostic input area with better organization
tab1, tab2 = st.tabs(["📋 OBD & Maintenance", "🔊 Symptoms"])

with tab1:
    col1, col2 = st.columns([1, 1], gap="medium")
    with col1:
        code = st.text_input(
            "Diagnostic Code (DTC)", 
            placeholder="e.g., P0171, P0300, B1234",
            help="Enter OBD-II diagnostic trouble code"
        )
    with col2:
        maintenance_query = st.text_input(
            "Maintenance Query", 
            placeholder="What should I service?",
            help="Ask about maintenance based on mileage or time"
        )

with tab2:
    symptoms = st.text_area(
        "Describe Vehicle Symptoms",
        placeholder="E.g., rough idle, check engine light, poor fuel economy, burning smell...",
        height=140,
        help="Be as detailed as possible for better diagnosis"
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


if st.button("🚀 Run Full Diagnostics", type="primary", use_container_width=True):
    with st.spinner("⏳ Running advanced diagnostic workflow..."):
        try:
            result = diagnose()
            st.success("✅ Diagnostic report generated successfully!")

            # Create tabs for results organization
            result_tab1, result_tab2, result_tab3, result_tab4 = st.tabs(
                ["📊 Summary", "🔧 Repairs", "🛠️ Maintenance", "📈 Analysis"]
            )

            with result_tab1:
                # Diagnostic Summary
                st.markdown('<div class="result-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">📋 Diagnosis Summary</div>', unsafe_allow_html=True)
                st.markdown(result.get("diagnosis", "No diagnosis generated."))
                
                # Severity with color coding
                severity = result.get("severity", "Unknown")
                st.markdown('<div class="section-title">🚨 Severity Assessment</div>', unsafe_allow_html=True)
                _render_severity_badge(severity)
                st.markdown("</div>", unsafe_allow_html=True)

            with result_tab2:
                # Root Cause Analysis
                st.markdown('<div class="result-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">🔍 Root Cause Analysis</div>', unsafe_allow_html=True)
                _render_list(result.get("possible_causes", []), "No specific causes identified.")
                st.markdown("</div>", unsafe_allow_html=True)

                # Repair Recommendations
                st.markdown('<div class="result-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">🔧 Repair Steps</div>', unsafe_allow_html=True)
                _render_list(result.get("repair_steps", []), "No repair recommendations available.")
                st.markdown("</div>", unsafe_allow_html=True)

            with result_tab3:
                # Maintenance Recommendations
                st.markdown('<div class="result-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">🛠️ Recommended Maintenance</div>', unsafe_allow_html=True)
                _render_list(
                    result.get("maintenance_recommendations", []),
                    "No maintenance recommendations available.",
                )
                st.markdown("</div>", unsafe_allow_html=True)

            with result_tab4:
                # Confidence Score with metrics
                confidence = float(result.get("confidence_score", 0.0))
                st.markdown('<div class="result-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">📊 Diagnosis Confidence</div>', unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.progress(max(0.0, min(confidence, 1.0)))
                with col2:
                    st.metric(label="Confidence Score", value=f"{confidence:.0%}")
                with col3:
                    confidence_level = "High" if confidence >= 0.7 else "Medium" if confidence >= 0.5 else "Low"
                    st.metric(label="Reliability", value=confidence_level)
                
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
