"""Transparent short-horizon cash-flow projections from recorded monthly data.

This is a simple planning baseline, not an ML forecast or lending decision.
Inputs must be reviewed monthly totals with at least two consecutive months.
"""
from statistics import mean


def _positive_number(value, label):
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a valid number.") from None
    if number < 0:
        raise ValueError(f"{label} cannot be negative.")
    return number


def _normalise_months(months):
    if not isinstance(months, (list, tuple)):
        raise ValueError("months must be a list of monthly records.")
    if len(months) < 2:
        raise ValueError("At least two recorded months are required.")
    normalized = []
    seen = set()
    for row in months:
        month = str(row.get("month", "")).strip()
        if len(month) != 7 or month[4] != "-" or not month[:4].isdigit() or not month[5:].isdigit() or not 1 <= int(month[5:]) <= 12:
            raise ValueError(f"Invalid month value: {month}")
        if month in seen:
            raise ValueError(f"Duplicate month: {month}")
        seen.add(month)
        normalized.append({
            "month": month,
            "inflows": _positive_number(row.get("inflows", 0), "inflows"),
            "outflows": _positive_number(row.get("outflows", 0), "outflows"),
        })
    normalized.sort(key=lambda item: item["month"])
    return normalized


def build_cash_flow_outlook(months, forecast_months=3, reserve_pct=30.0,
                            receipt_shock_pct=0.0, cost_increase_pct=0.0):
    """Project monthly inflows/outflows using the mean of up to 3 latest months.

    Stress percentages are applied to the baseline forecast. The reserve is
    withheld from projected net cash before calculating planning headroom.
    """
    records = _normalise_months(months)
    if not isinstance(forecast_months, int) or not 1 <= forecast_months <= 12:
        raise ValueError("forecast_months must be an integer from 1 to 12.")
    reserve_pct = _positive_number(reserve_pct, "reserve_pct")
    receipt_shock_pct = _positive_number(receipt_shock_pct, "receipt_shock_pct")
    cost_increase_pct = _positive_number(cost_increase_pct, "cost_increase_pct")
    if reserve_pct > 100 or receipt_shock_pct > 100 or cost_increase_pct > 200:
        raise ValueError("Reserve and stress percentages exceed supported limits.")

    window = records[-3:]
    avg_inflows = mean(row["inflows"] for row in window)
    avg_outflows = mean(row["outflows"] for row in window)
    baseline_net = avg_inflows - avg_outflows
    projected_inflows = avg_inflows * (1 - receipt_shock_pct / 100)
    projected_outflows = avg_outflows * (1 + cost_increase_pct / 100)
    stressed_net = projected_inflows - projected_outflows
    reserve = max(stressed_net, 0) * reserve_pct / 100
    headroom = stressed_net - reserve

    forecast = [{
        "period": index + 1,
        "baseline_inflows": round(avg_inflows, 2),
        "baseline_outflows": round(avg_outflows, 2),
        "baseline_net": round(baseline_net, 2),
        "stressed_inflows": round(projected_inflows, 2),
        "stressed_outflows": round(projected_outflows, 2),
        "stressed_net": round(stressed_net, 2),
        "reserve": round(reserve, 2),
        "planning_headroom": round(headroom, 2),
    } for index in range(forecast_months)]

    return {
        "method": "Mean of up to the latest 3 recorded months; flat monthly baseline",
        "historical_months_used": [row["month"] for row in window],
        "forecast_months": forecast,
        "assumptions": {
            "reserve_pct": reserve_pct,
            "receipt_shock_pct": receipt_shock_pct,
            "cost_increase_pct": cost_increase_pct,
        },
        "limitations": [
            "Requires at least two recorded months; results may be unstable with short history.",
            "Assumes the selected historical average remains representative.",
            "Does not model seasonality, invoice timing, taxes, working capital or one-off events.",
            "Planning headroom is not profit, a credit score, or a borrowing recommendation.",
        ],
    }
