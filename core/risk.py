"""
==========================================
Financial Risk Engine
AI Powered EMI Planner
==========================================
"""

from core.affordability import analyze_affordability
from core.emi import calculate_loan_details
from utils.state_manager import save_risk_data

def analyze_financial_risk(
    loan_amount,
    interest_rate,
    tenure_years,
    monthly_income,
    monthly_expenses,
    credit_score
):
    """
    Analyze user's financial risk, calculate health score, approval status,
    and recommendation, and save the result to the session state.
    """
    try:
        loan_amount = float(loan_amount)
        interest_rate = float(interest_rate)
        tenure_years = float(tenure_years)
        monthly_income = float(monthly_income)
        monthly_expenses = float(monthly_expenses)
        credit_score = int(credit_score)
    except (ValueError, TypeError):
        loan_amount = 0.0
        interest_rate = 0.0
        tenure_years = 0.0
        monthly_income = 0.0
        monthly_expenses = 0.0
        credit_score = 300

    affordability = analyze_affordability(
        loan_amount,
        interest_rate,
        tenure_years,
        monthly_income,
        monthly_expenses
    )

    emi_percentage = affordability.get("EMI Percentage", 0.0)
    monthly_emi = affordability.get("Monthly EMI", 0.0)

    # Compute Credit Component (out of 100)
    if credit_score >= 750:
        credit_status = "Excellent"
        credit_component = 100.0
    elif credit_score >= 650:
        credit_status = "Good"
        credit_component = 80.0 + (credit_score - 650) * 0.2
    elif credit_score >= 550:
        credit_status = "Fair"
        credit_component = 50.0 + (credit_score - 550) * 0.3
    else:
        credit_status = "Poor"
        credit_component = max(0.0, (credit_score - 300) * (50.0 / 250.0))

    # Compute Debt-to-Income (EMI Percentage) Component (out of 100)
    if emi_percentage <= 20:
        dti_component = 100.0
    elif emi_percentage <= 40:
        dti_component = 100.0 - (emi_percentage - 20) * 2.0
    elif emi_percentage <= 60:
        dti_component = 60.0 - (emi_percentage - 40) * 2.0
    else:
        dti_component = max(0.0, 20.0 - (emi_percentage - 60) * 1.0)

    # Compute Disposable Income / Savings Buffer Component (out of 100)
    disposable = monthly_income - monthly_expenses - monthly_emi
    savings_ratio = disposable / monthly_income if monthly_income > 0 else 0.0
    if savings_ratio >= 0.3:
        savings_component = 100.0
    elif savings_ratio >= 0:
        savings_component = (savings_ratio / 0.3) * 100.0
    else:
        savings_component = 0.0

    # Calculate Financial Health Score (0 - 100)
    financial_health = int(round(0.4 * credit_component + 0.4 * dti_component + 0.2 * savings_component))
    financial_health = max(0, min(100, financial_health))

    # Determine Risk Level
    if financial_health >= 75:
        risk_level = "Low"
    elif financial_health >= 50:
        risk_level = "Medium"
    else:
        risk_level = "High"

    # Determine Approval Status
    if disposable < 0 or credit_score < 550 or emi_percentage > 60:
        approval_status = "Declined"
    elif risk_level == "Low" and credit_score >= 650:
        approval_status = "Approved"
    else:
        approval_status = "Review Required"

    # Recommendation
    if approval_status == "Approved":
        recommendation = "Your financial profile is strong. The EMI is well within your disposable income, and you have a solid credit history. Recommendation: Proceed with the loan application. You can negotiate for lower interest rates."
        estimated_savings = round(disposable * 12 * 0.2, 2)
    elif approval_status == "Review Required":
        recommendation = "Your financial metrics are borderline. We recommend either reducing the loan amount, extending the tenure to lower the monthly EMI, or working on raising your credit score before applying to secure better terms."
        estimated_savings = round(max(0.0, disposable) * 12 * 0.1, 2)
    else:
        recommendation = "The current loan EMI exceeds your disposable income or your credit score is too low. Recommendation: Avoid taking on this debt at the moment. Focus on reducing current expenses, clearing existing debt, and improving your financial buffer."
        estimated_savings = 0.0

    # Save outputs and inputs to session state
    save_risk_data(
        risk_level=risk_level,
        financial_health=financial_health,
        recommendation=recommendation,
        approval_status=approval_status,
        estimated_savings=estimated_savings,
        credit_score=credit_score,
        monthly_expenses=monthly_expenses,
        loan_amount=loan_amount,
        interest_rate=interest_rate,
        tenure=tenure_years,
        monthly_income=monthly_income
    )

    return {
        "EMI Percentage": emi_percentage,
        "Risk Level": risk_level,
        "Credit Score": credit_score,
        "Credit Status": credit_status,
        "Financial Health %": financial_health,
        "Approval Status": approval_status,
        "Recommendation": recommendation,
        "Estimated Savings": estimated_savings
    }