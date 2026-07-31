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
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    * {
        font-family: 'Inter', sans-serif;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Main App Background */
    .stApp {
        background: #f8f9fa;
    }

    .main {
        padding: 2rem 1.5rem;
    }

    /* Header Section */
    .header-container {
        background: white;
        border-bottom: 1px solid #e5e7eb;
        padding: 2rem 0;
        margin: -2rem -1.5rem 2rem -1.5rem;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
    }

    .header-title {
        margin: 0;
        padding: 0;
        font-size: 2rem;
        font-weight: 700;
        color: #111827;
        letter-spacing: -0.5px;
    }

    .header-subtitle {
        margin: 0.5rem 0 0 0;
        padding: 0;
        font-size: 0.95rem;
        color: #6b7280;
        font-weight: 400;
    }

    /* Form Container */
    .form-container {
        background: white;
        border-radius: 12px;
        padding: 2rem;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        margin-bottom: 2rem;
    }

    .form-section-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #374151;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 1.2rem;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid #f3f4f6;
    }

    /* Input Fields */
    .stTextInput, .stNumberInput, .stTextArea {
        margin-bottom: 1rem;
    }

    .stTextInput input, .stNumberInput input, .stTextArea textarea {
        background-color: #ffffff !important;
        border: 1.5px solid #d1d5db !important;
        border-radius: 8px !important;
        padding: 0.75rem 1rem !important;
        font-size: 0.95rem !important;
        color: #111827 !important;
        transition: all 0.2s ease !important;
    }

    .stTextInput input::placeholder, .stNumberInput input::placeholder, .stTextArea textarea::placeholder {
        color: #9ca3af !important;
        font-weight: 400 !important;
    }

    .stTextInput input:hover, .stNumberInput input:hover, .stTextArea textarea:hover {
        border-color: #9ca3af !important;
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.05) !important;
    }

    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
        border-color: #4f46e5 !important;
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1) !important;
        outline: none !important;
    }

    .input-label {
        font-size: 0.9rem;
        font-weight: 600;
        color: #111827;
        margin-bottom: 0.5rem;
        display: block;
    }

    .input-helper {
        font-size: 0.8rem;
        color: #9ca3af;
        margin-top: 0.25rem;
    }

    /* Button Styling */
    .stButton > button {
        width: 100%;
        padding: 0.75rem 1.5rem !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        border: none !important;
        background: linear-gradient(135deg, #4f46e5 0%, #4f46e5 100%) !important;
        color: white !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 8px rgba(79, 70, 229, 0.3) !important;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #4338ca 0%, #4338ca 100%) !important;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.4) !important;
        transform: translateY(-1px) !important;
    }

    .stButton > button:active {
        transform: translateY(0) !important;
    }

    /* Result Cards */
    .result-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        margin-bottom: 1.25rem;
        animation: slideUp 0.3s ease;
    }

    @keyframes slideUp {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .result-card-title {
        font-size: 0.85rem;
        font-weight: 700;
        color: #4f46e5;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
    }

    .result-card-content {
        font-size: 0.95rem;
        color: #374151;
        line-height: 1.6;
    }

    .result-card-section {
        margin-bottom: 1rem;
    }

    .result-card-section:last-child {
        margin-bottom: 0;
    }

    .result-list {
        list-style: none;
        padding: 0;
        margin: 0;
    }

    .result-list li {
        padding: 0.5rem 0 0.5rem 1.5rem;
        position: relative;
        color: #374151;
        line-height: 1.6;
    }

    .result-list li:before {
        content: "→";
        position: absolute;
        left: 0;
        color: #4f46e5;
        font-weight: 600;
    }

    /* Confidence Score */
    .confidence-container {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        border-radius: 12px;
        padding: 1.5rem;
        color: white;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
    }

    .confidence-label {
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        opacity: 0.9;
        margin-bottom: 0.75rem;
    }

    .confidence-score {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
    }

    .confidence-sublabel {
        font-size: 0.9rem;
        opacity: 0.85;
        margin-top: 0.5rem;
    }

    /* Progress Bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%) !important;
        border-radius: 4px !important;
    }

    /* Success Message */
    .stSuccess {
        background-color: #d1fae5 !important;
        color: #065f46 !important;
        border: 1px solid #6ee7b7 !important;
        border-radius: 8px !important;
    }

    .stError {
        background-color: #fee2e2 !important;
        color: #7f1d1d !important;
        border: 1px solid #fca5a5 !important;
        border-radius: 8px !important;
    }

    /* Sidebar */
    .sidebar .sidebar-content {
        padding: 1.5rem;
    }

    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1rem !important;
    }

    /* Two Column Layout */
    .two-column-input {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1.5rem;
        margin-bottom: 1rem;
    }

    @media (max-width: 900px) {
        .two-column-input {
            grid-template-columns: 1fr;
            gap: 1rem;
        }
    }

    /* Empty State */
    .empty-state {
        text-align: center;
        padding: 2rem;
        color: #9ca3af;
        font-size: 0.95rem;
    }

    /* Divider */
    .divider {
        height: 1px;
        background: #e5e7eb;
        margin: 1.5rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="header-container">
        <h1 class="header-title">Vehicle Diagnostics Assistant</h1>
        <p class="header-subtitle">Comprehensive diagnostic reports powered by advanced AI analysis</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Main Input Section
st.markdown('<div class="form-container">', unsafe_allow_html=True)

st.markdown('<div class="form-section-title">Vehicle Information</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1.5, 1.5, 1])
with col1:
    st.markdown('<label class="input-label">Vehicle Make</label>', unsafe_allow_html=True)
    make = st.text_input("", placeholder="e.g., Toyota, Honda, Ford", key="make", label_visibility="collapsed")
with col2:
    st.markdown('<label class="input-label">Vehicle Model</label>', unsafe_allow_html=True)
    model = st.text_input("", placeholder="e.g., Corolla, Civic, F-150", key="model", label_visibility="collapsed")
with col3:
    st.markdown('<label class="input-label">Year</label>', unsafe_allow_html=True)
    year = st.number_input("", min_value=1950, max_value=2100, value=2020, key="year", label_visibility="collapsed")

st.markdown('<div class="input-helper">Optional: Enter mileage for maintenance recommendations</div>', unsafe_allow_html=True)
mileage_input = st.text_input("", placeholder="e.g., 60000 or leave blank", key="mileage", label_visibility="collapsed")

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

st.markdown('<div class="form-section-title">Diagnostic Information</div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])
with col1:
    st.markdown('<label class="input-label">Diagnostic Code (DTC)</label>', unsafe_allow_html=True)
    code = st.text_input("", placeholder="e.g., P0171, P0300, C0010", key="code", label_visibility="collapsed")
    st.markdown('<div class="input-helper">Optional: Enter vehicle error/fault code</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<label class="input-label">Maintenance Query</label>', unsafe_allow_html=True)
    maintenance_query = st.text_input("", placeholder="e.g., What service is due at 60k miles?", key="maintenance", label_visibility="collapsed")
    st.markdown('<div class="input-helper">Optional: Ask about maintenance schedules</div>', unsafe_allow_html=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

st.markdown('<label class="input-label">Vehicle Symptoms</label>', unsafe_allow_html=True)
symptoms = st.text_area(
    "",
    placeholder="Describe any symptoms (e.g., rough idle, poor fuel economy, check engine light)",
    height=100,
    key="symptoms",
    label_visibility="collapsed",
)
st.markdown('<div class="input-helper">Optional: Describe any symptoms you\'ve observed</div>', unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

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


# Diagnose Button
if st.button("🔍 Run Diagnostics", type="primary", use_container_width=True):
    with st.spinner("Analyzing vehicle data and generating report..."):
        try:
            result = diagnose()
            
            st.markdown('<div style="margin-top: 2rem;"></div>', unsafe_allow_html=True)

            # Diagnostic Summary
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown('<div class="result-card-title">📋 Diagnostic Summary</div>', unsafe_allow_html=True)
            st.markdown('<div class="result-card-content">' + result.get("diagnosis", "No diagnosis generated.") + '</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # Severity
            severity = result.get("severity", "Unknown")
            severity_color = "#ef4444" if severity.lower() == "high" else "#f59e0b" if severity.lower() == "medium" else "#10b981"
            st.markdown(f'''
            <div class="result-card">
                <div class="result-card-title">⚠️ Severity Level</div>
                <div style="font-size: 1.2rem; font-weight: 600; color: {severity_color};">{severity}</div>
            </div>
            ''', unsafe_allow_html=True)

            # Root Causes
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown('<div class="result-card-title">🔍 Root Cause Analysis</div>', unsafe_allow_html=True)
            causes = result.get("possible_causes", [])
            if causes:
                st.markdown('<ul class="result-list">', unsafe_allow_html=True)
                for cause in causes:
                    st.markdown(f'<li>{cause}</li>', unsafe_allow_html=True)
                st.markdown('</ul>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="empty-state">No specific causes identified</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # Repair Recommendations
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown('<div class="result-card-title">🔧 Repair Recommendations</div>', unsafe_allow_html=True)
            repair_steps = result.get("repair_steps", [])
            if repair_steps:
                st.markdown('<ul class="result-list">', unsafe_allow_html=True)
                for step in repair_steps:
                    st.markdown(f'<li>{step}</li>', unsafe_allow_html=True)
                st.markdown('</ul>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="empty-state">No repair recommendations available</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # Maintenance Recommendations
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown('<div class="result-card-title">🛠️ Maintenance Recommendations</div>', unsafe_allow_html=True)
            maintenance = result.get("maintenance_recommendations", [])
            if maintenance:
                st.markdown('<ul class="result-list">', unsafe_allow_html=True)
                for item in maintenance:
                    st.markdown(f'<li>{item}</li>', unsafe_allow_html=True)
                st.markdown('</ul>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="empty-state">No maintenance recommendations available</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # Confidence Score
            confidence = float(result.get("confidence_score", 0.0))
            confidence_pct = confidence * 100
            confidence_text = "Very High" if confidence >= 0.85 else "High" if confidence >= 0.70 else "Medium" if confidence >= 0.50 else "Low"
            
            st.markdown(f'''
            <div class="confidence-container">
                <div class="confidence-label">✨ Confidence Score</div>
                <div class="confidence-score">{confidence_pct:.0f}%</div>
                <div class="confidence-sublabel">{confidence_text} confidence in this diagnosis</div>
            </div>
            ''', unsafe_allow_html=True)

            # Sources
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown('<div class="result-card-title">📚 Information Sources</div>', unsafe_allow_html=True)
            sources = result.get("sources", [])
            if sources:
                st.markdown('<ul class="result-list">', unsafe_allow_html=True)
                for source in sources:
                    st.markdown(f'<li>{_format_source(source)}</li>', unsafe_allow_html=True)
                st.markdown('</ul>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="empty-state">No specific sources referenced</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        except requests.HTTPError as exc:
            st.error(f"❌ Backend Error: {exc}")
        except Exception as exc:
            st.error(f"❌ Analysis Failed: {exc}")
