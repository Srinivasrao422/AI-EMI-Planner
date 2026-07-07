def validate_loan_inputs(
    loan_amount,
    interest_rate,
    tenure_years
):
    """
    Validate loan inputs.
    """

    if loan_amount <= 0:
        raise ValueError(
            "Loan amount must be greater than zero."
        )

    if interest_rate < 0:
        raise ValueError(
            "Interest rate cannot be negative."
        )

    if tenure_years <= 0:
        raise ValueError(
            "Loan tenure must be greater than zero."
        )