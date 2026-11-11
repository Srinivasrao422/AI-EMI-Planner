from pathlib import Path
import sys

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from components.theme import load_theme
from core.cash_flow import build_cash_flow_projection
from database.business_profiles import get_user_business_profiles
from database.financial_records import get_business_financial_records
from utils.auth_helper import require_login


st.set_page_config(
    page_title="MSME Cash Flow Outlook | MSME Credit & Financial Risk Platform",
    layout="wide",
)
load_theme()

if require_login():
    user_id = st.session_state.user_id
    st.title("MSME Cash Flow Outlook")
    st.caption(
        "Explore a short-term planning scenario using your latest three recorded "
        "months. Actual records are never changed."
    )

    businesses = get_user_business_profiles(user_id)
    if not businesses:
        st.info("Create a business profile before preparing a cash-flow outlook.")
        st.page_link("pages/9_Business_Profile.py", label="Create business profile")
        st.stop()

    options = {
        f"{item['business_name']} — {item['city']}, {item['state']}": item["id"]
        for item in businesses
    }
    selected = st.selectbox("Select business", list(options))
    records = get_business_financial_records(user_id, options[selected])

    if len(records) < 3:
        st.warning(
            f"You have {len(records)} recorded month(s). Add at least "
            f"{3 - len(records)} more distinct month(s) to unlock this outlook."
        )
        st.page_link(
            "pages/10_Financial_Records.py",
            label="Add monthly financial records",
        )
        st.stop()

    st.subheader("Planning assumptions")
    st.caption(
        "These are user-controlled what-if assumptions, not AI-generated estimates."
    )
    left, right = st.columns(2)
    with left:
        horizon = st.selectbox("Projection horizon", [3, 4, 5, 6], index=0)
        revenue_change = st.slider(
            "Monthly sales change (%)", -20, 20, 0, 1,
            help="A constant monthly increase or decrease applied to sales.",
        )
        delayed_sales = st.slider(
            "Sales not collected within the month (%)", 0, 100, 0, 1,
            help="A simplified collection-delay assumption applied to projected sales.",
        )
    with right:
        cost_change = st.slider(
            "Monthly direct and operating cost change (%)", -20, 20, 0, 1,
            help="A constant monthly increase or decrease applied to direct and operating costs.",
        )
        additional_emi = st.number_input(
            "Additional monthly EMI (₹)",
            min_value=0.0,
            value=0.0,
            step=500.0,
        )

    try:
        result = build_cash_flow_projection(
            records,
            months=horizon,
            monthly_revenue_change_percent=revenue_change,
            monthly_cost_increase_percent=cost_change,
            delayed_sales_percent=delayed_sales,
            additional_monthly_emi=additional_emi,
        )
    except ValueError as error:
        st.error(str(error))
        st.stop()

    st.divider()
    st.subheader("Projection overview")
    st.caption(
        "Baseline averages use these saved months: "
        + ", ".join(month for month in result["baseline_months"] if month)
    )

    projected = result["projections"]
    first, last = projected[0], projected[-1]
    c1, c2, c3 = st.columns(3)
    c1.metric("Month 1 cash headroom", f"₹{first['cash_headroom']:,.0f}")
    c2.metric(f"Month {horizon} cash headroom", f"₹{last['cash_headroom']:,.0f}")
    c3.metric("Months with negative headroom", f"{len(result['negative_months'])} / {horizon}")

    chart_data = pd.DataFrame(
        {
            "Projected collections": [row["total_collections"] for row in projected],
            "Projected outflows": [row["total_outflows"] for row in projected],
            "Cash headroom": [row["cash_headroom"] for row in projected],
        },
        index=[f"Month {row['month_number']}" for row in projected],
    )
    st.subheader("Projected monthly cash movement")
    st.line_chart(chart_data, use_container_width=True)

    if result["negative_months"]:
        month_labels = ", ".join(f"Month {month}" for month in result["negative_months"])
        st.error(
            f"Projected cash headroom is negative in: {month_labels}. "
            "Review the assumptions and underlying records."
        )
    else:
        st.success("Cash headroom remains non-negative in all selected planning months.")

    st.subheader("Month-by-month breakdown")
    display_rows = []
    for row in projected:
        display_rows.append({
            "Period": f"Month {row['month_number']}",
            "Sales collected": row["sales_collected"],
            "Other income": row["other_income"],
            "Direct costs": row["direct_costs"],
            "Operating expenses": row["operating_expenses"],
            "Owner drawings": row["owner_drawings"],
            "Existing debt": row["existing_debt"],
            "Additional EMI": row["additional_emi"],
            "Cash headroom": row["cash_headroom"],
        })
    st.dataframe(
        pd.DataFrame(display_rows),
        use_container_width=True,
        hide_index=True,
    )

    with st.expander("How this outlook is calculated"):
        st.write(
            "The engine averages revenue, other income, direct costs, operating "
            "expenses, owner drawings and existing debt service across the three "
            "latest saved months. It then applies the assumptions you selected "
            "month by month."
        )
        st.write(result["limitations"])

    st.caption(
        "Planning aid only. This is not an AI prediction, audited cash-flow forecast, "
        "credit score, default probability or lender decision."
    )
