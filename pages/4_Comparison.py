from pathlib import Path
import sys
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from components.page_shell import render_page_header
from components.theme import load_theme
from core.comparison import compare_loans
from utils.state_manager import get_financial_data
from utils.auth_helper import require_login

st.set_page_config(
    page_title="Loan Comparison | AI Powered EMI Planner",
    layout="wide",
)

load_theme()

# Protect page and render custom sidebar navigation if authenticated
if require_login():
    render_page_header(
        "Loan Comparison",
        "Compare different banks using your latest EMI calculation data.",
    )

    # ===================================
    # LOAD SESSION DATA
    # ===================================
    data = get_financial_data()
    base_amount = data["loan_amount"]
    base_tenure = data["tenure"]

    st.info("Using latest loan details from EMI Calculator.")

    # ===================================
    # BANK OFFERS
    # ===================================
    with st.container(border=True):
        st.caption("Modify bank offers and compare repayment options.")
        columns = st.columns(3)
        offers = []
        defaults = (
            ("SBI", 8.5),
            ("HDFC", 9.2),
            ("ICICI", 9.8),
        )

        for index, (bank, default_rate) in enumerate(defaults, start=1):
            with columns[index - 1]:
                st.subheader(f"Offer {index}")
                bank_name = st.text_input(
                    "Bank",
                    value=bank,
                    key=f"bank_{index}",
                )
                loan_amount = st.number_input(
                    "Loan Amount (INR)",
                    min_value=10000,
                    max_value=100000000,
                    value=int(base_amount),
                    step=10000,
                    key=f"amount_{index}",
                )
                interest_rate = st.slider(
                    "Interest Rate (%)",
                    min_value=1.0,
                    max_value=20.0,
                    value=float(default_rate),
                    step=0.1,
                    key=f"rate_{index}",
                )
                tenure_years = st.slider(
                    "Tenure (Years)",
                    min_value=1,
                    max_value=30,
                    value=int(base_tenure),
                    key=f"tenure_{index}",
                )

                offers.append(
                    {
                        "bank_name": bank_name.strip() or f"Offer {index}",
                        "loan_amount": loan_amount,
                        "interest_rate": interest_rate,
                        "tenure_years": tenure_years,
                    }
                )

    # ===================================
    # RESULT
    # ===================================
    comparison = compare_loans(offers)
    comparison_df = pd.DataFrame(comparison)

    st.divider()
    st.subheader("Comparison Results")
    st.dataframe(
        comparison_df,
        use_container_width=True,
        hide_index=True
    )

    # ===================================
    # BEST OFFER
    # ===================================
    best_offer = comparison_df.sort_values("Total Payment").iloc[0]
    st.success(
        f"{best_offer['Bank']} has the lowest projected payment: "
        f"INR {best_offer['Total Payment']:,.2f}"
    )