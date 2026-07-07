"""
Application footer.
"""

import streamlit as st


def show_footer():
    """Render the footer with lightweight product metadata."""

    st.divider()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption("AI Powered EMI Planner")
    with col2:
        st.caption("Version 1.0")
    with col3:
        st.caption("(c) 2026 Srinivas Rao")

    st.caption("Built with Python, Streamlit, Plotly, and AI-assisted planning.")
