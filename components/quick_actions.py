"""
Quick action entry points for dashboard modules.
"""

import streamlit as st

QUICK_ACTIONS = (
    {
        "title": "EMI Calculator",
        "description": "Calculate monthly EMI from loan amount, interest rate, and tenure.",
        "page": "pages/2_EMI_Calculator.py",
    },
    {
        "title": "Loan Comparison",
        "description": "Compare multiple loan options and review repayment impact.",
        "page": "pages/4_Comparison.py",
    },
    {
        "title": "Risk Analysis",
        "description": "Review affordability, debt ratio, and financial stability.",
        "page": "pages/5_Risk_Analysis.py",
    },
    {
        "title": "Repayment Schedule",
        "description": "Generate a month-by-month principal and interest schedule.",
        "page": "pages/3_Repayment.py",
    },
    {
        "title": "AI Assistant",
        "description": "Explore guided recommendations for smarter loan planning.",
        "page": "pages/6_AI_Assistant.py",
    },
    {
        "title": "Analytics",
        "description": "Inspect financial charts and repayment trends.",
        "page": "pages/2_EMI_Calculator.py",
    },
)

def _show_action(action):
    with st.container(border=True):
        st.subheader(action["title"])
        st.caption(action["description"])
        st.page_link(
            action["page"],
            label=f"Open {action['title']}",
            use_container_width=True,
        )

def show_quick_actions(actions=QUICK_ACTIONS):
    """Render quick action cards without raw HTML."""

    st.subheader("Quick Access Modules")

    for start in range(0, len(actions), 3):
        columns = st.columns(3)
        for column, action in zip(columns, actions[start:start + 3]):
            with column:
                _show_action(action)
