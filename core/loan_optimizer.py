"""Transparent MSME loan repayment-capacity and scenario calculations.

This module estimates mathematical EMI headroom from a recorded month. It is
not a lender underwriting model, credit score, or loan approval.
"""
from core.emi import calculate_emi
from database.financial_records import calculate_monthly_summary


def _non_negative(value, label):
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be numeric.") from exc
    if number < 0:
        raise ValueError(f"{label} cannot be negative.")
    return number


def maximum_principal_for_emi(monthly_emi, annual_rate, tenure_years):
    """Return principal whose rounded EMI does not exceed monthly_emi."""
    emi = _non_negative(monthly_emi, "Monthly EMI")
    rate = _non_negative(annual_rate, "Interest rate")
    tenure = _non_negative(tenure_years, "Tenure")
    if tenure <= 0:
        raise ValueError("Tenure must be greater than zero.")
    months = int(round(tenure * 12))
    if months <= 0:
        raise ValueError("Tenure must include at least one month.")
    if emi <= 0:
        return 0.0
    monthly_rate = rate / 1200
    if monthly_rate == 0:
        principal = emi * months
    else:
        factor = (1 + monthly_rate) ** months
        principal = emi * (factor - 1) / (monthly_rate * factor)
    return round(max(0.0, principal), 2)


def analyze_repayment_capacity(record, reserve_buffer_percent=30.0):
    """Calculate headroom and an explicitly user-selected cash reserve buffer."""
    try:
        buffer_percent = float(reserve_buffer_percent)
    except (TypeError, ValueError) as exc:
        raise ValueError("Reserve buffer must be numeric.") from exc
    if not 0 <= buffer_percent <= 90:
        raise ValueError("Reserve buffer must be between 0% and 90%.")

    summary = calculate_monthly_summary(record)
    raw_headroom = summary["cash_headroom"]
    reserve = max(0.0, raw_headroom) * buffer_percent / 100
    available_emi = max(0.0, raw_headroom - reserve)

    return {
        "period_month": record.get("period_month"),
        "total_income": summary["total_income"],
        "operating_surplus": summary["operating_surplus"],
        "cash_headroom": raw_headroom,
        "reserve_buffer_percent": buffer_percent,
        "reserve_amount": round(reserve, 2),
        "estimated_monthly_emi_capacity": round(available_emi, 2),
        "is_headroom_negative": raw_headroom < 0,
        "limitations": (
            "Uses one recorded month and the reserve percentage selected by the "
            "user. It does not assess bank statements, existing informal debt, "
            "credit bureau data, tax liabilities, seasonality, receivables ageing, "
            "collateral, lender policies or future business conditions. The result "
            "is a planning estimate, not a lending decision or guarantee."
        ),
    }


def compare_loan_scenarios(loan_amount, annual_rate, tenures_years, monthly_emi_capacity):
    """Compare the same principal across tenures and show capacity differences."""
    principal = _non_negative(loan_amount, "Loan amount")
    rate = _non_negative(annual_rate, "Interest rate")
    capacity = _non_negative(monthly_emi_capacity, "Monthly EMI capacity")
    if principal <= 0:
        raise ValueError("Loan amount must be greater than zero.")
    if not tenures_years:
        raise ValueError("Select at least one loan tenure.")

    results = []
    for raw_tenure in tenures_years:
        tenure = _non_negative(raw_tenure, "Tenure")
        if tenure <= 0 or tenure > 30:
            raise ValueError("Tenure must be between 1 and 30 years.")
        emi = calculate_emi(principal, rate, tenure)
        months = int(round(tenure * 12))
        total_payment = round(emi * months, 2)
        results.append({
            "tenure_years": tenure,
            "monthly_emi": emi,
            "total_interest": round(max(0.0, total_payment - principal), 2),
            "total_payment": total_payment,
            "within_estimated_capacity": emi <= capacity,
            "monthly_capacity_difference": round(capacity - emi, 2),
            "maximum_principal_at_capacity": maximum_principal_for_emi(
                capacity, rate, tenure
            ),
        })
    return results
