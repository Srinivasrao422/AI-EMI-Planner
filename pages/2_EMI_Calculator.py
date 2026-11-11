"""
==========================================
EMI Calculator Page
==========================================
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from components.charts import show_charts
from components.theme import load_theme

from core.emi import calculate_emi
from core.repayment import generate_repayment_schedule

from utils.state_manager import save_emi_data, get_financial_data
from utils.auth_helper import require_login
from database.loan_history import save_loan

st.set_page_config(
    page_title="EMI Calculator | MSME Credit & Financial Risk Platform",
    layout="wide",
)

load_theme()

# Protect page and render custom sidebar navigation if authenticated
if require_login():
    st.title("AI EMI Calculator")
    st.caption("Calculate your EMI instantly and plan your amortization schedule.")
    st.divider()

    # Retrieve current active details
    data = get_financial_data()

    # Layout: Left inputs, Right results
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("Loan Inputs")
        with st.container(border=True):
            loan_amount = st.number_input(
                "Loan Amount (INR)",
                min_value=10000,
                max_value=100000000,
                value=int(data["loan_amount"]),
                step=10000,
            )
            interest_rate = st.slider(
                "Interest Rate (%)",
                min_value=1.0,
                max_value=20.0,
                value=float(data["interest_rate"]),
                step=0.1,
            )
            tenure = st.slider(
                "Loan Tenure (Years)",
                min_value=1,
                max_value=30,
                value=int(data["tenure"]),
            )
            monthly_income = st.number_input(
                "Monthly Income (INR)",
                min_value=10000,
                value=int(data["monthly_income"]),
                step=1000,
            )
            calculate = st.button("Calculate EMI", type="primary", use_container_width=True)

    if calculate:
        # Calculate loan details
        monthly_emi = calculate_emi(loan_amount, interest_rate, tenure)
        total_payment = round(monthly_emi * tenure * 12, 2)
        total_interest = round(total_payment - loan_amount, 2)

        # Save to global session state
        save_emi_data(
            loan_amount=loan_amount,
            interest_rate=interest_rate,
            tenure=tenure,
            income=monthly_income,
            emi=monthly_emi,
            interest=total_interest,
            payment=total_payment
        )

        # Save automatically to SQLite database
        save_loan(st.session_state.user_id, {
            "loan_amount": loan_amount,
            "interest_rate": interest_rate,
            "tenure": tenure,
            "monthly_income": monthly_income,
            "monthly_emi": monthly_emi,
            "total_interest": total_interest,
            "total_payment": total_payment,
            "risk_level": "Pending"
        })

        st.success("Calculation saved successfully")
        
        # Reload active session data
        data = get_financial_data()

    with col_right:
        st.subheader("Calculation Results")
        with st.container(border=True):
            # Card 1: Monthly EMI
            st.markdown(
                f"""
                <div style="background-color: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 1.25rem; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                    <div style="font-size: 0.8rem; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px;">Monthly EMI</div>
                    <div style="font-size: 1.8rem; font-weight: 700; color: var(--text); margin-top: 0.25rem; font-family: 'Outfit', sans-serif;">₹{data['monthly_emi']:,.2f}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            # Card 2: Interest Amount
            st.markdown(
                f"""
                <div style="background-color: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 1.25rem; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                    <div style="font-size: 0.8rem; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px;">Interest Amount</div>
                    <div style="font-size: 1.8rem; font-weight: 700; color: var(--text); margin-top: 0.25rem; font-family: 'Outfit', sans-serif;">₹{data['total_interest']:,.2f}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            # Card 3: Total Payment
            st.markdown(
                f"""
                <div style="background-color: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                    <div style="font-size: 0.8rem; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px;">Total Payment</div>
                    <div style="font-size: 1.8rem; font-weight: 700; color: var(--text); margin-top: 0.25rem; font-family: 'Outfit', sans-serif;">₹{data['total_payment']:,.2f}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.divider()
    
    # Amortization charts and schedule table
    schedule = generate_repayment_schedule(
        data["loan_amount"],
        data["interest_rate"],
        data["tenure"]
    )

    show_charts(
        data["loan_amount"],
        data["total_interest"],
        schedule
    )