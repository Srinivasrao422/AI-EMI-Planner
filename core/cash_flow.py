"""Transparent short-horizon cash-flow planning from recorded MSME history.

This is a sensitivity-based planning projection, not an AI forecast or guarantee.
"""
from collections import defaultdict


REQUIRED_FIELDS = (
    "revenue",
    "other_income",
    "cost_of_goods_sold",
    "operating_expenses",
    "owner_drawings",
    "existing_debt_service",
)


def _amount(record, field):
    try:
        value = float(record.get(field, 0) or 0)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric.") from exc
    if value < 0:
        raise ValueError(f"{field} cannot be negative.")
    return value


def build_cash_flow_projection(
    records,
    months=3,
    monthly_revenue_change_percent=0.0,
    monthly_cost_increase_percent=0.0,
    delayed_sales_percent=0.0,
    additional_monthly_emi=0.0,
):
    """Project monthly cash headroom using the average of up to 3 recent months.

    Records must be ordered newest first. At least three distinct reporting
    months are required to avoid presenting a single month as a trend.
    """
    if len(records) < 3:
        raise ValueError(
            "At least 3 recorded months are required for a cash-flow planning projection."
        )
    if months < 1 or months > 6:
        raise ValueError("Projection horizon must be between 1 and 6 months.")

    for name, value in (
        ("Monthly revenue change", monthly_revenue_change_percent),
        ("Monthly cost increase", monthly_cost_increase_percent),
        ("Delayed sales", delayed_sales_percent),
    ):
        if not -100 <= float(value) <= 100:
            raise ValueError(f"{name} must be between -100% and 100%.")
    if not 0 <= float(delayed_sales_percent) <= 100:
        raise ValueError("Delayed sales must be between 0% and 100%.")
    if float(additional_monthly_emi) < 0:
        raise ValueError("Additional monthly EMI cannot be negative.")

    # Use the three latest actual records; don't fill missing months with estimates.
    baseline_records = records[:3]
    averages = {
        field: sum(_amount(row, field) for row in baseline_records) / 3
        for field in REQUIRED_FIELDS
    }

    revenue_change = float(monthly_revenue_change_percent) / 100
    cost_increase = float(monthly_cost_increase_percent) / 100
    receipt_factor = 1 - float(delayed_sales_percent) / 100
    additional_emi = float(additional_monthly_emi)

    rows = []
    for offset in range(1, months + 1):
        sales = averages["revenue"] * ((1 + revenue_change) ** offset)
        collected_sales = sales * receipt_factor
        other_income = averages["other_income"]
        direct_costs = averages["cost_of_goods_sold"] * ((1 + cost_increase) ** offset)
        operating_expenses = averages["operating_expenses"] * ((1 + cost_increase) ** offset)
        owner_drawings = averages["owner_drawings"]
        existing_debt = averages["existing_debt_service"]

        total_collections = collected_sales + other_income
        total_outflows = (
            direct_costs + operating_expenses + owner_drawings
            + existing_debt + additional_emi
        )
        rows.append({
            "month_number": offset,
            "sales": round(sales, 2),
            "sales_collected": round(collected_sales, 2),
            "other_income": round(other_income, 2),
            "direct_costs": round(direct_costs, 2),
            "operating_expenses": round(operating_expenses, 2),
            "owner_drawings": round(owner_drawings, 2),
            "existing_debt": round(existing_debt, 2),
            "additional_emi": round(additional_emi, 2),
            "total_collections": round(total_collections, 2),
            "total_outflows": round(total_outflows, 2),
            "cash_headroom": round(total_collections - total_outflows, 2),
        })

    return {
        "baseline_months": [row.get("period_month") for row in baseline_records],
        "baseline_averages": {key: round(value, 2) for key, value in averages.items()},
        "projections": rows,
        "negative_months": [row["month_number"] for row in rows if row["cash_headroom"] < 0],
        "limitations": (
            "This planning projection uses the average of the three latest saved "
            "reporting records. It assumes the selected monthly revenue and cost "
            "changes continue at a constant rate, keeps other income, owner drawings "
            "and existing debt payments at their three-month averages, and applies "
            "the delayed-sales percentage to each projected month's sales. It does "
            "not model opening bank balance, actual invoice due dates, receivables "
            "ageing, inventory, taxes, seasonality, one-off expenses or working "
            "capital. It is not an AI prediction, audited forecast, credit score "
            "or lending decision."
        ),
    }
