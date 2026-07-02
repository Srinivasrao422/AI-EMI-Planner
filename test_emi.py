from core.emi import calculate_loan_details

loan = 500000
interest = 8.5
tenure = 5

loan_details = calculate_loan_details(
    loan,
    interest,
    tenure,
)

print("\n========== LOAN DETAILS ==========\n")

print(f"Loan Amount     : ₹{loan_details['loan_amount']:,}")
print(f"Interest Rate   : {loan_details['interest_rate']}%")
print(f"Tenure          : {loan_details['tenure_years']} Years")
print(f"Months          : {loan_details['months']}")

print("----------------------------------")

print(f"Monthly EMI     : ₹{loan_details['emi']:,.2f}")
print(f"Total Payment   : ₹{loan_details['total_payment']:,.2f}")
print(f"Total Interest  : ₹{loan_details['total_interest']:,.2f}")

print("\n==================================")