"""
Hero banner for the AI Powered EMI Planner home page.

This is the only component that intentionally uses HTML so the top banner can
keep the branded gradient treatment that Streamlit does not expose natively.
"""

import streamlit as st


def show_hero():
    """Render the branded dashboard hero."""

    hero_html = """
    <section class="app-hero">
        <p class="app-hero__eyebrow">Modern FinTech Dashboard</p>
        <h1>AI Powered EMI Planner</h1>
        <p class="app-hero__copy">
            Plan loans, compare repayment impact, and review AI-assisted
            financial insights in one streamlined workspace.
        </p>
        <div class="app-hero__features">
            <span>EMI Calculator</span>
            <span>Loan Comparison</span>
            <span>Risk Analysis</span>
            <span>AI Recommendations</span>
        </div>
    </section>
    """

    st.markdown(hero_html, unsafe_allow_html=True)
