"""
AI recommendation panel for home dashboard insights.
"""

import streamlit as st
from utils.state_manager import get_financial_data

def show_ai_card():
    """Render dynamic AI-style guidance using session state."""

    data = get_financial_data()

    st.subheader("AI Financial Insights 🤖")

    with st.container(border=True):
        risk_level = data.get("risk_level", "Low")
        financial_health = data.get("financial_health", 92)
        estimated_savings = data.get("estimated_savings", 48000.0)
        recommendation = data.get("recommendation", "Approved")
        approval_status = data.get("approval_status", "Approved")

        if approval_status == "Approved":
            st.success(f"✔️ Loan Approval Status: {approval_status}")
        elif approval_status == "Review Required":
            st.warning(f"⚠️ Loan Approval Status: {approval_status}")
        else:
            st.error(f"❌ Loan Approval Status: {approval_status}")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Risk Level", risk_level)
            st.metric("Financial Health Score", f"{financial_health}%")

        with col2:
            st.metric("Projected Savings (Annual)", f"INR {estimated_savings:,.2f}")
            st.metric("Recommendation", approval_status)

        st.divider()
        st.info("AI Analyst Recommendation Details")
        st.markdown(recommendation)

        st.page_link(
            "pages/6_AI_Assistant.py",
            label="💬 Chat with AI Advisor for more details",
            use_container_width=True
        )
