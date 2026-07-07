from core.comparison import compare_loans
import pandas as pd

loans = [

    {
        "bank_name": "SBI",
        "loan_amount": 500000,
        "interest_rate": 8.5,
        "tenure_years": 5
    },

    {
        "bank_name": "HDFC",
        "loan_amount": 500000,
        "interest_rate": 9.2,
        "tenure_years": 5
    },

    {
        "bank_name": "ICICI",
        "loan_amount": 500000,
        "interest_rate": 9.8,
        "tenure_years": 5
    }

]

comparison = compare_loans(loans)

df = pd.DataFrame(comparison)

print("\n========== LOAN COMPARISON ==========\n")

print(df)