"""
==========================================
EMI Calculation Engine
AI Powered EMI Planner
==========================================
"""

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
    try:
        p = float(principal)
        r = float(annual_interest_rate)
        t = float(tenure_years)
    except (ValueError, TypeError):
        raise ValueError("Invalid numeric input type.")

    if p <= 0:
        raise ValueError("Loan amount must be greater than zero.")
    if r < 0:
        raise ValueError("Interest rate cannot be negative.")
    if t <= 0:
        raise ValueError("Loan tenure must be greater than zero.")

    # Number of months
    months = t * 12

    # Handle zero interest loan
    if r == 0:
        return round(p / months, 2)

    # Monthly interest rate
    monthly_interest_rate = r / (12 * 100)

    try:
        # Standard EMI Formula: P * r * (1+r)^n / ((1+r)^n - 1)
        pow_term = math.pow(1 + monthly_interest_rate, months)
        emi = (p * monthly_interest_rate * pow_term) / (pow_term - 1)
        return round(emi, 2)
    except (ZeroDivisionError, OverflowError):
        return 0.0


def calculate_loan_details(principal, annual_interest_rate, tenure_years):
    """
    Calculate complete loan details.

    Returns:
        dict
    """
    try:
        p = float(principal)
        r = float(annual_interest_rate)
        t = float(tenure_years)
        
        emi = calculate_emi(p, r, t)
        months = int(t * 12)
        total_payment = round(emi * months, 2) if months > 0 else 0.0
        total_interest = round(total_payment - p, 2) if total_payment >= p else 0.0
        
        return {
            "loan_amount": p,
            "interest_rate": r,
            "tenure_years": t,
            "months": months,
            "emi": emi,
            "total_payment": total_payment,
            "total_interest": total_interest,
        }
    except ValueError as e:
        # Return safe defaults if validation fails
        return {
            "loan_amount": 0.0,
            "interest_rate": 0.0,
            "tenure_years": 0.0,
            "months": 0,
            "emi": 0.0,
            "total_payment": 0.0,
            "total_interest": 0.0,
            "error": str(e)
        }