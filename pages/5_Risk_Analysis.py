"""
====================================
Risk Analysis Page
====================================
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from components.page_shell import render_page_header
from components.theme import load_theme

from core.risk import analyze_financial_risk
from utils.state_manager import get_financial_data
from utils.auth_helper import require_login
from database.loan_history import save_loan

st.set_page_config(
    page_title="Risk Analysis | MSME Credit & Financial Risk Platform",
    layout="wide",
)

load_theme()

# Protect page and render custom sidebar navigation if authenticated
if require_login():
    render_page_header(
        "Risk Analysis",
        "Analyze loan affordability, credit standing, and view automated risk review metrics.",
    )

    # Load active profile data
    data = get_financial_data()

    st.info("Using baseline configuration data. Adjust values below to run analysis.")

    # User inputs form
    with st.container(border=True):
        col1, col2 = st.columns(2)

        with col1:
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
            tenure_years = st.slider(
                "Tenure (Years)",
                min_value=1,
                max_value=30,
                value=int(data["tenure"]),
            )

        with col2:
            monthly_income = st.number_input(
                "Monthly Income (INR)",
                min_value=10000,
                value=int(data["monthly_income"]),
                step=1000,
            )
            monthly_expenses = st.number_input(
                "Monthly Expenses (INR)",
                min_value=0,
                value=int(data.get("monthly_expenses", 25000.0)),
                step=1000,
            )
            credit_score = st.slider(
                "Credit Score",
                min_value=300,
                max_value=900,
                value=int(data.get("credit_score", 760)),
            )

        run_btn = st.button("Analyze & Save Result", type="primary", use_container_width=True)

    # Calculate results
    analysis = analyze_financial_risk(
        loan_amount=loan_amount,
        interest_rate=interest_rate,
        tenure_years=tenure_years,
        monthly_income=monthly_income,
        monthly_expenses=monthly_expenses,
        credit_score=credit_score,
    )

    if run_btn:
        # Save to SQLite
        from core.emi import calculate_emi
        emi = calculate_emi(loan_amount, interest_rate, tenure_years)
        payment = round(emi * tenure_years * 12, 2)
        interest = round(payment - loan_amount, 2)
        
        save_loan(st.session_state.user_id, {
            "loan_amount": loan_amount,
            "interest_rate": interest_rate,
            "tenure": tenure_years,
            "monthly_income": monthly_income,
            "monthly_emi": emi,
            "total_interest": interest,
            "total_payment": payment,
            "risk_level": analysis["Risk Level"]
        })
        st.success("Risk analysis results successfully saved to database history.")

    st.divider()
    st.subheader("Risk Assessment Results")

    # Grid for results
    col_r1, col_r2, col_r3, col_r4 = st.columns(4)
    with col_r1:
        with st.container(border=True):
            st.metric("Risk Level", analysis["Risk Level"])
    with col_r2:
        with st.container(border=True):
            st.metric("Financial Health Score", f"{analysis['Financial Health %']}%")
    with col_r3:
        with st.container(border=True):
            st.metric("Credit Score", analysis["Credit Score"])
    with col_r4:
        with st.container(border=True):
            st.metric("Approval Status", analysis["Approval Status"])

    st.write("")
    st.write("Financial Health Index:")
    st.progress(analysis["Financial Health %"] / 100.0)

    # Recommendation - Emojis removed
    st.write("")
    col_rec, col_cred = st.columns([2, 1])
    
    with col_rec:
        with st.container(border=True):
            st.subheader("Financial Recommendation")
            st.write(analysis["Recommendation"])
            st.metric("Estimated Savings Buffer (Annual)", f"INR {analysis['Estimated Savings']:,.2f}")

    with col_cred:
        with st.container(border=True):
            st.subheader("Credit Standing")
            st.metric("Credit Score", analysis["Credit Score"])
            st.metric("Status", analysis["Credit Status"])
            
    st.write("---")
    if analysis["Approval Status"] == "Approved":
        st.info("Financial Risk Profile is healthy. Your loan affordability metrics are strongly within green levels.")
    elif analysis["Approval Status"] == "Review Required":
        st.warning("Warning: Moderate credit risk or border-line budget buffer detected. Recommend reducing loan amount or extending tenure.")
    else:
        st.error("High Risk Profile: Loan application declined by safety criteria. EMI exceeds net disposable income or credit score is too low.")