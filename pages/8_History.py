"""
==========================================
Loan History Page
==========================================
"""

from pathlib import Path
import sys
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from components.page_shell import render_page_header
from components.theme import load_theme
from utils.auth_helper import require_login
from database.loan_history import get_user_loans, delete_loan

st.set_page_config(
    page_title="Loan History | AI Powered EMI Planner",
    layout="wide",
)

load_theme()

# Protect page and render custom sidebar navigation if authenticated
if require_login():
    render_page_header(
        "Loan History",
        "View historical calculation records, remove entries, and check amortization history.",
    )

    user_id = st.session_state.user_id
    history_df = get_user_loans(user_id)

    if history_df.empty:
        st.info("No calculations stored yet. Use the EMI Calculator to calculate and save some loans!")
    else:
        st.divider()

        # Display history records
        st.subheader("Previous Calculations")
        
        display_df = history_df[
            ["id", "created_at", "loan_amount", "monthly_emi", "total_interest", "risk_level"]
        ].copy()
        
        display_df.columns = ["Record ID", "Date", "Loan Amount (₹)", "Monthly EMI (₹)", "Total Interest (₹)", "Risk Level"]
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Deletion Section
        st.subheader("Manage Records")
        with st.container(border=True):
            col_sel, col_btn = st.columns([3, 1])
            with col_sel:
                delete_id = st.selectbox(
                    "Select Record ID to delete",
                    options=display_df["Record ID"].tolist(),
                    key="delete_loan_select"
                )
            with col_btn:
                st.write("") # Spacing
                st.write("")
                if st.button("Delete Record", type="secondary", use_container_width=True):
                    success = delete_loan(delete_id)
                    if success:
                        st.success(f"Record {delete_id} successfully deleted.")
                        st.rerun()
                    else:
                        st.error("Failed to delete the record. Please try again.")

        st.divider()

        # Visual Graphs
        st.subheader("Historical Analytics")
        
        chart_df = history_df.copy()
        chart_df["created_at"] = pd.to_datetime(chart_df["created_at"])
        chart_df = chart_df.sort_values("created_at")

        tab_amount, tab_emi = st.tabs(["Loan Amount Trend", "EMI History"])
        
        with tab_amount:
            st.write("Loan Amount Over Time")
            line_data = chart_df.set_index("created_at")[["loan_amount"]]
            line_data.index = line_data.index.strftime('%Y-%m-%d %H:%M')
            st.line_chart(line_data, use_container_width=True)

        with tab_emi:
            st.write("EMI Calculations History")
            bar_data = chart_df.set_index("created_at")[["monthly_emi"]]
            bar_data.index = bar_data.index.strftime('%Y-%m-%d %H:%M')
            st.bar_chart(bar_data, use_container_width=True)
