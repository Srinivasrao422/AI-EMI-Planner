"""
==========================================
Repayment Schedule Engine
AI Powered EMI Planner
==========================================
"""

from core.emi import calculate_emi

def generate_repayment_schedule(
    principal,
    annual_interest_rate,
    tenure_years
):
    """
    Generate month-wise repayment schedule.
    """
    try:
        p = float(principal)
        r = float(annual_interest_rate)
        t = float(tenure_years)
    except (ValueError, TypeError):
        return []

    if p <= 0 or t <= 0 or r < 0:
        return []

    monthly_interest_rate = r / (12 * 100)
    months = int(t * 12)
    emi = calculate_emi(p, r, t)

    balance = p
    schedule = []

    for month in range(1, months + 1):
        if r > 0:
            interest_paid = round(balance * monthly_interest_rate, 2)
        else:
            interest_paid = 0.0

        if month == months:
            # Final month adjustments to clear the balance exactly
            principal_paid = round(balance, 2)
            balance = 0.0
            # Update EMI to be exactly the sum of principal and interest paid
            emi = round(principal_paid + interest_paid, 2)
        else:
            principal_paid = round(emi - interest_paid, 2)
            if principal_paid > balance:
                principal_paid = round(balance, 2)
                balance = 0.0
                emi = round(principal_paid + interest_paid, 2)
            else:
                balance = round(balance - principal_paid, 2)

        schedule.append({
            "Month": month,
            "EMI": emi,
            "Principal Paid": principal_paid,
            "Interest Paid": interest_paid,
            "Remaining Balance": balance
        })

        # Break early if balance is already 0
        if balance <= 0:
            break

    return schedule