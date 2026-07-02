from core.emi import calculate_emi


def generate_repayment_schedule(
    principal,
    annual_interest_rate,
    tenure_years
):
    """
    Generate month-wise repayment schedule.
    """

    monthly_interest_rate = annual_interest_rate / (12 * 100)

    months = tenure_years * 12

    emi = calculate_emi(
        principal,
        annual_interest_rate,
        tenure_years
    )

    balance = principal

    schedule = []

    for month in range(1, months + 1):

        interest_paid = round(
            balance * monthly_interest_rate,
            2
        )

        principal_paid = round(
            emi - interest_paid,
            2
        )

        balance = round(
            balance - principal_paid,
            2
        )

        if balance < 0:
            balance = 0

        schedule.append({
            "Month": month,
            "EMI": emi,
            "Principal Paid": principal_paid,
            "Interest Paid": interest_paid,
            "Remaining Balance": balance
        })

    return schedule