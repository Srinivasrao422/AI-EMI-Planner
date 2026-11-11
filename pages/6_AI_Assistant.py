"""
==========================================
AI Assistant Page
==========================================
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from components.page_shell import render_page_header
from components.theme import load_theme
from utils.state_manager import get_financial_data
from core.ai_engine import ask_ai_advisor, get_groq_client
from utils.auth_helper import require_login
from database.loan_history import get_latest_loan

st.set_page_config(
    page_title="AI Financial Assistant | MSME Credit & Financial Risk Platform",
    layout="wide",
)

load_theme()

# Protect page and render custom sidebar navigation if authenticated
if require_login():
    render_page_header(
        "AI Banking Assistant",
        "Consult our professional AI assistant regarding your loans, calculations, and financial recommendations.",
    )

    # Load user specific details (from SQLite latest, or state manager baseline)
    latest_loan = get_latest_loan(st.session_state.user_id)
    state_data = get_financial_data()

    if latest_loan:
        data = {
            "loan_amount": latest_loan["loan_amount"],
            "interest_rate": latest_loan["interest_rate"],
            "tenure": latest_loan["tenure"],
            "monthly_income": latest_loan["monthly_income"],
            "monthly_emi": latest_loan["monthly_emi"],
            "total_interest": latest_loan["total_interest"],
            "total_payment": latest_loan["total_payment"],
            "risk_level": latest_loan["risk_level"],
            "credit_score": state_data.get("credit_score", 760),
            "financial_health": state_data.get("financial_health", 92),
            "approval_status": state_data.get("approval_status", "Approved")
        }
    else:
        data = state_data

    # Active Profile Dashboard block
    st.subheader("Active Analysis Context")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Loan Amount", f"₹{data['loan_amount']:,.2f}")
    with col2:
        st.metric("Monthly EMI", f"₹{data['monthly_emi']:,.2f}")
    with col3:
        st.metric("Risk Status", data["risk_level"])
    with col4:
        st.metric("Approval Status", data["approval_status"])

    st.divider()

    # Check API key config
    client = get_groq_client()
    if not client:
        st.warning("Groq API key is missing or invalid. Please configure your `GROQ_API_KEY` in the `.env` file to enable the conversational AI Advisor.")
    else:
        st.subheader("Banking Advisor Chat")

        # Init chat history
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": (
                        f"Hello {st.session_state.username}, I am your AI Banking Advisor.\n\n"
                        "I have analyzed your active profile parameters. You can ask me about:\n"
                        "- Repayment optimizations and tenure buffers\n"
                        "- Risk status explanations\n"
                        "- General financial affordability indicators\n\n"
                        "How can I assist you with your financial planning today?"
                    )
                }
            ]

        # Render chat messages
        for message in st.session_state.messages:
            role_label = "User" if message["role"] == "user" else "Assistant"
            with st.chat_message(message["role"]):
                st.markdown(f"**{role_label}**")
                st.markdown(message["content"])

        # Suggested banking prompts - Emojis removed
        if len(st.session_state.messages) <= 1:
            st.write("**Suggested Prompts:**")
            s_col1, s_col2, s_col3 = st.columns(3)
            with s_col1:
                if st.button("How can I optimize my monthly EMI?", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": "How can I optimize my monthly EMI?"})
                    st.rerun()
            with s_col2:
                if st.button("Is my current risk status healthy?", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": "Is my current risk status healthy for my income?"})
                    st.rerun()
            with s_col3:
                if st.button("What repayment plan do you recommend?", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": "What interest saving repayment strategies do you recommend?"})
                    st.rerun()

        # Chat inputs
        prompt = st.chat_input("Ask a question about your financial planning...")
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.rerun()

        # Generate chatbot response
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
            user_msg = st.session_state.messages[-1]["content"]
            with st.chat_message("assistant"):
                st.markdown("**Assistant**")
                with st.spinner("Analyzing profile context..."):
                    response = ask_ai_advisor(
                        financial_data=data,
                        user_message=user_msg,
                        chat_history=st.session_state.messages[:-1]
                    )
                    st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()