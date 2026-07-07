"""
Reusable metric row rendering.
"""

import streamlit as st


def format_inr(value):
    """Format a numeric value as Indian rupee text without relying on symbols."""

    return f"INR {value:,.2f}"


def render_metric_row(metrics):
    """Render a responsive row of Streamlit metrics.

    Each metric item should include a label and value. Delta is optional.
    """

    columns = st.columns(len(metrics))
    for column, metric in zip(columns, metrics):
        with column:
            with st.container(border=True):
                st.metric(
                    label=metric["label"],
                    value=metric["value"],
                    delta=metric.get("delta"),
                )
                if metric.get("caption"):
                    st.caption(metric["caption"])
