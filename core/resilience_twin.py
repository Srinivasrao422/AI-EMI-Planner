"""Scenario-based MSME cash resilience calculations.

All results are deterministic calculations from the user's latest recorded
month and explicitly selected stress assumptions. They are not forecasts,
credit scores, or lending decisions.
"""


def _amount(record, key):
    try:
        value = float(record.get(key, 0) or 0)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be numeric.") from exc
    if value < 0:
        raise ValueError(f"{key} cannot be negative.")
    return value


def _percentage(value, name):
    try:
        value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric.") from exc
    if not 0 <= value <= 100:
        raise ValueError(f"{name} must be between 0 and 100.")
    return value


def simulate_resilience(
    record,
    revenue_drop_percent=0,
    cost_increase_percent=0,
    delayed_receipts_percent=0,
    proposed_new_emi=0,
):
    """Return base and stressed monthly cash headroom and reverse stress threshold.

    Revenue drop reduces sales. Delayed receipts then reduce the remaining sales
    collected in the reporting month. Other income is assumed collected in-month.
    The cost shock is applied to direct costs plus operating expenses.
    """
    revenue_drop = _percentage(revenue_drop_percent, "Revenue reduction")
    cost_increase = _percentage(cost_increase_percent, "Cost increase")
    delayed = _percentage(delayed_receipts_percent, "Delayed receipts")
    new_emi = _amount({"value": proposed_new_emi}, "value")

    revenue = _amount(record, "revenue")
    other_income = _amount(record, "other_income")
    direct_costs = _amount(record, "cost_of_goods_sold")
    operating_expenses = _amount(record, "operating_expenses")
    drawings = _amount(record, "owner_drawings")
    existing_debt = _amount(record, "existing_debt_service")

    base_headroom = (
        revenue + other_income - direct_costs - operating_expenses
        - drawings - existing_debt
    )
    stressed_sales_collected = revenue * (1 - revenue_drop / 100) * (1 - delayed / 100)
    stressed_costs = (direct_costs + operating_expenses) * (1 + cost_increase / 100)
    fixed_outflows = drawings + existing_debt + new_emi
    stressed_headroom = stressed_sales_collected + other_income - stressed_costs - fixed_outflows

    available_sales_after_delay = revenue * (1 - delayed / 100)
    required_sales_collected = stressed_costs + fixed_outflows - other_income
    if available_sales_after_delay <= 0:
        revenue_break_even = None
        break_even_note = "Cannot calculate a revenue threshold because no sales are available for collection."
    else:
        threshold = 1 - required_sales_collected / available_sales_after_delay
        if threshold < 0:
            revenue_break_even = 0.0
            break_even_note = "Cash headroom is already negative before any additional sales reduction."
        elif threshold >= 1:
            revenue_break_even = 100.0
            break_even_note = "Cash headroom remains non-negative even if all remaining sales are lost, under these simplified assumptions."
        else:
            revenue_break_even = round(threshold * 100, 2)
            break_even_note = "Estimated additional sales reduction from the current baseline that brings monthly cash headroom to zero."

    emi_capacity = max(0.0, stressed_headroom + new_emi)
    return {
        "period_month": record.get("period_month"),
        "base_cash_headroom": round(base_headroom, 2),
        "stressed_sales_collected": round(stressed_sales_collected, 2),
        "stressed_costs": round(stressed_costs, 2),
        "stressed_headroom": round(stressed_headroom, 2),
        "new_emi": round(new_emi, 2),
        "additional_emi_headroom": round(emi_capacity, 2),
        "revenue_break_even_drop_percent": revenue_break_even,
        "break_even_note": break_even_note,
        "is_stressed_headroom_negative": stressed_headroom < 0,
        "assumptions": {
            "revenue_drop_percent": revenue_drop,
            "cost_increase_percent": cost_increase,
            "delayed_receipts_percent": delayed,
        },
        "limitations": (
            "A one-month sensitivity simulation, not a forecast. It assumes other "
            "income is collected in-month, applies the cost shock uniformly to direct "
            "and operating costs, and does not model opening cash, receivable ageing, "
            "inventory timing, taxes, seasonality, supplier credit or working-capital "
            "cycles. Additional EMI headroom is a mathematical scenario result, not "
            "a loan recommendation or proof of repayment capacity."
        ),
    }
