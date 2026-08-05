import streamlit as st
from utils import format_source, get_severity_color, render_severity_badge, get_shared_css

st.set_page_config(
    page_title="Diagnosis Results",
    page_icon="🔍",
    layout="wide",
)

st.markdown(get_shared_css(), unsafe_allow_html=True)

# Check if results exist in session state
if "diagnostic_result" not in st.session_state:
    st.error("No diagnostic results found. Please run diagnostics from the home page.")
    if st.button("← Back to Home"):
        st.switch_page("streamlit_app.py")
    st.stop()

result = st.session_state.diagnostic_result

# Header
st.markdown(
    """
    <div class="hero-card">
      <h3 style="margin:0;">Diagnostic Analysis Results</h3>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

# SECTION 1: Diagnostic Summary & Severity
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown('<div class="section-title">📋 Diagnosis Summary</div>', unsafe_allow_html=True)
    st.markdown(result.get("diagnosis", "No diagnosis generated."))

with col2:
    severity = result.get("severity", "Unknown")
    st.markdown('<div class="section-title">🚨 Severity</div>', unsafe_allow_html=True)
    render_severity_badge(severity)

st.markdown("---")

# SECTION 2: Root Cause Analysis
st.markdown('<div class="section-title">🔍 Root Cause Analysis</div>', unsafe_allow_html=True)
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

# SECTION 3: Confidence & Analysis
st.markdown('<div class="section-title">📊 Diagnosis Confidence & Analysis</div>', unsafe_allow_html=True)

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

# Navigation buttons
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    if st.button("← Back to Home", use_container_width=True):
        st.switch_page("streamlit_app.py")

with col3:
    if st.button("View Repair & Maintenance →", use_container_width=True):
        st.switch_page("pages/2_🔧_Repair_&_Maintenance.py")
