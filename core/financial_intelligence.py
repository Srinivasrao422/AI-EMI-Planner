"""Deterministic, evidence-linked MSME financial trend explanations.

All figures are calculated from saved monthly records. No score, forecast, or
lender decision is produced by this module.
"""
from database.financial_records import calculate_monthly_summary


TRACKED_FIELDS = {
    "revenue": "Sales revenue",
    "cost_of_goods_sold": "Direct costs",
    "operating_expenses": "Operating expenses",
    "owner_drawings": "Owner drawings",
    "existing_debt_service": "Existing debt payments",
}


def _amount(record, field):
    try:
        value = float(record.get(field, 0) or 0)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric.") from exc
    if value < 0:
        raise ValueError(f"{field} cannot be negative.")
    return value


def analyze_business_trends(records):
    """Compare the two latest saved months and explain observable changes."""
    if not records:
        raise ValueError("At least one saved monthly record is required.")

    latest = records[0]
    latest_summary = calculate_monthly_summary(latest)
    previous = records[1] if len(records) > 1 else None
    changes = []

    if previous:
        previous_summary = calculate_monthly_summary(previous)
        for field, label in TRACKED_FIELDS.items():
            old = _amount(previous, field)
            new = _amount(latest, field)
            delta = new - old
            pct = (delta / old * 100) if old else None
            changes.append({
                "field": field,
                "label": label,
                "previous_month": previous.get("period_month"),
                "latest_month": latest.get("period_month"),
                "previous_value": round(old, 2),
                "latest_value": round(new, 2),
                "change_amount": round(delta, 2),
                "change_percent": round(pct, 2) if pct is not None else None,
                "percentage_note": None if old else "Percentage change unavailable because the previous value was zero.",
            })
        previous_headroom = previous_summary["cash_headroom"]
        current_headroom = latest_summary["cash_headroom"]
        headroom_delta = current_headroom - previous_headroom
    else:
        previous_headroom = None
        headroom_delta = None

    findings = []
    recommendations = []
    latest_revenue = _amount(latest, "revenue")
    latest_direct = _amount(latest, "cost_of_goods_sold")
    latest_operating = _amount(latest, "operating_expenses")
    latest_headroom = latest_summary["cash_headroom"]

    if previous:
        by_field = {item["field"]: item for item in changes}
        revenue_change = by_field["revenue"]
        if revenue_change["change_percent"] is not None and revenue_change["change_percent"] <= -5:
            findings.append({
                "severity": "attention",
                "text": f"Sales revenue fell {abs(revenue_change['change_percent']):.2f}% from {revenue_change['previous_month']} to {revenue_change['latest_month']}.",
                "evidence": [revenue_change["previous_month"], revenue_change["latest_month"]],
            })
            recommendations.append("Review sales volume, customer orders and collections for the two compared months before changing the loan plan.")
        for field in ("cost_of_goods_sold", "operating_expenses"):
            item = by_field[field]
            if item["change_percent"] is not None and item["change_percent"] >= 5:
                findings.append({
                    "severity": "attention",
                    "text": f"{item['label']} increased {item['change_percent']:.2f}% from {item['previous_month']} to {item['latest_month']}.",
                    "evidence": [item["previous_month"], item["latest_month"]],
                })
                recommendations.append(f"Review the bills and line items behind the increase in {item['label'].lower()}; confirm whether it is recurring or one-off.")
        if headroom_delta is not None and headroom_delta < 0:
            findings.append({
                "severity": "attention",
                "text": f"Cash headroom decreased by ₹{abs(headroom_delta):,.2f} compared with {previous.get('period_month')}.",
                "evidence": [previous.get("period_month"), latest.get("period_month")],
            })
            recommendations.append("Protect a cash reserve and check the timing of customer receipts, supplier payments and debt instalments.")
    else:
        findings.append({
            "severity": "information",
            "text": "Only one month is recorded, so month-to-month trends cannot yet be calculated.",
            "evidence": [latest.get("period_month")],
        })
        recommendations.append("Record additional consecutive months before drawing conclusions about financial trends.")

    if latest_headroom < 0:
        findings.append({
            "severity": "high",
            "text": f"Latest recorded cash headroom is negative at ₹{latest_headroom:,.2f}.",
            "evidence": [latest.get("period_month")],
        })
        recommendations.append("Reconcile near-term cash receipts and payments, and avoid taking on additional EMI until the shortfall is understood.")
    elif latest_headroom == 0:
        findings.append({
            "severity": "attention",
            "text": "Latest recorded cash headroom is exactly zero, leaving no recorded monthly buffer.",
            "evidence": [latest.get("period_month")],
        })
        recommendations.append("Build a cash buffer and test proposed repayments against weaker-sales scenarios.")
    elif not any(item["severity"] in ("attention", "high") for item in findings):
        findings.append({
            "severity": "positive",
            "text": f"Latest recorded cash headroom is positive at ₹{latest_headroom:,.2f}.",
            "evidence": [latest.get("period_month")],
        })
        recommendations.append("Continue recording monthly figures and compare cash headroom across additional months before relying on this result.")

    return {
        "latest_month": latest.get("period_month"),
        "previous_month": previous.get("period_month") if previous else None,
        "latest_summary": latest_summary,
        "previous_cash_headroom": round(previous_headroom, 2) if previous_headroom is not None else None,
        "cash_headroom_change": round(headroom_delta, 2) if headroom_delta is not None else None,
        "changes": changes,
        "findings": findings,
        "recommendations": list(dict.fromkeys(recommendations)),
        "records_compared": 2 if previous else 1,
        "limitations": "These are comparisons of entered monthly figures, not forecasts. They do not verify bank balances, receivables, inventory, taxes, seasonality or unrecorded liabilities.",
    }
