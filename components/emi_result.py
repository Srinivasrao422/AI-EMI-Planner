"""
EMI result metrics.
"""

import streamlit as st

from components.metric_row import format_inr, render_metric_row


def show_emi_results(monthly_emi, total_interest, total_payment):
    """Display calculated EMI results."""

    st.subheader("EMI Results")

    metrics = (
        {"label": "Monthly EMI", "value": format_inr(monthly_emi)},
        {"label": "Interest Payable", "value": format_inr(total_interest)},
        {"label": "Total Payment", "value": format_inr(total_payment)},
    )

    render_metric_row(metrics)
    st.success("Calculation completed successfully.")


show_results = show_emi_results
