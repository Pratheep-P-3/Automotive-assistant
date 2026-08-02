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
        background: linear-gradient(135deg, #f0f4ff 0%, #e8eef9 50%, #f5f7ff 100%);
        min-height: 100vh;
        color: #1f2937;
    }

    /* ============= HEADER HERO CARD ============= */
    .hero-card {
        background: linear-gradient(135deg, #5b7cff 0%, #6b8fff 50%, #4c63e8 100%);
        padding: 2.5rem 2rem;
        border-radius: 24px;
        color: white;
        box-shadow: 0 25px 50px rgba(91, 124, 255, 0.25), 0 0 1px rgba(255, 255, 255, 0.2);
        margin-bottom: 2.5rem;
        border: 1px solid rgba(255, 255, 255, 0.25);
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
        background: linear-gradient(180deg, #ffffff 0%, #f8faff 100%);
        border-right: 1px solid #e5e7eb;
    }

    [data-testid="stSidebar"] [data-testid="stHeader"] {
        font-weight: 700;
        font-family: 'Poppins', sans-serif;
        color: #5b7cff;
        font-size: 1.1rem;
        margin-bottom: 1.8rem !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        padding: 1rem 0.5rem;
        border-bottom: 2px solid rgba(91, 124, 255, 0.25);
    }

    /* ============= INPUT FIELDS ============= */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        background: white !important;
        border: 2px solid #e5e7eb !important;
        border-radius: 14px !important;
        padding: 0.85rem 1rem !important;
        font-size: 0.95rem !important;
        transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
        font-weight: 500 !important;
        color: #1f2937 !important;
        outline: none !important;
        box-shadow: none !important;
    }

    .stTextInput > div > div > input::placeholder,
    .stNumberInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: #9ca3af !important;
    }

    /* AGGRESSIVE FOCUS STATE OVERRIDES - BLUE ONLY */
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus,
    input[type="text"]:focus,
    input[type="number"]:focus,
    textarea:focus,
    select:focus {
        border: 2px solid #5b7cff !important;
        box-shadow: 0 0 0 3px rgba(91, 124, 255, 0.1), inset 0 0 0 1px #5b7cff !important;
        background: #fafbff !important;
        outline: none !important;
    }

    /* TARGET FOCUS-WITHIN ON PARENT CONTAINERS */
    .stTextInput:focus-within > div > div > input,
    .stNumberInput:focus-within > div > div > input,
    .stTextArea:focus-within > div > div > textarea,
    .stSelectbox:focus-within > div > div > select {
        border: 2px solid #5b7cff !important;
        box-shadow: 0 0 0 3px rgba(91, 124, 255, 0.1), inset 0 0 0 1px #5b7cff !important;
        background: #fafbff !important;
    }

    /* REMOVE STREAMLIT'S DEFAULT BLUE/RED LINES */
    .stTextInput > div:focus-within,
    .stNumberInput > div:focus-within,
    .stTextArea > div:focus-within,
    .stSelectbox > div:focus-within {
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }

    /* DISABLE ANY PSEUDO-ELEMENT STYLING */
    .stTextInput > div > div::after,
    .stNumberInput > div > div::after,
    .stTextArea > div > div::after,
    .stSelectbox > div > div::after {
        display: none !important;
        border: none !important;
    }

    /* ============= LABELS ============= */
    .stTextInput > label,
    .stNumberInput > label,
    .stTextArea > label,
    .stSelectbox > label {
        font-weight: 700 !important;
        font-family: 'Poppins', sans-serif;
        color: #5b7cff !important;
        font-size: 0.9rem !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.7rem !important;
    }

    /* ============= BUTTONS ============= */
    .stButton > button {
        background: linear-gradient(135deg, #5b7cff 0%, #6b8fff 50%, #4c63e8 100%) !important;
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
        box-shadow: 0 10px 25px rgba(91, 124, 255, 0.3) !important;
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
        box-shadow: 0 15px 35px rgba(91, 124, 255, 0.4) !important;
    }

    .stButton > button:hover::before {
        left: 100%;
    }

    .stButton > button:active {
        transform: translateY(-1px) !important;
    }

    /* ============= TYPOGRAPHY ============= */
    .stSubheader {
        color: #5b7cff !important;
        font-weight: 800 !important;
        font-family: 'Poppins', sans-serif;
        font-size: 1.5rem !important;
        margin-top: 2.5rem !important;
        margin-bottom: 1.8rem !important;
        padding-bottom: 1rem;
        border-bottom: 3px solid #5b7cff;
        display: flex;
        align-items: center;
        gap: 0.8rem;
    }

    /* ============= RESULT CARDS ============= */
    .result-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-left: 5px solid #5b7cff;
        border-radius: 18px;
        padding: 1.8rem;
        box-shadow: 0 4px 15px rgba(91, 124, 255, 0.08);
        margin-bottom: 1.5rem;
        transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
        animation: fadeInUp 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
    }

    .result-card:hover {
        box-shadow: 0 8px 25px rgba(91, 124, 255, 0.15);
        transform: translateY(-4px);
        border-left-color: #5b7cff;
        border-color: #d1d5db;
    }

    /* ============= SECTION TITLES ============= */
    .section-title {
        font-weight: 800;
        font-family: 'Poppins', sans-serif;
        color: #5b7cff;
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
        background: linear-gradient(180deg, #5b7cff 0%, #4c63e8 100%);
        border-radius: 2px;
    }

    /* ============= SEVERITY BADGES ============= */
    .severity-critical {
        color: #b91c1c;
        font-weight: 700;
        font-family: 'Poppins', sans-serif;
        background: #fee2e2;
        padding: 0.8rem 1.2rem;
        border-radius: 10px;
        display: inline-block;
        border: 1px solid #fecaca;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.1);
    }

    .severity-high {
        color: #c2410c;
        font-weight: 700;
        font-family: 'Poppins', sans-serif;
        background: #fed7aa;
        padding: 0.8rem 1.2rem;
        border-radius: 10px;
        display: inline-block;
        border: 1px solid #fdba74;
        box-shadow: 0 4px 12px rgba(249, 115, 22, 0.1);
    }

    .severity-medium {
        color: #a16207;
        font-weight: 700;
        font-family: 'Poppins', sans-serif;
        background: #fef3c7;
        padding: 0.8rem 1.2rem;
        border-radius: 10px;
        display: inline-block;
        border: 1px solid #fde68a;
        box-shadow: 0 4px 12px rgba(217, 119, 6, 0.1);
    }

    .severity-low {
        color: #15803d;
        font-weight: 700;
        font-family: 'Poppins', sans-serif;
        background: #dcfce7;
        padding: 0.8rem 1.2rem;
        border-radius: 10px;
        display: inline-block;
        border: 1px solid #bbf7d0;
        box-shadow: 0 4px 12px rgba(34, 197, 94, 0.1);
    }

    /* ============= LISTS ============= */
    .result-card ul {
        list-style: none;
        padding: 0;
    }

    .result-card ul li {
        margin-bottom: 1rem;
        line-height: 1.8;
        color: #374151;
        padding-left: 1.5rem;
        position: relative;
        transition: all 0.3s ease;
    }

    .result-card ul li:hover {
        color: #5b7cff;
        padding-left: 2rem;
    }

    .result-card ul li::before {
        content: '→';
        color: #5b7cff;
        font-weight: 800;
        margin-right: 0.8rem;
        position: absolute;
        left: 0;
    }

    /* ============= PROGRESS BAR ============= */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #5b7cff 0%, #6b8fff 100%) !important;
        border-radius: 12px !important;
        box-shadow: 0 0 10px rgba(91, 124, 255, 0.3);
    }

    /* ============= MESSAGES ============= */
    .stSuccess {
        background: #dcfce7 !important;
        border-left: 5px solid #22c55e !important;
        border-radius: 14px !important;
        color: #166534 !important;
        padding: 1rem !important;
    }

    .stError {
        background: #fee2e2 !important;
        border-left: 5px solid #ef4444 !important;
        border-radius: 14px !important;
        color: #991b1b !important;
        padding: 1rem !important;
    }

    .stInfo {
        background: #eff6ff !important;
        border-left: 5px solid #5b7cff !important;
        border-radius: 14px !important;
        color: #1e3a8a !important;
        padding: 1rem !important;
    }

    /* ============= METRICS ============= */
    .stMetric {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 1.2rem;
        box-shadow: 0 2px 8px rgba(91, 124, 255, 0.05);
    }

    .stMetric [data-testid="stMetricValue"] {
        color: #5b7cff !important;
        font-family: 'Poppins', sans-serif;
        font-weight: 800 !important;
        font-size: 1.8rem !important;
    }

    .stMetric [data-testid="stMetricLabel"] {
        color: #6b7280 !important;
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
        border-top-color: #5b7cff !important;
        border-right-color: rgba(91, 124, 255, 0.3) !important;
        border-bottom-color: rgba(91, 124, 255, 0.3) !important;
        border-left-color: rgba(91, 124, 255, 0.3) !important;
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
        background: #f3f4f6;
    }

    ::-webkit-scrollbar-thumb {
        background: #5b7cff;
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #4c63e8;
    }

    /* ============= TAB STYLING ============= */
    [data-testid="stTabs"] {
        margin-top: 1.5rem;
    }

    [data-testid="stTabs"] [data-testid="stTab"] {
        background: white !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 14px 14px 0 0 !important;
        color: #6b7280 !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }

    [data-testid="stTabs"] [data-testid="stTab"]:hover {
        background: #f9fafb !important;
        color: #5b7cff !important;
    }

    [data-testid="stTabs"] [aria-selected="true"] {
        color: #5b7cff !important;
        border-bottom: 3px solid #5b7cff !important;
        background: #f0f4ff !important;
    }

    /* ============= CONTAINER STYLING ============= */
    .stContainer {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 1.5rem;
        margin: 1rem 0;
    }

    /* ============= FOCUS/ACTIVE STATE FIXES ============= */
    .stTextInput > div > div > input:active,
    .stTextInput > div > div > input:focus-visible,
    .stNumberInput > div > div > input:active,
    .stNumberInput > div > div > input:focus-visible,
    .stTextArea > div > div > textarea:active,
    .stTextArea > div > div > textarea:focus-visible {
        outline: none !important;
        border-color: #5b7cff !important;
        box-shadow: 0 0 0 4px rgba(91, 124, 255, 0.15), 0 0 20px rgba(91, 124, 255, 0.2) !important;
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

# Enhanced sidebar with better organization
with st.sidebar:
    st.header("Vehicle Profile")
    
    # Stack inputs vertically for better use of space and clarity
    make = st.text_input("Make", placeholder="Toyota", help="Vehicle manufacturer")
    model = st.text_input("Model", placeholder="Corolla", help="Vehicle model name")
    year_input = st.text_input("Year", placeholder="2020", help="Vehicle year of manufacture")
    mileage_input = st.text_input("Mileage", placeholder="60000", help="Current vehicle mileage")

st.subheader("Diagnostic Inputs")

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
        placeholder="What should I service?",
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
            st.success("Diagnostic report generated successfully")
            
            st.markdown("---")

            # SECTION 1: Diagnostic Summary & Severity
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown('<div class="section-title">📋 Diagnosis Summary</div>', unsafe_allow_html=True)
                st.markdown(result.get("diagnosis", "No diagnosis generated."))
            
            with col2:
                severity = result.get("severity", "Unknown")
                st.markdown('<div class="section-title">🚨 Severity</div>', unsafe_allow_html=True)
                _render_severity_badge(severity)
            
            st.markdown("---")

            # SECTION 2: Root Cause Analysis
            st.markdown('<div class="section-title">Root Cause Analysis</div>', unsafe_allow_html=True)
            st.markdown("""
            The following factors have been identified as potential causes for the vehicle's condition:
            """)
            causes = result.get("possible_causes", [])
            if causes:
                for i, cause in enumerate(causes, 1):
                    st.markdown(f"**{i}. {cause}**")
            else:
                st.info("No specific causes identified.")
            
            st.markdown("---")

            # SECTION 3: Repair Recommendations (Enhanced)
            st.markdown('<div class="section-title">Detailed Repair Steps</div>', unsafe_allow_html=True)
            st.markdown("""
            Follow these comprehensive repair steps to resolve the identified issues:
            """)
            repair_steps = result.get("repair_steps", [])
            if repair_steps:
                for i, step in enumerate(repair_steps, 1):
                    with st.container():
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #eff6ff 0%, #f0f9ff 100%); 
                                    border-left: 4px solid #5b7cff; border-radius: 8px; 
                                    padding: 1.2rem; margin: 0.8rem 0; 
                                    border: 1px solid #dbeafe;">
                        <strong style="color: #5b7cff; font-size: 1.1rem;">Step {i}</strong>
                        <p style="color: #374151; margin-top: 0.5rem; line-height: 1.8;">{step}</p>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No repair recommendations available.")
            
            st.markdown("---")

            # SECTION 4: Maintenance Recommendations (Enhanced)
            st.markdown('<div class="section-title">Recommended Maintenance</div>', unsafe_allow_html=True)
            st.markdown("""
            Perform the following maintenance tasks to ensure optimal vehicle performance:
            """)
            maintenance = result.get("maintenance_recommendations", [])
            if maintenance:
                for i, item in enumerate(maintenance, 1):
                    with st.container():
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%); 
                                    border-left: 4px solid #22c55e; border-radius: 8px; 
                                    padding: 1.2rem; margin: 0.8rem 0; 
                                    border: 1px solid #dcfce7;">
                        <strong style="color: #22c55e; font-size: 1.1rem;">Maintenance Item {i}</strong>
                        <p style="color: #374151; margin-top: 0.5rem; line-height: 1.8;">{item}</p>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No maintenance recommendations available.")
            
            st.markdown("---")

            # SECTION 5: Confidence & Analysis
            st.markdown('<div class="section-title">Diagnosis Confidence & Analysis</div>', unsafe_allow_html=True)
            
            confidence = float(result.get("confidence_score", 0.0))
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="Confidence Score", value=f"{confidence:.0%}")
            with col2:
                confidence_level = "High" if confidence >= 0.7 else "Medium" if confidence >= 0.5 else "Low"
                st.metric(label="Reliability Level", value=confidence_level)
            with col3:
                st.metric(label="Data Quality", value="Verified" if confidence >= 0.6 else "Moderate")
            
            st.progress(max(0.0, min(confidence, 1.0)))
            
            st.markdown("---")

            # SECTION 6: Knowledge Sources
            st.markdown('<div class="section-title">Knowledge Sources</div>', unsafe_allow_html=True)
            st.markdown("This diagnosis was powered by the following sources from our knowledge base:")
            
            sources = result.get("sources", [])
            if sources:
                for i, source in enumerate(sources, 1):
                    formatted_source = _format_source(source)
                    st.markdown(f"**Source {i}:** {formatted_source}")
            else:
                st.info("No sources available for this diagnosis.")

        except requests.HTTPError as exc:
            st.error(f"Backend Error: {exc}")
        except Exception as exc:
            st.error(f"Diagnosis Failed: {exc}")
