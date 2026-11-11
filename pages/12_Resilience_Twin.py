from pathlib import Path
import sys

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from components.theme import load_theme
from core.resilience_twin import simulate_resilience
from database.business_profiles import get_user_business_profiles
from database.financial_records import get_business_financial_records
from database.models import create_tables
from utils.auth_helper import require_login


st.set_page_config(
    page_title="MSME Financial Resilience Twin",
    layout="wide",
)
load_theme()
create_tables()

if require_login():
    user_id = st.session_state.user_id
    st.title("MSME Financial Resilience Twin")
    st.caption(
        "Stress-test one recorded business month. Change assumptions and see "
        "how monthly cash headroom responds."
    )

    businesses = get_user_business_profiles(user_id)
    if not businesses:
        st.warning("Create a business profile before running a resilience simulation.")
        st.page_link("pages/9_Business_Profile.py", label="Create Business Profile")
        st.stop()

    business_options = {
        f"{b['business_name']} — {b['city']}, {b['state']}": b["id"]
        for b in businesses
    }
    selected = st.selectbox("Select business", list(business_options))
    records = get_business_financial_records(user_id, business_options[selected])
    if not records:
        st.info("Add at least one month of actual financial figures first.")
        st.page_link("pages/10_Financial_Records.py", label="Add Monthly Financial Records")
        st.stop()

    latest = records[0]
    st.subheader(f"Baseline: {latest['period_month']}")
    st.caption("The baseline uses your latest saved month. Scenario changes are temporary and do not alter your records.")

    left, right = st.columns(2)
    with left:
        revenue_drop = st.slider(
            "Sales / revenue reduction (%)", 0, 100, 0, 1,
            help="Percentage reduction in sales compared with the recorded month.",
        )
        delayed_receipts = st.slider(
            "Sales receipts delayed beyond this month (%)", 0, 100, 0, 1,
            help="Share of remaining sales not collected within this reporting month.",
        )
    with right:
        cost_increase = st.slider(
            "Direct and operating cost increase (%)", 0, 100, 0, 1,
            help="Uniform increase applied to direct costs and operating expenses.",
        )
        proposed_emi = st.number_input(
            "Proposed additional monthly EMI (₹)",
            min_value=0.0,
            value=0.0,
            step=500.0,
        )

    try:
        result = simulate_resilience(
            latest,
            revenue_drop_percent=revenue_drop,
            cost_increase_percent=cost_increase,
            delayed_receipts_percent=delayed_receipts,
            proposed_new_emi=proposed_emi,
        )
    except ValueError as exc:
        st.error(str(exc))
        st.stop()

    st.divider()
    st.subheader("Scenario result")
    a, b, c = st.columns(3)
    a.metric("Baseline cash headroom", f"₹{result['base_cash_headroom']:,.0f}")
    b.metric(
        "Stressed cash headroom",
        f"₹{result['stressed_headroom']:,.0f}",
        delta=f"₹{result['stressed_headroom'] - result['base_cash_headroom']:,.0f} vs baseline",
        delta_color="normal",
    )
    c.metric("Additional EMI headroom", f"₹{result['additional_emi_headroom']:,.0f}")

    if result["is_stressed_headroom_negative"]:
        st.error("Under this scenario, monthly cash headroom becomes negative.")
    else:
        st.success("Under this scenario, monthly cash headroom remains non-negative.")

    st.subheader("What changed?")
    d1, d2 = st.columns(2)
    d1.metric("Sales collected in this month", f"₹{result['stressed_sales_collected']:,.0f}")
    d2.metric("Stressed direct + operating costs", f"₹{result['stressed_costs']:,.0f}")

    st.subheader("Reverse stress test")
    threshold = result["revenue_break_even_drop_percent"]
    if threshold is None:
        st.info(result["break_even_note"])
    else:
        st.metric("Sales reduction at zero headroom", f"{threshold:.2f}%")
        st.caption(result["break_even_note"])

    st.caption(
        "This threshold holds the selected cost increase, delayed-receipt percentage, "
        "owner drawings, existing debt and proposed EMI constant. It is not a probability."
    )

    with st.expander("Calculation assumptions and limitations"):
        st.write(
            "Stressed sales collected = recorded sales × (1 − revenue reduction) "
            "× (1 − delayed receipts)."
        )
        st.write(
            "Stressed costs = (direct costs + operating expenses) × "
            "(1 + cost increase)."
        )
        st.write(
            "Stressed cash headroom = stressed sales collected + other income − "
            "stressed costs − owner drawings − existing debt payments − proposed EMI."
        )
        st.write(result["limitations"])
