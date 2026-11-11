from pathlib import Path
import sys

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from components.theme import load_theme
from database.models import create_tables
from database.business_profiles import get_user_business_profiles
from database.financial_records import get_business_financial_records
from core.financial_health import analyze_financial_health
from utils.auth_helper import require_login


st.set_page_config(
    page_title="Financial Health | MSME Credit & Financial Risk Platform",
    layout="wide",
)
load_theme()
create_tables()

if require_login():
    user_id = st.session_state.user_id
    st.title("MSME Financial Health Analysis")
    st.caption(
        "Transparent financial ratios calculated from your recorded monthly "
        "business figures. No synthetic scores or AI-generated numbers."
    )

    businesses = get_user_business_profiles(user_id)
    if not businesses:
        st.warning("Create a business profile before running financial analysis.")
        st.page_link("pages/9_Business_Profile.py", label="Create Business Profile")
        st.stop()

    options = {
        f"{b['business_name']} — {b['city']}, {b['state']}": b["id"]
        for b in businesses
    }
    selected = st.selectbox("Select business", list(options))
    business_id = options[selected]
    records = get_business_financial_records(user_id, business_id)

    if not records:
        st.info("No financial records found. Add at least one month of actual figures.")
        st.page_link("pages/10_Financial_Records.py", label="Add Monthly Financial Records")
        st.stop()

    try:
        result = analyze_financial_health(records)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()

    st.subheader(f"Analysis for {result['period_month']}")
    a, b, c = st.columns(3)
    a.metric("Total Income", f"₹{result['total_income']:,.2f}")
    b.metric("Operating Surplus", f"₹{result['operating_surplus']:,.2f}")
    c.metric("Cash Headroom", f"₹{result['cash_headroom']:,.2f}")

    st.caption(
        "Operating surplus = total income − direct costs − operating expenses. "
        "Cash headroom = operating surplus − owner drawings − existing debt payments."
    )
    st.divider()
    st.subheader("Financial indicators")
    display_rows = []
    for item in result["indicators"]:
        value = item["value"]
        formatted = "Not available" if value is None else (
            f"{value:,.2f}{item['unit']}"
        )
        display_rows.append({
            "Indicator": item["name"],
            "Value": formatted,
            "Interpretation": item["status"],
            "What it measures": item["description"],
        })
    st.dataframe(pd.DataFrame(display_rows), use_container_width=True, hide_index=True)

    st.subheader("Observations")
    for observation in result["observations"]:
        st.write(f"• {observation}")

    if result["revenue_trend"] is not None:
        trend = result["revenue_trend"]
        change = trend["revenue_change_percent"]
        st.subheader("Revenue movement")
        st.metric(
            f"{trend['current_month']} vs {trend['previous_month']}",
            f"{change:+.2f}%",
            help="Change in recorded sales revenue between the latest two available months.",
        )
    elif len(records) >= 2:
        st.info("Revenue change is not calculated because the previous month's revenue is zero.")

    with st.expander("Scope and limitations"):
        st.write(result["limitations"])
        st.write(
            "Debt service coverage proxy = operating surplus ÷ existing debt service. "
            "It is deliberately labelled a proxy because the current data model does "
            "not capture all formal DSCR adjustments."
        )

    st.caption(f"Months of data available: {result['records_analyzed']}")
