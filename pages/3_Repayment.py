from pathlib import Path
import sys
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from components.charts import show_charts
from components.metric_row import format_inr, render_metric_row
from components.page_shell import render_page_header
from components.theme import load_theme

from core.emi import calculate_emi
from core.repayment import generate_repayment_schedule

from utils.state_manager import get_financial_data
from utils.auth_helper import require_login

st.set_page_config(
    page_title="Repayment Schedule | MSME Credit & Financial Risk Platform",
    layout="wide",
)

load_theme()

# Protect page and render custom sidebar navigation if authenticated
if require_login():
    render_page_header(
        "Repayment Schedule",
        "Review your latest EMI calculation repayment details.",
    )

    # ================================
    # LOAD GLOBAL DATA
    # ================================
    data = get_financial_data()
    principal = data["loan_amount"]
    rate = data["interest_rate"]
    years = data["tenure"]

    with st.container(border=True):
        st.info("Showing latest EMI calculation data.")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Loan Amount", format_inr(principal))
        with col2:
            st.metric("Interest Rate", f"{rate}%")
        with col3:
            st.metric("Tenure", f"{years} Years")

    # ================================
    # CALCULATIONS
    # ================================
    monthly_emi = calculate_emi(principal, rate, years)
    total_payment = monthly_emi * years * 12
    total_interest = total_payment - principal

    schedule = generate_repayment_schedule(principal, rate, years)

    st.divider()

    render_metric_row((
        {
            "label": "Monthly EMI",
            "value": format_inr(monthly_emi)
        },
        {
            "label": "Total Interest",
            "value": format_inr(total_interest)
        },
        {
            "label": "Total Payment",
            "value": format_inr(total_payment)
        },
    ))

    st.divider()

    show_charts(principal, total_interest, schedule)

    st.subheader("Monthly Repayment Schedule")
    st.dataframe(
        pd.DataFrame(schedule),
        use_container_width=True,
        hide_index=True
    )