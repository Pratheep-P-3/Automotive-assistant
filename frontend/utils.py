"""Shared utilities for all pages."""
from typing import Any, Dict, List

def format_source(source: Dict[str, Any]) -> str:
    """Format source metadata for display."""
    filename = source.get("source_filename") or source.get("source", "Unknown Source")
    category = source.get("category", "")
    chunk_type = source.get("chunk_type", "")
    vector_score = source.get("vector_score", 0)
    rerank_score = source.get("rerank_score", 0)
    
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


def get_severity_color(severity: str) -> str:
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


def render_severity_badge(severity: str) -> str:
    """Return HTML for severity badge."""
    import streamlit as st
    css_class = get_severity_color(severity)
    st.markdown(
        f'<div class="{css_class}">{severity.upper()}</div>',
        unsafe_allow_html=True
    )


def render_list(items: List[str], empty_text: str) -> None:
    """Render a formatted list."""
    import streamlit as st
    if not items:
        st.info(empty_text)
        return
    st.markdown("<ul>", unsafe_allow_html=True)
    for item in items:
        st.markdown(f"<li>{item}</li>", unsafe_allow_html=True)
    st.markdown("</ul>", unsafe_allow_html=True)


def get_shared_css() -> str:
    """Return shared CSS for all pages."""
    return """
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
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 50%, #f0f4f8 100%);
        min-height: 100vh;
        color: #0f172a;
    }

    [data-testid="stAppViewContainer"] > section:first-child {
        max-width: 1000px;
        margin-left: auto;
        margin-right: auto;
        padding-left: 2rem;
        padding-right: 2rem;
    }

    [data-testid="stMainBlockContainer"] {
        max-width: 1000px;
        margin-left: auto;
        margin-right: auto;
    }

    .stApp > [data-testid="stAppViewContainer"] {
        width: 100% !important;
    }

    .stApp > [data-testid="stAppViewContainer"] > section {
        max-width: 1000px !important;
        margin-left: auto !important;
        margin-right: auto !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }

    .hero-card {
        background: linear-gradient(135deg, #1e40af 0%, #0ea5e9 100%);
        padding: 1.2rem 2rem;
        border-radius: 12px;
        color: white;
        box-shadow: 0 12px 32px rgba(30, 64, 175, 0.25);
        margin-bottom: 2rem;
        margin-left: -1.5rem;
        margin-right: -1.5rem;
        border: none;
        backdrop-filter: blur(10px);
        animation: slideDown 0.7s cubic-bezier(0.34, 1.56, 0.64, 1);
        position: relative;
        overflow: hidden;
        width: calc(100% + 3rem);
    }

    .hero-card::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(255,255,255,0.05) 0%, transparent 70%);
        border-radius: 50%;
        pointer-events: none;
    }

    .hero-card h2 {
        font-size: 2rem;
        font-weight: 800;
        font-family: 'Poppins', sans-serif;
        letter-spacing: -0.8px;
        margin: 0 !important;
        position: relative;
        z-index: 1;
        text-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }

    .hero-card h3 {
        font-size: 1.3rem;
        font-weight: 600;
        font-family: 'Poppins', sans-serif;
        margin: 0 !important;
        position: relative;
        z-index: 1;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
        border-right: 1px solid #e2e8f0;
    }

    [data-testid="stSidebar"] [data-testid="stHeader"] {
        font-weight: 700;
        font-family: 'Poppins', sans-serif;
        color: #1e40af;
        font-size: 1.1rem;
        margin-bottom: 1.8rem !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        padding: 1rem 0.5rem;
        border-bottom: 2px solid #0ea5e9;
    }

    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        background: white !important;
        border: 2px solid #e2e8f0 !important;
        border-radius: 10px !important;
        padding: 0.85rem 1rem !important;
        font-size: 0.95rem !important;
        transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
        font-weight: 500 !important;
        color: #0f172a !important;
        outline: none !important;
        box-shadow: none !important;
    }

    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus {
        border: 2px solid #0ea5e9 !important;
        box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.1), inset 0 0 0 1px #0ea5e9 !important;
        background: #f0f9fc !important;
        outline: none !important;
    }

    .stTextInput > label,
    .stNumberInput > label,
    .stTextArea > label,
    .stSelectbox > label {
        font-weight: 700 !important;
        font-family: 'Poppins', sans-serif;
        color: #1e40af !important;
        font-size: 0.9rem !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.7rem !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #1e40af 0%, #0ea5e9 100%) !important;
        color: white !important;
        font-weight: 700 !important;
        font-family: 'Poppins', sans-serif;
        font-size: 1.05rem !important;
        padding: 1rem 2.5rem !important;
        border: none !important;
        border-radius: 10px !important;
        cursor: pointer !important;
        transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        box-shadow: 0 10px 25px rgba(30, 64, 175, 0.3) !important;
        position: relative;
        overflow: hidden;
    }

    .stButton > button:hover {
        transform: translateY(-4px) !important;
        box-shadow: 0 15px 35px rgba(30, 64, 175, 0.3) !important;
    }

    .stSubheader {
        color: #1e40af !important;
        font-weight: 800 !important;
        font-family: 'Poppins', sans-serif;
        font-size: 1.4rem !important;
        margin-top: 2rem !important;
        margin-bottom: 1.5rem !important;
        padding-bottom: 0.8rem;
        border-bottom: 3px solid #0ea5e9;
        display: flex;
        align-items: center;
        gap: 0.8rem;
    }

    .result-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-left: 5px solid #0ea5e9;
        border-radius: 12px;
        padding: 1.8rem;
        box-shadow: 0 4px 15px rgba(30, 64, 175, 0.06);
        margin-bottom: 1.5rem;
        transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
        animation: fadeInUp 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
    }

    .result-card:hover {
        box-shadow: 0 8px 25px rgba(30, 64, 175, 0.12);
        transform: translateY(-4px);
        border-left-color: #0ea5e9;
        border-color: #cbd5e1;
    }

    .section-title {
        font-weight: 800;
        font-family: 'Poppins', sans-serif;
        color: #1e40af;
        font-size: 1.1rem;
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
        background: linear-gradient(180deg, #0ea5e9 0%, #1e40af 100%);
        border-radius: 2px;
    }

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
        color: #0ea5e9;
        padding-left: 2rem;
    }

    .result-card ul li::before {
        content: '→';
        color: #0ea5e9;
        font-weight: 800;
        margin-right: 0.8rem;
        position: absolute;
        left: 0;
    }

    .stProgress > div > div > div {
        background: linear-gradient(90deg, #0ea5e9 0%, #1e40af 100%) !important;
        border-radius: 12px !important;
        box-shadow: 0 0 10px rgba(14, 165, 233, 0.3);
    }

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
        border-left: 5px solid #0ea5e9 !important;
        border-radius: 14px !important;
        color: #082f49 !important;
        padding: 1rem !important;
    }

    .stMetric {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1.2rem;
        box-shadow: 0 2px 8px rgba(30, 64, 175, 0.04);
    }

    .stMetric [data-testid="stMetricValue"] {
        color: #1e40af !important;
        font-family: 'Poppins', sans-serif;
        font-weight: 800 !important;
        font-size: 1.8rem !important;
    }

    .stMetric [data-testid="stMetricLabel"] {
        color: #6b7280 !important;
        font-weight: 600 !important;
    }

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

    .stSpinner > div > div {
        border-top-color: #0ea5e9 !important;
        border-right-color: rgba(14, 165, 233, 0.3) !important;
        border-bottom-color: rgba(14, 165, 233, 0.3) !important;
        border-left-color: rgba(14, 165, 233, 0.3) !important;
    }

    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #f3f4f6;
    }

    ::-webkit-scrollbar-thumb {
        background: #0ea5e9;
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #1e40af;
    }

    .nav-buttons {
        display: flex;
        gap: 1rem;
        margin: 2rem 0;
        justify-content: center;
    }

    @media (max-width: 768px) {
        .hero-card {
            padding: 0.9rem 1.2rem;
            width: calc(100% + 2.4rem);
            margin-left: -1.2rem;
            margin-right: -1.2rem;
        }

        .hero-card h2 {
            font-size: 1.5rem;
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
    </style>
    """
