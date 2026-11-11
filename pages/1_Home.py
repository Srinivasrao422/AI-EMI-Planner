from pathlib import Path
import sys

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from components.theme import load_theme
from database.business_profiles import get_user_business_profiles
from database.financial_records import (
    calculate_monthly_summary,
    get_business_financial_records,
)
from database.loan_history import get_latest_loan, get_user_loans
from utils.auth_helper import require_login


st.set_page_config(
    page_title="Dashboard | MSME Credit & Financial Risk Platform",
    layout="wide",
)
load_theme()


def _inr(value):
    return f"₹{float(value):,.0f}"


def _render_section_heading(title, description=None):
    st.subheader(title)
    if description:
        st.caption(description)


if require_login():
    user_id = st.session_state.user_id
    username = st.session_state.username

    # Header
    st.markdown(
        """
        <div class="app-hero">
            <p style="margin:0 0 8px 0; color:#BFDBFE; font-size:0.78rem; font-weight:700; letter-spacing:0.12em;">
                MSME FINANCIAL WORKSPACE
            </p>
            <h1 style="margin:0; font-size:2.15rem;">Business overview</h1>
            <p class="app-hero__copy" style="margin:10px 0 0 0;">
                A clear view of your recorded business finances, loan plans and cash resilience.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    profiles = get_user_business_profiles(user_id)
    loans_df = get_user_loans(user_id)
    latest_loan = get_latest_loan(user_id)

    # Business selector and record-backed summary
    if profiles:
        profile_options = {
            f"{item['business_name']} · {item['city']}, {item['state']}": item["id"]
            for item in profiles
        }
        selected_label = st.selectbox(
            "Business workspace",
            list(profile_options),
            help="Switch between businesses owned by your account.",
        )
        selected_business_id = profile_options[selected_label]
        selected_profile = next(
            item for item in profiles if item["id"] == selected_business_id
        )
        records = get_business_financial_records(user_id, selected_business_id)
    else:
        selected_profile = None
        records = []
        st.info("No business profile has been created yet. Add one to unlock business financial insights.")
        st.page_link(
            "pages/9_Business_Profile.py",
            label="Create your first business profile",
            use_container_width=True,
        )

    st.write("")
    _render_section_heading(
        "At a glance",
        "Figures below come from your saved records. Missing data is shown as not recorded, never replaced with demo values.",
    )

    metric_cols = st.columns(4)
    metric_cols[0].metric("Business profiles", len(profiles))
    metric_cols[1].metric("Financial months recorded", len(records))
    metric_cols[2].metric("Loan calculations", len(loans_df))
    metric_cols[3].metric(
        "Latest reporting month",
        records[0]["period_month"] if records else "Not recorded",
    )

    st.divider()

    # Actual monthly business position
    _render_section_heading(
        "Business financial position",
        selected_profile["business_name"] if selected_profile else "Create a business profile to begin.",
    )

    if records:
        latest = records[0]
        summary = calculate_monthly_summary(latest)
        total_income = summary["total_income"]
        operating_surplus = summary["operating_surplus"]
        cash_headroom = summary["cash_headroom"]

        c1, c2, c3 = st.columns(3)
        c1.metric("Latest monthly income", _inr(total_income))
        c2.metric("Operating surplus", _inr(operating_surplus))
        c3.metric("Cash headroom", _inr(cash_headroom))

        if cash_headroom < 0:
            st.error(
                "The latest recorded month has negative cash headroom after owner drawings and existing debt payments."
            )
        elif cash_headroom == 0:
            st.warning("The latest recorded month is at cash-headroom break-even.")
        else:
            st.success("The latest recorded month has non-negative cash headroom.")

        # Trend chart only when there are at least two real monthly records.
        if len(records) >= 2:
            trend_rows = []
            for record in reversed(records):
                result = calculate_monthly_summary(record)
                trend_rows.append(
                    {
                        "Month": record["period_month"],
                        "Income": result["total_income"],
                        "Cash headroom": result["cash_headroom"],
                    }
                )
            trend_df = pd.DataFrame(trend_rows).set_index("Month")
            _render_section_heading(
                "Recorded monthly trend",
                "Based on saved monthly records only. No projections or interpolated values are included.",
            )
            st.line_chart(trend_df, use_container_width=True)
        else:
            st.info(
                "Add another reporting month to see a meaningful month-to-month financial trend."
            )

        _render_section_heading("Recent business records")
        table_rows = []
        for record in records[:6]:
            result = calculate_monthly_summary(record)
            table_rows.append(
                {
                    "Month": record["period_month"],
                    "Income": result["total_income"],
                    "Operating surplus": result["operating_surplus"],
                    "Cash headroom": result["cash_headroom"],
                }
            )
        st.dataframe(
            pd.DataFrame(table_rows),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info(
            "No monthly financial records are available for this business. "
            "Record actual figures to populate this dashboard."
        )

    st.divider()

    # Loan snapshot uses only saved loan calculations.
    _render_section_heading(
        "Loan planning snapshot",
        "Most recent saved EMI calculation for your account.",
    )
    if latest_loan:
        loan_cols = st.columns(4)
        loan_cols[0].metric("Loan amount", _inr(latest_loan["loan_amount"]))
        loan_cols[1].metric("Monthly EMI", _inr(latest_loan["monthly_emi"]))
        loan_cols[2].metric("Interest rate", f"{latest_loan['interest_rate']:.2f}%")
        loan_cols[3].metric("Tenure", f"{latest_loan['tenure']} years")
        st.caption(
            f"Last saved: {latest_loan.get('created_at') or 'Date not available'} · "
            f"Risk label stored with calculation: {latest_loan.get('risk_level') or 'Not recorded'}"
        )
    else:
        st.info("No saved loan calculation yet. Your loan snapshot will appear after using the EMI Calculator.")

    st.divider()

    # Core financial tools are kept in the dashboard workspace, not the sidebar.
    _render_section_heading(
        "Financial workspace",
        "Choose a tool. These four loan-planning tools are available here to keep navigation compact.",
    )
    core_tools = [
        ("EMI Calculator", "Calculate a loan's monthly instalment and total interest.", "pages/2_EMI_Calculator.py"),
        ("Repayment Schedule", "Review the month-by-month principal and interest schedule.", "pages/3_Repayment.py"),
        ("Loan Comparison", "Compare loan options, rates and repayment tenures.", "pages/4_Comparison.py"),
        ("Risk Analysis", "Review transparent affordability and risk indicators.", "pages/5_Risk_Analysis.py"),
    ]
    for row_start in range(0, len(core_tools), 2):
        cols = st.columns(2)
        for col, (label, description, target) in zip(cols, core_tools[row_start:row_start + 2]):
            with col:
                with st.container(border=True):
                    st.markdown(f"**{label}**")
                    st.caption(description)
                    st.page_link(target, label=f"Open {label}", use_container_width=True)

    st.divider()
    _render_section_heading(
        "MSME business tools",
        "Manage recorded business information and inspect cash resilience.",
    )
    business_tools = [
        ("Business profiles", "pages/9_Business_Profile.py"),
        ("Monthly financial records", "pages/10_Financial_Records.py"),
        ("Financial health", "pages/11_Financial_Health.py"),
        ("Financial Resilience Twin", "pages/12_Resilience_Twin.py"),
        ("Cash Flow Outlook", "pages/13_Cash_Flow_Outlook.py"),
        ("MSME Loan Optimizer", "pages/14_Loan_Optimizer.py"),
        ("Loan history", "pages/8_History.py"),
        ("AI Assistant", "pages/6_AI_Assistant.py"),
        ("Bank Statement Intelligence", "pages/15_Bank_Statement.py"),
    ]
    for row_start in range(0, len(business_tools), 4):
        cols = st.columns(4)
        for col, (label, target) in zip(cols, business_tools[row_start:row_start + 4]):
            with col:
                st.page_link(target, label=label, use_container_width=True)

    st.caption(
        "Dashboard figures are descriptive summaries of information saved in this account. "
        "They are not audited financial statements, credit scores, default predictions or lender decisions."
    )
