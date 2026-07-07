"""
Shared page layout helpers.
"""

import streamlit as st


def render_page_header(title, subtitle=None):
    """Render a consistent page title block."""

    st.title(title)
    if subtitle:
        st.caption(subtitle)


def render_feature_notice(title, message):
    """Render a consistent panel for features that are not fully connected."""

    with st.container(border=True):
        st.info(title)
        st.caption(message)
