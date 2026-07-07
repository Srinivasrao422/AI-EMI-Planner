"""
Shared Streamlit theme loader.
"""

from pathlib import Path

import streamlit as st


STYLE_PATH = Path(__file__).resolve().parents[1] / "assets" / "style.css"


@st.cache_data(show_spinner=False)
def _read_stylesheet(path):
    return Path(path).read_text(encoding="utf-8")


def load_theme():
    """Load the app stylesheet once per page."""

    if STYLE_PATH.exists():
        st.markdown(
            f"<style>{_read_stylesheet(str(STYLE_PATH))}</style>",
            unsafe_allow_html=True,
        )
