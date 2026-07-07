"""
Native Streamlit form controls for EMI inputs.
"""

import streamlit as st
from utils.state_manager import get_financial_data

LOAN_TYPES = (
    "Home Loan",
    "Car Loan",
    "Education Loan",
    "Personal Loan",
)

def show_emi_form():
    """Collect loan inputs for EMI calculation."""

    # Retrieve current global state for single source of truth
    data = get_financial_data()

    st.subheader("Loan Details")
    st.caption("Enter your loan details to calculate EMI.")

    with st.container(border=True):
        col1, col2 = st.columns(2)

        with col1:
            loan_amount = st.number_input(
                "Loan Amount (INR)",
                min_value=10000,
                max_value=100000000,
                value=int(data.get("loan_amount", 500000.0)),
                step=10000,
            )
            interest_rate = st.slider(
                "Interest Rate (%)",
                min_value=1.0,
                max_value=20.0,
                value=float(data.get("interest_rate", 8.5)),
                step=0.1,
            )

        with col2:
            tenure = st.slider(
                "Loan Tenure (Years)",
                min_value=1,
                max_value=30,
                value=int(data.get("tenure", 5)),
            )
            monthly_income = st.number_input(
                "Monthly Income (INR)",
                min_value=10000,
                value=int(data.get("monthly_income", 60000.0)),
                step=1000,
            )

        loan_type = st.selectbox("Loan Type", LOAN_TYPES)
        calculate = st.button(
            "Calculate EMI",
            use_container_width=True,
            type="primary",
        )

    return {
        "loan_amount": loan_amount,
        "interest_rate": interest_rate,
        "tenure": tenure,
        "monthly_income": monthly_income,
        "loan_type": loan_type,
        "calculate": calculate,
    }
