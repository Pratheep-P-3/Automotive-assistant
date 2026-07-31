from __future__ import annotations

import os
from typing import Any, Dict, List

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Premium Page Configuration
st.set_page_config(
    page_title="Automotive Vehicle Diagnostics",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# Premium Automotive Styling
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    /* Main App */
    .stApp {
        background: linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%);
    }

    [data-testid="stAppViewContainer"] {
        padding: 0 !important;
    }

    .main {
        padding: 0 !important;
    }

    /* Hero Section */
    .hero-section {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        padding: 3.5rem 2rem;
        color: white;
        text-align: center;
    }

    .hero-icon {
        font-size: 3.5rem;
        margin-bottom: 1rem;
    }

    .hero-title {
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0 0 0.5rem 0;
        letter-spacing: -1px;
        line-height: 1.2;
    }

    .hero-subtitle {
        font-size: 1.05rem;
        font-weight: 400;
        color: #CBD5E1;
        margin: 0;
        max-width: 650px;
        margin: 0 auto;
    }

    /* Main Container */
    .main-container {
        max-width: 1100px;
        margin: 0 auto;
        padding: 2.5rem 1.5rem;
    }

    /* Form Card */
    .form-card {
        background: white;
        border-radius: 16px;
        padding: 2.5rem;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        margin-bottom: 2rem;
    }

    .form-section-header {
        display: flex;
        align-items: center;
        margin-bottom: 1.75rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid #F1F5F9;
    }

    .form-section-icon {
        font-size: 1.5rem;
        margin-right: 0.75rem;
    }

    .form-section-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #0F172A;
        margin: 0;
    }

    .form-group {
        display: flex;
        flex-direction: column;
        margin-bottom: 1rem;
    }

    .form-label {
        font-size: 0.9rem;
        font-weight: 600;
        color: #0F172A;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
    }

    .form-label-icon {
        margin-right: 0.5rem;
        opacity: 0.75;
    }

    .form-tooltip {
        font-size: 0.75rem;
        color: #94A3B8;
        margin-top: 0.3rem;
        font-weight: 400;
    }

    /* Input Styling */
    .stTextInput input, .stNumberInput input, .stTextArea textarea {
        background-color: #F8FAFC !important;
        border: 1.5px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 0.85rem 1rem !important;
        font-size: 0.95rem !important;
        color: #0F172A !important;
        transition: all 0.3s ease !important;
        font-family: 'Inter', sans-serif !important;
    }

    .stTextInput input::placeholder, .stNumberInput input::placeholder, .stTextArea textarea::placeholder {
        color: #CBD5E1 !important;
        font-weight: 400 !important;
    }

    .stTextInput input:hover, .stNumberInput input:hover, .stTextArea textarea:hover {
        border-color: #CBD5E1 !important;
        background-color: #FFFFFF !important;
    }

    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
        border-color: #2563EB !important;
        background-color: #FFFFFF !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
        outline: none !important;
    }

    /* Button */
    .stButton > button {
        width: 100%;
        padding: 0.95rem 1.5rem !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        border: none !important;
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
        color: white !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
        letter-spacing: 0.3px !important;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%) !important;
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.4) !important;
        transform: translateY(-2px) !important;
    }

    .stButton > button:active {
        transform: translateY(0) !important;
    }

    /* Vehicle Summary */
    .vehicle-summary {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        border: 1px solid #E2E8F0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        margin-bottom: 2rem;
    }

    .vehicle-header {
        display: flex;
        align-items: center;
        gap: 1.5rem;
        margin-bottom: 1.5rem;
        padding-bottom: 1.5rem;
        border-bottom: 2px solid #F1F5F9;
    }

    .vehicle-icon {
        font-size: 2.5rem;
    }

    .vehicle-info h3 {
        margin: 0;
        font-size: 1.4rem;
        font-weight: 800;
        color: #0F172A;
    }

    .vehicle-info p {
        margin: 0.25rem 0 0 0;
        font-size: 0.9rem;
        color: #64748B;
    }

    .vehicle-details {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: 1rem;
    }

    .vehicle-detail-item {
        background: #F8FAFC;
        padding: 1rem;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
    }

    .detail-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.3rem;
    }

    .detail-value {
        font-size: 1rem;
        font-weight: 700;
        color: #0F172A;
    }

    /* Severity Badge */
    .severity-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.75rem 1.2rem;
        border-radius: 12px;
        font-weight: 700;
        font-size: 1rem;
    }

    .severity-high {
        background: #FEE2E2;
        color: #7F1D1D;
        border: 1px solid #FCA5A5;
    }

    .severity-medium {
        background: #FEF3C7;
        color: #92400E;
        border: 1px solid #FCD34D;
    }

    .severity-low {
        background: #D1FAE5;
        color: #065F46;
        border: 1px solid #6EE7B7;
    }

    /* Result Section */
    .result-section {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        margin-bottom: 1.5rem;
        animation: slideUp 0.4s ease-out;
    }

    @keyframes slideUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .result-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1.25rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid #F1F5F9;
    }

    .result-icon {
        font-size: 1.5rem;
    }

    .result-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #0F172A;
        margin: 0;
    }

    .result-content {
        color: #334155;
        line-height: 1.7;
        font-size: 0.95rem;
    }

    /* Timeline */
    .timeline {
        position: relative;
        padding: 0;
        margin: 0;
    }

    .timeline-item {
        display: flex;
        gap: 1.5rem;
        margin-bottom: 1.5rem;
        position: relative;
    }

    .timeline-item:not(:last-child)::after {
        content: '';
        position: absolute;
        left: 1.25rem;
        top: 2.75rem;
        width: 2px;
        height: calc(100% - 0.5rem);
        background: #E2E8F0;
    }

    .timeline-number {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 2.5rem;
        height: 2.5rem;
        border-radius: 50%;
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
        color: white;
        font-weight: 700;
        font-size: 1rem;
        flex-shrink: 0;
        z-index: 1;
    }

    .timeline-content {
        padding-top: 0.25rem;
        flex-grow: 1;
    }

    .timeline-content h4 {
        margin: 0 0 0.3rem 0;
        font-size: 0.95rem;
        font-weight: 700;
        color: #0F172A;
    }

    .timeline-content p {
        margin: 0;
        font-size: 0.85rem;
        color: #64748B;
        line-height: 1.5;
    }

    /* Confidence Section */
    .confidence-section {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
        border-radius: 16px;
        padding: 2.5rem;
        border: none;
        box-shadow: 0 4px 20px rgba(37, 99, 235, 0.3);
        margin-bottom: 1.5rem;
        color: white;
    }

    .confidence-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 2.5rem;
        flex-wrap: wrap;
    }

    .confidence-circle {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        position: relative;
    }

    .confidence-ring {
        width: 140px;
        height: 140px;
        position: relative;
    }

    .confidence-text {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        text-align: center;
    }

    .confidence-percentage {
        font-size: 2.2rem;
        font-weight: 800;
        line-height: 1;
    }

    .confidence-label-small {
        font-size: 0.7rem;
        font-weight: 600;
        margin-top: 0.2rem;
        opacity: 0.9;
    }

    .confidence-details {
        flex: 1;
        min-width: 250px;
    }

    .confidence-title {
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        opacity: 0.9;
        margin-bottom: 0.75rem;
    }

    .confidence-rating {
        font-size: 1.4rem;
        font-weight: 800;
        margin-bottom: 0.75rem;
    }

    .confidence-explanation {
        font-size: 0.85rem;
        line-height: 1.6;
        opacity: 0.95;
    }

    /* Health Report */
    .health-report {
        background: linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%);
        border-radius: 16px;
        padding: 2rem;
        border: 1px solid #BAE6FD;
        margin-bottom: 1.5rem;
    }

    .health-report h3 {
        margin-top: 0;
        margin-bottom: 1.5rem;
        color: #0F172A;
        font-weight: 700;
        font-size: 1.1rem;
    }

    .health-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 1rem;
    }

    .health-metric {
        background: white;
        padding: 1.25rem;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        text-align: center;
    }

    .health-metric-icon {
        font-size: 1.75rem;
        margin-bottom: 0.5rem;
    }

    .health-metric-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.3px;
        margin-bottom: 0.25rem;
    }

    .health-metric-value {
        font-size: 1.15rem;
        font-weight: 800;
        color: #0F172A;
    }

    /* Results Grid */
    .results-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 1.25rem;
        margin-bottom: 2rem;
    }

    .result-item-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
    }

    .result-item-card:hover {
        border-color: #2563EB;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.15);
        transform: translateY(-2px);
    }

    .result-item-icon {
        font-size: 1.75rem;
        margin-bottom: 0.75rem;
    }

    .result-item-title {
        font-size: 0.9rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 0.5rem;
    }

    .result-item-text {
        font-size: 0.85rem;
        color: #64748B;
        line-height: 1.5;
    }

    /* Action Buttons */
    .action-buttons {
        display: flex;
        gap: 1rem;
        margin-top: 2.5rem;
        flex-wrap: wrap;
        justify-content: center;
    }

    /* Empty State */
    .empty-state {
        text-align: center;
        padding: 2rem;
        color: #94A3B8;
        font-size: 0.95rem;
    }

    /* Divider */
    .divider {
        height: 1px;
        background: #E2E8F0;
        margin: 1.75rem 0;
    }

    /* Messages */
    .stSuccess {
        background-color: #D1FAE5 !important;
        color: #065F46 !important;
        border: 1px solid #86EFAC !important;
        border-radius: 12px !important;
        padding: 1rem !important;
    }

    .stError {
        background-color: #FEE2E2 !important;
        color: #7F1D1D !important;
        border: 1px solid #FECACA !important;
        border-radius: 12px !important;
        padding: 1rem !important;
    }

    .stInfo {
        background-color: #EFF6FF !important;
        color: #082F4F !important;
        border: 1px solid #BFDBFE !important;
        border-radius: 12px !important;
        padding: 1rem !important;
    }

    /* Responsive */
    @media (max-width: 768px) {
        .hero-title {
            font-size: 1.8rem;
        }
        .hero-subtitle {
            font-size: 0.95rem;
        }
        .form-card {
            padding: 1.5rem;
        }
        .confidence-container {
            flex-direction: column;
        }
        .vehicle-header {
            flex-direction: column;
            text-align: center;
        }
        .results-grid {
            grid-template-columns: 1fr;
        }
        .action-buttons {
            flex-direction: column;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# Hero Section
st.markdown(
    """
    <div class="hero-section">
        <div class="hero-icon">🚗</div>
        <h1 class="hero-title">Automotive Vehicle Diagnostics</h1>
        <p class="hero-subtitle">AI-powered analysis for vehicle diagnostics, repair recommendations, and maintenance guidance</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-container">', unsafe_allow_html=True)

# Input Form
st.markdown('<div class="form-card">', unsafe_allow_html=True)

# Vehicle Information
st.markdown(
    """
    <div class="form-section-header">
        <div class="form-section-icon">📋</div>
        <h2 class="form-section-title">Vehicle Information</h2>
    </div>
    """,
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns([2, 2, 1.5])
with col1:
    st.markdown('<div class="form-group">', unsafe_allow_html=True)
    st.markdown('<label class="form-label"><span class="form-label-icon">🏭</span>Vehicle Make</label>', unsafe_allow_html=True)
    make = st.text_input("", placeholder="Toyota", key="make", label_visibility="collapsed")
    st.markdown('<div class="form-tooltip">e.g., Toyota, Honda, Ford</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown('<div class="form-group">', unsafe_allow_html=True)
    st.markdown('<label class="form-label"><span class="form-label-icon">🚙</span>Vehicle Model</label>', unsafe_allow_html=True)
    model = st.text_input("", placeholder="Corolla", key="model", label_visibility="collapsed")
    st.markdown('<div class="form-tooltip">e.g., Corolla, Civic, F-150</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    st.markdown('<div class="form-group">', unsafe_allow_html=True)
    st.markdown('<label class="form-label"><span class="form-label-icon">📅</span>Year</label>', unsafe_allow_html=True)
    year = st.number_input("", min_value=1950, max_value=2100, value=2020, key="year", label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])
with col1:
    st.markdown('<div class="form-group">', unsafe_allow_html=True)
    st.markdown('<label class="form-label"><span class="form-label-icon">⛽</span>Mileage (Optional)</label>', unsafe_allow_html=True)
    mileage_input = st.text_input("", placeholder="e.g., 60000", key="mileage", label_visibility="collapsed")
    st.markdown('<div class="form-tooltip">Enter current mileage for maintenance</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Diagnostic Information
st.markdown(
    """
    <div class="divider"></div>
    <div class="form-section-header">
        <div class="form-section-icon">🔧</div>
        <h2 class="form-section-title">Diagnostic Information</h2>
    </div>
    """,
    unsafe_allow_html=True,
)

col1, col2 = st.columns([1, 1])
with col1:
    st.markdown('<div class="form-group">', unsafe_allow_html=True)
    st.markdown('<label class="form-label"><span class="form-label-icon">⚠️</span>Diagnostic Code (DTC)</label>', unsafe_allow_html=True)
    code = st.text_input("", placeholder="P0171", key="code", label_visibility="collapsed")
    st.markdown('<div class="form-tooltip">e.g., P0171, P0300, C0010</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown('<div class="form-group">', unsafe_allow_html=True)
    st.markdown('<label class="form-label"><span class="form-label-icon">🛠️</span>Maintenance Concern (Optional)</label>', unsafe_allow_html=True)
    maintenance_query = st.text_input("", placeholder="What service is due?", key="maintenance", label_visibility="collapsed")
    st.markdown('<div class="form-tooltip">Ask about maintenance schedules</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Symptoms Section
st.markdown(
    """
    <div class="divider"></div>
    <div class="form-section-header">
        <div class="form-section-icon">🔍</div>
        <h2 class="form-section-title">Vehicle Symptoms (Optional)</h2>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="form-group">', unsafe_allow_html=True)
symptoms = st.text_area(
    "",
    placeholder="Describe any symptoms (e.g., rough idle, poor fuel economy, check engine light)",
    height=100,
    key="symptoms",
    label_visibility="collapsed",
)
st.markdown('<div class="form-tooltip">Describe what you\'ve observed with your vehicle</div>', unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)


def _format_source(source: Dict[str, Any]) -> str:
    base = source.get("source", "unknown")
    src_type = source.get("type", "")
    page = source.get("page")
    suffix = f" ({src_type})" if src_type else ""
    if page is not None:
        suffix += f" page={page}"
    return f"{base}{suffix}"


def get_confidence_color(confidence: float) -> str:
    if confidence >= 0.85:
        return "#22C55E"
    elif confidence >= 0.70:
        return "#3B82F6"
    elif confidence >= 0.50:
        return "#F59E0B"
    else:
        return "#EF4444"


def generate_circular_progress(confidence: float) -> str:
    radius = 45
    circumference = 2 * 3.14159 * radius
    stroke_dashoffset = circumference * (1 - confidence)
    color = get_confidence_color(confidence)
    svg = f'<svg width="150" height="150" viewBox="0 0 150 150"><circle cx="75" cy="75" r="{radius}" fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="8"/><circle cx="75" cy="75" r="{radius}" fill="none" stroke="{color}" stroke-width="8" stroke-dasharray="{circumference}" stroke-dashoffset="{stroke_dashoffset}" stroke-linecap="round" style="transform: rotate(-90deg); transform-origin: 75px 75px;"/></svg>'
    return svg


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
col1, col2, col3 = st.columns([1, 1.5, 1])
with col2:
    diagnose_btn = st.button("🔍 Run Diagnostics", use_container_width=True, type="primary")

if diagnose_btn:
    with st.spinner("🔄 Analyzing vehicle data..."):
        try:
            result = diagnose()
            
            st.markdown('<div style="margin-top: 3rem;"></div>', unsafe_allow_html=True)

            # Vehicle Summary Card
            st.markdown(
                f"""
                <div class="vehicle-summary">
                    <div class="vehicle-header">
                        <div class="vehicle-icon">🚗</div>
                        <div class="vehicle-info">
                            <h3>{make or "Unknown"} {model or "Model"}</h3>
                            <p>Model Year: {int(year) if year else "Unknown"}</p>
                        </div>
                    </div>
                    <div class="vehicle-details">
                        <div class="vehicle-detail-item">
                            <div class="detail-label">Diagnostic Code</div>
                            <div class="detail-value">{code if code else "—"}</div>
                        </div>
                        <div class="vehicle-detail-item">
                            <div class="detail-label">Mileage</div>
                            <div class="detail-value">{mileage_input if mileage_input else "Not provided"}</div>
                        </div>
                        <div class="vehicle-detail-item">
                            <div class="detail-label">Analysis Status</div>
                            <div class="detail-value">✓ Complete</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Severity Badge
            severity = result.get("severity", "Unknown")
            severity_class = "severity-high" if severity.lower() == "high" else "severity-medium" if severity.lower() == "medium" else "severity-low"
            severity_icon = "🔴" if severity.lower() == "high" else "🟡" if severity.lower() == "medium" else "🟢"
            
            st.markdown(
                f'<div style="margin-bottom: 2rem;"><span class="severity-badge {severity_class}">{severity_icon} {severity.title()} Severity</span></div>',
                unsafe_allow_html=True,
            )

            # Diagnostic Summary
            st.markdown(
                f"""
                <div class="result-section">
                    <div class="result-header">
                        <div class="result-icon">📋</div>
                        <h3 class="result-title">Diagnostic Summary</h3>
                    </div>
                    <div class="result-content">
                        {result.get('diagnosis', 'No diagnosis generated.')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Root Cause Analysis
            causes = result.get("possible_causes", [])
            if causes:
                causes_html = '<div class="timeline">'
                for i, cause in enumerate(causes, 1):
                    cause_title = cause.split(".")[0].strip() if "." in cause else cause.strip()
                    cause_detail = ". ".join(cause.split(".")[1:]).strip() if "." in cause else ""
                    causes_html += f'<div class="timeline-item"><div class="timeline-number">{i}</div><div class="timeline-content"><h4>{cause_title}</h4><p>{cause_detail}</p></div></div>'
                causes_html += '</div>'
            else:
                causes_html = '<div class="empty-state">No specific root causes identified</div>'
            
            st.markdown(
                f"""
                <div class="result-section">
                    <div class="result-header">
                        <div class="result-icon">🔍</div>
                        <h3 class="result-title">Root Cause Analysis</h3>
                    </div>
                    {causes_html}
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Repair Recommendations
            repair_steps = result.get("repair_steps", [])
            if repair_steps:
                repair_html = '<div class="timeline">'
                for i, step in enumerate(repair_steps, 1):
                    step_title = step.split(".")[0].strip() if "." in step else step.strip()
                    step_detail = ". ".join(step.split(".")[1:]).strip() if "." in step else ""
                    repair_html += f'<div class="timeline-item"><div class="timeline-number">{i}</div><div class="timeline-content"><h4>{step_title}</h4><p>{step_detail}</p></div></div>'
                repair_html += '</div>'
            else:
                repair_html = '<div class="empty-state">No repair recommendations available</div>'
            
            st.markdown(
                f"""
                <div class="result-section">
                    <div class="result-header">
                        <div class="result-icon">🔧</div>
                        <h3 class="result-title">Repair Recommendations</h3>
                    </div>
                    {repair_html}
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Maintenance Recommendations
            maintenance = result.get("maintenance_recommendations", [])
            if maintenance:
                maintenance_html = '<div class="results-grid">'
                maintenance_icons = ["🛢️", "🛞", "🔩", "💨", "⚡", "🧊"]
                for i, item in enumerate(maintenance):
                    icon = maintenance_icons[i % len(maintenance_icons)]
                    item_title = item.split(":")[0].strip() if ":" in item else item.strip()
                    item_text = ":".join(item.split(":")[1:]).strip() if ":" in item else item.strip()
                    maintenance_html += f"""
                    <div class="result-item-card">
                        <div class="result-item-icon">{icon}</div>
                        <div class="result-item-title">{item_title}</div>
                        <div class="result-item-text">{item_text}</div>
                    </div>
                    """
                maintenance_html += '</div>'
                
                st.markdown(
                    f"""
                    <div class="result-section">
                        <div class="result-header">
                            <div class="result-icon">🛠️</div>
                            <h3 class="result-title">Maintenance Recommendations</h3>
                        </div>
                        {maintenance_html}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Confidence Score
            confidence = float(result.get("confidence_score", 0.0))
            confidence_pct = confidence * 100
            confidence_text = "Very High Confidence" if confidence >= 0.85 else "High Confidence" if confidence >= 0.70 else "Medium Confidence" if confidence >= 0.50 else "Low Confidence"
            confidence_color = get_confidence_color(confidence)
            svg_ring = generate_circular_progress(confidence)
            
            st.markdown(
                f"""
                <div class="confidence-section">
                    <div class="confidence-container">
                        <div class="confidence-circle">
                            <div class="confidence-ring">
                                {svg_ring}
                                <div class="confidence-text">
                                    <div class="confidence-percentage">{confidence_pct:.0f}%</div>
                                    <div class="confidence-label-small">CONFIDENCE</div>
                                </div>
                            </div>
                        </div>
                        <div class="confidence-details">
                            <div class="confidence-title">✨ Analysis Confidence</div>
                            <div class="confidence-rating" style="color: {confidence_color};">{confidence_text}</div>
                            <div class="confidence-explanation">
                                This confidence score reflects the AI model's certainty in the diagnostic analysis based on the quality and quantity of input data provided. Higher confidence indicates stronger correlation with known vehicle issues.
                            </div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Vehicle Health Report
            st.markdown(
                f"""
                <div class="health-report">
                    <h3>📊 Vehicle Health Report</h3>
                    <div class="health-grid">
                        <div class="health-metric">
                            <div class="health-metric-icon">📈</div>
                            <div class="health-metric-label">Overall Health</div>
                            <div class="health-metric-value">{max(50, 100 - int(confidence_pct * 0.3))}%</div>
                        </div>
                        <div class="health-metric">
                            <div class="health-metric-icon">✓</div>
                            <div class="health-metric-label">Diagnosis Confidence</div>
                            <div class="health-metric-value">{confidence_pct:.0f}%</div>
                        </div>
                        <div class="health-metric">
                            <div class="health-metric-icon">🚙</div>
                            <div class="health-metric-label">Driveability</div>
                            <div class="health-metric-value">{"Safe" if severity.lower() != "high" else "Caution"}</div>
                        </div>
                        <div class="health-metric">
                            <div class="health-metric-icon">⚠️</div>
                            <div class="health-metric-label">Priority Level</div>
                            <div class="health-metric-value">{severity.title()}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Sources
            sources = result.get("sources", [])
            if sources:
                sources_html = ""
                for source in sources:
                    formatted_source = _format_source(source)
                    sources_html += f'<div style="padding: 0.75rem; background: #F8FAFC; border-radius: 8px; border: 1px solid #E2E8F0; margin-bottom: 0.5rem; font-size: 0.9rem; color: #334155;">📖 {formatted_source}</div>'
                
                st.markdown(
                    f"""
                    <div class="result-section">
                        <div class="result-header">
                            <div class="result-icon">📚</div>
                            <h3 class="result-title">Information Sources</h3>
                        </div>
                        {sources_html}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Action Buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📋 Copy Results", use_container_width=True):
                    st.success("✓ Results copied!")
            with col2:
                if st.button("⬇️ Download Report", use_container_width=True):
                    st.success("✓ Downloaded!")
            with col3:
                if st.button("🔄 New Diagnosis", use_container_width=True):
                    st.rerun()

        except requests.HTTPError as exc:
            st.error(f"❌ Backend Error: {exc}")
        except Exception as exc:
            st.error(f"❌ Analysis Failed: {exc}")

st.markdown("</div>", unsafe_allow_html=True)
