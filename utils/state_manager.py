"""
==========================================
State Manager
AI Powered EMI Planner
Global Session Handler
==========================================
"""

import streamlit as st

# ---------------------------------------
# Initialize Global Session State
# ---------------------------------------

def init_state():
    if not st.runtime.exists():
        return

    defaults = {
        # Loan Details
        "loan_amount": 500000.0,
        "interest_rate": 8.5,
        "tenure": 5,

        # User Financial Details
        "monthly_income": 60000.0,
        "monthly_expenses": 25000.0,
        "credit_score": 760,

        # EMI Results
        "monthly_emi": 10258.27,
        "total_interest": 115496.20,
        "total_payment": 615496.20,

        # Risk Results
        "risk_level": "Low",
        "financial_health": 92,

        # AI Insights
        "recommendation": "Your financial profile is strong. The EMI is well within your disposable income, and you have a solid credit history.",
        "approval_status": "Approved",
        "estimated_savings": 48000.0,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ---------------------------------------
# Save EMI Calculator Data
# ---------------------------------------

def save_emi_data(
        loan_amount,
        interest_rate,
        tenure,
        income=60000.0,
        emi=0.0,
        interest=0.0,
        payment=0.0
):
    if not st.runtime.exists():
        return

    init_state()

    st.session_state.loan_amount = float(loan_amount)
    st.session_state.interest_rate = float(interest_rate)
    st.session_state.tenure = int(tenure)
    st.session_state.monthly_income = float(income)
    st.session_state.monthly_emi = float(emi)
    st.session_state.total_interest = float(interest)
    st.session_state.total_payment = float(payment)


# ---------------------------------------
# Save Risk Analysis Data
# ---------------------------------------

def save_risk_data(
        risk=None,
        risk_level=None,
        health=None,
        financial_health=None,
        recommendation=None,
        savings=None,
        estimated_savings=None,
        score=None,
        credit_score=None,
        approval_status=None,
        status=None,
        monthly_expenses=None,
        loan_amount=None,
        interest_rate=None,
        tenure=None,
        monthly_income=None,
        **kwargs
):
    if not st.runtime.exists():
        return

    init_state()

    # Normalize arguments to support both legacy and new names
    final_risk = risk_level or risk or kwargs.get("risk_level") or kwargs.get("risk") or st.session_state.risk_level
    final_health = financial_health or health or kwargs.get("financial_health") or kwargs.get("health") or st.session_state.financial_health
    final_recommendation = recommendation or kwargs.get("recommendation") or st.session_state.recommendation
    final_approval_status = approval_status or status or kwargs.get("approval_status") or kwargs.get("status") or st.session_state.approval_status
    final_savings = estimated_savings or savings or kwargs.get("estimated_savings") or kwargs.get("savings") or st.session_state.estimated_savings
    final_score = credit_score or score or kwargs.get("credit_score") or kwargs.get("score") or st.session_state.credit_score

    # Save outputs
    st.session_state.risk_level = str(final_risk)
    st.session_state.financial_health = int(final_health)
    st.session_state.recommendation = str(final_recommendation)
    st.session_state.approval_status = str(final_approval_status)
    st.session_state.estimated_savings = float(final_savings)
    st.session_state.credit_score = int(final_score)

    # Save updated inputs if provided
    if monthly_expenses is not None:
        st.session_state.monthly_expenses = float(monthly_expenses)
    if loan_amount is not None:
        st.session_state.loan_amount = float(loan_amount)
    if interest_rate is not None:
        st.session_state.interest_rate = float(interest_rate)
    if tenure is not None:
        st.session_state.tenure = int(tenure)
    if monthly_income is not None:
        st.session_state.monthly_income = float(monthly_income)


# ---------------------------------------
# Get All Financial Data
# ---------------------------------------

def get_financial_data():
    if not st.runtime.exists():
        return {
            "loan_amount": 500000.0,
            "interest_rate": 8.5,
            "tenure": 5,
            "monthly_income": 60000.0,
            "monthly_expenses": 25000.0,
            "credit_score": 760,
            "monthly_emi": 10258.27,
            "total_interest": 115496.20,
            "total_payment": 615496.20,
            "risk_level": "Low",
            "financial_health": 92,
            "recommendation": "Your financial profile is strong. The EMI is well within your disposable income, and you have a solid credit history.",
            "approval_status": "Approved",
            "estimated_savings": 48000.0,
        }

    init_state()

    return {
        "loan_amount": st.session_state.loan_amount,
        "interest_rate": st.session_state.interest_rate,
        "tenure": st.session_state.tenure,
        "monthly_income": st.session_state.monthly_income,
        "monthly_expenses": st.session_state.monthly_expenses,
        "credit_score": st.session_state.credit_score,
        "monthly_emi": st.session_state.monthly_emi,
        "total_interest": st.session_state.total_interest,
        "total_payment": st.session_state.total_payment,
        "risk_level": st.session_state.risk_level,
        "financial_health": st.session_state.financial_health,
        "recommendation": st.session_state.recommendation,
        "approval_status": st.session_state.approval_status,
        "estimated_savings": st.session_state.estimated_savings,
    }