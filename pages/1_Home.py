from pathlib import Path
import sys
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ======================================
# IMPORTS
# ======================================
from components.ai_card import show_ai_card
from components.footer import show_footer
from components.theme import load_theme
from utils.state_manager import get_financial_data
from utils.auth_helper import require_login
from database.loan_history import get_user_loans, get_latest_loan

# ======================================
# PAGE CONFIG
# ======================================
st.set_page_config(
    page_title="Dashboard | MSME Credit & Financial Risk Platform",
    layout="wide",
)

load_theme()

# Require Login and render sidebar
if require_login():
    username = st.session_state.username
    user_id = st.session_state.user_id
    
    # ======================================
    # HERO SECTION
    # ======================================
    st.markdown(
        """
        <div class="app-hero">
            <h1 style="font-size: 2.5rem; margin: 0; font-family: 'Outfit', sans-serif;">MSME Credit & Financial Risk Platform</h1>
            <p class="app-hero__copy" style="font-size: 1.1rem; margin-top: 0.5rem; margin-bottom: 1.5rem;">AI-powered business profiling, loan planning and financial risk insights</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # CTA Buttons Row
    cta_col1, cta_col2, cta_col3, _ = st.columns([1, 1, 1.4, 2.6])
    with cta_col1:
        st.page_link("pages/2_EMI_Calculator.py", label="Calculate EMI", use_container_width=True)
    with cta_col2:
        st.page_link("pages/8_History.py", label="View History", use_container_width=True)
    with cta_col3:
        st.page_link("pages/9_Business_Profile.py", label="Business Profiles", use_container_width=True)

    st.page_link("pages/10_Financial_Records.py", label="Record Monthly Business Finances", use_container_width=True)
    st.page_link("pages/11_Financial_Health.py", label="Analyze MSME Financial Health", use_container_width=True)
    st.page_link("pages/12_Resilience_Twin.py", label="Open Financial Resilience Twin", use_container_width=True)

    st.write("")
    st.write("")

    # ======================================
    # FEATURE CARDS
    # ======================================
    st.subheader("MSME Platform Capabilities")
    feat_col1, feat_col2, feat_col3, feat_col4 = st.columns(4)
    with feat_col1:
        with st.container(border=True):
            st.markdown("**MSME Loan Planning**")
            st.caption("Plan loan repayments with EMI calculations and amortization schedules.")
    with feat_col2:
        with st.container(border=True):
            st.markdown("**Credit & Risk Review**")
            st.caption("Review loan affordability indicators. Results are decision-support, not lender approval.")
    with feat_col3:
        with st.container(border=True):
            st.markdown("**AI Financial Guidance**")
            st.caption("Get AI-assisted explanations and general financial planning guidance.")
    with feat_col4:
        with st.container(border=True):
            st.markdown("**Business Profile Management**")
            st.caption("Create and manage multiple MSME business profiles under your account.")
    with st.container(border=True):
        st.markdown("**Monthly Financial Records**")
        st.caption("Capture revenue, direct costs, operating expenses, owner drawings and existing debt payments by month.")

    st.divider()

    # Welcome header
    st.markdown(f"<h2 style='margin-bottom: 0.25rem;'>Welcome back, {username}</h2>", unsafe_allow_html=True)
    st.caption("Your active financial summary and advisor overview is loaded below.")
    st.write("")

    # Load active profile data (SQLite latest, fallback to state manager default)
    latest_loan = get_latest_loan(user_id)
    active_data = get_financial_data()
    
    if latest_loan:
        loan_amount = latest_loan["loan_amount"]
        interest_rate = latest_loan["interest_rate"]
        tenure = latest_loan["tenure"]
        monthly_income = latest_loan["monthly_income"]
        monthly_emi = latest_loan["monthly_emi"]
        total_interest = latest_loan["total_interest"]
        total_payment = latest_loan["total_payment"]
        risk_level = latest_loan["risk_level"]
    else:
        loan_amount = active_data["loan_amount"]
        interest_rate = active_data["interest_rate"]
        tenure = active_data["tenure"]
        monthly_income = active_data["monthly_income"]
        monthly_emi = active_data["monthly_emi"]
        total_interest = active_data["total_interest"]
        total_payment = active_data["total_payment"]
        risk_level = active_data["risk_level"]

    # ======================================
    # FINANCIAL DASHBOARD PREVIEW CARDS
    # ======================================
    st.subheader("Existing EMI Planning Snapshot")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        with st.container(border=True):
            st.metric("Total Loan", f"₹{loan_amount:,.2f}")
    with col2:
        with st.container(border=True):
            st.metric("Monthly EMI", f"₹{monthly_emi:,.2f}")
    with col3:
        with st.container(border=True):
            st.metric("Interest Rate", f"{interest_rate}%")
    with col4:
        with st.container(border=True):
            st.metric("Risk Status", risk_level)

    # ======================================
    # FINANCIAL SUMMARY DETAILS
    # ======================================
    st.subheader("Financial Summary Details")
    with st.container(border=True):
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            st.write("**Principal Amount:**")
            st.write(f"₹{loan_amount:,.2f}")
        with sc2:
            st.write("**Interest Payable:**")
            st.write(f"₹{total_interest:,.2f}")
        with sc3:
            st.write("**Total Repayment:**")
            st.write(f"₹{total_payment:,.2f}")

    st.divider()

    col_left, col_right = st.columns([3, 2])

    with col_left:
        # ======================================
        # RECENT SQLITE CALCULATIONS
        # ======================================
        st.subheader("Recent Calculations")
        user_loans_df = get_user_loans(user_id)
        if not user_loans_df.empty:
            recent_df = user_loans_df.head(5)[
                ["loan_amount", "interest_rate", "tenure", "monthly_emi", "risk_level", "created_at"]
            ].copy()
            recent_df.columns = ["Loan Amount (₹)", "Rate (%)", "Tenure (Yrs)", "Monthly EMI (₹)", "Risk Level", "Date"]
            st.dataframe(recent_df, use_container_width=True, hide_index=True)
        else:
            st.info("No calculations stored yet. Use the EMI Calculator to get started!")

        st.divider()
        # Clean quick actions
        st.subheader("Quick Navigation Actions")
        qa_col1, qa_col2 = st.columns(2)
        with qa_col1:
            st.page_link("pages/3_Repayment.py", label="Detailed Repayment Schedule", use_container_width=True)
        with qa_col2:
            st.page_link("pages/4_Comparison.py", label="Compare Bank Offers", use_container_width=True)

    with col_right:
        # ======================================
        # AI CARD
        # ======================================
        show_ai_card()

    show_footer()