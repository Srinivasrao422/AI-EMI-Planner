from core.emi import calculate_loan_details


def compare_loans(loans):
    """
    Compare multiple loan options.

    Parameters:
        loans (list): List of loan dictionaries.

    Returns:
        list: Loan comparison results.
    """

    comparison_results = []

    for loan in loans:

        details = calculate_loan_details(
            principal=loan["loan_amount"],
            annual_interest_rate=loan["interest_rate"],
            tenure_years=loan["tenure_years"]
        )

        comparison_results.append({
            "Bank": loan["bank_name"],
            "Loan Amount": details["loan_amount"],
            "Interest Rate": details["interest_rate"],
            "Tenure": details["tenure_years"],
            "Monthly EMI": details["emi"],
            "Total Interest": details["total_interest"],
            "Total Payment": details["total_payment"]
        })

    return comparison_results