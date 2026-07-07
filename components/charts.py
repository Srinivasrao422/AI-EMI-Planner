"""
Plotly analytics charts for loan breakdown and repayment progress.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

CHART_LAYOUT = {
    "template": "plotly_dark",
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font_color": "#E5E7EB",
    "height": 420,
    "margin": {"l": 24, "r": 24, "t": 64, "b": 24},
}

REQUIRED_SCHEDULE_COLUMNS = {"Month", "Remaining Balance"}

def _style_chart(fig):
    fig.update_layout(**CHART_LAYOUT)
    return fig

def show_charts(principal, total_interest, repayment_schedule):
    """Render dashboard analytics charts."""

    st.subheader("Financial Analytics")

    if not repayment_schedule:
        st.info("Charts will appear after a repayment schedule is generated.")
        return

    schedule_df = pd.DataFrame(repayment_schedule)
    missing_columns = REQUIRED_SCHEDULE_COLUMNS - set(schedule_df.columns)
    if missing_columns:
        st.warning("Repayment schedule data is missing chart-ready columns.")
        return

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            pie = px.pie(
                names=["Principal", "Interest"],
                values=[principal, total_interest],
                title="Loan Breakdown",
                hole=0.55,
                color_discrete_sequence=["#2563EB", "#38BDF8"],
            )
            st.plotly_chart(_style_chart(pie), use_container_width=True)

    with col2:
        with st.container(border=True):
            line = px.line(
                schedule_df,
                x="Month",
                y="Remaining Balance",
                markers=True,
                title="Remaining Loan Balance",
            )
            line.update_traces(line_color="#38BDF8", marker_color="#2563EB")
            st.plotly_chart(_style_chart(line), use_container_width=True)
