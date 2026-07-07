from core.risk import analyze_financial_risk

result = analyze_financial_risk(
    loan_amount=500000,
    interest_rate=8.5,
    tenure_years=5,
    monthly_income=60000,
    monthly_expenses=25000,
    credit_score=760
)

print("\n========== RISK REPORT ==========\n")

for key, value in result.items():
    print(f"{key}: {value}")