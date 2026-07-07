from core.emi import calculate_loan_details


def analyze_affordability(
    loan_amount,
    interest_rate,
    tenure_years,
    monthly_income,
    monthly_expenses
):
    """
    Analyze whether a loan is affordable.
    """

    loan = calculate_loan_details(
        loan_amount,
        interest_rate,
        tenure_years
    )

    emi = loan["emi"]

    disposable_income = monthly_income - monthly_expenses

    emi_percentage = round(
        (emi / monthly_income) * 100,
        2
    )

    if emi <= disposable_income:

        affordability = "Affordable"

    else:

        affordability = "Not Affordable"

    return {

        "Monthly Income": monthly_income,

        "Monthly Expenses": monthly_expenses,

        "Disposable Income": disposable_income,

        "Monthly EMI": emi,

        "EMI Percentage": emi_percentage,

        "Affordability": affordability

    }