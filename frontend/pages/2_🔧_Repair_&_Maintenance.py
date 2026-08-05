import streamlit as st
from utils import format_source, get_shared_css

st.set_page_config(
    page_title="Repair & Maintenance",
    page_icon="🔧",
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
      <h3 style="margin:0;">Repair & Maintenance Guide</h3>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

# SECTION 1: Detailed Repair Steps
st.markdown('<div class="section-title">🔧 Detailed Repair Steps</div>', unsafe_allow_html=True)
st.markdown("""
Follow these comprehensive repair steps to resolve the identified issues:
""")
repair_steps = result.get("repair_steps", [])
if repair_steps:
    for i, step in enumerate(repair_steps, 1):
        with st.container():
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #eff6ff 0%, #f0f9ff 100%); 
                        border-left: 4px solid #0ea5e9; border-radius: 8px; 
                        padding: 1.2rem; margin: 0.8rem 0; 
                        border: 1px solid #cffafe;">
            <strong style="color: #0ea5e9; font-size: 1.1rem;">Step {i}</strong>
            <p style="color: #374151; margin-top: 0.5rem; line-height: 1.8;">{step}</p>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("No repair recommendations available.")

st.markdown("---")

# SECTION 2: Maintenance Recommendations
st.markdown('<div class="section-title">📋 Recommended Maintenance</div>', unsafe_allow_html=True)
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

# SECTION 3: Knowledge Sources
st.markdown('<div class="section-title">📚 Knowledge Sources</div>', unsafe_allow_html=True)
st.markdown("This diagnosis was powered by the following sources from our knowledge base:")

sources = result.get("sources", [])
if sources:
    for i, source in enumerate(sources, 1):
        formatted_source = format_source(source)
        st.markdown(f"**Source {i}:** {formatted_source}")
else:
    st.info("No sources available for this diagnosis.")

st.markdown("---")

# Navigation buttons
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    if st.button("← Back to Diagnosis", use_container_width=True):
        st.switch_page("pages/1_🔍_Diagnosis.py")

with col3:
    if st.button("← Back to Home", use_container_width=True):
        st.switch_page("streamlit_app.py")
