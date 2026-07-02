import math


def calculate_emi(principal, annual_interest_rate, tenure_years):
    """
    Calculate Monthly EMI.

    Parameters:
        principal (float): Loan Amount
        annual_interest_rate (float): Annual Interest Rate (%)
        tenure_years (int): Loan Tenure in Years

    Returns:
        float: Monthly EMI
    """

    # Handle zero interest loan
    if annual_interest_rate == 0:
        months = tenure_years * 12
        return round(principal / months, 2)

    monthly_interest_rate = annual_interest_rate / (12 * 100)

    number_of_months = tenure_years * 12

    emi = (
        principal
        * monthly_interest_rate
        * math.pow((1 + monthly_interest_rate), number_of_months)
    ) / (
        math.pow((1 + monthly_interest_rate), number_of_months) - 1
    )

    return round(emi, 2)


def calculate_loan_details(principal, annual_interest_rate, tenure_years):
    """
    Calculate complete loan details.

    Returns:
        dict
    """

    emi = calculate_emi(
        principal,
        annual_interest_rate,
        tenure_years,
    )

    number_of_months = tenure_years * 12

    total_payment = round(
        emi * number_of_months,
        2,
    )

    total_interest = round(
        total_payment - principal,
        2,
    )

    return {
        "loan_amount": principal,
        "interest_rate": annual_interest_rate,
        "tenure_years": tenure_years,
        "months": number_of_months,
        "emi": emi,
        "total_payment": total_payment,
        "total_interest": total_interest,
    }