from pathlib import Path
import sys

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from components.theme import load_theme
from core.loan_optimizer import (
    analyze_repayment_capacity,
    compare_loan_scenarios,
    maximum_principal_for_emi,
)
from database.business_profiles import get_user_business_profiles
from database.financial_records import get_business_financial_records
from utils.auth_helper import require_login


st.set_page_config(
    page_title="MSME Loan Optimizer | MSME Credit & Financial Risk Platform",
    layout="wide",
)
load_theme()

if require_login():
    user_id = st.session_state.user_id
    st.title("MSME Loan Repayment Capacity & Optimizer")
    st.caption(
        "Estimate a planning EMI limit from recorded business cash headroom, "
        "then compare loan amounts and tenures."
    )

    businesses = get_user_business_profiles(user_id)
    if not businesses:
        st.info("Create a business profile before estimating repayment capacity.")
        st.page_link("pages/9_Business_Profile.py", label="Create business profile")
        st.stop()

    options = {
        f"{item['business_name']} — {item['city']}, {item['state']}": item["id"]
        for item in businesses
    }
    selected = st.selectbox("Select business", list(options))
    records = get_business_financial_records(user_id, options[selected])
    if not records:
        st.warning("Add actual monthly financial records before using the optimizer.")
        st.page_link("pages/10_Financial_Records.py", label="Add monthly financial records")
        st.stop()

    latest = records[0]
    st.subheader(f"Repayment baseline: {latest['period_month']}")
    st.caption(
        "The current calculation uses your latest saved month. Add more months "
        "and review Cash Flow Outlook and Financial Resilience Twin before making decisions."
    )

    buffer_percent = st.slider(
        "Cash reserve to retain (%)",
        min_value=0,
        max_value=90,
        value=30,
        step=5,
        help="This is your planning choice, not a bank-mandated percentage. "
             "The optimizer excludes this share of positive monthly cash headroom "
             "from the estimated EMI capacity.",
    )
    try:
        capacity = analyze_repayment_capacity(latest, buffer_percent)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()

    st.divider()
    st.subheader("Estimated monthly repayment capacity")
    c1, c2, c3 = st.columns(3)
    c1.metric("Recorded cash headroom", f"₹{capacity['cash_headroom']:,.0f}")
    c2.metric("Selected reserve amount", f"₹{capacity['reserve_amount']:,.0f}")
    c3.metric("Estimated EMI capacity", f"₹{capacity['estimated_monthly_emi_capacity']:,.0f}")

    if capacity["is_headroom_negative"]:
        st.error(
            "The latest recorded month has negative cash headroom. "
            "This calculation therefore shows zero additional EMI capacity."
        )
    elif capacity["estimated_monthly_emi_capacity"] == 0:
        st.warning("No additional EMI capacity remains after the selected reserve.")
    else:
        st.info(
            "This is a mathematical planning limit based on one reporting month, "
            "not a recommendation to borrow the full amount."
        )

    st.divider()
    st.subheader("Compare loan scenarios")
    left, right = st.columns(2)
    with left:
        requested_amount = st.number_input(
            "Loan amount to compare (₹)",
            min_value=10000,
            max_value=100000000,
            value=500000,
            step=10000,
        )
        annual_rate = st.number_input(
            "Annual interest rate (%)",
            min_value=0.0,
            max_value=40.0,
            value=12.0,
            step=0.25,
        )
    with right:
        selected_tenures = st.multiselect(
            "Tenures to compare (years)",
            options=[1, 2, 3, 4, 5, 7, 10, 12, 15],
            default=[3, 5, 7],
        )

    if selected_tenures:
        try:
            scenarios = compare_loan_scenarios(
                requested_amount,
                annual_rate,
                selected_tenures,
                capacity["estimated_monthly_emi_capacity"],
            )
        except ValueError as exc:
            st.error(str(exc))
            st.stop()

        table = []
        for item in scenarios:
            table.append({
                "Tenure (years)": item["tenure_years"],
                "Monthly EMI": item["monthly_emi"],
                "Total interest": item["total_interest"],
                "Total repayment": item["total_payment"],
                "Within estimated capacity": (
                    "Yes" if item["within_estimated_capacity"] else "No"
                ),
                "Maximum principal at capacity": item["maximum_principal_at_capacity"],
            })
        st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)

        st.subheader("Maximum principal at selected interest rate")
        amount_cols = st.columns(len(scenarios))
        for col, item in zip(amount_cols, scenarios):
            col.metric(
                f"{item['tenure_years']:g}-year scenario",
                f"₹{item['maximum_principal_at_capacity']:,.0f}",
            )
        st.caption(
            "Longer tenures can increase the mathematical principal supported by "
            "a fixed EMI, but generally increase total interest. Actual lender "
            "eligibility and terms may differ."
        )
    else:
        st.info("Select at least one tenure to compare loan scenarios.")

    st.divider()
    st.subheader("Calculate EMI for a custom loan")
    custom_left, custom_right = st.columns(2)
    with custom_left:
        custom_principal = st.number_input(
            "Custom principal (₹)",
            min_value=10000,
            max_value=100000000,
            value=300000,
            step=10000,
        )
        custom_tenure = st.selectbox("Custom tenure (years)", [1, 2, 3, 4, 5, 7, 10], index=4)
    with custom_right:
        custom_rate = st.number_input(
            "Custom annual rate (%)",
            min_value=0.0,
            max_value=40.0,
            value=12.0,
            step=0.25,
            key="custom_optimizer_rate",
        )
        custom_emi = st.number_input(
            "Proposed EMI to test (₹)",
            min_value=0.0,
            value=0.0,
            step=500.0,
        )

    from core.emi import calculate_emi
    custom_calculated_emi = calculate_emi(
        custom_principal, custom_rate, custom_tenure
    )
    custom_maximum = maximum_principal_for_emi(
        capacity["estimated_monthly_emi_capacity"],
        custom_rate,
        custom_tenure,
    )
    st.metric("Calculated EMI for custom loan", f"₹{custom_calculated_emi:,.2f}")
    st.metric(
        "Maximum principal at estimated capacity",
        f"₹{custom_maximum:,.0f}",
    )
    if custom_emi > 0:
        if custom_emi <= capacity["estimated_monthly_emi_capacity"]:
            st.success("The proposed EMI is within this selected planning capacity.")
        else:
            st.warning("The proposed EMI exceeds this selected planning capacity.")

    with st.expander("Method and limitations"):
        st.write(
            "Cash headroom = revenue + other income − direct costs − operating "
            "expenses − owner drawings − existing debt service."
        )
        st.write(
            "Estimated EMI capacity = max(0, cash headroom − selected reserve). "
            "Maximum principal is calculated by reversing the standard EMI formula "
            "at the selected rate and tenure."
        )
        st.write(capacity["limitations"])

    st.caption(
        "This tool does not check credit bureau history, collateral, lender policy, "
        "legal eligibility or loan approval. Confirm affordability using multiple "
        "months of records and professional financial advice."
    )
