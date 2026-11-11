from pathlib import Path
import sys
from datetime import date

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from components.theme import load_theme
from database.models import create_tables
from database.business_profiles import get_user_business_profiles
from database.financial_records import (
    calculate_monthly_summary,
    get_business_financial_records,
    save_business_financial_record,
)
from utils.auth_helper import require_login


st.set_page_config(
    page_title="MSME Financial Records | MSME Credit & Financial Risk Platform",
    layout="wide",
)
load_theme()
create_tables()

if require_login():
    user_id = st.session_state.user_id
    st.title("MSME Financial Records")
    st.caption(
        "Record actual monthly business income, operating costs and debt payments. "
        "These figures power the financial health and resilience analysis."
    )

    businesses = get_user_business_profiles(user_id)
    if not businesses:
        st.warning("Create a business profile before adding financial records.")
        st.page_link("pages/9_Business_Profile.py", label="Open Business Profiles")
        st.stop()

    business_options = {
        f"{item['business_name']} — {item['city']}, {item['state']}": item["id"]
        for item in businesses
    }
    selected_label = st.selectbox("Select business", list(business_options))
    business_id = business_options[selected_label]

    st.subheader("Add or update monthly figures")
    with st.form("monthly_financial_record"):
        period_month = st.text_input(
            "Reporting month (YYYY-MM)",
            value=date.today().strftime("%Y-%m"),
            help="Enter the month whose actual figures you are recording.",
        )
        left, right = st.columns(2)
        with left:
            revenue = st.number_input("Sales / business revenue (₹)", min_value=0.0, step=1000.0)
            other_income = st.number_input("Other business income (₹)", min_value=0.0, step=500.0)
            cost_of_goods_sold = st.number_input("Cost of goods / direct costs (₹)", min_value=0.0, step=1000.0)
        with right:
            operating_expenses = st.number_input("Operating expenses (₹)", min_value=0.0, step=1000.0)
            owner_drawings = st.number_input("Owner drawings (₹)", min_value=0.0, step=500.0)
            existing_debt_service = st.number_input("Existing monthly loan payments (₹)", min_value=0.0, step=500.0)
        notes = st.text_area("Notes (optional)", max_chars=1000)
        submitted = st.form_submit_button("Save Monthly Record", type="primary", use_container_width=True)

    if submitted:
        try:
            save_business_financial_record(
                user_id,
                business_id,
                {
                    "period_month": period_month,
                    "revenue": revenue,
                    "other_income": other_income,
                    "cost_of_goods_sold": cost_of_goods_sold,
                    "operating_expenses": operating_expenses,
                    "owner_drawings": owner_drawings,
                    "existing_debt_service": existing_debt_service,
                    "notes": notes,
                },
            )
            st.success("Monthly financial record saved.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))

    records = get_business_financial_records(user_id, business_id)
    st.divider()
    st.subheader("Recorded financial history")
    if not records:
        st.info("No monthly records yet. Add your first reporting month above.")
    else:
        latest = records[0]
        summary = calculate_monthly_summary(latest)
        c1, c2, c3 = st.columns(3)
        c1.metric("Latest Month Revenue", f"₹{summary['total_income']:,.0f}")
        c2.metric("Operating Surplus", f"₹{summary['operating_surplus']:,.0f}")
        c3.metric("Cash Headroom", f"₹{summary['cash_headroom']:,.0f}")
        st.caption(
            "Cash headroom = revenue + other income − direct costs − operating "
            "expenses − owner drawings − existing debt payments. This is a "
            "simplified monthly indicator, not audited profit or a lending decision."
        )

        table_rows = []
        for record in records:
            result = calculate_monthly_summary(record)
            table_rows.append({
                "Month": record["period_month"],
                "Revenue": record["revenue"],
                "Other income": record["other_income"],
                "Direct costs": record["cost_of_goods_sold"],
                "Operating expenses": record["operating_expenses"],
                "Owner drawings": record["owner_drawings"],
                "Existing debt": record["existing_debt_service"],
                "Operating surplus": result["operating_surplus"],
                "Cash headroom": result["cash_headroom"],
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
