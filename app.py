import streamlit as st
from utils.state_manager import init_state
from components.page_shell import render_page_header
from components.theme import load_theme
from database.models import create_tables
from utils.auth_helper import require_login

st.set_page_config(
    page_title="AI Powered EMI Planner",
    layout="wide",
)
init_state()
create_tables()
load_theme()

# Protect page and render custom sidebar navigation if authenticated
if require_login():
    render_page_header(
        f"Welcome back, {st.session_state.username}! 👋",
        "Your AI-Powered EMI Planner Workspace is ready. Use the sidebar to navigate or choose an option below.",
    )

    st.divider()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.page_link("pages/1_Home.py", label="🏠 Open Dashboard", use_container_width=True)
    with col2:
        st.page_link("pages/2_EMI_Calculator.py", label="💰 Calculate EMI", use_container_width=True)
    with col3:
        st.page_link("pages/5_Risk_Analysis.py", label="📊 Review Risk", use_container_width=True)
