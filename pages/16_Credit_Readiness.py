from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st

from components.theme import load_theme
from core.msme_credit_assessment import assess_credit_readiness
from database.business_profiles import get_user_business_profiles
from database.financial_records import get_business_financial_records
from utils.auth_helper import require_login


st.set_page_config(page_title="MSME Credit Readiness Review", layout="wide")
load_theme()

if require_login():
    st.title("MSME Credit Readiness Review")
    st.caption(
        "An explainable review of recorded cash-flow capacity and evidence coverage. "
        "This is not a bureau score or lender approval."
    )
    user_id = st.session_state.user_id
    profiles = get_user_business_profiles(user_id)
    if not profiles:
        st.info("Create a business profile before starting a credit-readiness review.")
        st.page_link("pages/9_Business_Profile.py", label="Create business profile")
        st.stop()

    options = {
        f"{item['business_name']} — {item['city']}, {item['state']}": item["id"]
        for item in profiles
    }
    selected = st.selectbox("Select business", list(options))
    records = get_business_financial_records(user_id, options[selected])

    if len(records) < 3:
        st.warning(
            f"At least three consecutive monthly records are required. "
            f"Currently available: {len(records)}."
        )
        st.page_link("pages/10_Financial_Records.py", label="Add monthly financial records")
        st.stop()

    st.subheader("Proposed repayment scenario")
    proposed_emi = st.number_input(
        "Proposed additional monthly EMI (₹)",
        min_value=0.0,
        value=0.0,
        step=500.0,
        help="Enter the EMI you want to test. This does not submit a loan application.",
    )
    try:
        result = assess_credit_readiness(records, proposed_monthly_emi=proposed_emi)
    except ValueError as error:
        st.error(str(error))
        st.stop()

    st.divider()
    st.subheader("Review outcome")
    st.info(result["status"])
    a, b, c = st.columns(3)
    a.metric("Latest cash headroom", f"₹{result['latest_cash_headroom']:,.0f}")
    b.metric("Average headroom · 3 months", f"₹{result['average_three_month_headroom']:,.0f}")
    c.metric("Headroom after proposed EMI", f"₹{result['headroom_after_proposed_emi']:,.0f}")

    d, e, f = st.columns(3)
    d.metric("Positive-headroom months", f"{result['positive_headroom_months']} / 3")
    e.metric(
        "Coverage proxy",
        "Not calculated" if result["coverage_proxy"] is None else f"{result['coverage_proxy']:.2f}x",
    )
    e.caption("Operating surplus ÷ existing debt service plus proposed EMI.")
    f.metric(
        "Latest revenue movement",
        "Not available" if result["revenue_change_percent"] is None else f"{result['revenue_change_percent']:+.2f}%",
    )

    st.subheader("Explainable findings")
    for finding in result["findings"]:
        st.write(f"• {finding}")

    st.subheader("Evidence gaps")
    for gap in result["evidence_gaps"]:
        st.write(f"• {gap}")

    st.subheader("Reviewed reporting months")
    st.dataframe(
        pd.DataFrame([
            {
                "Month": row["period_month"],
                "Revenue": row["revenue"],
                "Operating surplus": row["operating_surplus"],
                "Cash headroom": row["cash_headroom"],
            }
            for row in [
                {
                    "period_month": item["period_month"],
                    "revenue": item["revenue"],
                    "operating_surplus": item["operating_surplus"],
                    "cash_headroom": item["cash_headroom"],
                }
                for item in [
                    {
                        "period_month": record["period_month"],
                        "revenue": float(record["revenue"]),
                        "operating_surplus": float(record["revenue"]) + float(record["other_income"]) - float(record["cost_of_goods_sold"]) - float(record["operating_expenses"]),
                        "cash_headroom": float(record["revenue"]) + float(record["other_income"]) - float(record["cost_of_goods_sold"]) - float(record["operating_expenses"]) - float(record["owner_drawings"]) - float(record["existing_debt_service"]),
                    }
                    for record in records[:3]
                ]
            ]
        ]),
        use_container_width=True,
        hide_index=True,
    )

    with st.expander("Methodology and limitations"):
        st.write(
            "The review checks latest-month cash headroom, consistency across the "
            "latest three months, proposed EMI impact and a simplified coverage proxy. "
            "No weighted or machine-generated credit score is produced."
        )
        st.write(result["limitations"])

    st.caption(
        "For planning and information only. Confirm records and consult a qualified "
        "financial professional or lender before making borrowing decisions."
    )
