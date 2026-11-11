"""Transparent, rule-based MSME financial health indicators.

These calculations describe the entered monthly figures. They are not a
credit score, audited financial statement, default prediction, or lender decision.
"""


def _number(record, key):
    try:
        value = float(record.get(key, 0) or 0)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be a numeric value.") from exc
    if value < 0:
        raise ValueError(f"{key} cannot be negative.")
    return value


def analyze_financial_health(records):
    """Analyze monthly records, newest first, and return transparent indicators."""
    if not records:
        raise ValueError("Add at least one monthly financial record to run the analysis.")

    current = records[0]
    revenue = _number(current, "revenue")
    other_income = _number(current, "other_income")
    direct_costs = _number(current, "cost_of_goods_sold")
    operating_expenses = _number(current, "operating_expenses")
    owner_drawings = _number(current, "owner_drawings")
    debt_service = _number(current, "existing_debt_service")

    total_income = revenue + other_income
    operating_surplus = total_income - direct_costs - operating_expenses
    cash_headroom = operating_surplus - owner_drawings - debt_service

    gross_profit = revenue - direct_costs
    gross_margin = (gross_profit / revenue * 100) if revenue > 0 else None
    operating_margin = (operating_surplus / total_income * 100) if total_income > 0 else None
    operating_expense_ratio = (
        operating_expenses / total_income * 100
        if total_income > 0 else None
    )
    cash_headroom_margin = (
        cash_headroom / total_income * 100 if total_income > 0 else None
    )
    debt_service_coverage = (
        operating_surplus / debt_service if debt_service > 0 else None
    )

    indicators = [
        {
            "name": "Gross margin",
            "value": gross_margin,
            "unit": "%",
            "description": "Revenue remaining after direct costs, before operating expenses.",
            "status": (
                "Not available" if gross_margin is None else
                "Negative" if gross_margin < 0 else
                "Positive" if gross_margin > 0 else "Break-even"
            ),
        },
        {
            "name": "Operating margin",
            "value": operating_margin,
            "unit": "%",
            "description": "Operating surplus as a share of total income.",
            "status": (
                "Not available" if operating_margin is None else
                "Negative" if operating_margin < 0 else
                "Positive" if operating_margin > 0 else "Break-even"
            ),
        },
        {
            "name": "Operating expense ratio",
            "value": operating_expense_ratio,
            "unit": "%",
            "description": "Operating expenses divided by total income.",
            "status": "Not available" if operating_expense_ratio is None else "Calculated",
        },
        {
            "name": "Debt service coverage proxy",
            "value": debt_service_coverage,
            "unit": "x",
            "description": "Operating surplus divided by existing monthly debt payments. This is a simplified proxy, not formal DSCR.",
            "status": (
                "No debt payment entered" if debt_service_coverage is None else
                "Below 1.0x" if debt_service_coverage < 1 else
                "At least 1.0x"
            ),
        },
        {
            "name": "Cash headroom margin",
            "value": cash_headroom_margin,
            "unit": "%",
            "description": "Cash headroom after owner drawings and existing debt payments, as a share of total income.",
            "status": (
                "Not available" if cash_headroom_margin is None else
                "Negative" if cash_headroom_margin < 0 else
                "Non-negative"
            ),
        },
    ]

    observations = []
    if total_income <= 0:
        observations.append("No positive income was recorded; percentage margins cannot be calculated.")
    if gross_margin is not None and gross_margin < 0:
        observations.append("Direct costs exceed sales revenue in this reporting month.")
    if operating_surplus < 0:
        observations.append("Operating costs exceed total recorded income.")
    if debt_service > 0 and (debt_service_coverage or 0) < 1:
        observations.append("Operating surplus is below the existing monthly debt payments.")
    if cash_headroom < 0:
        observations.append("Cash headroom is negative after owner drawings and existing debt payments.")
    if cash_headroom >= 0 and total_income > 0:
        observations.append("Recorded monthly cash headroom is non-negative.")
    if debt_service == 0:
        observations.append("No existing monthly debt payment was entered; debt coverage is not calculated.")

    trend = None
    if len(records) >= 2:
        previous_revenue = _number(records[1], "revenue")
        if previous_revenue > 0:
            trend = {
                "previous_month": records[1].get("period_month"),
                "current_month": current.get("period_month"),
                "revenue_change_percent": round(
                    (revenue - previous_revenue) / previous_revenue * 100, 2
                ),
            }

    return {
        "period_month": current.get("period_month"),
        "total_income": round(total_income, 2),
        "gross_profit": round(gross_profit, 2),
        "operating_surplus": round(operating_surplus, 2),
        "cash_headroom": round(cash_headroom, 2),
        "indicators": indicators,
        "observations": observations,
        "revenue_trend": trend,
        "records_analyzed": len(records),
        "limitations": (
            "Based only on the monthly figures entered. It does not include "
            "bank-balance timing, receivables ageing, inventory movements, taxes, "
            "unrecorded liabilities or seasonality. It is not audited profit, "
            "a credit score, a default prediction or a lending decision."
        ),
    }
