"""
Financial overview metrics for the dashboard home page.
"""

import streamlit as st

from components.metric_row import render_metric_row


OVERVIEW_METRICS = (
    {
        "label": "Loan Amount",
        "value": "INR 5,00,000",
        "delta": "Healthy baseline",
        "caption": "Updated just now",
    },
    {
        "label": "Monthly EMI",
        "value": "INR 10,258",
        "delta": "Active estimate",
        "caption": "Updated just now",
    },
    {
        "label": "Interest",
        "value": "INR 1,15,496",
        "delta": "Normal range",
        "caption": "Updated just now",
    },
    {
        "label": "Total Payment",
        "value": "INR 6,15,496",
        "delta": "Projected total",
        "caption": "Updated just now",
    },
)


def show_metric_cards(metrics=OVERVIEW_METRICS):
    """Render the high-level financial snapshot."""

    st.subheader("Financial Overview")
    render_metric_row(metrics)
