from core.affordability import analyze_affordability


result = analyze_affordability(

    loan_amount=500000,

    interest_rate=8.5,

    tenure_years=5,

    monthly_income=60000,

    monthly_expenses=25000

)

print("\n========== AFFORDABILITY REPORT ==========\n")

for key, value in result.items():

    print(f"{key} : {value}")