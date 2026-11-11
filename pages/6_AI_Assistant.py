"""Grounded MSME and loan-planning assistant.

The model explains user-entered figures; it does not calculate or invent credit scores.
"""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from components.theme import load_theme
from core.ai_engine import ask_ai_advisor, get_groq_client
from core.financial_health import analyze_financial_health
from database.business_profiles import get_user_business_profiles
from database.financial_records import get_business_financial_records
from database.loan_history import get_latest_loan
from utils.auth_helper import require_login


st.set_page_config(
    page_title="AI Financial Assistant | MSME Credit & Financial Risk Platform",
    layout="wide",
)
load_theme()

if require_login():
    st.title("MSME Financial Assistant")
    st.caption(
        "Ask questions about your saved business records and loan calculations. "
        "Answers are explanations, not lender decisions."
    )

    user_id = st.session_state.user_id
    profiles = get_user_business_profiles(user_id)
    latest_loan = get_latest_loan(user_id)

    data = {
        "loan_amount": None,
        "interest_rate": None,
        "tenure": None,
        "monthly_income": None,
        "monthly_emi": None,
        "total_interest": None,
        "total_payment": None,
        "risk_level": "Not assessed",
        "credit_score": None,
        "financial_health": None,
        "approval_status": "Not assessed",
    }

    if latest_loan:
        data.update({
            "loan_amount": latest_loan.get("loan_amount"),
            "interest_rate": latest_loan.get("interest_rate"),
            "tenure": latest_loan.get("tenure"),
            "monthly_income": latest_loan.get("monthly_income"),
            "monthly_emi": latest_loan.get("monthly_emi"),
            "total_interest": latest_loan.get("total_interest"),
            "total_payment": latest_loan.get("total_payment"),
            "risk_level": latest_loan.get("risk_level") or "Not assessed",
        })

    if profiles:
        business_options = {
            f"{item['business_name']} — {item['city']}, {item['state']}": item["id"]
            for item in profiles
        }
        selected_business = st.selectbox(
            "Business context",
            list(business_options),
            help="The assistant will use saved figures for this business only.",
        )
        selected_id = business_options[selected_business]
        profile = next(item for item in profiles if item["id"] == selected_id)
        records = get_business_financial_records(user_id, selected_id)

        data["msme_context"] = {
            "business_name": profile["business_name"],
            "business_type": profile["business_type"],
            "industry": profile["industry"],
            "location": f"{profile['city']}, {profile['state']}, {profile['country']}",
            "reporting_months": [
                {
                    "period_month": row["period_month"],
                    "revenue": row["revenue"],
                    "other_income": row["other_income"],
                    "cost_of_goods_sold": row["cost_of_goods_sold"],
                    "operating_expenses": row["operating_expenses"],
                    "owner_drawings": row["owner_drawings"],
                    "existing_debt_service": row["existing_debt_service"],
                }
                for row in records[:3]
            ],
        }

        if records:
            health = analyze_financial_health(records)
            data["msme_context"]["latest_analysis"] = {
                "period_month": health["period_month"],
                "total_income": health["total_income"],
                "gross_profit": health["gross_profit"],
                "operating_surplus": health["operating_surplus"],
                "cash_headroom": health["cash_headroom"],
                "observations": health["observations"],
            }
            st.subheader(f"Context available · {profile['business_name']}")
            cols = st.columns(4)
            cols[0].metric("Reporting months", len(records))
            cols[1].metric("Latest month", health["period_month"])
            cols[2].metric("Operating surplus", f"₹{health['operating_surplus']:,.0f}")
            cols[3].metric("Cash headroom", f"₹{health['cash_headroom']:,.0f}")
        else:
            st.info("No monthly financial records exist for this business yet. The assistant will not assume business figures.")
    else:
        data["msme_context"] = None
        st.info("Create a business profile and add monthly records to enable business-specific explanations.")

    if latest_loan:
        with st.expander("Latest saved loan calculation"):
            st.write({
                "Loan amount (₹)": latest_loan.get("loan_amount"),
                "Interest rate (%)": latest_loan.get("interest_rate"),
                "Tenure (years)": latest_loan.get("tenure"),
                "Monthly EMI (₹)": latest_loan.get("monthly_emi"),
                "Total interest (₹)": latest_loan.get("total_interest"),
                "Total payment (₹)": latest_loan.get("total_payment"),
            })
    else:
        st.caption("No saved loan calculation is available; loan-specific answers will be limited.")

    st.divider()
    if not get_groq_client():
        st.warning("Groq API key is not configured. Add GROQ_API_KEY to your local .env file to enable chat.")
    else:
        if "messages" not in st.session_state:
            st.session_state.messages = [{
                "role": "assistant",
                "content": (
                    "I can explain your saved business figures, cash headroom, "
                    "loan calculations and planning assumptions. I will identify "
                    "missing information rather than inventing values."
                ),
            }]

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if len(st.session_state.messages) == 1:
            st.caption("Suggested questions")
            suggestions = [
                "Explain my latest month's cash headroom.",
                "Which recorded cost categories should I review?",
                "What information is missing before I assess a new EMI?",
            ]
            cols = st.columns(3)
            for col, suggestion in zip(cols, suggestions):
                if col.button(suggestion, use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": suggestion})
                    st.rerun()

        prompt = st.chat_input("Ask about your recorded business finances or loan plan...")
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.rerun()

        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
            user_message = st.session_state.messages[-1]["content"]
            with st.chat_message("assistant"):
                with st.spinner("Preparing an explanation from your saved figures..."):
                    response = ask_ai_advisor(
                        financial_data=data,
                        user_message=user_message,
                        chat_history=st.session_state.messages[:-1],
                    )
                    st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()

    st.caption(
        "AI explanations can be incomplete. Verify important decisions against original "
        "records and qualified financial advice. This tool does not approve loans or predict defaults."
    )
