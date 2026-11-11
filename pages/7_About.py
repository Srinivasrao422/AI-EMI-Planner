from pathlib import Path
import sys

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from components.page_shell import render_page_header
from components.theme import load_theme


st.set_page_config(
    page_title="About | MSME Credit & Financial Risk Platform",
    layout="wide",
)

load_theme()

render_page_header(
    "About",
    "An MSME-focused financial workspace for business profiles, loan planning, repayment analysis and decision-support risk review.",
)

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.subheader("Product Scope")
        st.caption("MSME business profile management")
        st.caption("Repayment schedule generation")
        st.caption("Loan comparison")
        st.caption("Loan affordability and risk review")
        st.caption("AI-style recommendations panel")

with col2:
    with st.container(border=True):
        st.subheader("Technology")
        st.caption("Python")
        st.caption("Streamlit")
        st.caption("Pandas")
        st.caption("Plotly")

st.divider()
st.info("Business calculations are isolated in the core package for maintainability.")
